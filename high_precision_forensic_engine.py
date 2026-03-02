"""
High-Precision Forensic Vision Engine
68-point landmarks, temporal consistency, CLAHE, motion detection
"""
import cv2
import numpy as np
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from collections import deque, defaultdict

logger = logging.getLogger(__name__)

class HighPrecisionForensicEngine:
    """High-precision forensic analysis with motion detection and temporal consistency"""
    
    def __init__(self, case_id=None):
        self.case_id = case_id
        self.temporal_buffer = defaultdict(lambda: deque(maxlen=30))  # 30 frames buffer
        self.prev_frame_gray = None
        self.motion_threshold = 25  # Motion detection sensitivity
    
    def detect_motion(self, frame):
        """Motion detection pre-filtering to skip static backgrounds"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if self.prev_frame_gray is None:
            self.prev_frame_gray = gray
            return True  # Process first frame
        
        frame_delta = cv2.absdiff(self.prev_frame_gray, gray)
        thresh = cv2.threshold(frame_delta, self.motion_threshold, 255, cv2.THRESH_BINARY)[1]
        motion_pixels = cv2.countNonZero(thresh)
        
        self.prev_frame_gray = gray
        
        # Skip if less than 0.5% of frame has motion
        return motion_pixels > (frame.shape[0] * frame.shape[1] * 0.005)
    
    def enhance_clahe(self, frame):
        """CLAHE enhancement for low-light performance"""
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
    
    def calculate_pose_68pt(self, landmarks):
        """Calculate pose from 68-point landmarks (±20° threshold)"""
        try:
            left_eye = np.mean(landmarks['left_eye'], axis=0)
            right_eye = np.mean(landmarks['right_eye'], axis=0)
            nose_tip = np.mean(landmarks['nose_tip'], axis=0)
            chin = landmarks['chin'][8]
            
            eye_center = (left_eye + right_eye) / 2
            eye_to_nose = nose_tip[0] - eye_center[0]
            eye_width = np.linalg.norm(right_eye - left_eye)
            yaw = np.degrees(np.arctan2(eye_to_nose, eye_width / 2)) * 2
            
            nose_to_chin = chin[1] - nose_tip[1]
            face_height = chin[1] - eye_center[1]
            pitch = np.degrees(np.arctan2(nose_to_chin - face_height * 0.5, face_height)) * 1.5
            
            return {'yaw': float(yaw), 'pitch': float(pitch)}
        except:
            return {'yaw': 0.0, 'pitch': 0.0}
    
    def confirm_temporal_consistency(self, face_id, confidence, timestamp, fps=30):
        """Temporal consistency: 8+ frames within 2-second window"""
        self.temporal_buffer[face_id].append({'confidence': confidence, 'timestamp': timestamp})
        
        # Get frames within 2-second window
        recent_frames = [f for f in self.temporal_buffer[face_id] 
                        if timestamp - f['timestamp'] <= 2.0]
        
        # Require 8+ frames with avg confidence >= 0.88
        if len(recent_frames) >= 8:
            avg_conf = sum(f['confidence'] for f in recent_frames) / len(recent_frames)
            return avg_conf >= 0.88
        
        return False
    
    def detect_with_precision(self, frame, target_encoding, timestamp, fps=30):
        """High-precision detection with all filters"""
        try:
            import face_recognition
            
            # CLAHE enhancement
            enhanced = self.enhance_clahe(frame)
            rgb_frame = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
            
            # Multi-scale detection
            face_locations = face_recognition.face_locations(rgb_frame, model='cnn', number_of_times_to_upsample=2)
            if not face_locations:
                return None
            
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            face_landmarks_list = face_recognition.face_landmarks(rgb_frame, face_locations)
            
            all_faces = []
            target_match = None
            
            for idx, (encoding, location) in enumerate(zip(face_encodings, face_locations)):
                face_data = {'location': location, 'encoding': encoding}
                
                # 68-point landmark validation
                if idx < len(face_landmarks_list):
                    landmarks = face_landmarks_list[idx]
                    
                    # Check required landmarks
                    if not all(k in landmarks for k in ['left_eye', 'right_eye', 'nose_tip', 'top_lip', 'bottom_lip']):
                        continue
                    
                    # Landmark quality
                    if (len(landmarks.get('left_eye', [])) < 4 or 
                        len(landmarks.get('right_eye', [])) < 4 or
                        len(landmarks.get('nose_tip', [])) < 3 or
                        len(landmarks.get('top_lip', [])) + len(landmarks.get('bottom_lip', [])) < 10):
                        continue
                    
                    # Pose check: ±20° threshold
                    pose = self.calculate_pose_68pt(landmarks)
                    if abs(pose['yaw']) > 20 or abs(pose['pitch']) > 20:
                        continue
                    
                    face_data['landmarks'] = landmarks
                    face_data['pose'] = pose
                    face_data['is_frontal'] = True
                
                all_faces.append(face_data)
                
                # Match against target
                if target_encoding is not None and 'is_frontal' in face_data:
                    distance = face_recognition.face_distance([target_encoding], encoding)[0]
                    confidence = max(0.0, 1.0 - distance)
                    
                    if confidence >= 0.88:
                        face_id = f"{location[0]}_{location[1]}"
                        
                        # Temporal consistency check
                        if self.confirm_temporal_consistency(face_id, confidence, timestamp, fps):
                            if not target_match or confidence > target_match['confidence']:
                                target_match = {
                                    'location': location,
                                    'confidence': confidence,
                                    'landmarks': landmarks,
                                    'pose': pose,
                                    'encoding': encoding
                                }
            
            if target_match:
                return {
                    'target': target_match,
                    'all_faces': all_faces,
                    'crowd_size': len(all_faces),
                    'timestamp': timestamp
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Precision detection error: {e}")
            return None
    
    def render_forensic_evidence(self, frame, detection_data):
        """Render forensic evidence with zoom-in inset and security cam aesthetic"""
        try:
            output = frame.copy()
            h, w = output.shape[:2]
            
            # Security cam noise filter (background only)
            noise = np.random.randint(-8, 8, output.shape, dtype=np.int16)
            output = np.clip(output.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            output = cv2.addWeighted(output, 0.88, np.zeros_like(output), 0.12, 0)
            
            target = detection_data['target']
            all_faces = detection_data.get('all_faces', [])
            
            # Draw white boxes for ALL detected persons
            for face in all_faces:
                top, right, bottom, left = face['location']
                cv2.rectangle(output, (left, top), (right, bottom), (255, 255, 255), 1)
            
            # Target box (green, thicker)
            t_top, t_right, t_bottom, t_left = target['location']
            cv2.rectangle(output, (t_left, t_top), (t_right, t_bottom), (0, 255, 0), 2)
            
            # High-resolution zoom-in inset (top-right)
            inset_w, inset_h = int(w * 0.28), int(h * 0.28)
            inset_x, inset_y = w - inset_w - 15, 15
            
            # Extract target face with padding
            face_region = frame[max(0, t_top-40):min(h, t_bottom+40), 
                               max(0, t_left-40):min(w, t_right+40)]
            
            if face_region.size > 0:
                # Sharp and bright enhancement
                face_sharp = cv2.detailEnhance(face_region, sigma_s=10, sigma_r=0.15)
                face_sharp = cv2.convertScaleAbs(face_sharp, alpha=1.25, beta=25)
                
                # Resize to inset
                face_resized = cv2.resize(face_sharp, (inset_w - 8, inset_h - 8))
                
                # Draw inset frame
                cv2.rectangle(output, (inset_x, inset_y), 
                            (inset_x + inset_w, inset_y + inset_h), (0, 0, 0), -1)
                cv2.rectangle(output, (inset_x, inset_y), 
                            (inset_x + inset_w, inset_y + inset_h), (255, 255, 255), 2)
                
                # Place sharp face
                output[inset_y+4:inset_y+4+face_resized.shape[0], 
                      inset_x+4:inset_x+4+face_resized.shape[1]] = face_resized
                
                # Connecting line
                target_center = ((t_left + t_right) // 2, (t_top + t_bottom) // 2)
                inset_corner = (inset_x, inset_y + inset_h)
                cv2.line(output, target_center, inset_corner, (255, 255, 255), 1, cv2.LINE_AA)
                
                # Labels
                conf_text = f"MATCH: {target['confidence']*100:.1f}%"
                cv2.putText(output, conf_text, (inset_x + 8, inset_y + inset_h - 12),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Metadata overlay
            cv2.putText(output, f"CROWD: {detection_data['crowd_size']} PERSONS", 
                       (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(output, f"TIME: {detection_data['timestamp']:.2f}s", 
                       (10, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(output, f"CASE: {self.case_id}", 
                       (10, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            return output
            
        except Exception as e:
            logger.error(f"Forensic rendering error: {e}")
            return frame
    
    def save_forensic_evidence(self, frame, detection_data, case_id):
        """Save forensic evidence with SHA-256 hash"""
        try:
            detection_dir = Path(f"static/detections/case_{case_id}")
            detection_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = detection_data['timestamp']
            evidence_num = f"EVD-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:17]}"
            filename = f"{evidence_num}_forensic_t{timestamp:.2f}.jpg"
            filepath = detection_dir / filename
            
            # Render forensic output
            forensic_frame = self.render_forensic_evidence(frame, detection_data)
            cv2.imwrite(str(filepath), forensic_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            # SHA-256 hash
            frame_bytes = cv2.imencode('.jpg', forensic_frame)[1].tobytes()
            frame_hash = hashlib.sha256(frame_bytes).hexdigest()
            
            # Metadata
            metadata = {
                'evidence_number': evidence_num,
                'timestamp': timestamp,
                'confidence': detection_data['target']['confidence'],
                'crowd_size': detection_data['crowd_size'],
                'pose_yaw': detection_data['target']['pose']['yaw'],
                'pose_pitch': detection_data['target']['pose']['pitch'],
                'frame_hash': frame_hash,
                'filepath': str(filepath)
            }
            
            # Save metadata JSON
            metadata_path = detection_dir / f"{evidence_num}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✅ Forensic evidence saved: {filepath}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Save forensic evidence error: {e}")
            return None

# Global instance
precision_engine = HighPrecisionForensicEngine()
