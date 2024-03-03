from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import smtplib
import queue
import threading
from flasgger import Swagger
from flasgger.utils import swag_from
import unittest
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emails.db'
db = SQLAlchemy(app)
swagger = Swagger(app)

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    email_subject = db.Column(db.String(255), nullable=False)
    email_content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    recipients = db.relationship('Recipient', backref='email', lazy=True)

class Recipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=False)
    email_address = db.Column(db.String(255), nullable=False)

# Queue for storing emails to be sent
email_queue = queue.Queue()

def send_email_worker():
    while True:
        try:
            email_data = email_queue.get(timeout=60)  # Wait for 1 minute for new emails
            send_email(email_data['subject'], email_data['content'], email_data['recipients'])
            email_queue.task_done()
        except queue.Empty:
            pass  # No emails in the queue, continue waiting

def send_email(email_subject, email_content, recipients):
    # SMTP configuration
    smtp_server = 'live.smtp.mailtrap.io'
    smtp_port = 587
    # smtp_username = 'api'
    smtp_username = 'mailtrap@demomailtrap.com'
    smtp_password = '6c2bff14d67a3b2c878f0125024c640f' 
    
    # Create email message
    message = f"Subject: {email_subject}\n\n{email_content}"
    
    # Create SMTP session
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        # Send email to each recipient
        for recipient in recipients:
            server.sendmail(smtp_username, recipient, message)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/save_emails', methods=['POST'])
@swag_from('swagger_save_emails.yml')
def save_emails():
    data = request.form
    event_id = data.get('event_id')
    email_subject = data.get('email_subject')
    email_content = data.get('email_content')
    timestamp = datetime.strptime(data.get('timestamp'), '%d %b %Y %H:%M')
    recipients = data.getlist('recipients')  # List of email addresses

    if None in (event_id, email_subject, email_content, timestamp, recipients):
        return jsonify({'error': 'Missing parameters'}), 400

    new_email = Email(
        event_id=event_id,
        email_subject=email_subject,
        email_content=email_content,
        timestamp=timestamp
    )
    db.session.add(new_email)
    db.session.commit()

    # Save recipients
    for recipient_email in recipients:
        new_recipient = Recipient(email_id=new_email.id, email_address=recipient_email)
        db.session.add(new_recipient)
    db.session.commit()

    # Add email data to the queue
    email_data = {
        'subject': new_email.email_subject,
        'content': new_email.email_content,
        'recipients': [recipient.email_address for recipient in new_email.recipients]
    }
    email_queue.put(email_data)

    return jsonify({'message': 'Email saved successfully'}), 200

def check_email_schedule():
    utc8_now = datetime.utcnow() + timedelta(hours=8) # Adjust for UTC+8
    pending_emails = Email.query.filter(Email.timestamp <= utc8_now).all()
    for email in pending_emails:
        recipients = [recipient.email_address for recipient in email.recipients]
        send_email(email.email_subject, email.email_content, recipients)
        db.session.delete(email)
    db.session.commit()

# Start the email sending worker thread
email_sender_thread = threading.Thread(target=send_email_worker)
email_sender_thread.daemon = True
email_sender_thread.start()

class TestApp(unittest.TestCase):
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_index(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'TimeMail-Scheduler Management', response.data)
    
    def test_save_emails_missing_parameters(self):
        response = self.app.post('/save_emails')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
