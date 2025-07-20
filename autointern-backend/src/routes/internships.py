from flask import Blueprint, request, jsonify
from src.models.user import db, Internship, Application, ApplicationTracking
from src.routes.auth import verify_token
from datetime import datetime

internships_bp = Blueprint('internships', __name__)

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = verify_token(token)
        
        if not user_id:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.current_user_id = user_id
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@internships_bp.route('/internships', methods=['GET'])
@require_auth
def get_internships():
    """Get all internships with optional filtering"""
    try:
        # Get query parameters
        query = request.args.get('query', '')
        location = request.args.get('location', '')
        company = request.args.get('company', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Build query
        internships_query = Internship.query
        
        if query:
            internships_query = internships_query.filter(
                Internship.title.contains(query) | 
                Internship.description.contains(query) |
                Internship.requirements.contains(query)
            )
        
        if location:
            internships_query = internships_query.filter(
                Internship.location.contains(location)
            )
        
        if company:
            internships_query = internships_query.filter(
                Internship.company.contains(company)
            )
        
        # Order by creation date (newest first)
        internships_query = internships_query.order_by(Internship.created_at.desc())
        
        # Paginate
        internships = internships_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'internships': [internship.to_dict() for internship in internships.items],
            'total': internships.total,
            'pages': internships.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@internships_bp.route('/internships/<int:internship_id>', methods=['GET'])
@require_auth
def get_internship(internship_id):
    """Get specific internship by ID"""
    try:
        internship = Internship.query.get(internship_id)
        if not internship:
            return jsonify({'error': 'Internship not found'}), 404
        
        return jsonify(internship.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@internships_bp.route('/internships/apply', methods=['POST'])
@require_auth
def apply_to_internship():
    """Apply to an internship"""
    try:
        data = request.get_json()
        internship_id = data.get('internship_id')
        cover_letter = data.get('cover_letter', '')
        resume_url = data.get('resume_url', '')
        notes = data.get('notes', '')
        
        if not internship_id:
            return jsonify({'error': 'Internship ID is required'}), 400
        
        # Check if internship exists
        internship = Internship.query.get(internship_id)
        if not internship:
            return jsonify({'error': 'Internship not found'}), 404
        
        # Check if user already applied
        existing_application = Application.query.filter_by(
            user_id=request.current_user_id,
            internship_id=internship_id
        ).first()
        
        if existing_application:
            return jsonify({'error': 'You have already applied to this internship'}), 409
        
        # Create application
        application = Application(
            user_id=request.current_user_id,
            internship_id=internship_id,
            cover_letter=cover_letter,
            resume_url=resume_url,
            notes=notes,
            status='submitted'
        )
        
        db.session.add(application)
        db.session.commit()
        
        # Create tracking entry
        tracking = ApplicationTracking(
            application_id=application.id,
            status='submitted',
            notes='Application submitted',
            changed_by=request.current_user_id
        )
        
        db.session.add(tracking)
        db.session.commit()
        
        return jsonify(application.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@internships_bp.route('/applications', methods=['GET'])
@require_auth
def get_user_applications():
    """Get current user's applications"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        status = request.args.get('status', '')
        
        # Build query
        applications_query = Application.query.filter_by(user_id=request.current_user_id)
        
        if status:
            applications_query = applications_query.filter_by(status=status)
        
        # Order by application date (newest first)
        applications_query = applications_query.order_by(Application.applied_date.desc())
        
        # Paginate
        applications = applications_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'applications': [app.to_dict() for app in applications.items],
            'total': applications.total,
            'pages': applications.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@internships_bp.route('/applications/<int:application_id>', methods=['GET'])
@require_auth
def get_application(application_id):
    """Get specific application"""
    try:
        application = Application.query.get(application_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Check if user owns this application
        if application.user_id != request.current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        app_data = application.to_dict()
        # Include tracking history
        app_data['tracking'] = [track.to_dict() for track in application.tracking]
        
        return jsonify(app_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@internships_bp.route('/applications/<int:application_id>', methods=['PUT'])
@require_auth
def update_application(application_id):
    """Update application"""
    try:
        application = Application.query.get(application_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Check if user owns this application
        if application.user_id != request.current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        old_status = application.status
        
        # Update application fields
        updatable_fields = ['status', 'cover_letter', 'resume_url', 'notes', 'interview_date']
        
        for field in updatable_fields:
            if field in data:
                if field == 'interview_date' and data[field]:
                    # Parse interview date
                    application.interview_date = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                else:
                    setattr(application, field, data[field])
        
        db.session.commit()
        
        # Create tracking entry if status changed
        if 'status' in data and data['status'] != old_status:
            tracking = ApplicationTracking(
                application_id=application.id,
                status=data['status'],
                notes=data.get('status_notes', f'Status changed to {data["status"]}'),
                changed_by=request.current_user_id
            )
            db.session.add(tracking)
            db.session.commit()
        
        return jsonify(application.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@internships_bp.route('/applications/<int:application_id>', methods=['DELETE'])
@require_auth
def delete_application(application_id):
    """Delete application"""
    try:
        application = Application.query.get(application_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Check if user owns this application
        if application.user_id != request.current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        db.session.delete(application)
        db.session.commit()
        
        return jsonify({'message': 'Application deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
