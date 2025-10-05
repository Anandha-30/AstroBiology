import requests
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import re

class NASADataFetcher:
    """Fetches data from NASA's Open Data Portal and PubSpace"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AstroBio Explorer/1.0'
        })
        
        # NASA API endpoints
        self.nasa_open_data_url = "https://data.nasa.gov/api/views"
        self.nasa_techreports_url = "https://ntrs.nasa.gov/api/citations/search"
        self.pubspace_url = "https://pubspace.larc.nasa.gov/search"
        
    def search_nasa_techreports(self, query: str = "bioscience", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search NASA Technical Reports Server (NTRS)
        """
        publications = []
        
        try:
            # NTRS API parameters
            params = {
                'q': query,
                'size': limit,
                'from': 0,
                'sort': 'date_desc'
            }
            
            response = self.session.get(self.nasa_techreports_url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                
                for result in data.get('results', []):
                    pub = self._parse_ntrs_result(result)
                    if pub and self._is_bioscience_relevant(pub):
                        publications.append(pub)
                        
        except Exception as e:
            print(f"Error fetching from NTRS: {e}")
            
        return publications
    
    def search_nasa_open_data(self, keywords: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search NASA Open Data Portal for bioscience datasets
        """
        if keywords is None:
            keywords = ['bioscience', 'biology', 'life sciences', 'astrobiology', 'space biology']
            
        publications = []
        
        for keyword in keywords:
            try:
                # NASA Open Data uses CKAN API
                url = "https://data.nasa.gov/api/3/action/package_search"
                params = {
                    'q': keyword,
                    'rows': 50,
                    'sort': 'metadata_modified desc'
                }
                
                response = self.session.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    
                    for dataset in data.get('result', {}).get('results', []):
                        pub = self._parse_open_data_result(dataset)
                        if pub:
                            publications.append(pub)
                            
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"Error fetching from Open Data Portal: {e}")
                
        return publications
    
    def search_pubspace(self, query: str = "space biology", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search NASA PubSpace (simplified approach - would need to be adapted based on actual API)
        """
        publications = []
        
        try:
            # This is a simplified approach - actual PubSpace API might differ
            params = {
                'q': query,
                'limit': limit,
                'format': 'json'
            }
            
            response = self.session.get(self.pubspace_url, params=params, timeout=30)
            if response.status_code == 200:
                # Parse based on actual response format
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                
                # This would need to be adapted based on actual PubSpace API structure
                for result in data.get('results', []):
                    pub = self._parse_pubspace_result(result)
                    if pub:
                        publications.append(pub)
                        
        except Exception as e:
            print(f"Error fetching from PubSpace: {e}")
            
        return publications
    
    def _parse_ntrs_result(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse NTRS API result into standardized format"""
        try:
            return {
                'nasa_id': result.get('id'),
                'title': result.get('title', ''),
                'abstract': result.get('abstract', ''),
                'authors': [author.get('name', '') for author in result.get('authors', [])],
                'publication_date': self._parse_date(result.get('published')),
                'publication_year': self._extract_year(result.get('published')),
                'url': result.get('download', {}).get('pdf'),
                'publication_type': result.get('type', 'technical_report'),
                'source': 'NTRS',
                'keywords': result.get('keywords', []),
                'doi': result.get('doi'),
                'raw_data': result  # Store original for reference
            }
        except Exception as e:
            print(f"Error parsing NTRS result: {e}")
            return None
    
    def _parse_open_data_result(self, dataset: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse NASA Open Data result into standardized format"""
        try:
            return {
                'nasa_id': dataset.get('id'),
                'title': dataset.get('title', ''),
                'abstract': dataset.get('notes', ''),  # Description field
                'authors': [org.get('name', '') for org in dataset.get('organization', {})],
                'publication_date': self._parse_date(dataset.get('metadata_created')),
                'publication_year': self._extract_year(dataset.get('metadata_created')),
                'url': dataset.get('url'),
                'publication_type': 'dataset',
                'source': 'NASA Open Data',
                'keywords': [tag.get('name', '') for tag in dataset.get('tags', [])],
                'raw_data': dataset
            }
        except Exception as e:
            print(f"Error parsing Open Data result: {e}")
            return None
    
    def _parse_pubspace_result(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse PubSpace result into standardized format"""
        # This would need to be implemented based on actual PubSpace API structure
        try:
            return {
                'nasa_id': result.get('id'),
                'title': result.get('title', ''),
                'abstract': result.get('abstract', ''),
                'authors': result.get('authors', []),
                'publication_date': self._parse_date(result.get('date')),
                'publication_year': self._extract_year(result.get('date')),
                'url': result.get('url'),
                'publication_type': 'journal_article',
                'source': 'PubSpace',
                'doi': result.get('doi'),
                'raw_data': result
            }
        except Exception as e:
            print(f"Error parsing PubSpace result: {e}")
            return None
    
    def _is_bioscience_relevant(self, pub: Dict[str, Any]) -> bool:
        """Check if publication is relevant to bioscience research"""
        bioscience_keywords = [
            'biology', 'bioscience', 'astrobiology', 'life sciences', 'microgravity',
            'space biology', 'plant', 'human', 'microbe', 'organism', 'biomedical',
            'physiological', 'biological', 'biomedicine', 'biotechnology', 'genetics',
            'molecular biology', 'cell biology', 'radiation effects', 'bone density',
            'immune system', 'metabolism', 'growth', 'development', 'adaptation'
        ]
        
        text_to_check = f"{pub.get('title', '')} {pub.get('abstract', '')}".lower()
        
        return any(keyword in text_to_check for keyword in bioscience_keywords)
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        if not date_str:
            return None
            
        date_formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%m/%d/%Y',
            '%Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str[:len(fmt.replace('%f', '123456'))], fmt)
            except ValueError:
                continue
                
        return None
    
    def _extract_year(self, date_str: str) -> Optional[int]:
        """Extract year from date string"""
        if not date_str:
            return None
            
        # Try to find a 4-digit year
        year_match = re.search(r'(\d{4})', str(date_str))
        if year_match:
            year = int(year_match.group(1))
            if 1900 <= year <= 2030:  # Reasonable range
                return year
                
        return None
    
    def classify_organism_type(self, pub: Dict[str, Any]) -> str:
        """Classify the organism type based on content"""
        text = f"{pub.get('title', '')} {pub.get('abstract', '')}".lower()
        
        if any(word in text for word in ['human', 'astronaut', 'crew', 'personnel', 'person']):
            return 'Human'
        elif any(word in text for word in ['plant', 'arabidopsis', 'crop', 'vegetation', 'botanical']):
            return 'Plant'
        elif any(word in text for word in ['microbe', 'bacteria', 'virus', 'microbial', 'pathogen']):
            return 'Microbe'
        elif any(word in text for word in ['animal', 'mouse', 'rat', 'rodent', 'mammal']):
            return 'Animal'
        else:
            return 'Other'
    
    def classify_research_domain(self, pub: Dict[str, Any]) -> str:
        """Classify the research domain"""
        text = f"{pub.get('title', '')} {pub.get('abstract', '')}".lower()
        
        if any(word in text for word in ['microgravity', 'weightless', 'zero gravity']):
            return 'Microgravity'
        elif any(word in text for word in ['radiation', 'cosmic ray', 'solar particle']):
            return 'Radiation'
        elif any(word in text for word in ['bone', 'skeleton', 'osteo', 'density']):
            return 'Bone/Musculoskeletal'
        elif any(word in text for word in ['immune', 'immunity', 'infection']):
            return 'Immunology'
        elif any(word in text for word in ['cardiovascular', 'heart', 'circulation']):
            return 'Cardiovascular'
        elif any(word in text for word in ['psychological', 'behavior', 'stress']):
            return 'Psychology/Behavior'
        else:
            return 'General'

def get_nasa_data_fetcher() -> NASADataFetcher:
    """Get NASA data fetcher instance"""
    return NASADataFetcher()