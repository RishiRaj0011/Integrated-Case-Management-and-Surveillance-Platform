"""
Real-World CCTV Enhancements:
1. Pose-Adaptive Weighting
2. Occlusion Awareness (Mask Detection)
3. Smart Super-Resolution (Face-only)
4. Fallback Mechanism (90-97% Review)
"""
import cv2
import numpy as np
from typing import Dict, Tuple, Optional
from advanced_identity_fusion import identity_fusion

class PoseAdaptiveMatcher:
    def __init__(self):
        # Pose-based profile weights
        self.pose_weights = {
            'frontal': {'front': 0.7, 'left_profile': 0.15, 'right_profile': 0.15},
            'left_side': {'front': 0.2, 'left_profile': 0.7, 'right_profile': 0.1},
            'right_side': {'front': 0.2, 'left_profile': 0.1, 'right_profile': 0.7}
        }
        
        # Confidence thresholds
        self.THRESHOLD_AUTO_APPROVE = 0.97
        self.THRESHOLD_REVIEW = 0.90
        
    def classify_pose(self, yaw: float) -> str:
        """Classify face pose based on yaw angle"""
        if -20 <= yaw <= 20:
            return 'frontal'
        elif yaw > 20:
            return 'left_side'
        else:
            return 'right_side'
    
    def match_with_pose_adaptation(self, cctv_face_data: Dict, 
                                   master_embeddings: Dict) -> Dict:
        """
        Match CCTV face with pose-adaptive weighting
        
        Args:
            cctv_face_data: {'embedding': np.ndarray, 'pose': {'yaw': float}}
            master_embeddings: {'front': np.ndarray, 'left_profile': np.ndarray, 'right_profile': np.ndarray}
        
        Returns:
            Match result with confidence and review status
        """
        yaw = cctv_face_data['pose']['yaw']
        pose_category = self.classify_pose(yaw)
        weights = self.pose_weights[pose_category]
        
        # Calculate weighted similarity
        total_similarity = 0.0
        total_weight = 0.0
        
        for view_type, weight in weights.items():
            if view_type in master_embeddings and master_embeddings[view_type] is not None:
                similarity = identity_fusion.compare_embeddings(
                    cctv_face_data['embedding'],
                    master_embeddings[view_type]
                )
                total_similarity += similarity * weight
                total_weight += weight
        
        final_confidence = total_similarity / total_weight if total_weight > 0 else 0.0
        
        # Determine status
        if final_confidence >= self.THRESHOLD_AUTO_APPROVE:
            status = 'AUTO_CONFIRMED'
        elif final_confidence >= self.THRESHOLD_REVIEW:
            status = 'FLAGGED_FOR_REVIEW'
        else:
            status = 'REJECTED'
        
        return {
            'confidence': final_confidence,
            'status': status,
            'pose_category': pose_category,
            'weights_used': weights,
            'yaw_angle': yaw
        }


class OcclusionAwareMatcher:
    """Handle partial face matching (masks, occlusions)"""
    
    def __init__(self):
        self.face_regions = {
            'eyes': (0.2, 0.4),      # Top 20-40% of face
            'nose': (0.35, 0.55),    # Middle 35-55%
            'mouth': (0.55, 0.8),    # Bottom 55-80%
            'forehead': (0.0, 0.25)  # Top 0-25%
        }
    
    def detect_occlusion(self, face_image: np.ndarray) -> Dict:
        """
        Detect which parts of face are occluded
        Simple approach: Check pixel variance in each region
        """
        h, w = face_image.shape[:2]
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY) if len(face_image.shape) == 3 else face_image
        
        occlusion_map = {}
        
        for region_name, (top_ratio, bottom_ratio) in self.face_regions.items():
            top = int(h * top_ratio)
            bottom = int(h * bottom_ratio)
            region = gray[top:bottom, :]
            
            # Low variance = likely occluded
            variance = np.var(region)
            is_occluded = variance < 100  # Threshold for occlusion
            
            occlusion_map[region_name] = {
                'occluded': is_occluded,
                'variance': float(variance)
            }
        
        return occlusion_map
    
    def extract_partial_embedding(self, face_image: np.ndarray, 
                                  visible_regions: list) -> Optional[np.ndarray]:
        """
        Extract embedding from visible face regions only
        Focus on eyes/forehead if mouth is covered
        """
        h, w = face_image.shape[:2]
        
        # Create mask for visible regions
        mask = np.zeros((h, w), dtype=np.uint8)
        
        for region in visible_regions:
            if region in self.face_regions:
                top_ratio, bottom_ratio = self.face_regions[region]
                top = int(h * top_ratio)
                bottom = int(h * bottom_ratio)
                mask[top:bottom, :] = 255
        
        # Apply mask
        masked_face = cv2.bitwise_and(face_image, face_image, mask=mask)
        
        # Extract embedding from masked face
        try:
            faces = identity_fusion.app.get(masked_face)
            if faces:
                return faces[0].embedding
        except:
            pass
        
        return None
    
    def match_with_occlusion(self, cctv_face: np.ndarray, 
                            master_embedding: np.ndarray) -> Dict:
        """Match considering occlusions"""
        
        # Detect occlusions
        occlusion_map = self.detect_occlusion(cctv_face)
        
        # Find visible regions
        visible_regions = [region for region, data in occlusion_map.items() 
                          if not data['occluded']]
        
        # If mouth occluded but eyes visible, still attempt match
        if occlusion_map['mouth']['occluded'] and not occlusion_map['eyes']['occluded']:
            partial_emb = self.extract_partial_embedding(cctv_face, visible_regions)
            
            if partial_emb is not None:
                similarity = identity_fusion.compare_embeddings(partial_emb, master_embedding)
                
                return {
                    'confidence': similarity * 0.9,  # Slight penalty for occlusion
                    'occlusion_detected': True,
                    'visible_regions': visible_regions,
                    'match_type': 'partial_face'
                }
        
        # Full face match
        try:
            faces = identity_fusion.app.get(cctv_face)
            if faces:
                similarity = identity_fusion.compare_embeddings(faces[0].embedding, master_embedding)
                return {
                    'confidence': similarity,
                    'occlusion_detected': False,
                    'match_type': 'full_face'
                }
        except:
            pass
        
        return {'confidence': 0.0, 'occlusion_detected': True, 'match_type': 'failed'}


class SmartSuperResolution:
    """Apply super-resolution only to face bounding boxes"""
    
    def __init__(self):
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    
    def enhance_face_only(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Apply super-resolution only to detected face region
        Saves GPU memory and processing time
        
        Args:
            frame: Full CCTV frame
            bbox: (x, y, w, h) face bounding box
        
        Returns:
            Enhanced face region
        """
        x, y, w, h = bbox
        
        # Extract face region with padding
        padding = 20
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(frame.shape[1], x + w + padding)
        y2 = min(frame.shape[0], y + h + padding)
        
        face_region = frame[y1:y2, x1:x2]
        
        # Super-resolution (2x upscale)
        h_face, w_face = face_region.shape[:2]
        upscaled = cv2.resize(face_region, (w_face * 2, h_face * 2), 
                             interpolation=cv2.INTER_CUBIC)
        
        # CLAHE enhancement
        if len(upscaled.shape) == 3:
            lab = cv2.cvtColor(upscaled, cv2.COLOR_BGR2LAB)
            lab[:, :, 0] = self.clahe.apply(lab[:, :, 0])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            enhanced = self.clahe.apply(upscaled)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
        
        return denoised
    
    def process_cctv_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, list]:
        """
        Process CCTV frame: detect faces, enhance only face regions
        
        Returns:
            (original_frame, list of enhanced face regions with bboxes)
        """
        # Detect faces
        faces = identity_fusion.app.get(frame)
        
        enhanced_faces = []
        for face in faces:
            bbox = face.bbox.astype(int)
            x, y, x2, y2 = bbox
            w, h = x2 - x, y2 - y
            
            # Enhance this face only
            enhanced_face = self.enhance_face_only(frame, (x, y, w, h))
            
            enhanced_faces.append({
                'enhanced_region': enhanced_face,
                'bbox': (x, y, w, h),
                'original_bbox': bbox
            })
        
        return frame, enhanced_faces


# Global instances
pose_adaptive_matcher = PoseAdaptiveMatcher()
occlusion_matcher = OcclusionAwareMatcher()
smart_sr = SmartSuperResolution()
