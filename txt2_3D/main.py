import sys
import os
import glob
import gc
import time
import torch
import numpy as np
import trimesh
import open3d as o3d
from PIL import Image
from torchvision import transforms
import multiprocessing as mp

# --- Add project root to Python path ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

# --- Local imports (relative to project root) ---
from Image_generator import mymodel
from fathomnet.api import images
from utils import get_best_crop_image
from GenAI_image_generator import text_to_image
from hy3dgen.texgen import Hunyuan3DPaintPipeline
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
from hy3dgen.rembg import BackgroundRemover

# --- Locate custom rasterizer .so ---
rasterizer_libs = glob.glob(
    os.path.join(PROJECT_ROOT, "hy3dgen", "texgen", "custom_rasterizer", "build", "lib.*", "*custom_rasterizer_kernel*.so")
)
if rasterizer_libs:
    sys.path.append(os.path.dirname(rasterizer_libs[0]))


def clean_memory():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
        print("GPU memory cleared.")
    else:
        print("No GPU available.")


def generate_mesh(image, save_path, mesh_pipeline):
        """Runs mesh generation pipeline in a separate process"""
        if mesh_pipeline is None:
            mesh_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
                'tencent/Hunyuan3D-2',
                subfolder='hunyuan3d-dit-v2-0',
                use_safetensors=False,
                variant='fp16',
                runtime=True,
            )
        mesh_pipeline.enable_model_cpu_offload(device="cuda")
        print("Mesh model loaded successfully")

        mesh = mesh_pipeline(image=image)[0]
        mesh.export(save_path)
        clean_memory()
        return save_path

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    clean_memory()
    
    # --- Device selection ---
    DEVICE_2 = torch.device("cuda:1" if torch.cuda.device_count() > 1 else ("cuda:0" if torch.cuda.is_available() else "cpu"))

    # --- Load Generation Pipeline ---
    # TEMP loading at runtime
    # mesh_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
    #     'tencent/Hunyuan3D-2',
    #     subfolder='hunyuan3d-dit-v2-0',
    #     variant='fp16',
    #     device = DEVICE_2,
    #     runtime=True
    # )

    # paint_pipeline = Hunyuan3DPaintPipeline.from_pretrained(
    #     'tencent/Hunyuan3D-2',
    #     subfolder='hunyuan3d-paint-v2-0-turbo',
    #     runtime=True
    # )
    # print("Model Loaded")

    # --- Load Generation Pipeline in processes ---
    mesh_pipeline = None
    paint_pipeline = None

    # ------------------ IMAGE SOURCE CHOICE ------------------
    # choice = input("Choose image source - [1] FathomNet fetch  [2] GenAI generation: ").strip()
    choice = "1" # TEMP_choice for testing purpose

    if choice == "2":
        # --- GenAI IMAGE GENERATION ---
        print("Generating image using GenAI...")
        user_input = input("Enter concept name (default: Grimpoteuthis): ").strip()
        concept = user_input if user_input else "Grimpoteuthis"

        positive_prompt = (
            f"photograph of a {concept}, anatomically correct, centered, full body, "
            "plain white background, bright studio lighting, 4k, high detail, sharp focus."
        )

        negative_prompt = (
            "blurry, deformed, mutated, disfigured, extra limbs, cartoon, painting, artistic, "
            "dark, shadows, text, watermark, underwater scene, noisy background."
        )

        output_file = f"{concept}_genai.png"
        best_image = text_to_image(
            prompt=positive_prompt,
            output_path=output_file,
            negative_prompt=negative_prompt
        )
        best_image = Image.open(output_file)  # reload to continue pipeline

    else:
        # --- IMAGE FETCHING (FathomNet + SRGAN) ---
        print("Fetching images from FathomNet...")
        CONCEPT = "Grimpoteuthis"
        fathomnet_image_list = images.find_by_concept(CONCEPT)
        image_urls = [img.url for img in fathomnet_image_list]

        # Load SRGAN model
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = mymodel()
        model.load_state_dict(torch.load(os.path.join(PROJECT_ROOT, "image_model", "SR_GAN_best.pth"), map_location=device))
        model.to(device)
        model.eval()

        sr_transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        ])

        # user_input = input("Enter concept name (default: Grimpoteuthis): ").strip() # TEMP comment for kaggle run
        # concept = user_input if user_input else "Grimpoteuthis"
        concept = "Grimpoteuthis"
        best_image = get_best_crop_image(concept, model, sr_transform, device)
        del model  # free memory
        # if best_image:
        #     best_image.show()
        #     best_image.save("best_result.jpg")

    # ------------------ CONTINUE PIPELINE (common for both) ------------------

    image = best_image.convert("RGBA")
    rembg = BackgroundRemover()
    image = rembg(image)
    del rembg

    # Create output directory if it doesn't exist
    output_dir = os.path.join(PROJECT_ROOT, "output")
    os.makedirs(output_dir, exist_ok=True)
    # Save processed input image
    if choice == "2":
        image_path = os.path.join(output_dir, f"{concept}_genai.png")
    else:
        image_path = os.path.join(output_dir, f"{concept}_fathomnet.png")
    image.save(image_path)

    # Mesh Gneration
    raw_mesh_path = os.path.join(output_dir, f"img_mesh_{concept}.glb")
    mesh_proc = mp.Process(target=generate_mesh, args=(image, raw_mesh_path, mesh_pipeline))
    mesh_proc.start()
    mesh_proc.join()
    img_mesh = trimesh.load(raw_mesh_path)

    if isinstance(img_mesh, trimesh.Scene):
        meshes = [g for g in img_mesh.geometry.values()]
        mesh = trimesh.util.concatenate(meshes)
    else:
        mesh = img_mesh

    print("mesh_loaded")

    initial_tic = time.time()

    # Convert to Open3D format
    o3d_mesh = o3d.geometry.TriangleMesh()
    o3d_mesh.vertices = o3d.utility.Vector3dVector(mesh.vertices)
    o3d_mesh.triangles = o3d.utility.Vector3iVector(mesh.faces)


    target_faces = 50000 # Target number of faces fixed to 50000 for consistency with animation
    simplified = o3d_mesh.simplify_quadric_decimation(target_faces)

    simplified.remove_unreferenced_vertices()
    simplified = simplified.remove_degenerate_triangles()
    simplified = simplified.remove_duplicated_triangles()
    simplified = simplified.remove_duplicated_vertices()
    simplified = simplified.remove_non_manifold_edges()

    decimated_mesh = trimesh.Trimesh(
        vertices=np.asarray(simplified.vertices),
        faces=np.asarray(simplified.triangles),
        process=False
    )

    # Texture Generation
    if paint_pipeline is None:
        paint_pipeline = Hunyuan3DPaintPipeline.from_pretrained(
            'tencent/Hunyuan3D-2',
            subfolder='hunyuan3d-paint-v2-0-turbo',
            runtime=True
        )
        paint_pipeline.enable_model_cpu_offload(device="cuda")
        print("Paint model loaded successfully")
    paint_mesh = paint_pipeline(decimated_mesh, image=image)

    print("Total Time for model formation with decimation:", time.time() - initial_tic)

    clean_memory()

    # Export results
    painted_mesh_path = os.path.join(output_dir, f"paint_mesh_{concept}.glb")
    paint_mesh.export(painted_mesh_path)

    print(f"All outputs saved in: {output_dir}")

