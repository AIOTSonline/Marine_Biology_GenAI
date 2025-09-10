from flask import Flask, request, jsonify, send_from_directory
import os
import torch
import sys
# --- Add project root to Python path ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(PROJECT_ROOT)

from txt2_3D.generate_3d import generate_3d

# -------------------------------
# Load models globally at startup
# -------------------------------
print("[INFO] Loading models once at startup...")

from hy3dgen.texgen import Hunyuan3DPaintPipeline
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

DEVICE = torch.device(
    "cuda:1" if torch.cuda.device_count() > 1
    else ("cuda:0" if torch.cuda.is_available() else "cpu")
)

flag = input("Have you downloaded the pre-trained models in the dedicated repo? answer: Y/N")

if flag=='Y' or flag=='y':
    local = True
    MESH_PIPELINE = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
        "models",
        device=DEVICE
    )

    PAINT_PIPELINE = Hunyuan3DPaintPipeline.from_pretrained(
        "models",
        subfolder="hunyuan3d-paint-v2-0-turbo",
    )
elif flag=='N' or flag=='n':
    local = False
    MESH_PIPELINE = None
    PAINT_PIPELINE = None
else:
    print("Please use: Y for yes and N for no")

print("[INFO] Models loaded successfully.")

# -------------------------------
# Flask app
# -------------------------------
app = Flask(__name__)
OUTPUT_DIR = "output_assets"
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.route("/generate", methods=["POST"])
def generate():
    """Generate 3D assets and save as mesh.glb and painted.glb"""
    data = request.get_json(force=True)
    concept = data.get("concept")
    method = data.get("method", "genai")

    if not concept:
        return jsonify({"error": "Missing 'concept' field"}), 400

    try:
        result_paths = generate_3d(
            concept=concept,
            method=method,
            output_dir=OUTPUT_DIR,
            mesh_pipeline=MESH_PIPELINE,
            paint_pipeline=PAINT_PIPELINE,
            local = local,
        )

        # Always overwrite -> mesh.glb, painted.glb
        return jsonify({
            "status": "done",
            "glb_files": [
                os.path.basename(result_paths["raw_mesh"]),
                os.path.basename(result_paths["painted_mesh"]),
                os.path.basename(result_paths["image"])
            ]
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    """Download generated .glb files"""
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    # Disable reloader to avoid duplicate processes
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
