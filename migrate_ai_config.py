"""
Database Migration: Add AIConfig Table
Run this script to create the ai_config table
"""

from __init__ import create_app, db
from ai_config_model import AIConfig

def migrate_ai_config():
    """Create AIConfig table and initialize default settings"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create table
            db.create_all()
            print("✅ AIConfig table created successfully")
            
            # Initialize default config
            config = AIConfig.get_config()
            print(f"✅ Default AI configuration initialized:")
            print(f"   - Threshold: {config.forensic_threshold}")
            print(f"   - Facial Weight: {config.facial_weight}")
            print(f"   - Clothing Weight: {config.clothing_weight}")
            print(f"   - Temporal Weight: {config.temporal_weight}")
            print(f"   - Frame Skip: {config.frame_skip_rate}")
            print(f"   - Active Preset: {config.active_preset}")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("AI Configuration Database Migration")
    print("=" * 60)
    
    if migrate_ai_config():
        print("\n✅ Migration completed successfully!")
        print("\nYou can now access AI Settings at:")
        print("   http://localhost:5000/admin/ai-settings")
    else:
        print("\n❌ Migration failed. Check errors above.")
