from flask import Blueprint, jsonify, request
from src.models.user import Internship, Application, db
from src.routes.auth import token_required

internships_bp = Blueprint('internships', __name__)

@internships_bp.route('/internships', methods=['GET'])
def get_internships():
    try:
        # Get query parameters for filtering
        query = request.args.get('query', '')
        location = request.args.get('location', '')
        
        # Build query
        internships_query = Internship.query
        
        if query:
            internships_query = internships_query.filter(
                Internship.title.contains(query) | 
                Internship.company.contains(query) |
                Internship.description.contains(query)
            )
        
        if location:
            internships_query = internships_query.filter(
                Internship.location.contains(location)
            )
        
        internships = internships_query.all()
        return jsonify([internship.to_dict() for internship in internships]), 200
        
    except Exception as e:
        return jsonify({'message': 'Internal server error'}), 500

@internships_bp.route('/internships', methods=['POST'])
@token_required
def create_internship(current_user):
    try:
        data = request.json
        title = data.get('title')
        company = data.get('company')
        location = data.get('location')
        description = data.get('description')
        url = data.get('url')
        
        if not all([title, company, location, description, url]):
            return jsonify({'message': 'All fields are required'}), 400
        
        internship = Internship(
            title=title,
            company=company,
            location=location,
            description=description,
            url=url
        )
        
        db.session.add(internship)
        db.session.commit()
        
        return jsonify(internship.to_dict()), 201
        
    except Exception as e:
        return jsonify({'message': 'Internal server error'}), 500

@internships_bp.route('/internships/apply', methods=['POST'])
@token_required
def apply_for_internship(current_user):
    try:
        data = request.json
        internship_id = data.get('internship_id')
        
        if not internship_id:
            return jsonify({'message': 'Internship ID is required'}), 400
        
        # Check if internship exists
        internship = Internship.query.get(internship_id)
        if not internship:
            return jsonify({'message': 'Internship not found'}), 404
        
        # Check if user has already applied
        existing_application = Application.query.filter_by(
            user_id=current_user.id,
            internship_id=internship_id
        ).first()
        
        if existing_application:
            return jsonify({'message': 'Already applied for this internship'}), 409
        
        # Create application
        application = Application(
            user_id=current_user.id,
            internship_id=internship_id,
            status='applied'
        )
        
        db.session.add(application)
        db.session.commit()
        
        return jsonify({
            'application_id': application.id,
            'status': application.status
        }), 201
        
    except Exception as e:
        return jsonify({'message': 'Internal server error'}), 500

@internships_bp.route('/applications', methods=['GET'])
@token_required
def get_user_applications(current_user):
    try:
        applications = Application.query.filter_by(user_id=current_user.id).all()
        return jsonify([application.to_dict() for application in applications]), 200
        
    except Exception as e:
        return jsonify({'message': 'Internal server error'}), 500

@internships_bp.route('/applications/<int:application_id>', methods=['PUT'])
@token_required
def update_application_status(current_user, application_id):
    try:
        data = request.json
        status = data.get('status')
        
        if not status:
            return jsonify({'message': 'Status is required'}), 400
        
        # Valid statuses
        valid_statuses = ['applied', 'interview', 'rejected', 'accepted']
        if status not in valid_statuses:
            return jsonify({'message': 'Invalid status'}), 400
        
        # Find application
        application = Application.query.filter_by(
            id=application_id,
            user_id=current_user.id
        ).first()
        
        if not application:
            return jsonify({'message': 'Application not found'}), 404
        
        application.status = status
        db.session.commit()
        
        return jsonify({
            'application_id': application.id,
            'status': application.status
        }), 200
        
    except Exception as e:
        return jsonify({'message': 'Internal server error'}), 500
