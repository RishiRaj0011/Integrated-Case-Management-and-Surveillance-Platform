# Admin Panel Quick Reference Guide

## 🎯 All Admin Routes - Post-Fix

### 📊 Main Dashboard & Analytics
- **Dashboard**: `/admin/dashboard`
- **Analytics**: `/admin/analytics`
- **Charts & Analytics**: `/admin/charts-analytics`
- **System Status**: `/admin/system-status`
- **System Report**: `/admin/system-report`

### 👥 User Management
- **All Users**: `/admin/users`
- **User Details**: `/admin/users/<user_id>`
- **Export Users**: `/admin/export/users`

### 📋 Case Management
- **All Cases**: `/admin/cases`
- **Case Details**: `/admin/cases/<case_id>`
- **Case Review**: `/admin/cases/<case_id>/review`
- **Case Timeline**: `/admin/case-timeline/<case_id>`
- **Export Cases**: `/admin/export/cases`

### 🎥 Surveillance & AI Analysis
- **Surveillance Footage**: `/admin/surveillance-footage`
- **Upload Footage**: `/admin/surveillance-footage/upload`
- **Enhanced Upload**: `/admin/enhanced/enhanced-surveillance-upload` ⭐ NEW PREFIX
- **AI Analysis Dashboard**: `/admin/ai-analysis`
- **Analysis Details**: `/admin/ai-analysis/<match_id>`
- **Forensic Timeline**: `/admin/ai-analysis/<match_id>/forensic-timeline`

### 🤖 AI Settings & Configuration
- **AI Settings Control Center**: `/admin/ai-settings` ⭐ FIXED
  - Forensic Threshold: 0.50 - 0.99
  - Feature Weights: Facial, Clothing, Temporal
  - Frame Skip Rate: Performance optimization
  - Presets: Forensic, Balanced, Fast

### 🧠 Continuous Learning System
- **Learning Dashboard**: `/admin/learning/continuous-learning` ⭐ NEW PREFIX
- **Record Feedback**: `/admin/learning/record-feedback`
- **Trigger Learning**: `/admin/learning/trigger-learning`
- **Learning Performance**: `/admin/learning/learning-performance`
- **Pattern Analysis**: `/admin/learning/pattern-analysis`

### 📍 Location Intelligence
- **Location Insights**: `/admin/location-insights`
- **Location Matching**: `/admin/location/...` (various routes)

### 📢 Communication
- **Announcements**: `/admin/announcements`
- **Create Announcement**: `/admin/announcements/create`
- **Messages**: `/admin/messages`
- **Contact Messages**: `/admin/contact-messages`
- **Admin Chats**: `/admin/chats`

### 🔍 Advanced Features
- **Confidence Analysis**: `/admin/confidence-analysis`
- **Autonomous Resolution**: `/admin/autonomous-case-resolution`
- **Outcome Prediction**: `/admin/case-outcome-prediction/<case_id>`
- **Batch Analysis**: `/admin/batch-analysis`
- **High-Precision Batch**: `/admin/high-precision-batch-analysis`

### 🛠️ System Management
- **System Self-Management**: `/admin/system-self-management`
- **AI Validation Dashboard**: `/admin/ai-validation-dashboard`
- **Optimize Database**: `/admin/optimize-database` (POST)
- **Clear Cache**: `/admin/clear-cache` (POST)

## 🔧 API Endpoints

### Real-time Status
- `GET /admin/api/notifications` - Admin notification count
- `GET /admin/api/system-status` - System health status
- `GET /admin/api/system-logs` - Recent system logs
- `GET /admin/api/check-analysis-completion` - Completed analyses

### AI & Analysis
- `POST /admin/api/targeted-analysis` - Start targeted deep scan
- `GET /admin/api/batch-progress/<batch_id>` - Batch progress
- `GET /admin/api/hp-batch-progress/<batch_id>` - High-precision progress
- `GET /admin/api/confidence-analysis` - Confidence distribution data

### Learning System
- `POST /admin/learning/record-feedback` - Record admin feedback
- `POST /admin/learning/trigger-learning` - Trigger learning
- `GET /admin/learning/learning-insights` - Get insights

## 🎨 Key Features by Section

### AI Settings Control Center (`/admin/ai-settings`)
```
✅ Forensic Threshold Control (0.88 default)
✅ Feature Weight Management
   - Facial Recognition: 40%
   - Clothing Analysis: 35%
   - Temporal Consistency: 25%
✅ Performance Optimization
   - Frame Skip Rate: 10 (default)
✅ Preset Configurations
   - Forensic Mode (High Accuracy)
   - Balanced Mode
   - Fast Mode (High Speed)
✅ Real-time Testing
```

### Enhanced Surveillance Upload (`/admin/enhanced/enhanced-surveillance-upload`)
```
✅ Large File Support (up to 10GB per file, 50GB total)
✅ Multi-file Upload
✅ Real-time Progress Tracking
✅ Automatic Location Matching
✅ AI Case Matching
✅ Automatic Notifications
```

### Continuous Learning (`/admin/learning/continuous-learning`)
```
✅ Adaptive Thresholds
✅ Pattern Recognition
✅ False Positive Reduction
✅ Performance Metrics
✅ Admin Feedback Integration
✅ Automatic Optimization
```

## 🚀 Quick Actions

### Start AI Analysis
1. Go to `/admin/cases/<case_id>/review`
2. Select footage
3. Click "Start Analysis"

### Upload Surveillance Footage
1. Go to `/admin/enhanced/enhanced-surveillance-upload`
2. Fill location details
3. Upload video files
4. System auto-matches cases

### Adjust AI Sensitivity
1. Go to `/admin/ai-settings`
2. Adjust forensic threshold
3. Modify feature weights
4. Test configuration
5. Save changes

### View Analysis Results
1. Go to `/admin/ai-analysis`
2. Click on match
3. View forensic timeline
4. Download evidence

## 📱 Mobile Access
All routes are responsive and work on mobile devices.

## 🔐 Security
All routes require:
- User authentication (`@login_required`)
- Admin privileges (`@admin_required`)

## 📝 Notes
- All POST endpoints require CSRF token
- API endpoints return JSON responses
- File uploads support chunked transfer
- Real-time updates via SocketIO (where available)

---

**Last Updated**: 2026-03-06
**Version**: Post-Blueprint-Fix
**Status**: All Routes Operational ✅
