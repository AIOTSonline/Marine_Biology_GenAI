from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

# -------------------------------
# Flask app
# -------------------------------
app = Flask(__name__)
CORS(app)  # enable CORS for all routes

# Get absolute path to output_assets relative to this file
OUTPUT_DIR = "output_assets"

os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route("/generate", methods=["POST"])
def generate():
    """Fake generation for local testing: return existing glb and image paths"""
    data = request.get_json(force=True)
    concept = data.get("concept")
    method = data.get("method", "genai")

    if not concept:
        return jsonify({"error": "Missing 'concept' field"}), 400

    try:
        # Local placeholder files
        raw_mesh = os.path.join(OUTPUT_DIR, "mesh.glb")
        painted_mesh = os.path.join(OUTPUT_DIR, "painted.glb")
        image_file = os.path.join(OUTPUT_DIR, "image.png")  # new image file

        # Ensure files exist
        missing_files = [f for f in [raw_mesh, painted_mesh, image_file] if not os.path.exists(f)]
        if missing_files:
            return jsonify({
                "status": "error",
                "error": f"Missing files: {', '.join(missing_files)}"
            }), 500

        return jsonify({
            "status": "done",
            "files": [
                os.path.basename(raw_mesh),
                os.path.basename(painted_mesh),
                os.path.basename(image_file)  # include image
            ]
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    """Download files from local folder"""
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
