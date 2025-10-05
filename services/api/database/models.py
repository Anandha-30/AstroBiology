from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base

# Association tables for many-to-many relationships
publication_authors = Table(
    'publication_authors',
    Base.metadata,
    Column('publication_id', Integer, ForeignKey('publications.id')),
    Column('author_id', Integer, ForeignKey('authors.id'))
)

publication_keywords = Table(
    'publication_keywords',
    Base.metadata,
    Column('publication_id', Integer, ForeignKey('publications.id')),
    Column('keyword_id', Integer, ForeignKey('keywords.id'))
)

publication_missions = Table(
    'publication_missions',
    Base.metadata,
    Column('publication_id', Integer, ForeignKey('publications.id')),
    Column('mission_id', Integer, ForeignKey('missions.id'))
)

class Publication(Base):
    __tablename__ = 'publications'
    
    id = Column(Integer, primary_key=True, index=True)
    nasa_id = Column(String, unique=True, index=True)  # NASA's unique identifier
    title = Column(String, nullable=False, index=True)
    abstract = Column(Text)
    full_text = Column(Text)  # If available
    doi = Column(String, unique=True)
    url = Column(String)
    publication_date = Column(DateTime)
    publication_year = Column(Integer, index=True)
    publication_type = Column(String)  # journal, conference, report, etc.
    journal_name = Column(String)
    volume = Column(String)
    issue = Column(String)
    pages = Column(String)
    
    # Bioscience-specific fields
    organism_type = Column(String, index=True)  # Human, Plant, Microbe, etc.
    research_domain = Column(String, index=True)  # Microgravity, Radiation, etc.
    
    # AI-generated fields
    ai_summary = Column(Text)
    ai_tags = Column(Text)  # JSON string of tags
    key_takeaways = Column(Text)  # JSON string of takeaways
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_processed = Column(Boolean, default=False)  # AI processing complete
    
    # Relationships
    authors = relationship("Author", secondary=publication_authors, back_populates="publications")
    keywords = relationship("Keyword", secondary=publication_keywords, back_populates="publications")
    missions = relationship("Mission", secondary=publication_missions, back_populates="publications")

class Author(Base):
    __tablename__ = 'authors'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String)
    affiliation = Column(String)
    orcid = Column(String, unique=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    publications = relationship("Publication", secondary=publication_authors, back_populates="authors")

class Keyword(Base):
    __tablename__ = 'keywords'
    
    id = Column(Integer, primary_key=True, index=True)
    term = Column(String, nullable=False, unique=True, index=True)
    category = Column(String)  # organism, mission, domain, method, etc.
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    usage_count = Column(Integer, default=0)
    
    # Relationships
    publications = relationship("Publication", secondary=publication_keywords, back_populates="keywords")

class Mission(Base):
    __tablename__ = 'missions'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    mission_type = Column(String)  # ISS, Shuttle, Apollo, Artemis, etc.
    status = Column(String)  # active, completed, planned
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    publications = relationship("Publication", secondary=publication_missions, back_populates="missions")

class DataSource(Base):
    __tablename__ = 'data_sources'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # NASA Open Data, PubSpace, etc.
    base_url = Column(String)
    api_endpoint = Column(String)
    last_sync = Column(DateTime)
    total_records = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class SearchIndex(Base):
    __tablename__ = 'search_index'
    
    id = Column(Integer, primary_key=True, index=True)
    publication_id = Column(Integer, ForeignKey('publications.id'))
    content = Column(Text)  # Preprocessed searchable content
    embedding = Column(Text)  # JSON string of embedding vector (if using embeddings)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    publication = relationship("Publication")

# User-related tables for personalization
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    role = Column(String)  # student, researcher, admin
    interests = Column(Text)  # JSON string of interests
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

class UserFavorite(Base):
    __tablename__ = 'user_favorites'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    publication_id = Column(Integer, ForeignKey('publications.id'))
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User")
    publication = relationship("Publication")

class SearchLog(Base):
    __tablename__ = 'search_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    query = Column(String, nullable=False)
    filters = Column(Text)  # JSON string of filters applied
    results_count = Column(Integer)
    search_time = Column(Float)  # Time taken in seconds
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User")