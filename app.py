from flask import Flask, request, jsonify, abort
from flask_migrate import Migrate
from functools import wraps
import datetime
from models import db, User, Session

def create_app():
    app = Flask(__name__)
    # Update with your MySQL credentials and database name.
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://<username>:<password>@<host>/<database>'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    Migrate(app, db)

    register_routes(app)
    return app

# API Key Authentication
API_KEY = "<your-api-key>"

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('x-api-key')
        if key != API_KEY:
            abort(401, description="Unauthorized: API key is missing or incorrect.")
        return f(*args, **kwargs)
    return decorated

# Dummy geolocation lookup – replace with real API in production.
def get_geolocation(ip):
    return {"country": "USA", "city": "New York"}

def collect_data_endpoint():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = ["user_id", "page", "session_time", "referral_source", "user_agent"]
    missing = [field for field in required_fields if field not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    ip_address = request.remote_addr
    location = get_geolocation(ip_address)
    now = datetime.datetime.utcnow()

    # Create or update user.
    user = User.query.get(data["user_id"])
    if not user:
        user = User(
            user_id=data["user_id"],
            ip_address=ip_address,
            location_country=location.get("country"),
            location_city=location.get("city"),
            first_login=now
        )
        db.session.add(user)
    # Record a new session.
    session_record = Session(
        user_id=data["user_id"],
        page=data["page"],
        session_time=data["session_time"],
        referral_source=data["referral_source"],
        user_agent=data["user_agent"],
        feedback=data.get("feedback", ""),
        timestamp=now
    )
    db.session.add(session_record)
    db.session.commit()
    return jsonify({"message": "Data collected successfully"}), 200

def register_routes(app):
    app.add_url_rule('/api/collect', 'collect_data', require_api_key(collect_data_endpoint), methods=['POST'])

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Optionally, create tables if not already present.
        # db.create_all()
        pass
    app.run(debug=True)
