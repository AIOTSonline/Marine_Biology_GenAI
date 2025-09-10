from huggingface_hub import login, snapshot_download

# To be prompted for your token in the terminal or a notebook widget:
login(token="") # enter your token


# Folder where models will be saved
save_dir = "models/stable-diffusion-3.5-large-turbo"

# Download *all* files from the repo into save_dir
snapshot_download(
    repo_id="stabilityai/stable-diffusion-3.5-large-turbo",
    local_dir=save_dir,
    local_dir_use_symlinks=False  # Make actual copies instead of symlinks
)
# Repo ID for the NF4-quantized T5 encoder
repo_id = "diffusers/t5-nf4"

# Destination folder
local_dir = "models/t5-nf4"

# Download the full repo into models/t5-nf4
snapshot_download(
    repo_id=repo_id,
    local_dir=local_dir,
    local_dir_use_symlinks=False  # ensures actual files instead of symlinks
)

print("T5 NF4 model downloaded to:", local_dir)
print(f"Model fully downloaded to: {save_dir}")
