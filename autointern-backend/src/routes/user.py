from flask import Blueprint, request, jsonify
from src.models.user import db, User, UserProfile
from src.routes.auth import verify_token

user_bp = Blueprint('user', __name__)

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
        
        # Add user_id to request context
        request.current_user_id = user_id
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@user_bp.route('/users/<int:user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    """Get user by ID"""
    try:
        # Users can only access their own data or this could be admin-only
        if request.current_user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = user.to_dict()
        if user.profile:
            user_data['profile'] = user.profile.to_dict()
        
        return jsonify(user_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@require_auth
def update_user(user_id):
    """Update user information"""
    try:
        # Users can only update their own data
        if request.current_user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update user fields
        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            # Check if email is already taken
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({'error': 'Email already taken'}), 409
            user.email = data['email']
        
        db.session.commit()
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>/profile', methods=['GET'])
@require_auth
def get_user_profile(user_id):
    """Get user profile"""
    try:
        if request.current_user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.profile:
            # Create empty profile if it doesn't exist
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
            db.session.commit()
            user.profile = profile
        
        return jsonify(user.profile.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>/profile', methods=['PUT'])
@require_auth
def update_user_profile(user_id):
    """Update user profile"""
    try:
        if request.current_user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.profile:
            user.profile = UserProfile(user_id=user_id)
            db.session.add(user.profile)
        
        data = request.get_json()
        profile = user.profile
        
        # Update profile fields
        updatable_fields = [
            'first_name', 'last_name', 'phone', 'linkedin_url', 
            'github_url', 'portfolio_url', 'skills', 'education', 
            'experience', 'bio', 'avatar_url'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(profile, field, data[field])
        
        db.session.commit()
        
        return jsonify(profile.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_auth
def delete_user(user_id):
    """Delete user account"""
    try:
        if request.current_user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
