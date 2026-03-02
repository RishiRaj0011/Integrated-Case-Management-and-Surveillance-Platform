"""
FAISS Index Migration Script
Rebuilds the FAISS index from IndexFlatIP to IndexIVFFlat for 10x faster search
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from __init__ import create_app, db
from models import PersonProfile
from vector_search_service import get_face_search_service
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_faiss_index():
    """Migrate FAISS index to new IVF implementation"""
    app = create_app()
    
    with app.app_context():
        logger.info("="*60)
        logger.info("FAISS Index Migration - IndexFlatIP → IndexIVFFlat")
        logger.info("="*60)
        
        try:
            # Get all person profiles
            logger.info("Fetching person profiles from database...")
            profiles = PersonProfile.query.all()
            logger.info(f"Found {len(profiles)} person profiles")
            
            if len(profiles) == 0:
                logger.warning("No person profiles found. Nothing to migrate.")
                return
            
            # Get FAISS service
            logger.info("Initializing FAISS service...")
            service = get_face_search_service()
            
            # Rebuild index
            logger.info("Rebuilding FAISS index with IVF implementation...")
            service.rebuild_from_database(profiles)
            
            # Verify
            index_size = service.get_index_size()
            logger.info(f"✅ Migration complete! Index size: {index_size} encodings")
            
            # Performance info
            if index_size > 10000:
                logger.info(f"🚀 Expected search speedup: ~10x faster")
            else:
                logger.info(f"ℹ️  For datasets >10k faces, you'll see significant speedup")
            
            logger.info("="*60)
            logger.info("Migration successful!")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {str(e)}")
            logger.error("Please check the error and try again")
            raise

if __name__ == "__main__":
    logger.info("Starting FAISS index migration...")
    migrate_faiss_index()
    logger.info("Migration script completed")
