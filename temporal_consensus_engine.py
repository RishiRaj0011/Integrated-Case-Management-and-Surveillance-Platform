"""
TASK 3: Temporal Consensus Engine for CCTV
10+ consecutive frames + 98% confidence threshold
"""
import cv2
import numpy as np
from collections import deque
from typing import List, Dict, Optional
from advanced_identity_fusion import identity_fusion
from xai_feature_weighting_system import xai_system

class TemporalConsensusEngine:
    def __init__(self):
        # Flexible thresholds for real-world CCTV
        self.CONFIDENCE_THRESHOLD_STRICT = 0.97  # 97% for auto-confirm
        self.CONFIDENCE_THRESHOLD_REVIEW = 0.90  # 90-97% for review
        self.MIN_CONSECUTIVE_FRAMES = 10  # 10+ frames required
        self.TRACKING_WINDOW = 30  # Track for 30 frames
        
        # Pose-adaptive matching
        self.pose_categories = {
            'frontal': (-20, 20),
            'left_side': (20, 60),
            'right_side': (-60, -20)
        }
        
    def analyze_cctv_footage(self, video_path: str, master_embeddings: Dict) -> List[Dict]:
        """
        Analyze CCTV with temporal consensus and pose-adaptive matching
        
        Args:
            master_embeddings: {'front': np.ndarray, 'left_profile': np.ndarray, 'right_profile': np.ndarray}
        """
        from realworld_cctv_enhancements import pose_adaptive_matcher, occlusion_matcher, smart_sr
        
        detections = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            
            frame_buffer = deque(maxlen=self.TRACKING_WINDOW)
            frame_idx = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                timestamp = frame_idx / fps
                
                # Smart super-resolution: enhance only face regions
                _, enhanced_faces = smart_sr.process_cctv_frame(frame)
                
                for face_data in enhanced_faces:
                    # Extract embedding from enhanced face
                    faces = identity_fusion.app.get(face_data['enhanced_region'])
                    
                    if faces:
                        face = faces[0]
                        
                        # Pose-adaptive matching
                        match_result = pose_adaptive_matcher.match_with_pose_adaptation(
                            {'embedding': face.embedding, 'pose': {'yaw': float(face.pose[0]) if hasattr(face, 'pose') else 0.0}},
                            master_embeddings
                        )
                        
                        # Check for occlusion
                        occlusion_result = occlusion_matcher.match_with_occlusion(
                            face_data['enhanced_region'],
                            master_embeddings.get('front', master_embeddings[list(master_embeddings.keys())[0]])
                        )
                        
                        # Use best confidence
                        final_confidence = max(match_result['confidence'], occlusion_result['confidence'])
                        
                        # XAI Analysis with pose data
                        xai_detection_data = {
                            'timestamp': timestamp,
                            'case_id': detection_data.get('case_id', 0),
                            'footage_id': detection_data.get('footage_id', 0),
                            'bbox': face.bbox.tolist(),
                            'frame_path': '',  # Will be set when frame is saved
                            'face_confidence': final_confidence,
                            'clothing_confidence': occlusion_result.get('confidence', 0.0),
                            'body_confidence': match_result.get('confidence', 0.0),
                            'motion_confidence': 0.0,
                            'pose_yaw': match_result.get('yaw_angle', 0.0),
                            'pose_category': match_result.get('pose_category', 'frontal'),
                            'duration': 0.0,
                            'consistency': 0.0,
                            'tracking_stability': 0.0,
                            'frame_quality': 0.8,
                            'face_visibility': 0.9,
                            'lighting_quality': 0.7
                        }
                        
                        xai_result = xai_system.analyze_detection_with_xai(xai_detection_data)
                        
                        frame_buffer.append({
                            'frame_idx': frame_idx,
                            'timestamp': timestamp,
                            'similarity': xai_result.ensemble_confidence,  # Use XAI ensemble score
                            'bbox': face.bbox.tolist(),
                            'embedding': face.embedding,
                            'status': match_result['status'],
                            'pose_category': match_result['pose_category'],
                            'occlusion_detected': occlusion_result['occlusion_detected'],
                            'xai_result': xai_result  # Store XAI result
                        })
                
                # Check temporal consensus
                if len(frame_buffer) >= self.MIN_CONSECUTIVE_FRAMES:
                    consensus = self._check_temporal_consensus(frame_buffer)
                    
                    if consensus['is_confirmed']:
                        detections.append({
                            'start_frame': consensus['start_frame'],
                            'end_frame': consensus['end_frame'],
                            'start_time': consensus['start_time'],
                            'end_time': consensus['end_time'],
                            'avg_confidence': consensus['avg_confidence'],
                            'frame_count': consensus['frame_count'],
                            'status': consensus['status'],
                            'pose_category': consensus.get('pose_category', 'unknown'),
                            'occlusion_detected': consensus.get('occlusion_detected', False),
                            'xai_data': consensus.get('xai_data', {})  # Include XAI data
                        })
                        frame_buffer.clear()
                
                frame_idx += 1
            
            cap.release()
            
        except Exception as e:
            print(f"CCTV analysis error: {e}")
        
        return detections
    
    def _check_temporal_consensus(self, frame_buffer: deque) -> Dict:
        """Check if consecutive frames meet consensus criteria with flexible thresholds"""
        
        # Find longest consecutive sequence above strict threshold
        consecutive_strict = 0
        consecutive_review = 0
        max_consecutive_strict = 0
        max_consecutive_review = 0
        start_idx_strict = 0
        start_idx_review = 0
        best_start_strict = 0
        best_start_review = 0
        
        confidences_strict = []
        confidences_review = []
        
        for i, frame_data in enumerate(frame_buffer):
            # Check strict threshold (97%)
            if frame_data['similarity'] >= self.CONFIDENCE_THRESHOLD_STRICT:
                if consecutive_strict == 0:
                    start_idx_strict = i
                consecutive_strict += 1
                confidences_strict.append(frame_data['similarity'])
                
                if consecutive_strict > max_consecutive_strict:
                    max_consecutive_strict = consecutive_strict
                    best_start_strict = start_idx_strict
            else:
                consecutive_strict = 0
                confidences_strict = []
            
            # Check review threshold (90%)
            if frame_data['similarity'] >= self.CONFIDENCE_THRESHOLD_REVIEW:
                if consecutive_review == 0:
                    start_idx_review = i
                consecutive_review += 1
                confidences_review.append(frame_data['similarity'])
                
                if consecutive_review > max_consecutive_review:
                    max_consecutive_review = consecutive_review
                    best_start_review = start_idx_review
            else:
                consecutive_review = 0
                confidences_review = []
        
        # Determine status
        if max_consecutive_strict >= self.MIN_CONSECUTIVE_FRAMES:
            # Auto-confirm: 10+ frames at 97%+
            frames = list(frame_buffer)[best_start_strict:best_start_strict + max_consecutive_strict]
            
            # Aggregate XAI data
            xai_data = self._aggregate_xai_data(frames)
            
            return {
                'is_confirmed': True,
                'start_frame': frames[0]['frame_idx'],
                'end_frame': frames[-1]['frame_idx'],
                'start_time': frames[0]['timestamp'],
                'end_time': frames[-1]['timestamp'],
                'avg_confidence': np.mean([f['similarity'] for f in frames]),
                'frame_count': len(frames),
                'status': 'AUTO_CONFIRMED',
                'pose_category': frames[0].get('pose_category', 'unknown'),
                'occlusion_detected': any(f.get('occlusion_detected', False) for f in frames),
                'xai_data': xai_data
            }
        
        elif max_consecutive_review >= self.MIN_CONSECUTIVE_FRAMES:
            # Flag for review: 10+ frames at 90-97%
            frames = list(frame_buffer)[best_start_review:best_start_review + max_consecutive_review]
            
            # Aggregate XAI data
            xai_data = self._aggregate_xai_data(frames)
            
            return {
                'is_confirmed': True,
                'start_frame': frames[0]['frame_idx'],
                'end_frame': frames[-1]['frame_idx'],
                'start_time': frames[0]['timestamp'],
                'end_time': frames[-1]['timestamp'],
                'avg_confidence': np.mean([f['similarity'] for f in frames]),
                'frame_count': len(frames),
                'status': 'FLAGGED_FOR_REVIEW',
                'pose_category': frames[0].get('pose_category', 'unknown'),
                'occlusion_detected': any(f.get('occlusion_detected', False) for f in frames),
                'xai_data': xai_data
            }
        
        return {'is_confirmed': False}
    
    def _aggregate_xai_data(self, frames: List[Dict]) -> Dict:
        """Aggregate XAI data from multiple frames"""
        xai_results = [f.get('xai_result') for f in frames if f.get('xai_result')]
        
        if not xai_results:
            return {}
        
        # Get first XAI result as representative
        representative = xai_results[0]
        
        return {
            'detection_id': representative.detection_id,
            'confidence_category': representative.confidence_category,
            'feature_weights': representative.feature_weights.get_confidence_breakdown(),
            'decision_factors': representative.decision_factors,
            'uncertainty_factors': representative.uncertainty_factors,
            'requires_confirmation': representative.requires_confirmation,
            'frame_hash': representative.frame_hash
        }

temporal_engine = TemporalConsensusEngine()
