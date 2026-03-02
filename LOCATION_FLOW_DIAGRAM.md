# Location Matching System - Visual Flow Diagram

## 🎯 Complete Data Flow: Footage Upload → AI Analysis → Results

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ADMIN UPLOADS FOOTAGE                             │
│  Location: "Connaught Place, Delhi"                                 │
│  File: surveillance_video.mp4                                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FILE: admin.py (Line 1500)                                         │
│  ROUTE: /admin/surveillance-footage/upload                          │
│                                                                      │
│  def upload_surveillance_footage():                                 │
│      footage = SurveillanceFootage(                                 │
│          location_name="Connaught Place, Delhi",                    │
│          video_path="surveillance/video.mp4"                        │
│      )                                                              │
│      db.session.add(footage)                                        │
│      db.session.commit()                                            │
│                                                                      │
│      # ✅ TRIGGER AI PROCESSOR                                      │
│      location_engine.process_new_footage(footage.id)                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DATABASE: surveillance_footage                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ id: 123                                                       │  │
│  │ location_name: "Connaught Place, Delhi"                      │  │
│  │ video_path: "surveillance/video.mp4"                         │  │
│  │ uploaded_by: 1 (admin)                                       │  │
│  │ created_at: 2026-03-02 08:00:00                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FILE: location_matching_engine.py (Line 240)                       │
│  FUNCTION: process_new_footage(footage_id=123)                      │
│                                                                      │
│  # Get all active cases                                             │
│  active_cases = Case.query.filter(                                  │
│      status.in_(['Approved', 'Active'])                             │
│  ).all()                                                            │
│                                                                      │
│  # Found 3 active cases:                                            │
│  # Case 1: "Rahul Kumar" - Last seen: "Connaught Place"            │
│  # Case 2: "Priya Sharma" - Last seen: "CP, Delhi"                 │
│  # Case 3: "Amit Singh" - Last seen: "Karol Bagh"                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MATCHING ALGORITHM: _calculate_name_similarity()                   │
│                                                                      │
│  Case 1: "Connaught Place" vs "Connaught Place, Delhi"             │
│  ├─ Exact match? NO                                                 │
│  ├─ Substring match? YES ✅                                         │
│  └─ Match Score: 0.85 (85%)                                         │
│                                                                      │
│  Case 2: "CP, Delhi" vs "Connaught Place, Delhi"                   │
│  ├─ Exact match? NO                                                 │
│  ├─ Substring match? NO                                             │
│  ├─ Word overlap: {"delhi"} = 1/3                                  │
│  └─ Match Score: 0.35 (35%)                                         │
│                                                                      │
│  Case 3: "Karol Bagh" vs "Connaught Place, Delhi"                  │
│  ├─ Exact match? NO                                                 │
│  ├─ Substring match? NO                                             │
│  ├─ Word overlap: {"delhi"} = 1/3                                  │
│  └─ Match Score: 0.15 (15%) ❌ BELOW THRESHOLD                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DATABASE: location_match (2 records created)                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Match 1:                                                      │  │
│  │   case_id: 1 (Rahul Kumar)                                   │  │
│  │   footage_id: 123                                             │  │
│  │   match_score: 0.85                                           │  │
│  │   status: 'pending'                                           │  │
│  │   created_at: 2026-03-02 08:00:05                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Match 2:                                                      │  │
│  │   case_id: 2 (Priya Sharma)                                  │  │
│  │   footage_id: 123                                             │  │
│  │   match_score: 0.35                                           │  │
│  │   status: 'pending'                                           │  │
│  │   created_at: 2026-03-02 08:00:05                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ADMIN DASHBOARD: Shows 2 pending matches                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 🎯 Match 1: Rahul Kumar (85% match)                          │  │
│  │    [Analyze Now] button                                       │  │
│  │                                                               │  │
│  │ 🎯 Match 2: Priya Sharma (35% match)                         │  │
│  │    [Analyze Now] button                                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼ (Admin clicks "Analyze Now" for Match 1)
┌─────────────────────────────────────────────────────────────────────┐
│  FILE: admin.py (Line 1650)                                         │
│  ROUTE: /admin/surveillance-footage/123/analyze                     │
│                                                                      │
│  def analyze_surveillance_footage(footage_id=123):                  │
│      matches = LocationMatch.query.filter_by(                       │
│          footage_id=123,                                            │
│          status='pending'                                           │
│      ).all()                                                        │
│                                                                      │
│      for match in matches:                                          │
│          # ✅ TRIGGER AI ANALYSIS                                   │
│          location_engine.analyze_footage_for_person(match.id)       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FILE: location_matching_engine.py (Line 300)                       │
│  FUNCTION: analyze_footage_for_person(match_id=1)                   │
│                                                                      │
│  match = LocationMatch.query.get(1)                                 │
│  match.status = 'processing'                                        │
│  db.session.commit()                                                │
│                                                                      │
│  # Load target face encodings                                       │
│  target_profiles = _load_target_profiles(match.case)                │
│  # Returns: {                                                       │
│  #   'front': [0.123, 0.456, ...],  # 128-dim vector               │
│  #   'left_profile': [0.789, ...],                                  │
│  #   'right_profile': [0.234, ...]                                  │
│  # }                                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FILE: location_matching_engine.py (Line 400)                       │
│  FUNCTION: _multi_view_analyze_video()                              │
│                                                                      │
│  cap = cv2.VideoCapture("static/surveillance/video.mp4")            │
│  fps = 25                                                           │
│  total_frames = 15000 (10 minutes)                                  │
│                                                                      │
│  # Process every 30 frames (1 second intervals)                     │
│  for frame_count in [0, 30, 60, 90, ...]:                          │
│      timestamp = frame_count / fps                                  │
│      frame = cap.read()                                             │
│                                                                      │
│      # ✅ DETECT FACES IN FRAME                                     │
│      detection_data = vision_engine.detect_multi_view(              │
│          frame, target_profiles, timestamp, match_id                │
│      )                                                              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FILE: vision_engine.py                                             │
│  FUNCTION: detect_multi_view(frame, target_profiles)                │
│                                                                      │
│  # Detect all faces in frame                                        │
│  face_locations = face_recognition.face_locations(frame)            │
│  # Found 5 faces in frame                                           │
│                                                                      │
│  # Get encodings for all faces                                      │
│  face_encodings = face_recognition.face_encodings(frame, locations) │
│                                                                      │
│  # Compare each face with target profiles                           │
│  for encoding in face_encodings:                                    │
│      # Compare with front profile                                   │
│      distance_front = face_distance(target_profiles['front'], encoding) │
│      # distance_front = 0.35                                        │
│                                                                      │
│      # Compare with left profile                                    │
│      distance_left = face_distance(target_profiles['left'], encoding) │
│      # distance_left = 0.42                                         │
│                                                                      │
│      # Compare with right profile                                   │
│      distance_right = face_distance(target_profiles['right'], encoding) │
│      # distance_right = 0.38                                        │
│                                                                      │
│      # Best match                                                   │
│      best_distance = min(0.35, 0.42, 0.38) = 0.35                  │
│                                                                      │
│      # Convert to confidence                                        │
│      confidence = (1 - 0.35 / 0.6) × 100 = 41.67%                  │
│                                                                      │
│      # ❌ BELOW THRESHOLD (need 88%)                                │
│      # Skip this face                                               │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼ (Continue processing frames...)
┌─────────────────────────────────────────────────────────────────────┐
│  FRAME 120 (timestamp: 4.8 seconds)                                 │
│                                                                      │
│  # Found 3 faces                                                    │
│  # Face 1: distance = 0.55 → confidence = 8.33% ❌                  │
│  # Face 2: distance = 0.08 → confidence = 86.67% ❌ (close!)        │
│  # Face 3: distance = 0.05 → confidence = 91.67% ✅ MATCH!          │
│                                                                      │
│  # Save detection                                                   │
│  detection_data = {                                                 │
│      'confidence_score': 0.9167,                                    │
│      'face_match_score': 0.9167,                                    │
│      'detection_box': [100, 200, 300, 400],                         │
│      'frame_path': 'detections/detection_1_4.jpg',                  │
│      'frame_hash': 'a3f5b2c8...',                                   │
│      'evidence_number': 'EVD-2026-001',                             │
│      'matched_profile': 'front',                                    │
│      'is_frontal_face': True                                        │
│  }                                                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DATABASE: person_detection (1 record created)                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ location_match_id: 1                                          │  │
│  │ timestamp: 4.8                                                │  │
│  │ confidence_score: 0.9167 (91.67%)                             │  │
│  │ face_match_score: 0.9167                                      │  │
│  │ detection_box: {"top":100,"right":200,"bottom":300,"left":400}│  │
│  │ frame_path: "detections/detection_1_4.jpg"                    │  │
│  │ frame_hash: "a3f5b2c8..."                                     │  │
│  │ evidence_number: "EVD-2026-001"                               │  │
│  │ is_frontal_face: True                                         │  │
│  │ analysis_method: "multi_view_forensic"                        │  │
│  │ created_at: 2026-03-02 08:05:30                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼ (Continue processing all frames...)
┌─────────────────────────────────────────────────────────────────────┐
│  ANALYSIS COMPLETE                                                  │
│                                                                      │
│  Total frames processed: 600 (10 min video, 1 sec intervals)       │
│  Total detections: 15                                               │
│  Average confidence: 89.3%                                          │
│  Time taken: 45 seconds                                             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  DATABASE: location_match (updated)                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ id: 1                                                         │  │
│  │ case_id: 1 (Rahul Kumar)                                     │  │
│  │ footage_id: 123                                               │  │
│  │ match_score: 0.85                                             │  │
│  │ status: 'completed' ✅                                        │  │
│  │ detection_count: 15                                           │  │
│  │ person_found: True                                            │  │
│  │ confidence_score: 0.893                                       │  │
│  │ ai_analysis_started: 2026-03-02 08:05:00                     │  │
│  │ ai_analysis_completed: 2026-03-02 08:05:45                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ADMIN DASHBOARD: Results displayed                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ ✅ Match 1: Rahul Kumar                                       │  │
│  │    Status: Completed                                          │  │
│  │    Detections: 15 found                                       │  │
│  │    Confidence: 89.3%                                          │  │
│  │    [View Detections] button                                   │  │
│  │                                                               │  │
│  │    Timeline:                                                  │  │
│  │    ├─ 00:04.8 - 91.67% confidence                            │  │
│  │    ├─ 00:12.3 - 88.45% confidence                            │  │
│  │    ├─ 00:18.7 - 92.11% confidence                            │  │
│  │    └─ ... (12 more detections)                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## 🔑 Key Takeaways

1. **Footage Upload** → Automatically creates LocationMatch records
2. **LocationMatch** → Stored with status='pending'
3. **Admin Trigger** → Starts AI analysis
4. **AI Analysis** → Processes video frame-by-frame
5. **Face Detection** → Compares with target profiles
6. **High Confidence** → Saves PersonDetection records (>88%)
7. **Results** → Displayed in admin dashboard

**Total Time:** ~45 seconds for 10-minute video
**Accuracy:** 89.3% average confidence
**Detections:** 15 high-confidence matches found
