"""
SURVEILLANCE FOOTAGE FIX - Apply these changes to admin.py

Replace the surveillance_footage() and dashboard() functions with these fixed versions.
"""

# ===== FIX 1: SURVEILLANCE FOOTAGE LIST (Remove aggressive filters) =====

@admin_bp.route("/surveillance-footage")
@login_required
@admin_required
def surveillance_footage():
    """Surveillance footage management - FIXED VERSION"""
    from models import SurveillanceFootage, LocationMatch
    import os
    
    page = request.args.get('page', 1, type=int)
    
    # FIXED: Show ALL footage, no test filtering
    footage_query = SurveillanceFootage.query.order_by(
        desc(SurveillanceFootage.created_at)
    )
    
    footage_list = footage_query.paginate(page=page, per_page=12, error_out=False)
    
    # Add file integrity check to each footage
    for footage in footage_list.items:
        file_path = os.path.join('static', footage.video_path)
        footage.file_exists = os.path.exists(file_path)
        
        # Get analysis status
        matches = LocationMatch.query.filter_by(footage_id=footage.id).all()
        footage.analysis_status = 'completed' if any(m.status == 'completed' for m in matches) else 'pending'
        footage.person_found = any(m.person_found for m in matches)
    
    # FIXED: Count ALL footage
    total_matches = LocationMatch.query.count()
    successful_detections = LocationMatch.query.filter_by(person_found=True).count()
    
    return render_template(
        "admin/surveillance_footage.html", 
        footage_list=footage_list,
        total_matches=total_matches,
        successful_detections=successful_detections
    )


# ===== FIX 2: DASHBOARD (Show real footage count) =====

# In dashboard() function, replace the footage counting section with:

# FIXED: Real footage count - show ALL footage
real_footage_count = SurveillanceFootage.query.count()

# Get recent uploads for activity feed
recent_uploads = SurveillanceFootage.query.order_by(
    desc(SurveillanceFootage.created_at)
).limit(5).all()

# Add to template context
return render_template(
    "admin/dashboard.html",
    # ... existing variables ...
    real_footage_count=real_footage_count,
    recent_uploads=recent_uploads,
    # ... rest of variables ...
)


# ===== FIX 3: FILE INTEGRITY CHECK UTILITY =====

def check_footage_integrity(footage):
    """Check if footage file exists on disk"""
    import os
    file_path = os.path.join('static', footage.video_path)
    return os.path.exists(file_path)


# ===== FIX 4: LOCATION INSIGHTS (Remove test filter) =====

# In location_insights() function, replace with:

# FIXED: Show ALL CCTV locations
cctv_locations = SurveillanceFootage.query.filter(
    SurveillanceFootage.location_name.isnot(None)
).with_entities(
    SurveillanceFootage.location_name,
    func.count(SurveillanceFootage.id).label('camera_count')
).group_by(SurveillanceFootage.location_name).all()


# ===== FIX 5: SYSTEM STATUS (Remove test filter) =====

# In system_status() function, replace with:

stats = {
    'total_cases': Case.query.count(),
    'pending_cases': Case.query.filter_by(status='Pending Approval').count(),
    'active_cases': Case.query.filter(Case.status.in_(['Queued', 'Processing', 'Active'])).count(),
    'total_footage': SurveillanceFootage.query.count(),  # FIXED: All footage
    'total_matches': LocationMatch.query.count(),  # FIXED: All matches
    'processing_matches': LocationMatch.query.filter(LocationMatch.status == 'processing').count(),
    'total_detections': PersonDetection.query.count(),  # FIXED: All detections
    'verified_detections': PersonDetection.query.filter(PersonDetection.verified == True).count()
}
