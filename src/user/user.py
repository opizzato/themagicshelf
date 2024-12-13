import flask
import json
from flask_bcrypt import Bcrypt 
import logging
import os
import jwt

logger = logging.getLogger(__name__)
bcrypt = Bcrypt()

def check_run_id_does_not_exist(run_id):
    return not os.path.exists(os.path.join("output", run_id))

def create_user_profile(email, password, api_key = None):
    # Create users directory if it doesn't exist
    users_dir = "users"
    if not os.path.exists(users_dir):
        os.makedirs(users_dir)
        
    # check if user profile file exists
    user_file = os.path.join(users_dir, f"{email}.json")
    if os.path.exists(user_file):
        return False

    # generate a unique run_id from shortened hashed email
    run_id = bcrypt.generate_password_hash(email).decode('utf-8')[-8:]
    while not check_run_id_does_not_exist(run_id):
        run_id = bcrypt.generate_password_hash(email).decode('utf-8')[-8:]
    logger.info(f"Generated run_id: {run_id}")

    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    logger.info(f"Hash: {password_hash}")
    user_data = {
        "email": email,
        "password": password_hash,
        "api_key": api_key,
        "run_id": run_id
    }

    auto_check = bcrypt.check_password_hash(password_hash, password) # returns True
    logger.info(f"Auto check: {auto_check}")

    with open(user_file, 'w') as f:
        json.dump(user_data, f, indent=2)

    return True

def update_user_profile(email, password = None, api_key = None):
    # Create users directory if it doesn't exist
    users_dir = "users"
    if not os.path.exists(users_dir):
        os.makedirs(users_dir)
        
    # Create or update user profile file
    user_file = os.path.join(users_dir, f"{email}.json")
    if not os.path.exists(user_file):
        return False
    
    user_data = json.load(open(user_file))
    user_data = {
        "email": email,
        "password": user_data.get("password", None),
        "api_key": user_data.get("api_key", api_key),
        "run_id": user_data.get("run_id", None)
    }
    
    # Hash password if provided
    if password:
        user_data["password"] = bcrypt.generate_password_hash(password).decode('utf-8')
    with open(user_file, 'w') as f:
        json.dump(user_data, f, indent=2)

    return True

def get_user_profile(email):
    user_file = os.path.join("users", f"{email}.json")
    if not os.path.exists(user_file):
        return None
    return json.load(open(user_file))

def check_user_password_from_profile(user_profile, password):
    return bcrypt.check_password_hash(user_profile["password"], password)

def check_user_password(email, password):
    user_profile = get_user_profile(email)
    return user_profile and check_user_password_from_profile(user_profile, password)


def create_token(email, api_key=None, run_id=None):
    return jwt.encode(
        {"email": email, "api_key": api_key, "run_id": run_id},
        os.environ.get("SECRET_KEY") or "secret",
        algorithm='HS256'
    )

def decode_token(token):
    return jwt.decode(token, os.environ.get("SECRET_KEY") or "secret", algorithms=['HS256'])


def require_auth(f):
    def decorated_function(*args, **kwargs):
        auth_header = flask.request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return flask.jsonify({
                "error": "Missing or invalid authorization header"
            }), 401
            
        token = auth_header.split(' ')[1]
        try:
            decoded = decode_token(token)
            flask.g.user_email = decoded['email']
            flask.g.user_api_key = decoded['api_key']
            flask.g.user_run_id = decoded['run_id']
            logger.info(f"decoded user token: {flask.g.user_email=} {flask.g.user_api_key=} {flask.g.user_run_id=}")
            return f(*args, **kwargs)
        except jwt.InvalidTokenError:
            return flask.jsonify({
                "error": "Invalid token"
            }), 401

    decorated_function.__name__ = f.__name__
    return decorated_function

def save_api_key_in_profile(email, api_key):
    user_profile = get_user_profile(email)
    if not user_profile:
        return False
    user_profile["api_key"] = api_key
    with open(os.path.join("users", f"{email}.json"), 'w') as f:
        json.dump(user_profile, f, indent=2)
    return True
