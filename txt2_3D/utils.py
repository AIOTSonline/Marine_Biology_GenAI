import os
import sys
import requests
import numpy as np
import cv2
import torch
from PIL import Image
from torchvision import transforms
from fathomnet.api import images
import gc
import time
import torch
import numpy as np
import open3d as o3d
import trimesh

# --- Fix sys.path for local imports ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.append(PROJECT_ROOT)

from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

# Assumes `model`, `sr_transform`, and `device` are defined globally
# You will need to ensure they are initialized before calling these functions.

# --- Scoring functions ---
def score_crop_quality(crop, weights=(0.2, 0.3, 0.5)):
    if crop.size == 0:
        return 0.0
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
    contrast = gray.std()

    b_score = min(max((brightness - 30) / (255 - 30), 0), 1)
    s_score = min(sharpness / 300.0, 1.0)
    c_score = min(contrast / 60.0, 1.0)

    return weights[0] * b_score + weights[1] * s_score + weights[2] * c_score


# --- Process and score images ---
def get_best_crop_image(concept, model, sr_transform, device):
    results = []
    for img in images.find_by_concept(concept):
        try:
            img_url = img.url
            # print(img_url)
            response = requests.get(img_url)
            img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            original_img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if original_img is None:
                continue

            # Super-resolve image
            pil_img = Image.fromarray(cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB))
            input_tensor = sr_transform(pil_img).unsqueeze(0).to(device)
            with torch.no_grad():
                sr_tensor = model(input_tensor)[0].detach().cpu()

            sr_img = transforms.ToPILImage()(sr_tensor.clamp(-1, 1) * 0.5 + 0.5)
            sr_img = np.array(sr_img)
            sr_img = cv2.resize(sr_img, (original_img.shape[1], original_img.shape[0]))
            sr_img = cv2.cvtColor(sr_img, cv2.COLOR_RGB2BGR)

            for box in img.boundingBoxes:
                if box.concept != concept:
                    continue
                x1, y1 = max(0, box.x), max(0, box.y)
                x2 = min(original_img.shape[1], box.x + box.width)
                y2 = min(original_img.shape[0], box.y + box.height)

                crop_orig = original_img[y1:y2, x1:x2]
                crop_sr = sr_img[y1:y2, x1:x2]

                score_orig = score_crop_quality(crop_orig)
                score_sr = score_crop_quality(crop_sr)

                best_crop = crop_sr if score_sr > score_orig else crop_orig
                best_crop_rgb = cv2.cvtColor(best_crop, cv2.COLOR_BGR2RGB)
                pil_crop = Image.fromarray(best_crop_rgb)
                results.append((max(score_sr, score_orig), pil_crop))
        except Exception:
            continue
    # print(results)
    return sorted(results, key=lambda x: x[0], reverse=True)[0][1] if results else None


def get_all_cropped_images(concept):
    results = []
    for img in images.find_by_concept(concept):
        try:
            img_url = img.url
            response = requests.get(img_url)
            img_array = np.asarray(bytearray(response.content), dtype=np.uint8)
            original_img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if original_img is None:
                continue

            # Super-resolve image
            pil_img = Image.fromarray(cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB))
            input_tensor = sr_transform(pil_img).unsqueeze(0).to(device)
            with torch.no_grad():
                sr_tensor = model(input_tensor)[0].detach().cpu()

            sr_img = transforms.ToPILImage()(sr_tensor.clamp(-1, 1) * 0.5 + 0.5)
            sr_img = np.array(sr_img)
            sr_img = cv2.resize(sr_img, (original_img.shape[1], original_img.shape[0]))
            sr_img = cv2.cvtColor(sr_img, cv2.COLOR_RGB2BGR)

            for box in img.boundingBoxes:
                if box.concept != concept:
                    continue
                x1, y1 = max(0, box.x), max(0, box.y)
                x2 = min(original_img.shape[1], box.x + box.width)
                y2 = min(original_img.shape[0], box.y + box.height)

                crop_orig = original_img[y1:y2, x1:x2]
                crop_sr = sr_img[y1:y2, x1:x2]

                score_orig = score_crop_quality(crop_orig)
                score_sr = score_crop_quality(crop_sr)

                best_crop = crop_sr if score_sr > score_orig else crop_orig
                best_crop_rgb = cv2.cvtColor(best_crop, cv2.COLOR_BGR2RGB)
                pil_crop = Image.fromarray(best_crop_rgb)
                results.append((max(score_sr, score_orig), pil_crop))
        except Exception:
            continue

    return sorted(results, key=lambda x: x[0], reverse=True)


# ------------------ MEMORY CLEANUP ------------------
def clean_memory():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()

# ------------------ MESH GENERATION ------------------
def generate_mesh(image, save_path, mesh_pipeline = None, runtime):
    """Runs mesh generation pipeline in a separate process"""
    if mesh_pipeline is None:
        mesh_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            'tencent/Hunyuan3D-2',
            subfolder='hunyuan3d-dit-v2-0',
            use_safetensors=False,
            variant='fp16',
            runtime=runtime,
        )
    mesh_pipeline.enable_model_cpu_offload(device="cuda")

    print("Mesh model loaded successfully")
    tic = time.time()

    mesh = mesh_pipeline(image=image)[0]

    # Cleanup mesh with Open3D
    o3d_mesh = o3d.geometry.TriangleMesh()
    o3d_mesh.vertices = o3d.utility.Vector3dVector(mesh.vertices)
    o3d_mesh.triangles = o3d.utility.Vector3iVector(mesh.faces)

    simplified = o3d_mesh.simplify_quadric_decimation(50000)
    simplified.remove_unreferenced_vertices()
    o3d_mesh = simplified.remove_degenerate_triangles()
    o3d_mesh = o3d_mesh.remove_duplicated_triangles()
    o3d_mesh = o3d_mesh.remove_duplicated_vertices()
    o3d_mesh = o3d_mesh.remove_non_manifold_edges()

    decimated_mesh = trimesh.Trimesh(
        vertices=np.asarray(o3d_mesh.vertices),
        faces=np.asarray(o3d_mesh.triangles),
        process=False
    )
    decimated_mesh.export(save_path)

    clean_memory()
    return save_path