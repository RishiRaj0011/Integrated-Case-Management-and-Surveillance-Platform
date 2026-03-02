"""
Example Usage: Multi-View Face Tracking System
Demonstrates how to use the multi-view forensic engine
"""
import cv2
import face_recognition
from vision_engine import get_vision_engine
from location_matching_engine import LocationMatchingEngine

def example_1_basic_multi_view_detection():
    """Example 1: Basic multi-view detection on single frame"""
    print("=" * 60)
    print("Example 1: Basic Multi-View Detection")
    print("=" * 60)
    
    # Load target images
    front_image = face_recognition.load_image_file("static/uploads/person_front.jpg")
    left_image = face_recognition.load_image_file("static/uploads/person_left.jpg")
    right_image = face_recognition.load_image_file("static/uploads/person_right.jpg")
    
    # Generate encodings
    front_encoding = face_recognition.face_encodings(front_image)[0]
    left_encoding = face_recognition.face_encodings(left_image)[0]
    right_encoding = face_recognition.face_encodings(right_image)[0]
    
    # Create target profiles
    target_profiles = {
        'front': front_encoding,
        'left_profile': left_encoding,
        'right_profile': right_encoding
    }
    
    # Load video frame
    cap = cv2.VideoCapture("static/footage/surveillance_video.mp4")
    ret, frame = cap.read()
    cap.release()
    
    # Get vision engine
    vision_engine = get_vision_engine(case_id=1)
    
    # Detect with multi-view
    result = vision_engine.detect_multi_view(
        frame=frame,
        target_profiles=target_profiles,
        timestamp=0.0,
        case_id=1
    )
    
    if result:
        print(f"✅ Match found!")
        print(f"   Confidence: {result['confidence_score'] * 100:.1f}%")
        print(f"   Matched Profile: {result['matched_profile']}")
        print(f"   Temporal Frames: {result['temporal_count']}")
        print(f"   Crowd Size: {result['crowd_size']}")
        print(f"   Evidence: {result['evidence_number']}")
        print(f"   Hash: {result['frame_hash'][:16]}...")
        print(f"   Saved: {result['frame_path']}")
    else:
        print("❌ No match found")


def example_2_video_analysis_with_progress():
    """Example 2: Full video analysis with multi-view"""
    print("\n" + "=" * 60)
    print("Example 2: Full Video Analysis")
    print("=" * 60)
    
    # Initialize engine
    engine = LocationMatchingEngine()
    
    # Analyze footage for case
    case_id = 1
    footage_id = 5
    match_id = 10
    
    print(f"Analyzing footage {footage_id} for case {case_id}...")
    
    # This automatically:
    # 1. Loads multi-view profiles from case images
    # 2. Processes video with motion masking
    # 3. Applies temporal consensus (10+ frames)
    # 4. Generates forensic outputs
    # 5. Saves to database
    
    success = engine.analyze_footage_for_person(match_id)
    
    if success:
        print("✅ Analysis completed successfully")
        
        # Get results
        from models import LocationMatch, PersonDetection
        match = LocationMatch.query.get(match_id)
        
        print(f"\nResults:")
        print(f"   Detections: {match.detection_count}")
        print(f"   Person Found: {match.person_found}")
        print(f"   Avg Confidence: {match.confidence_score * 100:.1f}%")
        
        # Get individual detections
        detections = PersonDetection.query.filter_by(
            location_match_id=match_id,
            analysis_method='multi_view_forensic'
        ).all()
        
        print(f"\nDetailed Detections:")
        for i, det in enumerate(detections[:5], 1):
            print(f"   {i}. Time: {det.timestamp:.1f}s | Confidence: {det.confidence_score*100:.1f}%")
            print(f"      Evidence: {det.evidence_number}")
            print(f"      Forensic: static/{det.frame_path}")
    else:
        print("❌ Analysis failed")


def example_3_batch_processing():
    """Example 3: Batch process multiple footage files"""
    print("\n" + "=" * 60)
    print("Example 3: Batch Processing")
    print("=" * 60)
    
    from tasks import process_batch_high_precision
    
    case_id = 1
    footage_ids = [5, 6, 7, 8, 9]
    
    print(f"Starting batch analysis for {len(footage_ids)} videos...")
    
    # Start async batch processing
    task = process_batch_high_precision.delay(case_id, footage_ids)
    
    print(f"✅ Batch job started: {task.id}")
    print(f"   Monitor progress in admin panel")
    print(f"   Or check task status: task.status")


def example_4_custom_thresholds():
    """Example 4: Custom detection thresholds"""
    print("\n" + "=" * 60)
    print("Example 4: Custom Thresholds")
    print("=" * 60)
    
    from multi_view_forensic_engine import MultiViewForensicEngine
    
    # Create engine with custom settings
    engine = MultiViewForensicEngine(case_id=1)
    
    # Adjust thresholds
    engine.MATCH_THRESHOLD = 0.90  # Higher confidence required
    engine.TEMPORAL_WINDOW = 15    # More frames required
    
    print(f"Custom settings:")
    print(f"   Match Threshold: {engine.MATCH_THRESHOLD}")
    print(f"   Temporal Window: {engine.TEMPORAL_WINDOW} frames")
    
    # Use custom engine
    # ... (same as example 1)


def example_5_forensic_output_verification():
    """Example 5: Verify forensic output integrity"""
    print("\n" + "=" * 60)
    print("Example 5: Forensic Output Verification")
    print("=" * 60)
    
    import hashlib
    from models import PersonDetection
    
    # Get a detection
    detection = PersonDetection.query.filter_by(
        analysis_method='multi_view_forensic'
    ).first()
    
    if detection:
        print(f"Verifying detection: {detection.evidence_number}")
        
        # Load forensic image
        image_path = f"static/{detection.frame_path}"
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Compute hash
        computed_hash = hashlib.sha256(image_data).hexdigest()
        stored_hash = detection.frame_hash
        
        if computed_hash == stored_hash:
            print(f"✅ Hash verification PASSED")
            print(f"   Stored:   {stored_hash[:32]}...")
            print(f"   Computed: {computed_hash[:32]}...")
        else:
            print(f"❌ Hash verification FAILED")
            print(f"   Evidence may be tampered!")
        
        # Display metadata
        import json
        factors = json.loads(detection.decision_factors)
        
        print(f"\nDecision Factors:")
        for factor in factors:
            print(f"   - {factor}")
    else:
        print("No detections found")


def example_6_profile_type_detection():
    """Example 6: Automatic profile type detection"""
    print("\n" + "=" * 60)
    print("Example 6: Profile Type Detection")
    print("=" * 60)
    
    engine = LocationMatchingEngine()
    
    # Test filenames
    test_files = [
        "person_front.jpg",
        "person_left_profile.jpg",
        "person_right.jpg",
        "mugshot_frontal.jpg",
        "side_view_left.jpg"
    ]
    
    print("Detecting profile types from filenames:")
    for filename in test_files:
        profile_type = engine._detect_profile_type(filename, None)
        print(f"   {filename:30s} → {profile_type}")


def example_7_motion_analysis():
    """Example 7: Motion masking demonstration"""
    print("\n" + "=" * 60)
    print("Example 7: Motion Masking")
    print("=" * 60)
    
    from multi_view_forensic_engine import MultiViewForensicEngine
    
    engine = MultiViewForensicEngine(case_id=1)
    
    # Load video
    cap = cv2.VideoCapture("static/footage/surveillance_video.mp4")
    
    frame_count = 0
    motion_frames = 0
    static_frames = 0
    
    while cap.isOpened() and frame_count < 100:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Update motion mask
        engine._update_motion_mask(frame)
        
        # Check motion
        if engine.motion_mask is not None:
            motion_ratio = np.sum(engine.motion_mask > 0) / engine.motion_mask.size
            
            if motion_ratio > 0.1:
                motion_frames += 1
            else:
                static_frames += 1
        
        frame_count += 1
    
    cap.release()
    
    print(f"Motion Analysis Results:")
    print(f"   Total Frames: {frame_count}")
    print(f"   Motion Frames: {motion_frames} ({motion_frames/frame_count*100:.1f}%)")
    print(f"   Static Frames: {static_frames} ({static_frames/frame_count*100:.1f}%)")
    print(f"   Efficiency Gain: {static_frames/frame_count*100:.1f}% reduction")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Multi-View Face Tracking - Usage Examples")
    print("=" * 60)
    
    # Run examples
    try:
        example_1_basic_multi_view_detection()
    except Exception as e:
        print(f"Example 1 error: {e}")
    
    try:
        example_2_video_analysis_with_progress()
    except Exception as e:
        print(f"Example 2 error: {e}")
    
    try:
        example_3_batch_processing()
    except Exception as e:
        print(f"Example 3 error: {e}")
    
    try:
        example_4_custom_thresholds()
    except Exception as e:
        print(f"Example 4 error: {e}")
    
    try:
        example_5_forensic_output_verification()
    except Exception as e:
        print(f"Example 5 error: {e}")
    
    try:
        example_6_profile_type_detection()
    except Exception as e:
        print(f"Example 6 error: {e}")
    
    try:
        example_7_motion_analysis()
    except Exception as e:
        print(f"Example 7 error: {e}")
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
