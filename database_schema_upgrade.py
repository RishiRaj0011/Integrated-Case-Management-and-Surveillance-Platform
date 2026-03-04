"""
TASK 4: Database Schema Updates
Add 512-d vector storage + FAISS integration fields
"""

# Add these columns to existing models.py

"""
UPDATE PersonProfile Model:
"""
# Add to PersonProfile class in models.py:

# 512-d ArcFace embeddings (instead of 128-d)
master_embedding_512d = db.Column(db.Text)  # JSON array of 512-d vector
front_embedding_512d = db.Column(db.Text)
left_profile_embedding_512d = db.Column(db.Text)
right_profile_embedding_512d = db.Column(db.Text)

# Video keyframe embeddings
video_keyframe_embeddings = db.Column(db.Text)  # JSON array of embeddings

# Fusion metadata
fusion_confidence = db.Column(db.Float, default=0.0)
num_fusion_sources = db.Column(db.Integer, default=0)
view_types_used = db.Column(db.String(200))  # Comma-separated

# Liveness detection results
liveness_verified = db.Column(db.Boolean, default=False)
liveness_confidence = db.Column(db.Float, default=0.0)
liveness_details = db.Column(db.Text)  # JSON

# FAISS index reference
faiss_index_id = db.Column(db.Integer)  # Reference to FAISS index position

"""
UPDATE PersonDetection Model:
"""
# Add to PersonDetection class:

# Temporal consensus data
temporal_frame_count = db.Column(db.Integer, default=0)
temporal_start_frame = db.Column(db.Integer)
temporal_end_frame = db.Column(db.Integer)
temporal_avg_confidence = db.Column(db.Float, default=0.0)
temporal_consensus_verified = db.Column(db.Boolean, default=False)

# CCTV enhancement applied
enhancement_applied = db.Column(db.Boolean, default=False)
enhancement_type = db.Column(db.String(50))  # 'super_resolution', 'clahe', 'night_vision'

# 512-d embedding for this detection
detection_embedding_512d = db.Column(db.Text)

"""
NEW Model: FAISSIndex
"""
class FAISSIndex(db.Model):
    """FAISS vector index for fast similarity search"""
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'), nullable=False)
    person_profile_id = db.Column(db.Integer, db.ForeignKey('person_profile.id'))
    
    # Index metadata
    index_position = db.Column(db.Integer, unique=True)  # Position in FAISS index
    embedding_512d = db.Column(db.Text, nullable=False)  # JSON array
    
    # Search optimization
    embedding_norm = db.Column(db.Float)  # L2 norm for quick filtering
    quality_score = db.Column(db.Float, default=0.0)
    
    # Timestamps
    indexed_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_searched = db.Column(db.DateTime)
    search_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f"<FAISSIndex Case {self.case_id} Position {self.index_position}>"

"""
Migration Script:
"""
# Run this to add new columns:
"""
from flask import Flask
from __init__ import db, create_app

app = create_app()
with app.app_context():
    # Add columns using raw SQL
    db.engine.execute('''
        ALTER TABLE person_profile 
        ADD COLUMN master_embedding_512d TEXT,
        ADD COLUMN front_embedding_512d TEXT,
        ADD COLUMN left_profile_embedding_512d TEXT,
        ADD COLUMN right_profile_embedding_512d TEXT,
        ADD COLUMN video_keyframe_embeddings TEXT,
        ADD COLUMN fusion_confidence FLOAT DEFAULT 0.0,
        ADD COLUMN num_fusion_sources INTEGER DEFAULT 0,
        ADD COLUMN view_types_used VARCHAR(200),
        ADD COLUMN liveness_verified BOOLEAN DEFAULT FALSE,
        ADD COLUMN liveness_confidence FLOAT DEFAULT 0.0,
        ADD COLUMN liveness_details TEXT,
        ADD COLUMN faiss_index_id INTEGER
    ''')
    
    db.engine.execute('''
        ALTER TABLE person_detection
        ADD COLUMN temporal_frame_count INTEGER DEFAULT 0,
        ADD COLUMN temporal_start_frame INTEGER,
        ADD COLUMN temporal_end_frame INTEGER,
        ADD COLUMN temporal_avg_confidence FLOAT DEFAULT 0.0,
        ADD COLUMN temporal_consensus_verified BOOLEAN DEFAULT FALSE,
        ADD COLUMN enhancement_applied BOOLEAN DEFAULT FALSE,
        ADD COLUMN enhancement_type VARCHAR(50),
        ADD COLUMN detection_embedding_512d TEXT
    ''')
    
    # Create FAISS index table
    db.create_all()
    
    print("✅ Database schema updated successfully")
"""
