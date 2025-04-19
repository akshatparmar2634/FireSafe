from flask import request, jsonify, Response
from models import db, User, Feed
from auth import token_required
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta

def init_routes(app):
    WEBSOCKET_PORT = 8765  # Must match the port used in app.py

    @app.route('/signup', methods=['POST'])
    def signup():
        print("[ROUTE DEBUG] Received signup request")
        try:
            data = request.json
            print(data)
            if not data or 'email' not in data or 'password' not in data:
                print("[ROUTE DEBUG] Missing email or password in signup")
                return jsonify({'message': 'Missing email or password'}), 400
            
            if User.query.filter_by(email=data['email']).first():
                print("[ROUTE DEBUG] Email already registered")
                return jsonify({'message': 'Email already registered'}), 400
            
            hashed_password = generate_password_hash(data['password'])
            new_user = User(email=data['email'], password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            print("[ROUTE DEBUG] User created successfully")
            return jsonify({'message': 'User created successfully'}), 201
        except Exception as e:
            print(f"[ROUTE DEBUG] Signup error: {e}")
            return jsonify({'message': 'Server error'}), 500

    @app.route('/login', methods=['POST'])
    def login():
        print("[ROUTE DEBUG] Received login request")
        try:
            data = request.json
            if not data or 'email' not in data or 'password' not in data:
                print("[ROUTE DEBUG] Missing email or password in login")
                return jsonify({'message': 'Missing email or password'}), 400
            
            print(f"[ROUTE DEBUG] Login attempt: {data}")
            user = User.query.filter_by(email=data['email']).first()
            
            if user and check_password_hash(user.password, data['password']):
                token = jwt.encode({
                    'user_id': user.id,
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }, app.config['SECRET_KEY'])
                print(f"[ROUTE DEBUG] Generated token: {token}")
                return jsonify({'token': token})
            
            print("[ROUTE DEBUG] Invalid credentials")
            return jsonify({'message': 'Invalid credentials'}), 401
        except Exception as e:
            print(f"[ROUTE DEBUG] Login error: {e}")
            return jsonify({'message': 'Server error'}), 500

    @app.route('/feeds', methods=['GET'])
    @token_required
    def get_feeds(current_user):
        print(f"[ROUTE DEBUG] Fetching feeds for user: {current_user}")
        feeds = Feed.query.filter_by(user_id=current_user.id).all()
        return jsonify([{
            'id': feed.id,
            'name': feed.name,
            'location': feed.location,
            'rtsp_url': feed.rtsp_url,
            'fireDetected': feed.fire_detected,
            'lastFireTime': feed.last_fire_detected_time,
            'status': feed.status
        } for feed in feeds])

    @app.route('/feeds', methods=['POST'])
    @token_required
    def add_feed(current_user):
        print("[ROUTE DEBUG] Received add feed request")
        try:
            data = request.json
            name = data.get('name')
            location = data.get('location')
            ip = data.get('ip')
            username = data.get('username')
            password = data.get('password')

            if not all([name, location, ip, username, password]):
                print("[ROUTE DEBUG] Missing required fields in add feed")
                return jsonify({'message': 'Missing required fields'}), 400

            rtsp_url = f"rtsp://{username}:{password}@{ip}:554/stream1"
            new_feed = Feed(
                name=name,
                location=location,
                rtsp_url=rtsp_url,
                user_id=current_user.id
            )
            db.session.add(new_feed)
            db.session.commit()

            print(f"[ROUTE DEBUG] Feed added successfully: {new_feed}")
            return jsonify({
                'id': new_feed.id,
                'name': new_feed.name,
                'location': new_feed.location,
                'rtsp_url': new_feed.rtsp_url,
                'fireDetected': new_feed.fire_detected,
                'lastFireTime': new_feed.last_fire_detected_time,
                'status': new_feed.status
            }), 201
        except Exception as e:
            print(f"[ROUTE DEBUG] Add feed error: {e}")
            return jsonify({'message': 'Server error'}), 500
    
    @app.route('/feeds/<int:feed_id>', methods=['GET'])
    @token_required
    def get_single_feed(current_user, feed_id):
        print(f"[ROUTE DEBUG] Fetching feed {feed_id} for user {current_user}")
        feed = Feed.query.filter_by(id=feed_id, user_id=current_user.id).first()
        if not feed:
            print("[ROUTE DEBUG] Feed not found")
            return jsonify({'message': 'Feed not found'}), 404

        return jsonify({
            'id': feed.id,
            'name': feed.name,
            'location': feed.location,
            'rtsp_url': feed.rtsp_url,
            'fireDetected': feed.fire_detected,
            'lastFireTime': feed.last_fire_detected_time,
            'status': feed.status
        })

    @app.route('/feeds/<int:feed_id>/stream', methods=['GET'])
    @token_required
    def video_feed_info(current_user, feed_id):
        print(f"[ROUTE DEBUG] Request for video stream info for feed_id: {feed_id}, user_id: {current_user.id}")
        feed = Feed.query.filter_by(id=feed_id, user_id=current_user.id).first()
        if not feed:
            print(f"[ROUTE DEBUG] Feed {feed_id} not found for user {current_user.id}")
            return jsonify({'message': 'Feed not found'}), 404

        # For an Android emulator, use 10.0.2.2 as the IP address.
        websocket_url = f'ws://10.0.2.2:{WEBSOCKET_PORT}/feeds/{feed_id}'
        print(f"[ROUTE DEBUG] Returning WebSocket URL: {websocket_url}")
        return jsonify({
            'message': 'Connect to WebSocket for streaming',
            'websocket_url': websocket_url
        })
