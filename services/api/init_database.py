#!/usr/bin/env python3
"""
Database initialization script for AstroBio Explorer

This script:
1. Creates all database tables
2. Seeds the database with sample NASA data
3. Sets up basic missions and data sources
"""

import sys
import os
from pathlib import Path

# Add the services/api directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from database import create_tables, get_database, SessionLocal
from database.models import Mission, DataSource
from database.service import get_database_service
from nasa_data.fetcher import get_nasa_data_fetcher
from datetime import datetime


def init_missions(db_session):
    """Initialize common space missions"""
    missions = [
        {
            'name': 'ISS',
            'description': 'International Space Station - ongoing laboratory in low Earth orbit',
            'mission_type': 'Space Station',
            'status': 'active',
            'start_date': datetime(1998, 11, 20)
        },
        {
            'name': 'Apollo',
            'description': 'Apollo lunar exploration program',
            'mission_type': 'Lunar',
            'status': 'completed',
            'start_date': datetime(1969, 7, 16),
            'end_date': datetime(1975, 7, 24)
        },
        {
            'name': 'Shuttle',
            'description': 'Space Shuttle program',
            'mission_type': 'Transport',
            'status': 'completed',
            'start_date': datetime(1981, 4, 12),
            'end_date': datetime(2011, 7, 21)
        },
        {
            'name': 'Artemis',
            'description': 'Artemis lunar exploration program',
            'mission_type': 'Lunar',
            'status': 'planned',
            'start_date': datetime(2024, 1, 1)
        }
    ]
    
    for mission_data in missions:
        existing = db_session.query(Mission).filter(Mission.name == mission_data['name']).first()
        if not existing:
            mission = Mission(**mission_data)
            db_session.add(mission)
            print(f"Added mission: {mission_data['name']}")
    
    db_session.commit()


def init_data_sources(db_session):
    """Initialize NASA data sources"""
    sources = [
        {
            'name': 'NTRS',
            'base_url': 'https://ntrs.nasa.gov',
            'api_endpoint': 'https://ntrs.nasa.gov/api/citations/search',
            'is_active': True
        },
        {
            'name': 'NASA Open Data',
            'base_url': 'https://data.nasa.gov',
            'api_endpoint': 'https://data.nasa.gov/api/3/action/package_search',
            'is_active': True
        },
        {
            'name': 'PubSpace',
            'base_url': 'https://pubspace.larc.nasa.gov',
            'api_endpoint': 'https://pubspace.larc.nasa.gov/search',
            'is_active': True
        }
    ]
    
    for source_data in sources:
        existing = db_session.query(DataSource).filter(DataSource.name == source_data['name']).first()
        if not existing:
            source = DataSource(**source_data)
            db_session.add(source)
            print(f"Added data source: {source_data['name']}")
    
    db_session.commit()


def seed_sample_publications(db_session):
    """Add some sample publications for testing"""
    db_service = get_database_service(db_session)
    
    # Sample publications based on the original demo corpus
    sample_pubs = [
        {
            'nasa_id': 'sample-1',
            'title': 'Microgravity Effects on Human Bone Density',
            'abstract': 'Microgravity accelerates bone density loss in astronauts. Countermeasures include resistance exercise and nutritional interventions.',
            'authors': ['Smith, J.', 'Johnson, M.'],
            'publication_year': 2014,
            'publication_type': 'journal_article',
            'source': 'Sample Data',
            'keywords': ['microgravity', 'bone density', 'astronauts', 'exercise']
        },
        {
            'nasa_id': 'sample-2',
            'title': 'Plant Growth Dynamics in Spaceflight',
            'abstract': 'Arabidopsis exhibits altered root morphology and gene expression in microgravity. Light directionality affects auxin transport and growth.',
            'authors': ['Davis, K.', 'Wilson, P.'],
            'publication_year': 2018,
            'publication_type': 'journal_article',
            'source': 'Sample Data',
            'keywords': ['arabidopsis', 'microgravity', 'plant growth', 'auxin']
        },
        {
            'nasa_id': 'sample-3',
            'title': 'Immune Response Modulation under Space Conditions',
            'abstract': 'Spaceflight suppresses certain immune pathways while upregulating stress responses. Findings inform crew health risk assessments.',
            'authors': ['Brown, L.', 'Taylor, R.'],
            'publication_year': 2019,
            'publication_type': 'technical_report',
            'source': 'Sample Data',
            'keywords': ['immune response', 'spaceflight', 'stress', 'crew health']
        }
    ]
    
    for pub_data in sample_pubs:
        try:
            publication = db_service.create_publication(pub_data)
            print(f"Added sample publication: {publication.title}")
        except Exception as e:
            print(f"Error adding sample publication: {e}")


def main():
    """Main initialization function"""
    print("Initializing AstroBio Explorer database...")
    
    # Create tables
    print("Creating database tables...")
    create_tables()
    print("✓ Database tables created")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Initialize reference data
        print("Initializing missions...")
        init_missions(db)
        print("✓ Missions initialized")
        
        print("Initializing data sources...")
        init_data_sources(db)
        print("✓ Data sources initialized")
        
        print("Adding sample publications...")
        seed_sample_publications(db)
        print("✓ Sample publications added")
        
        print("\n🎉 Database initialization complete!")
        print("\nYou can now:")
        print("1. Start the API server: uvicorn main:app --reload")
        print("2. Ingest NASA data via: POST /nasa-data/ingest")
        print("3. View stats at: GET /nasa-data/stats")
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()