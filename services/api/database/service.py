from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from .models import (
    Publication, Author, Keyword, Mission, DataSource, 
    SearchIndex, User, UserFavorite, SearchLog,
    publication_authors, publication_keywords, publication_missions
)
try:
    from ..nasa_data.fetcher import NASADataFetcher
except ImportError:
    # Handle direct script execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from nasa_data.fetcher import NASADataFetcher


class DatabaseService:
    """Service for database operations"""
    
    def __init__(self, db: Session):
        self.db = db
        
    # Publication operations
    def create_publication(self, pub_data: Dict[str, Any]) -> Publication:
        """Create a new publication record"""
        
        # Check if publication already exists
        existing = self.db.query(Publication).filter(
            Publication.nasa_id == pub_data.get('nasa_id')
        ).first()
        
        if existing:
            return existing
            
        # Create publication
        publication = Publication(
            nasa_id=pub_data.get('nasa_id'),
            title=pub_data.get('title', ''),
            abstract=pub_data.get('abstract', ''),
            doi=pub_data.get('doi'),
            url=pub_data.get('url'),
            publication_date=pub_data.get('publication_date'),
            publication_year=pub_data.get('publication_year'),
            publication_type=pub_data.get('publication_type', 'unknown'),
            journal_name=pub_data.get('journal_name'),
            organism_type=self._classify_organism_type(pub_data),
            research_domain=self._classify_research_domain(pub_data)
        )
        
        self.db.add(publication)
        self.db.flush()  # Get the ID
        
        # Add authors
        self._add_authors_to_publication(publication, pub_data.get('authors', []))
        
        # Add keywords
        self._add_keywords_to_publication(publication, pub_data.get('keywords', []))
        
        # Add to search index
        self._create_search_index(publication)
        
        self.db.commit()
        return publication
    
    def get_publication(self, publication_id: int) -> Optional[Publication]:
        """Get publication by ID"""
        return self.db.query(Publication).filter(Publication.id == publication_id).first()
    
    def search_publications(
        self, 
        query: str = None, 
        filters: Dict[str, Any] = None, 
        limit: int = 20, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search publications with filters"""
        
        base_query = self.db.query(Publication)
        
        # Apply filters
        if filters:
            if filters.get('organism_type'):
                base_query = base_query.filter(Publication.organism_type == filters['organism_type'])
            if filters.get('research_domain'):
                base_query = base_query.filter(Publication.research_domain == filters['research_domain'])
            if filters.get('publication_year'):
                base_query = base_query.filter(Publication.publication_year == filters['publication_year'])
            if filters.get('publication_type'):
                base_query = base_query.filter(Publication.publication_type == filters['publication_type'])
        
        # Apply text search
        if query:
            search_filter = or_(
                Publication.title.ilike(f'%{query}%'),
                Publication.abstract.ilike(f'%{query}%')
            )
            base_query = base_query.filter(search_filter)
        
        # Get total count
        total = base_query.count()
        
        # Apply pagination and ordering
        publications = base_query.order_by(desc(Publication.publication_year)).offset(offset).limit(limit).all()
        
        return {
            'publications': publications,
            'total': total,
            'offset': offset,
            'limit': limit
        }
    
    def get_publication_stats(self) -> Dict[str, Any]:
        """Get publication statistics"""
        total_pubs = self.db.query(Publication).count()
        
        # Publications by organism type
        organism_stats = self.db.query(
            Publication.organism_type, 
            func.count(Publication.id)
        ).group_by(Publication.organism_type).all()
        
        # Publications by research domain
        domain_stats = self.db.query(
            Publication.research_domain, 
            func.count(Publication.id)
        ).group_by(Publication.research_domain).all()
        
        # Publications by year (last 10 years)
        current_year = datetime.now().year
        year_stats = self.db.query(
            Publication.publication_year, 
            func.count(Publication.id)
        ).filter(
            Publication.publication_year >= current_year - 10
        ).group_by(Publication.publication_year).order_by(Publication.publication_year).all()
        
        return {
            'total_publications': total_pubs,
            'by_organism': dict(organism_stats),
            'by_domain': dict(domain_stats),
            'by_year': dict(year_stats)
        }
    
    # NASA data ingestion
    def ingest_nasa_data(self, source_name: str, limit: int = 100) -> Dict[str, Any]:
        """Ingest data from NASA sources"""
        fetcher = NASADataFetcher()
        ingested = 0
        errors = []
        
        try:
            if source_name.lower() == 'ntrs':
                publications = fetcher.search_nasa_techreports(limit=limit)
            elif source_name.lower() == 'open_data':
                publications = fetcher.search_nasa_open_data()
            elif source_name.lower() == 'pubspace':
                publications = fetcher.search_pubspace(limit=limit)
            else:
                # Try all sources
                publications = []
                publications.extend(fetcher.search_nasa_techreports(limit=limit//3))
                publications.extend(fetcher.search_nasa_open_data())
                publications.extend(fetcher.search_pubspace(limit=limit//3))
            
            # Store publications
            for pub_data in publications:
                try:
                    # Enhance with classifications
                    pub_data['organism_type'] = fetcher.classify_organism_type(pub_data)
                    pub_data['research_domain'] = fetcher.classify_research_domain(pub_data)
                    
                    self.create_publication(pub_data)
                    ingested += 1
                except Exception as e:
                    errors.append(f"Error processing {pub_data.get('title', 'Unknown')}: {str(e)}")
            
            # Update data source record
            self._update_data_source(source_name, ingested)
            
        except Exception as e:
            errors.append(f"Error fetching from {source_name}: {str(e)}")
        
        return {
            'source': source_name,
            'ingested': ingested,
            'errors': errors,
            'timestamp': datetime.now()
        }
    
    # Helper methods
    def _add_authors_to_publication(self, publication: Publication, author_names: List[str]):
        """Add authors to publication"""
        for author_name in author_names:
            if not author_name.strip():
                continue
                
            # Find or create author
            author = self.db.query(Author).filter(Author.name == author_name.strip()).first()
            if not author:
                author = Author(name=author_name.strip())
                self.db.add(author)
                self.db.flush()
            
            # Add to publication
            if author not in publication.authors:
                publication.authors.append(author)
    
    def _add_keywords_to_publication(self, publication: Publication, keywords: List[str]):
        """Add keywords to publication"""
        for keyword_term in keywords:
            if not keyword_term.strip():
                continue
                
            # Find or create keyword
            keyword = self.db.query(Keyword).filter(Keyword.term == keyword_term.strip()).first()
            if not keyword:
                keyword = Keyword(term=keyword_term.strip())
                self.db.add(keyword)
                self.db.flush()
            
            # Increment usage count
            keyword.usage_count += 1
            
            # Add to publication
            if keyword not in publication.keywords:
                publication.keywords.append(keyword)
    
    def _create_search_index(self, publication: Publication):
        """Create search index entry for publication"""
        content = f"{publication.title} {publication.abstract or ''}"
        
        search_entry = SearchIndex(
            publication_id=publication.id,
            content=content.strip()
        )
        self.db.add(search_entry)
    
    def _classify_organism_type(self, pub_data: Dict[str, Any]) -> str:
        """Classify organism type from publication data"""
        fetcher = NASADataFetcher()
        return fetcher.classify_organism_type(pub_data)
    
    def _classify_research_domain(self, pub_data: Dict[str, Any]) -> str:
        """Classify research domain from publication data"""
        fetcher = NASADataFetcher()
        return fetcher.classify_research_domain(pub_data)
    
    def _update_data_source(self, source_name: str, records_count: int):
        """Update data source statistics"""
        data_source = self.db.query(DataSource).filter(DataSource.name == source_name).first()
        
        if not data_source:
            data_source = DataSource(
                name=source_name,
                total_records=0
            )
            self.db.add(data_source)
        
        data_source.last_sync = datetime.now()
        data_source.total_records += records_count
        
        self.db.commit()


def get_database_service(db: Session) -> DatabaseService:
    """Get database service instance"""
    return DatabaseService(db)