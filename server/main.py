import os
from pathlib import Path
from flask import Flask, send_file, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
FILES_DIR = Path(os.getenv("FILES_DIR", "./files"))

CORS(app, resources={r"/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})

def ensure_files_dir():
    """Ensure the files directory exists."""
    FILES_DIR.mkdir(parents=True, exist_ok=True)


@app.route("/")
def index():
    """List available files."""
    ensure_files_dir()
    
    files = {
        "zips": [],
        "manifests": []
    }
    
    for file_path in FILES_DIR.iterdir():
        if file_path.is_file():
            if file_path.suffix.lower() == ".zip":
                files["zips"].append(file_path.name)
            elif file_path.suffix.lower() in [".json", ".manifest"]:
                files["manifests"].append(file_path.name)
    
    return jsonify({
        "message": "File server is running",
        "files": files,
        "endpoints": {
            "list": "/",
            "download_zip": "/zip/<filename>",
            "download_manifest": "/manifest/<filename>",
            "download_server": "/server/<filename>",
            "latest_zip": "/latest/zip",
            "latest_manifest": "/latest/manifest",
        }
    })

@app.route("/server/<filename>")
def serve_server(filename):
    """Serve a server file by name."""
    ensure_files_dir()
    file_path = FILES_DIR / secure_filename(filename)
    
    # Check if file exists and ends with .tar.gz
    if not file_path.exists() or not file_path.name.lower().endswith(".tar.gz"):
        return jsonify({"error": "File not found"}), 404
    
    return send_file(
        file_path,
        mimetype="application/tar+gzip",
        as_attachment=False,
        download_name=filename
    )

@app.route("/zip/<filename>")
def serve_zip(filename):
    """Serve a zip file by name."""
    ensure_files_dir()
    file_path = FILES_DIR / secure_filename(filename)
    
    if not file_path.exists() or file_path.suffix.lower() != ".zip":
        return jsonify({"error": "File not found"}), 404
    
    return send_file(
        file_path,
        mimetype="application/zip",
        as_attachment=False,
        download_name=filename
    )


@app.route("/latest/zip")
def serve_latest_zip():
    """Serve the latest zip file."""
    ensure_files_dir()
    
    zip_files = [f for f in FILES_DIR.iterdir() if f.is_file() and f.suffix.lower() == ".zip"]
    if not zip_files:
        return jsonify({"error": "No zip files found"}), 404
    
    latest = max(zip_files, key=lambda p: p.stat().st_mtime)
    
    return send_file(
        latest,
        mimetype="application/zip",
        as_attachment=False,
        download_name=latest.name
    )


@app.route("/manifest/<filename>")
def serve_manifest(filename):
    """Serve a manifest file by name."""
    ensure_files_dir()
    file_path = FILES_DIR / secure_filename(filename)
    
    if not file_path.exists() or file_path.suffix.lower() not in [".json", ".manifest"]:
        return jsonify({"error": "File not found"}), 404
    
    return send_file(
        file_path,
        mimetype="application/json",
        as_attachment=False,
        download_name=filename
    )


@app.route("/latest/manifest")
def serve_latest_manifest():
    """Serve the latest manifest file."""
    ensure_files_dir()
    
    manifest_files = [f for f in FILES_DIR.iterdir() if f.is_file() and f.suffix.lower() in [".json", ".manifest"]]
    if not manifest_files:
        return jsonify({"error": "No manifest files found"}), 404
    
    latest = max(manifest_files, key=lambda p: p.stat().st_mtime)
    
    return send_file(
        latest,
        mimetype="application/json",
        as_attachment=False,
        download_name=latest.name
    )


if __name__ == "__main__":
    ensure_files_dir()
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"Starting file server on {host}:{port}")
    print(f"Files directory: {FILES_DIR.absolute()}")
    print(f"Place zip and manifest files in: {FILES_DIR.absolute()}")
    
    app.run(host=host, port=port, debug=debug)