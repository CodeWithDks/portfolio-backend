from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key")  # Required for Flask-Login
CORS(app)  # Enable CORS for all routes

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "portfolio_db"
COLLECTION_NAME = "submissions"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Dummy user for demonstration
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Hardcoded user credentials (replace with a database in production)
USERS = {
    "Radhe": "Radhemaaji@09"
}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)




@app.route("/test_db")
def test_db():
    try:
        collection.insert_one({"test": "MongoDB is connected!"})
        return "✅ MongoDB Connection Successful!"
    except Exception as e:
        return f"❌ MongoDB Connection Failed: {e}"
    



@app.route("/api/contact", methods=["POST"])
def contact():
    try:
        data = request.json  # Get JSON data from the frontend
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Insert data into MongoDB
        collection.insert_one(data)

        return jsonify({"message": "Contact form submitted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500





@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in USERS and USERS[username] == password:
            user = User(username)
            login_user(user)
            return redirect("/admin")
        return "Invalid credentials", 401
    return """
    <form method="POST">
        <label>Username:</label>
        <input type="text" name="username"><br>
        <label>Password:</label>
        <input type="password" name="password"><br>
        <button type="submit">Login</button>
    </form>
    """

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route("/admin")
@login_required
def admin():
    return render_template("admin.html")

@app.route("/api/submissions", methods=["GET"])
@login_required
def get_submissions():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        skip = (page - 1) * per_page

        # Fetch paginated submissions from MongoDB
        submissions = list(collection.find({}, {"_id": 0}).skip(skip).limit(per_page))
        total = collection.count_documents({})

        return jsonify({
            "submissions": submissions,
            "total": total,
            "page": page,
            "per_page": per_page
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/submissions/search", methods=["GET"])
@login_required
def search_submissions():
    try:
        query = request.args.get("query", "")
        field = request.args.get("field", "name")  # Default to searching by name

        # Build the MongoDB query
        search_query = {field: {"$regex": query, "$options": "i"}}  # Case-insensitive search

        # Fetch filtered submissions
        submissions = list(collection.find(search_query, {"_id": 0}))
        return jsonify(submissions), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)