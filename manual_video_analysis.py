"""
MANUAL VIDEO ANALYSIS SYSTEM
Admin-Controlled Forensic Analysis (No Auto Location Matching)
"""
import os
import json
from flask import Blueprint, request, jsonify, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
from __init__ import db
from models import Case, PersonProfile, PersonDetection
from integrated_case_processor import integrated_processor
from temporal_consensus_engine import temporal_engine
from realworld_cctv_enhancements import smart_sr
import numpy as np

bp = Blueprint('manual_analysis', __name__, url_prefix='/admin/manual-analysis')

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'}

def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

@bp.route('/case/<int:case_id>')
@login_required
def analysis_page(case_id):
    """Admin page to upload and analyze specific video for a case"""
    if not current_user.is_admin:
        flash("Admin access required", "error")
        return redirect(url_for('main.dashboard'))
    
    case = Case.query.get_or_404(case_id)
    
    # Get person profile
    profile = PersonProfile.query.filter_by(case_id=case_id).first()
    
    # Get previous analysis results
    previous_analyses = PersonDetection.query.filter_by(case_id=case_id).order_by(
        PersonDetection.created_at.desc()
    ).limit(10).all()
    
    return render_template(
        'admin/manual_video_analysis.html',
        case=case,
        profile=profile,
        previous_analyses=previous_analyses
    )

@bp.route('/upload-and-analyze/<int:case_id>', methods=['POST'])
@login_required
def upload_and_analyze(case_id):
    """Upload video and trigger AI analysis for specific case"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    case = Case.query.get_or_404(case_id)
    
    # Check if video file uploaded
    if 'video_file' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    video_file = request.files['video_file']
    
    if video_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_video_file(video_file.filename):
        return jsonify({'error': 'Invalid video format'}), 400
    
    try:
        # Save video file
        filename = secure_filename(video_file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"manual_analysis_{case_id}_{timestamp}_{filename}"
        
        upload_dir = os.path.join('static', 'manual_analysis')
        os.makedirs(upload_dir, exist_ok=True)
        
        video_path = os.path.join(upload_dir, unique_filename)
        video_file.save(video_path)
        
        # Get master embedding from PersonProfile
        profile = PersonProfile.query.filter_by(case_id=case_id).first()
        
        if not profile or not profile.master_embedding_512d:
            return jsonify({'error': 'No master embedding found for this case'}), 400
        
        master_embedding = np.array(json.loads(profile.master_embedding_512d))
        
        # Load all profile embeddings for pose-adaptive matching
        master_embeddings = {}
        if profile.front_embedding_512d:
            master_embeddings['front'] = np.array(json.loads(profile.front_embedding_512d))
        if profile.left_profile_embedding_512d:
            master_embeddings['left_profile'] = np.array(json.loads(profile.left_profile_embedding_512d))
        if profile.right_profile_embedding_512d:
            master_embeddings['right_profile'] = np.array(json.loads(profile.right_profile_embedding_512d))
        
        # If no profile embeddings, use master
        if not master_embeddings:
            master_embeddings['front'] = master_embedding
        
        # Trigger AI analysis with temporal consensus
        print(f"🎬 Starting manual analysis for case {case_id}")
        print(f"📹 Video: {unique_filename}")
        
        detections = temporal_engine.analyze_cctv_footage(
            video_path,
            master_embeddings
        )
        
        # Save detections to database with XAI data
        saved_detections = []
        for detection in detections:
            xai_data = detection.get('xai_data', {})
            
            det_record = PersonDetection(
                case_id=case_id,
                timestamp=detection['start_time'],
                confidence_score=detection['avg_confidence'],
                temporal_frame_count=detection['frame_count'],
                temporal_start_frame=detection['start_frame'],
                temporal_end_frame=detection['end_frame'],
                temporal_avg_confidence=detection['avg_confidence'],
                temporal_consensus_verified=True,
                review_status=detection['status'],
                pose_category=detection.get('pose_category', 'unknown'),
                occlusion_detected=detection.get('occlusion_detected', False),
                match_type='manual_analysis',
                analysis_method='manual_admin_upload',
                video_source=unique_filename,
                # XAI Data
                detection_id=xai_data.get('detection_id', ''),
                frame_hash=xai_data.get('frame_hash', ''),
                feature_weights=json.dumps(xai_data.get('feature_weights', {})),
                decision_factors=json.dumps(xai_data.get('decision_factors', [])),
                uncertainty_factors=json.dumps(xai_data.get('uncertainty_factors', [])),
                confidence_category=xai_data.get('confidence_category', 'medium'),
                requires_confirmation=xai_data.get('requires_confirmation', False)
            )
            db.session.add(det_record)
            saved_detections.append({
                'start_time': detection['start_time'],
                'end_time': detection['end_time'],
                'confidence': detection['avg_confidence'],
                'status': detection['status'],
                'frame_count': detection['frame_count'],
                'xai_rationale': xai_data.get('decision_factors', [])
            })
        
        db.session.commit()
        
        print(f"✅ Analysis complete: {len(detections)} detections found")
        
        return jsonify({
            'success': True,
            'detections': saved_detections,
            'total_detections': len(detections),
            'video_path': f"/static/manual_analysis/{unique_filename}"
        })
        
    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@bp.route('/results/<int:case_id>')
@login_required
def view_results(case_id):
    """View all manual analysis results for a case"""
    if not current_user.is_admin:
        flash("Admin access required", "error")
        return redirect(url_for('main.dashboard'))
    
    case = Case.query.get_or_404(case_id)
    
    # Get all detections for this case
    detections = PersonDetection.query.filter_by(
        case_id=case_id,
        match_type='manual_analysis'
    ).order_by(PersonDetection.created_at.desc()).all()
    
    # Group by video source
    grouped_detections = {}
    for det in detections:
        video = det.video_source or 'Unknown'
        if video not in grouped_detections:
            grouped_detections[video] = []
        grouped_detections[video].append(det)
    
    return render_template(
        'admin/manual_analysis_results.html',
        case=case,
        grouped_detections=grouped_detections
    )

@bp.route('/delete-detection/<int:detection_id>', methods=['POST'])
@login_required
def delete_detection(detection_id):
    """Delete a specific detection"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    detection = PersonDetection.query.get_or_404(detection_id)
    case_id = detection.case_id
    
    db.session.delete(detection)
    db.session.commit()
    
    flash("Detection deleted successfully", "success")
    return redirect(url_for('manual_analysis.view_results', case_id=case_id))

# Add to models.py
"""
Add these columns to PersonDetection model:

video_source = db.Column(db.String(200))  # Source video filename
case_id = db.Column(db.Integer, db.ForeignKey('case.id'))  # Direct case reference
"""
