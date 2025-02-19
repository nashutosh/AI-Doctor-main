from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from models import db, Session, HealthRecord, Consultation, MedicalReport
import os
from dotenv import load_dotenv
import uuid
from config import Config  # Import the Config class

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Load configuration from Config class
app.config.from_object(Config)

db.init_app(app)

def get_or_create_session():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        db_session = Session(session_id=session['session_id'])
        db.session.add(db_session)
        db.session.commit()
    return Session.query.filter_by(session_id=session['session_id']).first()

@app.route('/')
def index():
    # Check if user is coming for the first time
    if not session.get('visited'):
        session['visited'] = True
        return render_template('splash.html')
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/consultation')
def consultation():
    return render_template('consultation.html')

@app.route('/emergency')
def emergency():
    return render_template('emergency.html')

@app.route('/medication')
def medication():
    return render_template('medication.html')

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/monitoring')
def monitoring():
    return render_template('monitoring.html')

@app.route('/api/health/record', methods=['POST'])
def add_health_record():
    data = request.json
    current_session = get_or_create_session()
    
    record = HealthRecord(
        session_id=current_session.id,
        vital_type=data['type'],
        value=data['value'],
        notes=data.get('notes')
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/health/history')
def get_health_history():
    vital_type = request.args.get('type')
    current_session = get_or_create_session()
    
    records = HealthRecord.query.filter_by(
        session_id=current_session.id,
        vital_type=vital_type
    ).order_by(HealthRecord.timestamp.desc()).limit(10).all()
    
    return jsonify([{
        'value': r.value,
        'timestamp': r.timestamp.isoformat(),
        'notes': r.notes
    } for r in records])

@app.route('/api/consultation', methods=['POST'])
def create_consultation():
    data = request.json
    consultation = Consultation(
        symptoms=data['symptoms']
    )
    # TODO: Integrate with Google Gemini AI
    consultation.ai_response = "AI response placeholder"
    
    db.session.add(consultation)
    db.session.commit()
    return jsonify({'response': consultation.ai_response})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    # TODO: Integrate with Google Gemini AI
    ai_response = "I understand you're experiencing symptoms. While I can provide general information, please consult a healthcare professional for accurate diagnosis and treatment."
    
    return jsonify({
        'response': ai_response
    })

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Add this to handle favicon.ico requests
@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

@app.before_request
def check_first_visit():
    # Skip for static files and the splash screen itself
    if not request.endpoint or \
       request.endpoint.startswith('static') or \
       request.endpoint in ['index', 'home']:
        return
    
    # If haven't seen splash screen, redirect to it
    if not session.get('visited'):
        return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 