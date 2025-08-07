import os
import re
import requests
import mimetypes
from flask import Flask, request, render_template, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev")

DRIME_API_TOKEN = os.environ.get("DRIME_API_TOKEN")
if not DRIME_API_TOKEN:
    raise RuntimeError("Missing DRIME_API_TOKEN environment variable.")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        cdn_url = request.form.get("cdn_url")
        if not cdn_url:
            flash("Please provide a file URL.", "error")
            return redirect(url_for("index"))

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": cdn_url
        }

        try:
            # Get filename
            filename = None
            head = requests.head(cdn_url, headers=headers, allow_redirects=True)
            cd = head.headers.get("Content-Disposition")
            if cd:
                match = re.findall("filename=\"?([^\";]+)\"?", cd)
                if match:
                    filename = match[0]
            if not filename:
                filename = cdn_url.split("/")[-1].split("?")[0] or "downloaded_file"

            # Download
            r = requests.get(cdn_url, stream=True, headers=headers, timeout=60)
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Detect MIME
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "application/octet-stream"

            # Upload to Drime
            with open(filename, "rb") as file_data:
                upload = requests.post(
                    "https://app.drime.cloud/api/v1/uploads",
                    headers={"Authorization": f"Bearer {DRIME_API_TOKEN}"},
                    files={"file": (filename, file_data, mime_type)},
                )
            data = upload.json()
            if upload.status_code != 200 or data.get("status") != "success":
                flash(f"Upload failed: {data}", "error")
                os.remove(filename)
                return redirect(url_for("index"))

            entry_id = data["fileEntry"]["id"]

            # Create shareable link
            share = requests.post(
                f"https://app.drime.cloud/api/v1/file-entries/{entry_id}/shareable-link",
                headers={"Authorization": f"Bearer {DRIME_API_TOKEN}"}
            )

            os.remove(filename)

            if share.status_code == 200:
                share_url = share.json().get("url")
                return render_template("index.html", success=True, link=share_url)
            else:
                flash(f"Failed to generate shareable link: {share.text}", "error")
                return redirect(url_for("index"))

        except Exception as e:
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("index"))

    return render_template("index.html", success=False)
