# Multi-View Face Tracking - Quick Reference Card

## 🚀 Quick Start (30 seconds)

```python
# 1. Import
from location_matching_engine import LocationMatchingEngine

# 2. Analyze
engine = LocationMatchingEngine()
success = engine.analyze_footage_for_person(match_id=10)

# 3. Done! (Automatically handles multi-view, motion masking, forensic output)
```

---

## 📋 Key Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `MATCH_THRESHOLD` | 0.85 | Min confidence for profile match |
| `TEMPORAL_WINDOW` | 10 frames | Required consecutive detections |
| `TEMPORAL_SPAN` | 2.0 sec | Max time between frames |
| `MOTION_BLUR_THRESHOLD` | 100 | Laplacian variance cutoff |
| `INSET_SIZE` | 28% | Zoom-in inset width |

---

## 🎯 Profile Types

### Filename Convention
```
person_front.jpg        → 'front'
person_left.jpg         → 'left_profile'
person_right.jpg        → 'right_profile'
mugshot_frontal.jpg     → 'front'
side_view_left.jpg      → 'left_profile'
```

---

## 💻 Common Code Patterns

### Pattern 1: Single Frame Detection
```python
from vision_engine import get_vision_engine

engine = get_vision_engine(case_id=1)
result = engine.detect_multi_view(frame, target_profiles, timestamp, case_id)

if result:
    print(f"Match: {result['confidence_score']*100:.1f}%")
```

### Pattern 2: Full Video Analysis
```python
from location_matching_engine import LocationMatchingEngine

engine = LocationMatchingEngine()
engine.analyze_footage_for_person(match_id)
```

### Pattern 3: Batch Processing
```python
from tasks import process_batch_high_precision

task = process_batch_high_precision.delay(case_id, footage_ids)
```

### Pattern 4: Load Profiles
```python
engine = LocationMatchingEngine()
profiles = engine._load_target_profiles(case)
# Returns: {'front': enc1, 'left_profile': enc2, 'right_profile': enc3}
```

### Pattern 5: Verify Evidence
```python
import hashlib
from models import PersonDetection

detection = PersonDetection.query.get(id)
with open(f"static/{detection.frame_path}", 'rb') as f:
    computed = hashlib.sha256(f.read()).hexdigest()

if computed == detection.frame_hash:
    print("✅ Verified")
```

---

## 🎨 Forensic Output Structure

```
Frame Layout:
├── Background (CCTV aesthetic: grain + muted colors)
├── All Faces (thin white boxes, 1px)
├── Target Face (bold white box, 3px)
├── Zoom-In Inset (top-right, 28% width, sharp+bright)
├── Connecting Line (white, 1px, AA)
└── Metadata Overlay (bottom, semi-transparent)
    ├── Evidence Hash (SHA-256, 16 chars)
    ├── Timestamp (YYYY-MM-DD HH:MM:SS)
    └── Stats (Confidence, Profile, Frames)
```

---

## 🔍 Database Queries

### Get Multi-View Detections
```python
from models import PersonDetection

detections = PersonDetection.query.filter_by(
    location_match_id=match_id,
    analysis_method='multi_view_forensic'
).all()
```

### Get High-Confidence Matches
```python
detections = PersonDetection.query.filter(
    PersonDetection.confidence_score >= 0.85,
    PersonDetection.analysis_method == 'multi_view_forensic'
).all()
```

### Get Detections by Profile
```python
import json

detections = PersonDetection.query.filter_by(
    analysis_method='multi_view_forensic'
).all()

for det in detections:
    factors = json.loads(det.decision_factors)
    if 'LEFT_PROFILE' in str(factors):
        print(f"Left profile match: {det.id}")
```

---

## 🐛 Debugging Checklist

### Issue: No matches found
- [ ] Check profile filenames (front/left/right in name?)
- [ ] Verify encodings loaded (`len(target_profiles) > 0`)
- [ ] Check confidence threshold (try lowering to 0.80)
- [ ] Verify temporal window (try reducing to 5 frames)

### Issue: Too many false positives
- [ ] Increase `MATCH_THRESHOLD` to 0.90
- [ ] Increase `TEMPORAL_WINDOW` to 15 frames
- [ ] Check motion blur filtering is active
- [ ] Verify temporal span is 2.0 seconds

### Issue: Forensic output not saving
- [ ] Check directory exists: `static/detections/case_X/`
- [ ] Verify write permissions
- [ ] Check disk space
- [ ] Review logs for errors

### Issue: Slow processing
- [ ] Enable motion masking (should be automatic)
- [ ] Increase frame sampling (every 60 frames instead of 30)
- [ ] Use batch processing for multiple videos
- [ ] Check GPU availability

---

## 📊 Performance Tips

### Optimization 1: Frame Sampling
```python
# Process every N frames
if frame_count % 30 == 0:  # 1 second intervals
    result = engine.detect_multi_view(...)
```

### Optimization 2: Early Exit
```python
# Skip if no motion
if engine._has_motion_blur(frame):
    continue  # Skip blurred frames
```

### Optimization 3: Batch Processing
```python
# Process multiple videos in parallel
from tasks import process_batch_high_precision
task = process_batch_high_precision.delay(case_id, footage_ids)
```

---

## 🔐 Security Checklist

- [ ] SHA-256 hash generated for every forensic frame
- [ ] Evidence number unique (EVD-YYYYMMDDHHMMSSMMM)
- [ ] Timestamp watermarked on output
- [ ] Metadata stored in database
- [ ] Chain of custody maintained
- [ ] File permissions restricted (read-only after creation)

---

## 📈 Monitoring

### Log Levels
```python
import logging

# Enable debug logging
logger = logging.getLogger('multi_view_forensic_engine')
logger.setLevel(logging.DEBUG)
```

### Performance Metrics
```python
import time

start = time.time()
result = engine.detect_multi_view(...)
elapsed = time.time() - start

print(f"Detection: {elapsed:.2f}s")
```

### Memory Usage
```python
import psutil
import os

process = psutil.Process(os.getpid())
memory_mb = process.memory_info().rss / 1024 / 1024
print(f"Memory: {memory_mb:.1f} MB")
```

---

## 🎓 Best Practices

1. ✅ **Always provide multiple profiles** (front + left + right)
2. ✅ **Use descriptive filenames** (person_front.jpg, person_left.jpg)
3. ✅ **Monitor temporal consensus** (check temporal_count in results)
4. ✅ **Verify forensic outputs** (hash verification before legal use)
5. ✅ **Enable motion masking** (automatic, but verify it's working)
6. ✅ **Batch process when possible** (parallel processing is faster)
7. ✅ **Test with diverse footage** (crowded, low-light, motion blur)

---

## 🚨 Common Errors

### Error: "No profiles loaded"
**Solution**: Check image filenames contain 'front', 'left', or 'right'

### Error: "Temporal consensus not reached"
**Solution**: Reduce `TEMPORAL_WINDOW` from 10 to 5 frames

### Error: "Motion mask is None"
**Solution**: Process at least 2 frames to initialize motion mask

### Error: "Frame hash mismatch"
**Solution**: Evidence may be tampered - investigate immediately

---

## 📞 Quick Help

### Documentation
- `MULTI_VIEW_TRACKING_GUIDE.md` - Full guide
- `example_multi_view_usage.py` - 7 examples
- `MULTI_VIEW_IMPLEMENTATION_SUMMARY.md` - Technical details

### Code Locations
- `multi_view_forensic_engine.py` - Core engine
- `vision_engine.py` - Integration layer
- `location_matching_engine.py` - Video analysis

### Key Classes
- `MultiViewForensicEngine` - Main detection engine
- `VisionEngine` - Unified interface
- `LocationMatchingEngine` - Video processing

---

## ✅ Pre-Flight Checklist

Before running analysis:
- [ ] Target images uploaded with correct naming
- [ ] Case approved and active
- [ ] Footage uploaded and accessible
- [ ] Database connection working
- [ ] Sufficient disk space (>1GB per video)
- [ ] Logs enabled for debugging

---

## 🎯 Success Criteria

A successful detection should have:
- ✅ Confidence score ≥ 0.85
- ✅ Temporal count ≥ 10 frames
- ✅ Temporal span ≤ 2.0 seconds
- ✅ Valid SHA-256 hash
- ✅ Forensic output saved
- ✅ Database record created

---

**Quick Reference Version**: 1.0  
**Last Updated**: 2024-01-15  
**Status**: Production Ready
