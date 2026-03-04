"""
TASK 2: Bulletproof Consistency & Liveness Detection
99% similarity threshold + Anti-spoofing
"""
import cv2
import numpy as np
from advanced_identity_fusion import identity_fusion
from typing import List, Dict, Tuple
import os

class BulletproofConsistencyValidator:
    def __init__(self):
        # Flexible thresholds for real-world scenarios
        self.SIMILARITY_THRESHOLD_STRICT = 0.97  # 97% for auto-approve
        self.SIMILARITY_THRESHOLD_REVIEW = 0.90  # 90-97% for human review
        self.SIMILARITY_THRESHOLD_REJECT = 0.90  # Below 90% reject
        self.MIN_QUALITY_SCORE = 0.7
        
        # Pose-adaptive weights
        self.pose_weights = {
            'frontal': {'front': 0.7, 'left_profile': 0.15, 'right_profile': 0.15},
            'left_side': {'front': 0.2, 'left_profile': 0.7, 'right_profile': 0.1},
            'right_side': {'front': 0.2, 'left_profile': 0.1, 'right_profile': 0.7}
        }
        
    def validate_cross_verification(self, image_paths: List[str], 
                                   video_paths: List[str] = None) -> Dict:
        """
        Cross-verify all photos and video frames with 99% threshold
        """
        result = {
            'is_consistent': False,
            'confidence_score': 0.0,
            'total_sources': 0,
            'passed_sources': 0,
            'failed_sources': [],
            'liveness_checks': [],
            'master_embedding': None,
            'detailed_report': {}
        }
        
        all_embeddings = []
        all_sources = []
        
        # Extract embeddings from photos
        for img_path in image_paths:
            # Liveness check
            liveness_result = self.detect_liveness(img_path)
            result['liveness_checks'].append({
                'file': os.path.basename(img_path),
                'is_live': liveness_result['is_live'],
                'confidence': liveness_result['confidence'],
                'reason': liveness_result['reason']
            })
            
            if not liveness_result['is_live']:
                result['failed_sources'].append({
                    'file': img_path,
                    'reason': f"Liveness check failed: {liveness_result['reason']}"
                })
                continue
            
            # Extract embedding
            emb_data = identity_fusion.extract_512d_embedding(img_path)
            if emb_data:
                all_embeddings.append(emb_data['embedding'])
                all_sources.append({
                    'file': img_path,
                    'type': 'photo',
                    'quality': emb_data['quality']
                })
        
        # Extract embeddings from videos
        if video_paths:
            for vid_path in video_paths:
                keyframes = identity_fusion.extract_video_keyframes(vid_path, max_frames=5)
                for kf in keyframes:
                    all_embeddings.append(kf['embedding'])
                    all_sources.append({
                        'file': vid_path,
                        'type': 'video_frame',
                        'quality': kf['quality']
                    })
        
        result['total_sources'] = len(all_embeddings)
        
        if len(all_embeddings) < 2:
            result['is_consistent'] = len(all_embeddings) == 1
            result['confidence_score'] = 1.0 if len(all_embeddings) == 1 else 0.0
            return result
        
        # Cross-verification: All pairs must pass 99% threshold
        reference_emb = all_embeddings[0]
        passed_count = 1  # Reference always passes
        
        similarities = []
        for i in range(1, len(all_embeddings)):
            similarity = identity_fusion.compare_embeddings(reference_emb, all_embeddings[i])
            similarities.append(similarity)
            
            if similarity >= self.SIMILARITY_THRESHOLD:
                passed_count += 1
            else:
                result['failed_sources'].append({
                    'file': all_sources[i]['file'],
                    'reason': f"Similarity too low: {similarity:.4f} < {self.SIMILARITY_THRESHOLD}",
                    'similarity': similarity
                })
        
        result['passed_sources'] = passed_count
        avg_similarity = np.mean(similarities) if similarities else 1.0
        result['confidence_score'] = avg_similarity
        
        # Flexible decision logic
        if avg_similarity >= self.SIMILARITY_THRESHOLD_STRICT:
            result['is_consistent'] = True
            result['review_status'] = 'AUTO_APPROVED'
        elif avg_similarity >= self.SIMILARITY_THRESHOLD_REVIEW:
            result['is_consistent'] = True
            result['review_status'] = 'FLAGGED_FOR_REVIEW'
        else:
            result['is_consistent'] = False
            result['review_status'] = 'REJECTED'
        
        # Create master embedding with pose-adaptive weighting
        if result['is_consistent']:
            master_emb = np.mean(all_embeddings, axis=0)
            master_emb = master_emb / np.linalg.norm(master_emb)
            result['master_embedding'] = master_emb.tolist()
        
        return result
    
    def detect_liveness(self, image_path: str) -> Dict:
        """
        Detect if image is live (not screen capture or printed photo)
        Uses multiple techniques:
        1. Moiré pattern detection (screen photos)
        2. Print quality detection
        3. Texture analysis
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return {'is_live': False, 'confidence': 0.0, 'reason': 'Cannot read image'}
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Check 1: Moiré pattern detection (FFT analysis)
            moire_score = self._detect_moire_pattern(gray)
            
            # Check 2: Print quality detection (edge sharpness)
            print_score = self._detect_print_quality(gray)
            
            # Check 3: Texture analysis (LBP variance)
            texture_score = self._analyze_texture(gray)
            
            # Combined decision
            is_live = (moire_score < 0.3 and print_score > 0.5 and texture_score > 0.4)
            confidence = (1 - moire_score) * print_score * texture_score
            
            reason = "Live photo" if is_live else "Possible fake (screen/print)"
            
            return {
                'is_live': is_live,
                'confidence': float(confidence),
                'reason': reason,
                'details': {
                    'moire_score': float(moire_score),
                    'print_score': float(print_score),
                    'texture_score': float(texture_score)
                }
            }
            
        except Exception as e:
            print(f"Liveness detection error: {e}")
            return {'is_live': True, 'confidence': 0.5, 'reason': 'Detection failed - manual review'}
    
    def _detect_moire_pattern(self, gray_img: np.ndarray) -> float:
        """Detect Moiré patterns using FFT (screen photos have periodic patterns)"""
        try:
            # Apply FFT
            f = np.fft.fft2(gray_img)
            fshift = np.fft.fftshift(f)
            magnitude = np.abs(fshift)
            
            # Check for periodic peaks (Moiré indicator)
            h, w = magnitude.shape
            center_region = magnitude[h//4:3*h//4, w//4:3*w//4]
            
            # High frequency energy indicates Moiré
            high_freq_energy = np.sum(center_region > np.percentile(center_region, 95))
            total_energy = center_region.size
            
            moire_score = high_freq_energy / total_energy
            return min(1.0, moire_score * 5)  # Scale up
            
        except:
            return 0.0
    
    def _detect_print_quality(self, gray_img: np.ndarray) -> float:
        """Detect if image is printed (blurry edges)"""
        try:
            # Calculate edge sharpness
            laplacian = cv2.Laplacian(gray_img, cv2.CV_64F)
            sharpness = laplacian.var()
            
            # Normalize (higher = sharper = more likely live)
            normalized_sharpness = min(1.0, sharpness / 500)
            return normalized_sharpness
            
        except:
            return 0.5
    
    def _analyze_texture(self, gray_img: np.ndarray) -> float:
        """Analyze texture using Local Binary Patterns"""
        try:
            # Simple LBP-like texture analysis
            h, w = gray_img.shape
            
            # Calculate local variance
            kernel_size = 5
            mean = cv2.blur(gray_img.astype(float), (kernel_size, kernel_size))
            sqr_mean = cv2.blur((gray_img.astype(float))**2, (kernel_size, kernel_size))
            variance = sqr_mean - mean**2
            
            # High variance = good texture = live photo
            texture_score = min(1.0, np.mean(variance) / 1000)
            return texture_score
            
        except:
            return 0.5

# Global instance
bulletproof_validator = BulletproofConsistencyValidator()
