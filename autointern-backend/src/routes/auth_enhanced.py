from flask import Blueprint, jsonify, request, current_app
from src.models.user import User, db
import jwt
import datetime
from functools import wraps
import traceback
import requests
import os

auth_bp = Blueprint("auth", __name__)

# JWT secret key (loaded from environment variables)
JWT_SECRET = os.getenv("SECRET_KEY", "your-secret-key-here")

def token_required(f):
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

def verify_google_id_token(id_token):
    try:
        # Google Token Info endpoint
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        claims = response.json()
        
        # Verify audience (client ID)
        if claims["aud"] != current_app.config["GOOGLE_CLIENT_ID"]:
            raise ValueError("Invalid Google Client ID")
        
        # Verify issuer
        if claims["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Invalid issuer")
            
        return claims
    except requests.exceptions.RequestException as e:
        print(f"Error verifying Google ID token: {e}")
        return None
    except ValueError as e:
        print(f"Google ID token verification failed: {e}")
        return None

@auth_bp.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.json
        if not data:
            return jsonify({"message": "No data provided"}), 400
            
        email = data.get("email")
        password = data.get("password")
        
        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"message": "User already exists"}), 409
        
        # Create new user
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Generate token
        token = jwt.encode({
            "user_id": user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)
        }, JWT_SECRET, algorithm="HS256")
        
        return jsonify({
            "user_id": user.id,
            "email": user.email,
            "token": token
        }), 201
        
    except Exception as e:
        print(f"Signup error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        if not data:
            return jsonify({"message": "No data provided"}), 400
            
        email = data.get("email")
        password = data.get("password")
        
        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({"message": "Invalid credentials"}), 401
        
        # Generate token
        token = jwt.encode({
            "user_id": user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)
        }, JWT_SECRET, algorithm="HS256")
        
        return jsonify({
            "user_id": user.id,
            "email": user.email,
            "token": token
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500

@auth_bp.route("/google-login", methods=["POST"])
def google_login():
    try:
        data = request.json
        if not data:
            return jsonify({"message": "No data provided"}), 400
            
        id_token = data.get("id_token") # Changed from google_id to id_token
        
        if not id_token:
            return jsonify({"message": "Google ID token is required"}), 400
        
        claims = verify_google_id_token(id_token)
        if not claims:
            return jsonify({"message": "Invalid Google ID token"}), 401
            
        email = claims.get("email")
        if not email:
            return jsonify({"message": "Email not found in Google ID token"}), 400

        # Find or create user
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, google_id=claims.get("sub")) # sub is Google user ID
            db.session.add(user)
        else:
            if not user.google_id:
                user.google_id = claims.get("sub")
        
        db.session.commit()
        
        # Generate token
        token = jwt.encode({
            "user_id": user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30)
        }, JWT_SECRET, algorithm="HS256")
        
        return jsonify({
            "user_id": user.id,
            "email": user.email,
            "token": token
        }), 200
        
    except Exception as e:
        print(f"Google login error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500

@auth_bp.route("/me", methods=["GET"])
@token_required
def get_current_user(current_user):
    return jsonify(current_user.to_dict()), 200

@auth_bp.route("/google_config", methods=["GET"])
def google_config():
    return jsonify({
        "GOOGLE_CLIENT_ID": current_app.config["GOOGLE_CLIENT_ID"]
    })
