from functools import wraps
from flask import request, jsonify, current_app
import jwt
from models import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        print("Raw Authorization header:", token)

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            # Extract token from "Bearer <token>"
            if not token.startswith("Bearer "):
                return jsonify({'message': 'Invalid token format'}), 401
            token = token.split(" ")[1]
            print("Token string:", token)

            # Decode token using the app's secret key
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            print("Decoded JWT payload:", data)

            # Fetch user from DB
            current_user = User.query.get(data['user_id'])
            if not current_user:
                print("User not found in database.")
                return jsonify({'message': 'User not found'}), 404

        except jwt.ExpiredSignatureError:
            print("Token expired.")
            return jsonify({'message': 'Token has expired'}), 401

        except jwt.InvalidTokenError as e:
            print("JWT decode error:", e)
            return jsonify({'message': 'Invalid token'}), 401

        return f(current_user, *args, **kwargs)

    return decorated