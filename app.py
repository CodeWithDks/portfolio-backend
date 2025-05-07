from flask import Flask, request, jsonify, render_template, redirect, send_from_directory, abort, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv
from bson import ObjectId
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets'))
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key")
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

# Initialize rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

CORS(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["portfolio_db"]
submissions_collection = db["submissions"]  # Renamed for clarity
users_collection = db["users"]
blogs_collection = db["blogs"]

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.role = user_data.get('role', 'user')

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    return User(user_data) if user_data else None

def create_initial_admin():
    if not users_collection.find_one({'role': 'admin'}):
        users_collection.insert_one({
            'username': os.getenv('ADMIN_USERNAME', 'admin'),
            'password': generate_password_hash(os.getenv('ADMIN_PASSWORD', 'admin123')),
            'role': 'admin',
            'created_at': datetime.utcnow()
        })

create_initial_admin()

# ======================
# ROUTES
# ======================

# Main routes
@app.route('/')
def serve_root():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return send_from_directory(root_dir, 'index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(app.static_folder, filename)

# Authentication routes
@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")
        
        user_data = users_collection.find_one({'username': username})
        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data)
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        
        flash('Invalid username or password', 'error')
        return redirect(url_for('login'))
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('serve_root'))

# Admin routes
@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        abort(403)
    
    stats = {
        'submissions_count': submissions_collection.count_documents({}),
        'unread_count': submissions_collection.count_documents({'read': False}),
        'blogs_count': blogs_collection.count_documents({}),
        'recent_messages': list(submissions_collection.find().sort("created_at", -1).limit(5))
    }
    
    # Convert ObjectIds to strings
    for msg in stats['recent_messages']:
        msg['_id'] = str(msg['_id'])
    
    return render_template("admin_dashboard.html", stats=stats)

@app.route("/admin/submissions")
@login_required
def view_submissions():
    if current_user.role != 'admin':
        abort(403)
    
    page = int(request.args.get("page", 1))
    per_page = 10
    skip = (page - 1) * per_page
    
    submissions = list(submissions_collection.find().sort("created_at", -1).skip(skip).limit(per_page))
    total = submissions_collection.count_documents({})
    
    for sub in submissions:
        sub['_id'] = str(sub['_id'])
    
    return render_template("submissions.html", 
                         submissions=submissions,
                         page=page,
                         per_page=per_page,
                         total=total)

# API routes
@app.route("/api/contact", methods=["POST"])
@limiter.limit("5 per minute")
def contact():
    try:
        data = request.get_json()
        if not data or not all(field in data for field in ['name', 'email', 'message']):
            return jsonify({"error": "Missing required fields"}), 400
        
        data.update({
            'created_at': datetime.utcnow(),
            'read': False
        })
        
        result = submissions_collection.insert_one(data)
        return jsonify({
            "message": "Thank you for your message!",
            "id": str(result.inserted_id)
        }), 200
        
    except Exception as e:
        app.logger.error(f"Contact form error: {str(e)}")
        return jsonify({"error": "Server error"}), 500

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(debug=True)