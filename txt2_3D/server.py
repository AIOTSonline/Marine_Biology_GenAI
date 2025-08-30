import sys
import os
import torch
from flask import Flask, request, jsonify

# --- Add project root to Python path ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

# --- Imports ---
from generate_3d import generate_3d  # expects preloaded models
from hy3dgen.texgen import Hunyuan3DPaintPipeline
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

# -------------------------------
# Load models globally at startup
# -------------------------------
print("[INFO] Loading models once at startup...")

DEVICE = torch.device(
    "cuda:1" if torch.cuda.device_count() > 1
    else ("cuda:0" if torch.cuda.is_available() else "cpu")
)


# TEMP for custom download paths, uncomment following code
#MESH_PIPELINE = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
#    os.path.join(PROJECT_ROOT, 'models'),
#    device=DEVICE
#)

# PAINT_PIPELINE = Hunyuan3DPaintPipeline.from_pretrained(
#    os.path.join(PROJECT_ROOT, 'models'),
#    subfolder='hunyuan3d-paint-v2-0-turbo'
#)


# TEMP With higher RAM allowance, uncomment following code to increase inferecence speed
# MESH_PIPELINE = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
#     'tencent/Hunyuan3D-2',
#     subfolder='hunyuan3d-dit-v2-0',
#     variant='fp16',
#     device = DEVICE,
#     runtime=True
# )

# PAINT_PIPELINE = Hunyuan3DPaintPipeline.from_pretrained(
#     'tencent/Hunyuan3D-2',
#     subfolder='hunyuan3d-paint-v2-0-turbo',
#     runtime=True
# )


# TEMP loading at runtime to save RAM, uncomment following code to run mesh pipeline and paint in separate processes
MESH_PIPELINE = None
PAINT_PIPELINE = None

# -------------------------------
# Flask app
# -------------------------------
app = Flask(__name__)

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    concept = data.get("concept")
    method = data.get("method", "genai")
    output = data.get("output") # Optional field for unity based extra output

    if not concept:
        return jsonify({"error": "Missing 'concept' field"}), 400

    try:
        # Pass preloaded pipelines to avoid reloading inside generate_3d
        result_paths = generate_3d(
            concept=concept,
            method=method,
            output=output,
            output_dir=os.path.join(PROJECT_ROOT, "output_assets"),
            mesh_pipeline=MESH_PIPELINE,
            paint_pipeline=PAINT_PIPELINE,
        )
        return jsonify({"status": "done", "results": result_paths}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == "__main__":
    # Disable reloader to avoid duplicate processes
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
