from flask import Blueprint, request, jsonify, current_app, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from src.models.user import db, User, UserProfile
import requests
import secrets
import urllib.parse

auth_github_bp = Blueprint('auth_github', __name__)

def generate_token(user_id):
    """Generate JWT token for user"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7)  # Token expires in 7 days
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    """Verify JWT token and return user_id"""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@auth_github_bp.route('/signup', methods=['POST'])
def signup():
    """User registration endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name', email.split('@')[0])
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'User already exists'}), 409
        
        # Create new user
        user = User(
            email=email,
            name=name
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Create user profile
        profile = UserProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
        
        # Generate token
        token = generate_token(user.id)
        
        return jsonify({
            'user_id': user.id,
            'email': user.email,
            'name': user.name,
            'token': token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_github_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate token
        token = generate_token(user.id)
        
        return jsonify({
            'user_id': user.id,
            'email': user.email,
            'name': user.name,
            'token': token
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed', 'message': str(e)}), 500

@auth_github_bp.route('/github/login', methods=['GET'])
def github_login():
    """Initiate GitHub OAuth login"""
    try:
        # Generate state parameter for security
        state = secrets.token_urlsafe(32)
        session['github_state'] = state
        
        # GitHub OAuth parameters
        github_client_id = current_app.config.get('GITHUB_CLIENT_ID')
        if not github_client_id:
            return jsonify({'error': 'GitHub OAuth not configured'}), 500
        
        # Build GitHub OAuth URL
        params = {
            'client_id': github_client_id,
            'redirect_uri': url_for('auth_github.github_callback', _external=True),
            'scope': 'user:email',
            'state': state
        }
        
        github_url = 'https://github.com/login/oauth/authorize?' + urllib.parse.urlencode(params)
        
        return jsonify({
            'auth_url': github_url,
            'state': state
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_github_bp.route('/github/callback', methods=['GET'])
def github_callback():
    """Handle GitHub OAuth callback"""
    try:
        # Verify state parameter
        state = request.args.get('state')
        if not state or state != session.get('github_state'):
            return jsonify({'error': 'Invalid state parameter'}), 400
        
        # Get authorization code
        code = request.args.get('code')
        if not code:
            return jsonify({'error': 'Authorization code not provided'}), 400
        
        # Exchange code for access token
        token_data = {
            'client_id': current_app.config.get('GITHUB_CLIENT_ID'),
            'client_secret': current_app.config.get('GITHUB_CLIENT_SECRET'),
            'code': code,
            'redirect_uri': url_for('auth_github.github_callback', _external=True)
        }
        
        token_response = requests.post(
            'https://github.com/login/oauth/access_token',
            data=token_data,
            headers={'Accept': 'application/json'}
        )
        
        if token_response.status_code != 200:
            return jsonify({'error': 'Failed to get access token'}), 400
        
        token_info = token_response.json()
        access_token = token_info.get('access_token')
        
        if not access_token:
            return jsonify({'error': 'Access token not received'}), 400
        
        # Get user information from GitHub
        user_response = requests.get(
            'https://api.github.com/user',
            headers={'Authorization': f'token {access_token}'}
        )
        
        if user_response.status_code != 200:
            return jsonify({'error': 'Failed to get user information'}), 400
        
        github_user = user_response.json()
        
        # Get user email if not public
        email = github_user.get('email')
        if not email:
            email_response = requests.get(
                'https://api.github.com/user/emails',
                headers={'Authorization': f'token {access_token}'}
            )
            if email_response.status_code == 200:
                emails = email_response.json()
                primary_email = next((e for e in emails if e['primary']), None)
                if primary_email:
                    email = primary_email['email']
        
        if not email:
            return jsonify({'error': 'Unable to get user email from GitHub'}), 400
        
        # Check if user exists
        github_id = str(github_user['id'])
        user = User.query.filter_by(github_id=github_id).first()
        
        if not user:
            # Check if user exists with same email
            user = User.query.filter_by(email=email).first()
            if user:
                # Link GitHub account to existing user
                user.github_id = github_id
                user.github_username = github_user.get('login')
            else:
                # Create new user
                user = User(
                    email=email,
                    name=github_user.get('name') or github_user.get('login'),
                    github_id=github_id,
                    github_username=github_user.get('login')
                )
                db.session.add(user)
                db.session.commit()
                
                # Create user profile
                profile = UserProfile(user_id=user.id)
                db.session.add(profile)
        
        db.session.commit()
        
        # Generate JWT token
        token = generate_token(user.id)
        
        # Clear session state
        session.pop('github_state', None)
        
        # Return success response with token
        return jsonify({
            'user_id': user.id,
            'email': user.email,
            'name': user.name,
            'github_username': user.github_username,
            'token': token,
            'message': 'GitHub login successful'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_github_bp.route('/google-login', methods=['POST'])
def google_login():
    """Google OAuth login endpoint"""
    try:
        data = request.get_json()
        google_id = data.get('google_id')
        email = data.get('email')
        name = data.get('name', email.split('@')[0] if email else 'User')
        
        if not google_id or not email:
            return jsonify({'error': 'Google ID and email are required'}), 400
        
        # Check if user exists
        user = User.query.filter_by(google_id=google_id).first()
        if not user:
            # Check if user exists with same email
            user = User.query.filter_by(email=email).first()
            if user:
                # Link Google account to existing user
                user.google_id = google_id
            else:
                # Create new user
                user = User(
                    email=email,
                    name=name,
                    google_id=google_id
                )
                db.session.add(user)
                db.session.commit()
                
                # Create user profile
                profile = UserProfile(user_id=user.id)
                db.session.add(profile)
        
        db.session.commit()
        
        # Generate token
        token = generate_token(user.id)
        
        return jsonify({
            'user_id': user.id,
            'email': user.email,
            'name': user.name,
            'token': token
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_github_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user information"""
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = verify_token(token)
        
        if not user_id:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = user.to_dict()
        if user.profile:
            user_data['profile'] = user.profile.to_dict()
        
        return jsonify(user_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_github_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Refresh JWT token"""
    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = verify_token(token)
        
        if not user_id:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Generate new token
        new_token = generate_token(user_id)
        
        return jsonify({'token': new_token}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_github_bp.route('/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    # In a stateless JWT system, logout is handled client-side
    # by removing the token from storage
    return jsonify({'message': 'Logged out successfully'}), 200

