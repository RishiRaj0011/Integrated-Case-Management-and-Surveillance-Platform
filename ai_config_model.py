"""AI Configuration Model for Dynamic Settings"""
from __init__ import db
from datetime import datetime

class AIConfig(db.Model):
    """Dynamic AI configuration settings"""
    __tablename__ = 'ai_config'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Detection Thresholds
    forensic_threshold = db.Column(db.Float, default=0.88, nullable=False)
    min_threshold = db.Column(db.Float, default=0.50, nullable=False)
    max_threshold = db.Column(db.Float, default=0.99, nullable=False)
    
    # XAI Feature Weights (must sum to 1.0)
    facial_weight = db.Column(db.Float, default=0.40, nullable=False)
    clothing_weight = db.Column(db.Float, default=0.35, nullable=False)
    temporal_weight = db.Column(db.Float, default=0.25, nullable=False)
    
    # Performance Settings
    frame_skip_rate = db.Column(db.Integer, default=10, nullable=False)
    max_frames_per_video = db.Column(db.Integer, default=1000, nullable=False)
    
    # Active Preset
    active_preset = db.Column(db.String(30), default='surveillance', nullable=False)
    
    # Metadata
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AIConfig Preset:{self.active_preset} Threshold:{self.forensic_threshold}>"
    
    @staticmethod
    def get_config():
        """Get current AI configuration (singleton pattern)"""
        config = AIConfig.query.first()
        if not config:
            config = AIConfig()
            db.session.add(config)
            db.session.commit()
        return config
    
    @staticmethod
    def apply_preset(preset_name):
        """Apply predefined preset configurations"""
        config = AIConfig.get_config()
        
        presets = {
            'forensic': {
                'forensic_threshold': 0.92,
                'facial_weight': 0.70,
                'clothing_weight': 0.20,
                'temporal_weight': 0.10,
                'frame_skip_rate': 1,
                'active_preset': 'forensic'
            },
            'surveillance': {
                'forensic_threshold': 0.88,
                'facial_weight': 0.40,
                'clothing_weight': 0.35,
                'temporal_weight': 0.25,
                'frame_skip_rate': 10,
                'active_preset': 'surveillance'
            },
            'fast_scan': {
                'forensic_threshold': 0.75,
                'facial_weight': 0.50,
                'clothing_weight': 0.30,
                'temporal_weight': 0.20,
                'frame_skip_rate': 30,
                'active_preset': 'fast_scan'
            }
        }
        
        if preset_name in presets:
            for key, value in presets[preset_name].items():
                setattr(config, key, value)
            db.session.commit()
            return True
        return False
    
    def validate_weights(self):
        """Ensure weights sum to 1.0"""
        total = self.facial_weight + self.clothing_weight + self.temporal_weight
        if abs(total - 1.0) > 0.01:
            # Auto-normalize
            self.facial_weight /= total
            self.clothing_weight /= total
            self.temporal_weight /= total
    
    def validate_threshold(self):
        """Ensure threshold is within bounds"""
        if self.forensic_threshold < self.min_threshold:
            self.forensic_threshold = self.min_threshold
        if self.forensic_threshold > self.max_threshold:
            self.forensic_threshold = self.max_threshold
