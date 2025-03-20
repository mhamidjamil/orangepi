"""Code for the Flask server that sends emails"""
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

DEFAULT_SUBJECT = 'Raspberry Mail'
SIGNATURE = "\n\n--\nSent using Orange Pi Flask server"

def send_email(to_email, subject, body):
    """Sends an email using the system's mail command."""
    subject = subject or DEFAULT_SUBJECT
    body += SIGNATURE

    # Use the system's mail command
    command = f'echo "{body}" | mail -s "{subject}" {to_email}'
    try:
        subprocess.run(command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error sending email: {e}")
        return False

@app.route('/send_email', methods=['POST'])
def send_email_api():
    """API endpoint to send an email"""
    data = request.json
    to_email = data.get('to_email')
    subject = data.get('subject')
    body = data.get('body')

    if not to_email or not body:
        return jsonify({"error": "Missing required fields 'to_email' or 'body'"}), 400

    success = send_email(to_email, subject, body)
    if success:
        return jsonify({"message": "Email sent successfully"}), 200

    return jsonify({"error": "Failed to send email"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3021)
