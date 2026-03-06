"""
Celery Tasks - Scalable Video Processing with Memory Management
NO THREADING FALLBACK - Celery only
"""
import psutil
import time
from celery import Task
from celery_app import celery, app
from __init__ import db
from models import LocationMatch, Case
import logging

logger = logging.getLogger(__name__)

# Memory threshold: 80%
MEMORY_THRESHOLD = 80
MAX_CONCURRENT_VIDEOS = 4

class MemoryAwareTask(Task):
    """Base task with memory checking"""
    def before_start(self, task_id, args, kwargs):
        """Check memory before starting"""
        while psutil.virtual_memory().percent > MEMORY_THRESHOLD:
            logger.warning(f"Memory at {psutil.virtual_memory().percent}% - pausing queue")
            time.sleep(10)

@celery.task(base=MemoryAwareTask, bind=True, max_retries=3)
def analyze_footage_match(self, match_id):
    """Analyze single footage match with smart snapshot sampling"""
    with app.app_context():
        try:
            import os
            from location_matching_engine import location_engine
            
            match = LocationMatch.query.get(match_id)
            if not match:
                return {'success': False, 'error': 'Match not found'}
            
            # Auto-create detection folder
            detection_dir = os.path.join('static', 'detections', f'match_{match_id}')
            os.makedirs(detection_dir, exist_ok=True)
            logger.info(f"Detection folder ready: {detection_dir}")
            
            match.status = 'processing'
            db.session.commit()
            
            # Check if manual_targeted for smart sampling
            frame_skip = 1 if match.match_type == 'manual_targeted' else 10
            snapshot_interval = 60 if match.match_type == 'manual_targeted' else 30  # 2 seconds at 30fps
            
            success = location_engine.analyze_footage_for_person(
                match_id, 
                frame_skip=frame_skip,
                snapshot_interval=snapshot_interval
            )
            
            return {'success': success, 'match_id': match_id}
            
        except Exception as e:
            logger.error(f"Task error for match {match_id}: {e}")
            if match:
                match.status = 'failed'
                db.session.commit()
            raise self.retry(exc=e, countdown=60)

@celery.task(base=MemoryAwareTask, bind=True)
def analyze_batch_parallel(self, case_id, footage_ids, batch_id):
    """Batch analysis with strict concurrency limit"""
    with app.app_context():
        try:
            from location_matching_engine import location_engine
            
            results = []
            for footage_id in footage_ids:
                # Check memory before each video
                if psutil.virtual_memory().percent > MEMORY_THRESHOLD:
                    logger.warning(f"Memory at {psutil.virtual_memory().percent}% - pausing")
                    time.sleep(30)
                
                match = LocationMatch.query.filter_by(
                    case_id=case_id,
                    footage_id=footage_id,
                    batch_id=batch_id
                ).first()
                
                if match:
                    match.status = 'processing'
                    db.session.commit()
                    
                    success = location_engine.analyze_footage_for_person(match.id)
                    results.append({'footage_id': footage_id, 'success': success})
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            logger.error(f"Batch analysis error: {e}")
            return {'success': False, 'error': str(e)}

@celery.task(base=MemoryAwareTask, bind=True)
def process_batch_with_progress(self, case_id, footage_ids, batch_id):
    """Batch processing with progress updates"""
    with app.app_context():
        try:
            from location_matching_engine import location_engine
            
            total = len(footage_ids)
            for idx, footage_id in enumerate(footage_ids):
                # Memory check
                if psutil.virtual_memory().percent > MEMORY_THRESHOLD:
                    logger.warning(f"Memory at {psutil.virtual_memory().percent}% - waiting")
                    time.sleep(30)
                
                # Update progress
                self.update_state(
                    state='PROGRESS',
                    meta={'current': idx + 1, 'total': total, 'percent': int((idx + 1) / total * 100)}
                )
                
                success = location_engine.analyze_with_progress(
                    case_id, footage_id, batch_id
                )
            
            return {'success': True, 'total': total}
            
        except Exception as e:
            logger.error(f"Progress batch error: {e}")
            return {'success': False, 'error': str(e)}

@celery.task(base=MemoryAwareTask, bind=True)
def process_footage_high_precision(self, case_id, footage_id, batch_id):
    """High-precision forensic analysis (0.88 threshold)"""
    with app.app_context():
        try:
            from location_matching_engine import location_engine
            
            # Check memory
            if psutil.virtual_memory().percent > MEMORY_THRESHOLD:
                logger.warning(f"Memory at {psutil.virtual_memory().percent}% - delaying")
                time.sleep(30)
            
            match = LocationMatch.query.filter_by(
                case_id=case_id,
                footage_id=footage_id,
                batch_id=batch_id
            ).first()
            
            if not match:
                match = LocationMatch(
                    case_id=case_id,
                    footage_id=footage_id,
                    batch_id=batch_id,
                    status='processing',
                    match_type='high_precision'
                )
                db.session.add(match)
                db.session.commit()
            
            # Use strict 0.88 threshold
            success = location_engine.analyze_footage_for_person(match.id)
            
            return {'success': success, 'footage_id': footage_id}
            
        except Exception as e:
            logger.error(f"HP analysis error: {e}")
            return {'success': False, 'error': str(e)}

@celery.task(base=MemoryAwareTask, bind=True)
def process_batch_high_precision(self, case_id, footage_ids, batch_id):
    """Batch high-precision analysis with memory management"""
    with app.app_context():
        try:
            results = []
            for footage_id in footage_ids:
                # Strict memory check
                while psutil.virtual_memory().percent > MEMORY_THRESHOLD:
                    logger.warning(f"Memory at {psutil.virtual_memory().percent}% - paused")
                    time.sleep(30)
                
                result = process_footage_high_precision(case_id, footage_id, batch_id)
                results.append(result)
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            logger.error(f"HP batch error: {e}")
            return {'success': False, 'error': str(e)}
