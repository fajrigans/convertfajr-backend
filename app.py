from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
import os
import uuid
import subprocess
import mimetypes

UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(app)

def get_file_type(mime_type):
    if mime_type.startswith('image/'):
        return 'image'
    elif mime_type.startswith('audio/'):
        return 'audio'
    elif mime_type.startswith('video/'):
        return 'video'
    elif mime_type in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']:
        return 'document'
    elif mime_type in ['application/zip', 'application/x-rar-compressed', 'application/x-tar', 'application/gzip']:
        return 'archive'
    return 'unknown'

@app.route('/api/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    original_filename = file.filename
    ext = os.path.splitext(original_filename)[1].lower()
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_FOLDER, unique_id + ext)
    file.save(input_path)

    # Check if file is empty
    if os.path.getsize(input_path) == 0:
        return jsonify({'error': 'Uploaded file is empty or corrupted'}), 400

    mime_type, _ = mimetypes.guess_type(input_path)
    file_type = get_file_type(mime_type or '')

    # Detect output format from frontend
    output_format = request.form.get('outputFormat', '').lower()
    if not output_format:
        return jsonify({'error': 'Output format not specified'}), 400

    output_path = os.path.join(CONVERTED_FOLDER, f"{unique_id}.{output_format}")

    try:
        if file_type in ['audio', 'video']:
            cmd = ['ffmpeg', '-y', '-i', input_path, output_path]
        elif file_type == 'image':
            cmd = ['convert', input_path, output_path]  # Requires ImageMagick
        elif file_type == 'document':
            cmd = ['pandoc', input_path, '-o', output_path]
        elif file_type == 'archive':
            cmd = ['7z', 'a', output_path, input_path]
        else:
            return jsonify({'error': f'Unsupported file type: {file_type}'}), 400

        print("Running:", ' '.join(cmd))
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            print("Error:", result.stderr)
            return jsonify({'error': 'Conversion failed', 'details': result.stderr}), 500

        return jsonify({
            'downloadUrl': f'/converted/{os.path.basename(output_path)}',
            'fileType': file_type
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/converted/<filename>')
def download_file(filename):
    return send_from_directory(CONVERTED_FOLDER, filename, as_attachment=False)

@app.route('/')
def home():
    return 'Backend is running.'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
