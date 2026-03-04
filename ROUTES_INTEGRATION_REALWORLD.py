"""
ROUTES.PY INTEGRATION CODE
Handle FLAGGED_FOR_REVIEW status in case registration
"""

# Add this code to routes.py in register_case function

"""
# After processing_result is obtained:

if not processing_result['success']:
    # Validation failed
    new_case.status = 'Rejected'
    error_details = "\\n".join([
        "❌ VALIDATION FAILED",
        "",
        "🔍 ISSUES:",
        *[f"• {error}" for error in processing_result['errors']],
    ])
    new_case.admin_message = error_details
    db.session.commit()
    flash("Case validation failed. Please review and resubmit.", "error")
    return redirect(url_for("main.profile"))

# Check review status
review_status = processing_result['validations'].get('consistency', {}).get('review_status', 'AUTO_APPROVED')

if review_status == 'AUTO_APPROVED':
    # High confidence (97%+) - Auto approve
    new_case.status = 'Approved'
    new_case.admin_message = f\"\"\"✅ AUTO-APPROVED (High Confidence)
    
📊 VALIDATION RESULTS:
• Confidence: {processing_result['validations']['consistency']['confidence_score']:.2%}
• Status: AUTO_APPROVED (97%+ threshold)
• Sources: {processing_result['embeddings']['num_sources']} verified
• FAISS Position: {processing_result['faiss_position']}

🎯 QUALITY METRICS:
• Liveness: ✅ Verified
• Consistency: ✅ Passed
• Multi-angle: ✅ {', '.join(processing_result['embeddings']['photo_views'])}

✅ Case ready for CCTV analysis with pose-adaptive matching.
\"\"\"
    
    flash(f"Case approved! Confidence: {processing_result['validations']['consistency']['confidence_score']:.0%}", "success")

elif review_status == 'FLAGGED_FOR_REVIEW':
    # Medium confidence (90-97%) - Flag for human review
    new_case.status = 'Pending Approval'  # Keep pending for admin review
    new_case.admin_message = f\"\"\"⚠️ FLAGGED FOR HUMAN REVIEW
    
📊 VALIDATION RESULTS:
• Confidence: {processing_result['validations']['consistency']['confidence_score']:.2%}
• Status: FLAGGED_FOR_REVIEW (90-97% range)
• Sources: {processing_result['embeddings']['num_sources']} verified
• FAISS Position: {processing_result['faiss_position']}

🎯 QUALITY METRICS:
• Liveness: ✅ Verified
• Consistency: ⚠️ Borderline (needs review)
• Multi-angle: {', '.join(processing_result['embeddings']['photo_views'])}

💡 ADMIN ACTION REQUIRED:
This case has moderate confidence (90-97%). Please review:
1. Check photo quality and angles
2. Verify person consistency manually
3. Approve or request better photos

⏳ Awaiting admin decision for final approval.
\"\"\"
    
    # Notify admins
    from models import User, Notification
    admins = User.query.filter_by(is_admin=True).all()
    for admin in admins:
        notification = Notification(
            user_id=admin.id,
            sender_id=current_user.id,
            title=f"⚠️ Review Required: {new_case.person_name}",
            message=f"Case flagged for review. Confidence: {processing_result['validations']['consistency']['confidence_score']:.0%} (90-97% range). Please review and approve/reject.",
            type="warning",
            related_url=f"/admin/cases/{new_case.id}",
            created_at=get_ist_now()
        )
        db.session.add(notification)
    
    flash(f"Case submitted for review. Confidence: {processing_result['validations']['consistency']['confidence_score']:.0%}", "info")

else:
    # Low confidence (<90%) - Reject
    new_case.status = 'Rejected'
    new_case.admin_message = f\"\"\"❌ REJECTED (Low Confidence)
    
📊 VALIDATION RESULTS:
• Confidence: {processing_result['validations']['consistency']['confidence_score']:.2%}
• Status: REJECTED (Below 90% threshold)

🎯 ISSUES DETECTED:
{chr(10).join([f'• {error}' for error in processing_result['errors']])}

💡 PLEASE IMPROVE:
• Upload clearer photos from multiple angles
• Ensure all photos show the same person
• Use live photos (not screen captures)
• Include front, left, and right profile views

🔄 Resubmit after addressing these issues.
\"\"\"
    
    flash("Case rejected due to low confidence. Please improve photo quality.", "error")

db.session.commit()
"""

# ============================================
# ADMIN DASHBOARD - REVIEW QUEUE
# ============================================

"""
Add this route to admin.py:

@bp.route('/review-queue')
@login_required
@admin_required
def review_queue():
    '''Show all cases flagged for human review'''
    
    # Get cases with FLAGGED_FOR_REVIEW status
    flagged_cases = Case.query.filter(
        Case.status == 'Pending Approval',
        Case.admin_message.like('%FLAGGED FOR HUMAN REVIEW%')
    ).order_by(Case.created_at.desc()).all()
    
    # Get detection results for each case
    review_data = []
    for case in flagged_cases:
        # Get person profile
        profile = PersonProfile.query.filter_by(case_id=case.id).first()
        
        # Get latest detections
        detections = PersonDetection.query.join(LocationMatch).filter(
            LocationMatch.case_id == case.id,
            PersonDetection.review_status == 'FLAGGED_FOR_REVIEW'
        ).order_by(PersonDetection.created_at.desc()).limit(5).all()
        
        review_data.append({
            'case': case,
            'profile': profile,
            'detections': detections,
            'confidence': profile.fusion_confidence if profile else 0.0
        })
    
    return render_template('admin/review_queue.html', review_data=review_data)


@bp.route('/review-case/<int:case_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_flagged_case(case_id):
    '''Manually approve a flagged case'''
    case = Case.query.get_or_404(case_id)
    
    case.status = 'Approved'
    case.admin_message += f\"\\n\\n✅ MANUALLY APPROVED by {current_user.username} on {get_ist_now().strftime('%Y-%m-%d %H:%M')}\"
    
    # Notify user
    notification = Notification(
        user_id=case.user_id,
        sender_id=current_user.id,
        title=f"✅ Case Approved: {case.person_name}",
        message=f"Your case has been manually reviewed and approved by admin. CCTV analysis will now proceed.",
        type="success",
        created_at=get_ist_now()
    )
    db.session.add(notification)
    db.session.commit()
    
    flash(f"Case {case_id} approved successfully!", "success")
    return redirect(url_for('admin.review_queue'))


@bp.route('/review-case/<int:case_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_flagged_case(case_id):
    '''Manually reject a flagged case'''
    case = Case.query.get_or_404(case_id)
    rejection_reason = request.form.get('reason', 'Quality not sufficient')
    
    case.status = 'Rejected'
    case.admin_message += f\"\\n\\n❌ MANUALLY REJECTED by {current_user.username} on {get_ist_now().strftime('%Y-%m-%d %H:%M')}\\nReason: {rejection_reason}\"
    
    # Notify user
    notification = Notification(
        user_id=case.user_id,
        sender_id=current_user.id,
        title=f"❌ Case Rejected: {case.person_name}",
        message=f"Your case was reviewed and rejected. Reason: {rejection_reason}. Please improve and resubmit.",
        type="error",
        created_at=get_ist_now()
    )
    db.session.add(notification)
    db.session.commit()
    
    flash(f"Case {case_id} rejected.", "info")
    return redirect(url_for('admin.review_queue'))
"""

print(__doc__)
