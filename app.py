from flask import Flask, request, jsonify
import os
import requests
import tqdm
import magic

app = Flask(__name__)

@app.route("/")
def home():
    return "🚀 Drime CDN-Uploader is running on Koyeb!"

# Example endpoint
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400
    
    # Save file locally
    filename = file.filename
    path = os.path.join("/tmp", filename)
    file.save(path)

    # Detect MIME type using python-magic
    mime = magic.from_file(path, mime=True)

    # Return some mock response
    return jsonify({
        "filename": filename,
        "mimetype": mime,
        "message": "File uploaded successfully."
    })
