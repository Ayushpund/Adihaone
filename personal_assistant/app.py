from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import agent
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure upload folder for voice messages
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Serve static files
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        if 'message' in request.form:
            # Text input
            user_input = request.form['message'].strip()
            if not user_input:
                return jsonify({'error': 'Empty message'}), 400
                
            response = agent.process_command(user_input)
            return jsonify({
                'response': response,
                'type': 'text'
            })
            
        elif 'audio' in request.files:
            # Voice input
            audio_file = request.files['audio']
            if audio_file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
                
            if audio_file:
                filename = secure_filename(audio_file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                audio_file.save(filepath)
                
                # Here you would typically process the audio file
                # For now, we'll just return a placeholder response
                return jsonify({
                    'response': 'Voice command received. Processing...',
                    'type': 'voice'
                })
        
        return jsonify({'error': 'Invalid request'}), 400
        
    except Exception as e:
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500

@app.route('/speak', methods=['POST'])
def speak():
    try:
        data = request.get_json()
        text = data.get('text', '')
        if text:
            agent.speak(text)
            return jsonify({'status': 'success'})
        return jsonify({'error': 'No text provided'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create uploads directory if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True, host='0.0.0.0', port=5000)
