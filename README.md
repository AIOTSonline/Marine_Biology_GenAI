# Marine_Biology_GenAI


A project dedicated to leveraging generative AI for the creation and enhancement of marine biology resources. This repository contains tools to generate 2D images and 3D models of marine creatures, aiding in research, education, and conservation efforts.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [File Structure](#file-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Usage](#usage)
- [Contributing](#contributing)
- [Future Goals](#future-goals)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Project Overview

This project focuses on developing AI-powered 3D models of marine species for educational and research applications. The system converts user text prompts into realistic 2D images using either Stable Diffusion 3.5 or real-world images from FathomNet for underrepresented species. These images are then transformed into interactive 3D assets using Tencent Hunyuan3D models, producing `.glb` files that can be rendered in Blender, Unity, or AR applications. The solution includes a web-based visualizer and a Unity-based interface to display both textured and mesh views, all deployed on RunPod for scalable access. The goal is to create dynamic, high-quality 3D representations of marine life for immersive learning experiences and scientific exploration.

<div style="text-align: center;">
  <img src="assets/first.gif" alt="Marine Dataset Architecture" width="800"/>
</div>


---

## Key Features
- **Dual-Mode Image Generation:** Translates user input into 2D images with two methods—Stable Diffusion 3.5 for generative images and FathomNet for actual images when unusual or underrepresented species are asked for.
- **Text-to-3D Conversion Pipeline:** Renders 3D GLB models from 2D images with Tencent Hunyuan3D models, delivering assets that are ready to use within Blender, Unity, or AR/VR projects.
-  **End-to-End Deployment:** Complete containerization solution deployed on RunPod with API endpoints to allow easy model execution on the cloud.
- **Interactive Web Visualizer:** Client based on HTML/CSS/JS for rendering 2D images and 3D models within the browser itself with support for viewing textured or mesh-only models.
- **Data Extensibility:** Framework prepared for eventual dataset generation—users can retrieve stored 3D assets from the server or create new ones dynamically.
- **Education-Oriented Design:** Models and tools designed for incorporation within high school biology syllabuses, rendering marine biology study interactive and fun.


<div style="text-align: center;">
  <img src="assets/flow.png" alt="Marine Dataset Architecture" width="800"/>
</div>

---

## File Structure

```
mArIne3D/
├── .gitignore
├── README.md
├── Report.md
├── assets
│   ├── dumbo.png
│   ├── first.gif
│   ├── first.mp4
│   ├── first.png
│   ├── flow.png
│   ├── wimg1.png
│   └── wimg2.png
├── hy3dgen
├── image_model
│   └── SR_GAN_best.pth
├── notebooks
│   └── marine-text-to-3d.ipynb
├── output
├── requirements.txt
├── txt2_3D
│   ├── GenAI_image_generator.py
│   ├── Image_generator.py
│   ├── __init__.py
│   ├── generate_3d.py
│   ├── get_img_models.py
│   ├── get_models.py
│   ├── main.py
│   └── utils.py
├── visualiser
│   └── web
│       ├── app.py
│       ├── dummy_server.py
│       ├── output_assets
│       │   ├── dumbo.png
│       │   ├── first.png
│       │   ├── image.png
│       │   ├── mesh.glb
│       │   └── painted.glb
│       ├── remote_server.py
│       ├── static
│       │   ├── css
│       │   │   └── style.css
│       │   └── js
│       │       └── viewer.js
│       └── templates
│           └── index.html
└── zip_conversion.py
```
---

## Getting Started

### Prerequisites

- Python ≥3.8
- CUDA-enabled GPU (recommended 24GB VRAM for Hunyuan3D 2)
- Git
- pip

---

### Installation

#### Install Python Packages

```bash
git clone https://github.com/Dhruvanshu-Joshi/Marine_Biology_GenAI.git
cd Marine_Biology_GenAI
pip install -r requirements.txt
```
---

#### Build Custom Rasterizer

```bash
cd hy3dgen/texgen/custom_rasterizer
python setup.py bdist_wheel
pip install dist/custom_rasterizer*.whl
```

Verify installation:

```bash
find  -name "*custom_rasterizer_kernel*.so"
```

Add to Python path:

```python
import sys
sys.path.append('path to custom_rasterizer_kernel.cpython-311-x86_64-linux-gnu.so (output returned by the find)')
```

---

#### Localize Pretrained Models

**Hunyuan3D 2 models:**

You must be authenticated with a Hugging Face account to interact with the Hub. Create an account if you don’t already have one, and then sign in to get your User Access Token from your Settings page. The User Access Token is used to authenticate your identity to the Hub. Enter the token here.

```python
from huggingface_hub import login, snapshot_download

login(token="") # enter your token

# Download mesh and paint pipelines
snapshot_download(
    repo_id="tencent/Hunyuan3D-2",
    local_dir="models",
    allow_patterns=["hunyuan3d-dit-v2-0/model.fp16.safetensors",
                    "hunyuan3d-dit-v2-0/config.yaml"]
)

snapshot_download(
    repo_id="tencent/Hunyuan3D-2",
    local_dir="models",
    allow_patterns=["hunyuan3d-paint-v2-0-turbo/**"]
)

snapshot_download(
    repo_id="tencent/Hunyuan3D-2",
    local_dir="models",
    allow_patterns=["hunyuan3d-delight-v2-0/**"]
)
```

**T5 NF4 encoder:**

```python
snapshot_download(
    repo_id="diffusers/t5-nf4",
    local_dir="models/t5-nf4",
    local_dir_use_symlinks=False
)
```

**Stable Diffusion 3.5 LT:**

```python
from huggingface_hub import login, snapshot_download

login(token="YOUR_HUGGINGFACE_TOKEN")

snapshot_download(
    repo_id="stabilityai/stable-diffusion-3.5-large-turbo",
    local_dir="models/stable-diffusion-3.5-large-turbo",
    local_dir_use_symlinks=False
)
```

---

## Usage

### Server-side code

Once the above steps are done and and the prerequisites are installed (this section is to be done on a remote server which was the runpod pod in our case and can be the local system in your case):

- **Download the Models**
```bash
cd txt2_3D
python get_models.py
python get_img_models.py
```


- **2D Image Generation**

  1. Generate a 2D image from a text prompt using **Stable Diffusion 3.5 LT**.
  2. Optionally, use **FathomNet images** enhanced with SR_GAN and filtered for brightness, contrast, and sharpness.

- **3D Model Generation**

  1. Use **Hunyuan3D 2** for generating a 3D mesh from a single 2D image.
  2. Steps:
      - Generate a **mesh** from the image.
      - **Simplify the mesh** to reduce the number of triangles (from 10–15k to ~10%).
      - Generate **textured mesh** using the paint pipeline.
  3. Optional: Serve via **Flask endpoint** or visualize in web/Unity-based viewer.

- **Serve endpoint**
```bash
cd ..
cd visualiser/web
python remote_server.py
cd ..
cd ..
```

The endpoint should now be live on  http://ip-address:5000

For End to end result generation on local system (with required specifications),

Simply run

```bash
cd txt2_3D
python main.py
cd ..
```

### Client Side

```bash
cd visualiser/web
python app.py
```

You can run the project on:  http://127.0.0.1:8000

### Notebook

To avoid all these, run the** marine-text-to-3d.ipynb** in notebooks.

## Contributing

Contributions are what make the open-source community amazing. Any contributions you make are greatly appreciated.

1. Fork the Project 
2. Set upstream 
3. Create your Feature Branch:
   ```bash
   git checkout -b feature/AmazingFeature
   ```
4. Commit your Changes:
   ```bash
   git commit -m "Add some AmazingFeature"
   ```
5. Rebase from main:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```
6. Push to the Branch:
   ```bash
   git push origin feature/AmazingFeature
   ```
7. Open a Pull Request

---
## Future Goals

This project lays the foundation for AI-powered 3D asset generation for marine biology education. While the current implementation already supports text-to-3D conversion, visualization, and deployment, several avenues can be explored to enhance its capabilities further:

1. **Dataset Creation:**  
   Extend the solution to build a full-fledged dataset for marine creatures. Users can either fetch pre-generated 3D assets from the server or generate them on-demand, enabling resource-efficient usage for educational applications.

2. **3D Printing Toolkit:**  
   Develop a toolkit that directly converts generated `.glb` files into formats compatible with 3D printers, allowing physical models of marine species to be created for research and education.

3. **Animation Pipeline:**  
   Enhance generated 3D assets with animations using tools like UniRig to build skeletal structures (rigging). A basic pipeline has already been initiated to support motion-enabled 3D assets for interactive AR/VR experiences.

4. **Domain-Specific Fine-Tuning:**  
   Expand the current solution beyond marine biology by creating a user-friendly toolkit for fine-tuning Stable Diffusion 3.5 on custom datasets. This will enable domain-specific 3D asset generation across various industries and research fields.

---

## Acknowledgements

I would like to express my heartfelt gratitude to my mentors, **Krishan Mohan Patel**, **Himanshu Kumar**, and **Supreeth Kumar M**, for their unwavering support and guidance throughout this project. Their collective expertise, patient mentorship, and thoughtful insights have been instrumental in shaping both the technical depth and the direction of this work. The lessons learned under their mentorship will serve as a lasting foundation for future endeavors in this domain.  

I would also like to extend my sincere appreciation to the developers of **[Stable Diffusion](https://stability.ai/stable-diffusion)**, whose groundbreaking contributions in generative AI have enabled the seamless conversion of text into high-quality 2D imagery.  

My gratitude further extends to **[Tencent Hunyuan3D](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.git)**, whose innovative work in text-to-3D asset generation has been invaluable in bringing this project to life.  

I would also like to acknowledge **[FathomNet](https://www.mbari.org/data/fathomnet//)** and the many **open-source projects** leveraged in this work. Their open contributions to the community have provided the essential tools, datasets, and frameworks that made this project possible.  

This project is a small step forward, built upon the remarkable advancements of the open-source and research communities. To each of these contributors and mentors, I extend my deepest thanks.  

