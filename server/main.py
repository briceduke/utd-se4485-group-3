import os
from pathlib import Path
from flask import Flask, send_file, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

FILES_DIR = Path(os.getenv("FILES_DIR", "./files"))


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
            "download_manifest": "/manifest/<filename>"
        }
    })


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


if __name__ == "__main__":
    ensure_files_dir()
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"Starting file server on {host}:{port}")
    print(f"Files directory: {FILES_DIR.absolute()}")
    print(f"Place zip and manifest files in: {FILES_DIR.absolute()}")
    
    app.run(host=host, port=port, debug=debug)