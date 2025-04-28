from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
import os
import subprocess
import uuid
import mimetypes
import shutil
from weasyprint import HTML

app = Flask(__name__)

# ✅ CORS global configuration: Allow Vercel and local dev
CORS(app, resources={r"/*": {"origins": ["https://fajrconvert.vercel.app", "http://localhost:5173"]}}, supports_credentials=True)

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "converted"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return "✅ Flask backend aktif dan berjalan!"

@app.route("/debug")
def debug():
    return jsonify({
        "ffmpeg": shutil.which("ffmpeg"),
        "pandoc": shutil.which("pandoc"),
        "pdftotext": shutil.which("pdftotext")
    })

def run_command(command):
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True)
    if result.returncode != 0:
        raise Exception(result.stderr.decode())
    return result.stdout.decode()

def convert_file(input_path, output_path, file_type, output_ext):
    if file_type == "video":
        run_command(f'ffmpeg -y -i "{input_path}" -c:v libx264 -preset veryfast -crf 23 -c:a aac -strict experimental "{output_path}"')
    elif file_type == "audio":
        run_command(f'ffmpeg -y -i "{input_path}" "{output_path}"')
    elif file_type == "image":
        run_command(f'ffmpeg -y -i "{input_path}" "{output_path}"')
    elif file_type == "document":
        ext = os.path.splitext(input_path)[1].lower()
        if ext == ".pdf":
            if output_ext == ".txt":
                run_command(f'pdftotext "{input_path}" "{output_path}"')
            else:
                temp_txt = input_path.replace('.pdf', '_temp.txt')
                run_command(f'pdftotext "{input_path}" "{temp_txt}"')
                run_command(f'pandoc "{temp_txt}" -o "{output_path}"')
                os.remove(temp_txt)
        elif ext == ".txt" and output_ext == ".pdf":
            from weasyprint import HTML
            temp_html = input_path.replace('.txt', '_temp.html')
            with open(input_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            html_content = f"<pre>{text_content}</pre>"
            with open(temp_html, 'w', encoding='utf-8') as f:
                f.write(html_content)
            HTML(temp_html).write_pdf(output_path)
            os.remove(temp_html)
        elif ext == ".docx" and output_ext == ".pdf":
            from weasyprint import HTML
            temp_html = input_path.replace('.docx', '_temp.html')
            run_command(f'pandoc "{input_path}" -o "{temp_html}"')
            HTML(temp_html).write_pdf(output_path)
            os.remove(temp_html)
        else:
            run_command(f'pandoc "{input_path}" -o "{output_path}"')
    elif file_type == "archive":
        if output_path.endswith(".zip"):
            run_command(f'zip -j "{output_path}" "{input_path}"')
        elif output_path.endswith(".tar.gz"):
            run_command(f'tar -czf "{output_path}" -C "{os.path.dirname(input_path)}" "{os.path.basename(input_path)}"')
        else:
            raise Exception("❌ Format arsip tidak didukung.")
    else:
        raise Exception("❌ Jenis file tidak didukung.")

@app.route("/api/convert", methods=["POST"])
@cross_origin(origins=["https://fajrconvert.vercel.app", "http://localhost:5173"])  # ✅ Tambahan CORS untuk endpoint ini
def convert():
    if 'file' not in request.files:
        return jsonify({"error": "❌ File tidak ditemukan."}), 400

    file = request.files['file']
    output_format = request.form.get('outputFormat')

    if not output_format:
        return jsonify({"error": "❌ Format output harus dipilih."}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    output_ext = "." + output_format
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

    if file_type == "unknown":
        return jsonify({"error": "❌ Jenis file tidak dikenali."}), 400

    unique_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_FOLDER, unique_id + ext)
    output_path = os.path.join(RESULT_FOLDER, unique_id + output_ext)
    file.save(input_path)

    try:
        convert_file(input_path, output_path, file_type, output_ext)
        download_url = f"/converted/{os.path.basename(output_path)}"
        return jsonify({"url": download_url})
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/converted/<filename>")
@cross_origin(origins=["https://fajrconvert.vercel.app", "http://localhost:5173"])  # ✅ Optional CORS untuk akses download
def download(filename):
    return send_from_directory(RESULT_FOLDER, filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
