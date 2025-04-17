from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import subprocess
import uuid
import mimetypes

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "converted"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True)
    if result.returncode != 0:
        raise Exception(result.stderr.decode())
    return result.stdout.decode()

def convert_file(input_path, output_path, file_type):
    if file_type == "image":
        run_command(f"ffmpeg -y -i {input_path} {output_path}")
    elif file_type == "audio":
        run_command(f"ffmpeg -y -i {input_path} {output_path}")
    elif file_type == "video":
        run_command(f"ffmpeg -y -i {input_path} {output_path}")
    elif file_type == "document":
        run_command(f"pandoc {input_path} -o {output_path}")
    elif file_type == "archive":
        if output_path.endswith(".zip"):
            run_command(f"zip -j {output_path} {input_path}")
        elif output_path.endswith(".tar.gz"):
            run_command(f"tar -czf {output_path} -C {os.path.dirname(input_path)} {os.path.basename(input_path)}")
        else:
            raise Exception("Unsupported archive output format.")
    else:
        raise Exception("Unsupported file type")

@app.route("/api/convert", methods=["POST"])
def convert():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    output_format = request.form.get('outputFormat')
    if not output_format:
        return jsonify({"error": "Output format required"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    mime_type = mimetypes.guess_type(file.filename)[0] or ""
    file_type = "unknown"
    if "image" in mime_type:
        file_type = "image"
    elif "audio" in mime_type:
        file_type = "audio"
    elif "video" in mime_type:
        file_type = "video"
    elif "pdf" in mime_type or "text" in mime_type or ext in ['.docx', '.txt', '.md', '.rtf']:
        file_type = "document"
    elif ext in ['.zip', '.rar', '.tar', '.gz']:
        file_type = "archive"

    unique_name = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_FOLDER, unique_name + ext)
    output_path = os.path.join(RESULT_FOLDER, unique_name + "." + output_format)
    file.save(input_path)

    try:
        convert_file(input_path, output_path, file_type)
        download_url = f"/converted/{os.path.basename(output_path)}"
        return jsonify({"url": download_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/converted/<filename>')
def download(filename):
    return send_from_directory(RESULT_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
