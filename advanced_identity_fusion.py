"""
TASK 1: Multi-Angle Identity Fusion with InsightFace (ArcFace)
512-d embeddings + View-Aware Fusion + Video Key-Frame Selection
"""
import cv2
import numpy as np
from insightface.app import FaceAnalysis
from insightface.model_zoo import get_model
import os
from typing import List, Dict, Tuple, Optional
import json

class AdvancedIdentityFusion:
    def __init__(self):
        # Initialize InsightFace with ArcFace model
        self.app = FaceAnalysis(providers=['CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        
        # View weights for fusion
        self.view_weights = {
            'front': 0.5,      # 50% weight
            'left_profile': 0.25,   # 25% weight
            'right_profile': 0.25   # 25% weight
        }
        
        # Head pose thresholds (degrees)
        self.pose_thresholds = {
            'front': {'yaw': (-15, 15), 'pitch': (-15, 15)},
            'left_profile': {'yaw': (30, 60), 'pitch': (-15, 15)},
            'right_profile': {'yaw': (-60, -30), 'pitch': (-15, 15)}
        }
    
    def extract_512d_embedding(self, image_path: str) -> Optional[Dict]:
        """Extract 512-d ArcFace embedding with pose estimation"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return None
            
            faces = self.app.get(img)
            if not faces:
                return None
            
            # Get best face (largest)
            face = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
            
            return {
                'embedding': face.embedding,  # 512-d vector
                'bbox': face.bbox.tolist(),
                'det_score': float(face.det_score),
                'pose': {
                    'yaw': float(face.pose[0]) if hasattr(face, 'pose') else 0.0,
                    'pitch': float(face.pose[1]) if hasattr(face, 'pose') else 0.0,
                    'roll': float(face.pose[2]) if hasattr(face, 'pose') else 0.0
                },
                'quality': float(face.det_score)
            }
        except Exception as e:
            print(f"Error extracting embedding: {e}")
            return None
    
    def classify_view_type(self, pose: Dict) -> str:
        """Classify face view based on head pose"""
        yaw = pose['yaw']
        pitch = pose['pitch']
        
        # Front view
        if self.pose_thresholds['front']['yaw'][0] <= yaw <= self.pose_thresholds['front']['yaw'][1]:
            return 'front'
        
        # Left profile
        elif self.pose_thresholds['left_profile']['yaw'][0] <= yaw <= self.pose_thresholds['left_profile']['yaw'][1]:
            return 'left_profile'
        
        # Right profile
        elif self.pose_thresholds['right_profile']['yaw'][0] <= yaw <= self.pose_thresholds['right_profile']['yaw'][1]:
            return 'right_profile'
        
        # Default to front if ambiguous
        return 'front'
    
    def extract_video_keyframes(self, video_path: str, max_frames: int = 5) -> List[Dict]:
        """Extract best 5 frames from video using pose diversity"""
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Sample frames
            sample_interval = max(1, total_frames // 50)
            keyframes = []
            
            frame_idx = 0
            while cap.isOpened() and len(keyframes) < max_frames * 3:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_idx % sample_interval == 0:
                    faces = self.app.get(frame)
                    if faces:
                        face = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
                        
                        keyframes.append({
                            'frame_idx': frame_idx,
                            'embedding': face.embedding,
                            'pose': {
                                'yaw': float(face.pose[0]) if hasattr(face, 'pose') else 0.0,
                                'pitch': float(face.pose[1]) if hasattr(face, 'pose') else 0.0,
                                'roll': float(face.pose[2]) if hasattr(face, 'pose') else 0.0
                            },
                            'quality': float(face.det_score),
                            'frame': frame
                        })
                
                frame_idx += 1
            
            cap.release()
            
            # Select best 5 frames with diverse poses
            selected = self._select_diverse_keyframes(keyframes, max_frames)
            return selected
            
        except Exception as e:
            print(f"Error extracting keyframes: {e}")
            return []
    
    def _select_diverse_keyframes(self, keyframes: List[Dict], max_frames: int) -> List[Dict]:
        """Select diverse keyframes covering different angles"""
        if len(keyframes) <= max_frames:
            return keyframes
        
        # Sort by quality
        keyframes.sort(key=lambda x: x['quality'], reverse=True)
        
        # Select frames with diverse poses
        selected = []
        pose_bins = {'front': [], 'left': [], 'right': []}
        
        for kf in keyframes:
            yaw = kf['pose']['yaw']
            if -15 <= yaw <= 15:
                pose_bins['front'].append(kf)
            elif yaw > 15:
                pose_bins['left'].append(kf)
            else:
                pose_bins['right'].append(kf)
        
        # Take best from each bin
        for bin_name in ['front', 'left', 'right']:
            if pose_bins[bin_name]:
                selected.append(pose_bins[bin_name][0])
        
        # Fill remaining with highest quality
        remaining = [kf for kf in keyframes if kf not in selected]
        selected.extend(remaining[:max_frames - len(selected)])
        
        return selected[:max_frames]
    
    def create_master_identity_vector(self, photo_embeddings: Dict[str, np.ndarray], 
                                     video_keyframes: List[Dict] = None) -> Dict:
        """
        Create Master Identity Vector with view-aware fusion
        
        Args:
            photo_embeddings: {'front': embedding, 'left_profile': embedding, 'right_profile': embedding}
            video_keyframes: List of keyframe data with embeddings
        
        Returns:
            Master identity vector with metadata
        """
        all_embeddings = []
        all_weights = []
        
        # Add photo embeddings with view weights
        for view_type, embedding in photo_embeddings.items():
            if embedding is not None:
                all_embeddings.append(embedding)
                all_weights.append(self.view_weights.get(view_type, 0.33))
        
        # Add video keyframe embeddings (equal weight distribution)
        if video_keyframes:
            video_weight = 0.2 / len(video_keyframes)  # 20% total for video
            for kf in video_keyframes:
                all_embeddings.append(kf['embedding'])
                all_weights.append(video_weight)
        
        if not all_embeddings:
            return None
        
        # Normalize weights
        all_weights = np.array(all_weights)
        all_weights = all_weights / all_weights.sum()
        
        # Weighted fusion
        master_vector = np.average(all_embeddings, axis=0, weights=all_weights)
        
        # L2 normalization
        master_vector = master_vector / np.linalg.norm(master_vector)
        
        return {
            'master_embedding': master_vector,
            'num_sources': len(all_embeddings),
            'photo_views': list(photo_embeddings.keys()),
            'video_frames': len(video_keyframes) if video_keyframes else 0,
            'confidence': self._calculate_fusion_confidence(all_embeddings)
        }
    
    def _calculate_fusion_confidence(self, embeddings: List[np.ndarray]) -> float:
        """Calculate confidence based on embedding consistency"""
        if len(embeddings) < 2:
            return 0.8
        
        # Calculate pairwise similarities
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                sim = np.dot(embeddings[i], embeddings[j])
                similarities.append(sim)
        
        avg_similarity = np.mean(similarities)
        return float(min(1.0, avg_similarity))
    
    def compare_embeddings(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Compare two 512-d embeddings using cosine similarity"""
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)

# Global instance
identity_fusion = AdvancedIdentityFusion()
