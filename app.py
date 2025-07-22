from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pydub import AudioSegment
import os
import csv

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Set a strong secret key for sessions
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def load_prompts(csv_path='prompts.csv'):
    prompts = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row:
                prompts.append(row[0])
    return prompts

# Simple login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if username:
            session['username'] = username
            return redirect(url_for('index'))
        return "Please enter a username", 400
    return render_template('login.html')  # You'll create this login form template

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Decorator to require login on routes
from functools import wraps
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    prompts = load_prompts()
    return render_template('index.html', prompts=prompts, username=session['username'])

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    audio_file = request.files.get('audio_data')
    filename = request.form.get('filename')
    username = session['username']

    if not audio_file or not filename:
        return "Missing data", 400

    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    temp_path = os.path.join(user_folder, filename + '.webm')
    audio_file.save(temp_path)

    wav_path = os.path.join(user_folder, filename)
    try:
        sound = AudioSegment.from_file(temp_path)
        sound.export(wav_path, format="wav")
        os.remove(temp_path)
    except Exception as e:
        return f"Conversion failed: {e}", 500

    return "Uploaded successfully", 200

@app.route('/delete', methods=['POST'])
@login_required
def delete_file():
    data = request.get_json()
    filename = data.get('filename')
    username = session['username']

    if not filename:
        return jsonify(success=False, message="Missing filename")

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], username, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify(success=True)
    else:
        return jsonify(success=False, message="File not found")

@app.route('/status')
@login_required
def status():
    username = session['username']
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
    prompts = load_prompts()
    uploaded_files = set()
    if os.path.exists(user_folder):
        uploaded_files = set(os.listdir(user_folder))

    # Check which prompt files have been uploaded
    status = []
    for i in range(len(prompts)):
        filename = f"00{i+1}.wav"
        status.append(filename in uploaded_files)
    return jsonify(status=status)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
