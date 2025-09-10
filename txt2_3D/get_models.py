from huggingface_hub import login, snapshot_download

login(token="") # enter your token

repo_id = "tencent/Hunyuan3D-2"

# Destination folder to save the model
local_dir = "models"

# Download the model
snapshot_download(
    repo_id="tencent/Hunyuan3D-2",
    local_dir="models",
    allow_patterns=[
        "hunyuan3d-dit-v2-0/model.fp16.safetensors",
        "hunyuan3d-dit-v2-0/config.yaml"
    ],
)

snapshot_download(
    repo_id="tencent/Hunyuan3D-2",
    local_dir="models",
    allow_patterns=["hunyuan3d-paint-v2-0-turbo/**"],  # <== download everything inside the subfolder
)

snapshot_download(
    repo_id="tencent/Hunyuan3D-2",
    local_dir="models",
    allow_patterns=["hunyuan3d-delight-v2-0/**"],  # <== download everything inside the subfolder
)
