"""
Multi-View Face Encoding Extractor
Extracts face encodings from multiple angles (Front, Left, Right) and video frames
"""
import cv2
import face_recognition
import numpy as np
import json
from pathlib import Path


class MultiViewFaceExtractor:
    """Extract face encodings from multiple views and video frames"""
    
    def __init__(self):
        self.min_face_quality = 0.7
        self.max_encodings_per_source = 5
    
    def extract_from_images(self, image_paths):
        """
        Extract face encodings from 3 images (Front, Left, Right)
        
        Args:
            image_paths: List of image file paths [front, left, right]
        
        Returns:
            dict: {
                'front': [encoding1, encoding2, ...],
                'left_profile': [encoding1, ...],
                'right_profile': [encoding1, ...],
                'all_encodings': [all encodings combined],
                'primary_encoding': best_quality_encoding
            }
        """
        result = {
            'front': [],
            'left_profile': [],
            'right_profile': [],
            'all_encodings': [],
            'primary_encoding': None
        }
        
        view_names = ['front', 'left_profile', 'right_profile']
        best_quality = 0
        
        for idx, img_path in enumerate(image_paths[:3]):
            if not img_path or not Path(img_path).exists():
                continue
            
            try:
                # Load image
                image = face_recognition.load_image_file(img_path)
                
                # Detect faces
                face_locations = face_recognition.face_locations(image, model='hog')
                if not face_locations:
                    continue
                
                # Get encodings
                encodings = face_recognition.face_encodings(image, face_locations)
                
                # Store best encoding for this view
                if encodings:
                    view_name = view_names[idx] if idx < len(view_names) else 'front'
                    encoding = encodings[0]  # Take first face
                    
                    # Calculate quality score
                    quality = self._calculate_face_quality(image, face_locations[0])
                    
                    result[view_name].append(encoding.tolist())
                    result['all_encodings'].append(encoding.tolist())
                    
                    # Track best quality encoding
                    if quality > best_quality:
                        best_quality = quality
                        result['primary_encoding'] = encoding.tolist()
                
            except Exception as e:
                print(f"Error extracting from {img_path}: {e}")
                continue
        
        # If no primary encoding found, use first available
        if not result['primary_encoding'] and result['all_encodings']:
            result['primary_encoding'] = result['all_encodings'][0]
        
        return result
    
    def extract_from_video(self, video_path, max_frames=5):
        """
        Extract high-quality face encodings from video
        
        Args:
            video_path: Path to video file
            max_frames: Maximum number of frames to extract
        
        Returns:
            list: List of face encodings from video
        """
        encodings = []
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return encodings
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # Sample frames evenly across video
            frame_indices = np.linspace(0, total_frames - 1, min(max_frames * 3, total_frames), dtype=int)
            
            quality_frames = []
            
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Detect faces
                face_locations = face_recognition.face_locations(rgb_frame, model='hog')
                if not face_locations:
                    continue
                
                # Calculate quality
                quality = self._calculate_face_quality(rgb_frame, face_locations[0])
                
                if quality >= self.min_face_quality:
                    # Get encoding
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    if face_encodings:
                        quality_frames.append({
                            'encoding': face_encodings[0],
                            'quality': quality,
                            'frame_idx': frame_idx
                        })
            
            cap.release()
            
            # Sort by quality and take top N
            quality_frames.sort(key=lambda x: x['quality'], reverse=True)
            encodings = [f['encoding'].tolist() for f in quality_frames[:max_frames]]
            
        except Exception as e:
            print(f"Error extracting from video {video_path}: {e}")
        
        return encodings
    
    def _calculate_face_quality(self, image, face_location):
        """
        Calculate face quality score based on size, clarity, and lighting
        
        Returns:
            float: Quality score 0.0-1.0
        """
        try:
            top, right, bottom, left = face_location
            face_height = bottom - top
            face_width = right - left
            
            # Size score (larger faces = better quality)
            img_height, img_width = image.shape[:2]
            size_ratio = (face_height * face_width) / (img_height * img_width)
            size_score = min(size_ratio * 10, 1.0)  # Normalize
            
            # Extract face region
            face_img = image[top:bottom, left:right]
            
            # Lighting score (check brightness variance)
            if len(face_img.shape) == 3:
                gray_face = cv2.cvtColor(face_img, cv2.COLOR_RGB2GRAY)
            else:
                gray_face = face_img
            
            brightness = np.mean(gray_face)
            brightness_score = 1.0 - abs(brightness - 128) / 128  # Optimal at 128
            
            # Sharpness score (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray_face, cv2.CV_64F).var()
            sharpness_score = min(laplacian_var / 500, 1.0)  # Normalize
            
            # Combined quality score
            quality = (size_score * 0.4 + brightness_score * 0.3 + sharpness_score * 0.3)
            
            return quality
            
        except Exception as e:
            return 0.5  # Default medium quality
    
    def create_person_profile(self, case_id, image_paths, video_path=None):
        """
        Create comprehensive person profile with multi-view encodings
        
        Args:
            case_id: Case ID
            image_paths: List of image paths [front, left, right]
            video_path: Optional video path for additional encodings
        
        Returns:
            dict: Complete person profile data
        """
        # Extract from images
        image_encodings = self.extract_from_images(image_paths)
        
        # Extract from video if provided
        video_encodings = []
        if video_path and Path(video_path).exists():
            video_encodings = self.extract_from_video(video_path)
        
        # Combine all encodings
        all_encodings = image_encodings['all_encodings'] + video_encodings
        
        # Select primary encoding (best quality from images)
        primary_encoding = image_encodings['primary_encoding']
        
        profile_data = {
            'case_id': case_id,
            'primary_face_encoding': json.dumps(primary_encoding) if primary_encoding else None,
            'all_face_encodings': json.dumps(all_encodings) if all_encodings else None,
            'front_encodings': json.dumps(image_encodings['front']) if image_encodings['front'] else None,
            'left_profile_encodings': json.dumps(image_encodings['left_profile']) if image_encodings['left_profile'] else None,
            'right_profile_encodings': json.dumps(image_encodings['right_profile']) if image_encodings['right_profile'] else None,
            'video_encodings': json.dumps(video_encodings) if video_encodings else None,
            'total_encodings': len(all_encodings),
            'face_quality_score': 0.9 if len(all_encodings) >= 3 else 0.7,
            'profile_confidence': min(len(all_encodings) / 8.0, 1.0)  # Max confidence at 8 encodings
        }
        
        return profile_data


# Global instance
_extractor = None

def get_face_extractor():
    """Get or create face extractor instance"""
    global _extractor
    if _extractor is None:
        _extractor = MultiViewFaceExtractor()
    return _extractor
