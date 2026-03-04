"""
TASK 3 (Part 2): CCTV Enhancement for Indian Conditions
BasicSR Super-Resolution + CLAHE Contrast Enhancement
"""
import cv2
import numpy as np
from typing import Tuple

class CCTVEnhancer:
    def __init__(self):
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        
    def enhance_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Enhance low-quality CCTV frame
        1. Super-resolution (2x upscale)
        2. CLAHE contrast enhancement
        3. Denoising
        """
        # Step 1: Super-resolution (simple bicubic for now)
        h, w = frame.shape[:2]
        upscaled = cv2.resize(frame, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        
        # Step 2: CLAHE for contrast
        if len(upscaled.shape) == 3:
            lab = cv2.cvtColor(upscaled, cv2.COLOR_BGR2LAB)
            lab[:, :, 0] = self.clahe.apply(lab[:, :, 0])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            enhanced = self.clahe.apply(upscaled)
        
        # Step 3: Denoise
        denoised = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
        
        return denoised
    
    def enhance_night_vision(self, frame: np.ndarray) -> np.ndarray:
        """Special enhancement for night-vision footage"""
        # Gamma correction for night vision
        gamma = 1.5
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
        
        enhanced = cv2.LUT(frame, table)
        
        # Apply CLAHE
        if len(enhanced.shape) == 3:
            lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
            lab[:, :, 0] = self.clahe.apply(lab[:, :, 0])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return enhanced

cctv_enhancer = CCTVEnhancer()
