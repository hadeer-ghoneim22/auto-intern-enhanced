"""
Authentication utility functions and decorators
"""
import jwt
import os
from functools import wraps
from flask import request, jsonify, current_app
from src.models.user import User

# JWT secret key (loaded from environment variables)
JWT_SECRET = os.getenv("SECRET_KEY", "your-secret-key-here")

def token_required(f):
    """
    Decorator to require JWT token authentication
    Usage: @token_required
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        
        try:
            if token.startswith("Bearer "):
                token = token[7:]
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            current_user = User.query.get(data["user_id"])
            if not current_user:
                return jsonify({"message": "Invalid token"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

def require_auth(f):
    """
    Alternative authentication decorator that adds user_id to request context
    Usage: @require_auth
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = data.get("user_id")
            if not user_id:
                return jsonify({'error': 'Invalid token'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Add user_id to request context
        request.current_user_id = user_id
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

def verify_token(token):
    """
    Verify JWT token and return user_id
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def generate_token(user_id, expires_days=30):
    """
    Generate JWT token for user
    """
    import datetime
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=expires_days)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')
