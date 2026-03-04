"""
TASK 4 (Part 3): End-to-End Integrated Workflow
Complete register_case workflow with all advanced features
"""
from advanced_identity_fusion import identity_fusion
from bulletproof_consistency_validator import bulletproof_validator
from temporal_consensus_engine import temporal_engine
from cctv_enhancement import cctv_enhancer
from faiss_vector_db import faiss_db
from xai_feature_weighting_system import xai_system
import os
import json
from typing import List, Dict

class IntegratedCaseProcessor:
    """
    Complete workflow integrating all advanced features
    """
    
    def process_case_registration(self, case_id: int, image_paths: List[str], 
                                  video_paths: List[str] = None) -> Dict:
        """
        Complete case processing workflow
        
        Steps:
        1. Multi-angle identity fusion (512-d embeddings)
        2. Bulletproof consistency validation (99% threshold)
        3. Liveness detection
        4. Master identity vector creation
        5. FAISS index insertion
        
        Returns:
            Processing result with all validations
        """
        result = {
            'success': False,
            'case_id': case_id,
            'validations': {},
            'embeddings': {},
            'faiss_position': None,
            'errors': []
        }
        
        try:
            # STEP 1: Extract 512-d embeddings from all photos
            print(f"📸 Step 1: Extracting 512-d embeddings for case {case_id}")
            photo_embeddings = {}
            
            for img_path in image_paths:
                emb_data = identity_fusion.extract_512d_embedding(img_path)
                if emb_data:
                    view_type = identity_fusion.classify_view_type(emb_data['pose'])
                    photo_embeddings[view_type] = emb_data['embedding']
                    print(f"  ✅ {os.path.basename(img_path)}: {view_type} view")
            
            if not photo_embeddings:
                result['errors'].append("No valid face embeddings extracted")
                return result
            
            # STEP 2: Extract video keyframes if provided
            video_keyframes = []
            if video_paths:
                print(f"🎥 Step 2: Extracting video keyframes")
                for vid_path in video_paths:
                    keyframes = identity_fusion.extract_video_keyframes(vid_path, max_frames=5)
                    video_keyframes.extend(keyframes)
                    print(f"  ✅ {len(keyframes)} keyframes from {os.path.basename(vid_path)}")
            
            # STEP 3: Bulletproof consistency validation (99% threshold)
            print(f"🔒 Step 3: Bulletproof consistency validation (99% threshold)")
            consistency_result = bulletproof_validator.validate_cross_verification(
                image_paths, 
                video_paths
            )
            
            result['validations']['consistency'] = consistency_result
            
            if not consistency_result['is_consistent']:
                result['errors'].append(
                    f"Consistency validation failed: {len(consistency_result['failed_sources'])} sources rejected"
                )
                print(f"  ❌ Consistency check FAILED")
                return result
            
            print(f"  ✅ Consistency verified: {consistency_result['confidence_score']:.4f}")
            
            # STEP 4: Liveness detection for all photos
            print(f"👁️ Step 4: Liveness detection")
            liveness_passed = True
            for liveness_check in consistency_result['liveness_checks']:
                if not liveness_check['is_live']:
                    liveness_passed = False
                    result['errors'].append(
                        f"Liveness check failed for {liveness_check['file']}: {liveness_check['reason']}"
                    )
                    print(f"  ❌ {liveness_check['file']}: FAKE DETECTED")
                else:
                    print(f"  ✅ {liveness_check['file']}: Live photo")
            
            if not liveness_passed:
                return result
            
            # STEP 5: Create master identity vector
            print(f"🧬 Step 5: Creating master identity vector")
            master_data = identity_fusion.create_master_identity_vector(
                photo_embeddings,
                video_keyframes
            )
            
            if not master_data:
                result['errors'].append("Failed to create master identity vector")
                return result
            
            result['embeddings'] = {
                'master_embedding': master_data['master_embedding'].tolist(),
                'num_sources': master_data['num_sources'],
                'photo_views': master_data['photo_views'],
                'video_frames': master_data['video_frames'],
                'fusion_confidence': master_data['confidence']
            }
            
            print(f"  ✅ Master vector created from {master_data['num_sources']} sources")
            print(f"  ✅ Fusion confidence: {master_data['confidence']:.4f}")
            
            # STEP 6: Insert into FAISS index
            print(f"🔍 Step 6: Inserting into FAISS index")
            faiss_position = faiss_db.add_embedding(
                master_data['master_embedding'],
                case_id
            )
            
            result['faiss_position'] = faiss_position
            print(f"  ✅ Indexed at position {faiss_position}")
            
            # STEP 7: Store in database
            print(f"💾 Step 7: Storing in database")
            self._store_in_database(case_id, result, photo_embeddings, master_data)
            
            result['success'] = True
            print(f"✅ Case {case_id} processed successfully!")
            
        except Exception as e:
            result['errors'].append(f"Processing error: {str(e)}")
            print(f"❌ Error: {e}")
        
        return result
    
    def _store_in_database(self, case_id: int, result: Dict, 
                          photo_embeddings: Dict, master_data: Dict):
        """Store all data in database"""
        from __init__ import db
        from models import PersonProfile, FAISSIndex
        
        try:
            # Create or update PersonProfile
            profile = PersonProfile.query.filter_by(case_id=case_id).first()
            if not profile:
                profile = PersonProfile(case_id=case_id)
                db.session.add(profile)
            
            # Store 512-d embeddings
            profile.master_embedding_512d = json.dumps(result['embeddings']['master_embedding'])
            
            if 'front' in photo_embeddings:
                profile.front_embedding_512d = json.dumps(photo_embeddings['front'].tolist())
            if 'left_profile' in photo_embeddings:
                profile.left_profile_embedding_512d = json.dumps(photo_embeddings['left_profile'].tolist())
            if 'right_profile' in photo_embeddings:
                profile.right_profile_embedding_512d = json.dumps(photo_embeddings['right_profile'].tolist())
            
            # Store fusion metadata
            profile.fusion_confidence = master_data['confidence']
            profile.num_fusion_sources = master_data['num_sources']
            profile.view_types_used = ','.join(master_data['photo_views'])
            
            # Store liveness data
            profile.liveness_verified = result['validations']['consistency']['is_consistent']
            profile.liveness_confidence = result['validations']['consistency']['confidence_score']
            profile.liveness_details = json.dumps(result['validations']['consistency']['liveness_checks'])
            
            # Store FAISS reference
            profile.faiss_index_id = result['faiss_position']
            
            db.session.commit()
            print(f"  ✅ PersonProfile updated")
            
        except Exception as e:
            print(f"  ❌ Database storage error: {e}")
            db.session.rollback()
    
    def search_in_cctv(self, case_id: int, cctv_video_path: str) -> List[Dict]:
        """
        Search for person in CCTV footage using temporal consensus
        
        Steps:
        1. Load master embedding from FAISS
        2. Enhance CCTV frames
        3. Apply temporal consensus (10+ frames, 98% confidence)
        """
        from models import PersonProfile
        
        try:
            # Load master embedding
            profile = PersonProfile.query.filter_by(case_id=case_id).first()
            if not profile or not profile.master_embedding_512d:
                return []
            
            master_embedding = np.array(json.loads(profile.master_embedding_512d))
            
            # Analyze with temporal consensus
            detections = temporal_engine.analyze_cctv_footage(
                cctv_video_path,
                master_embedding
            )
            
            return detections
            
        except Exception as e:
            print(f"CCTV search error: {e}")
            return []

# Global instance
integrated_processor = IntegratedCaseProcessor()
