"""
3d_printing.py

- Converts .glb/.gltf -> .stl using trimesh (no Blender required).
- Slices with PrusaSlicer CLI only.
- Requires a working PrusaSlicer installation with CLI available in PATH.
- Outputs G-code ready for 3D printing.
- Edit constants near the top to change behavior.
"""

import sys
import shutil
import subprocess
from pathlib import Path

import trimesh

# --------------------------
# USER-CONSTANTS
# --------------------------
INPUT_FILE = "./output/paint_mesh_a dolphin.glb"   # path to input GLB/STL/OBJ
SAVE_DIR = "./output/"
TMP_DIR = "./tmp/"
SLICER = "prusa"               
INFILL_FRACTION = 0.20
INFILL_PATTERN = "honeycomb"     
PRUSASLICER_BIN = "prusa-slicer" 
SCALE = 50
ENABLE_SUPPORTS = True      
# --------------------------

def ensure_dirs():
    Path(SAVE_DIR).mkdir(parents=True, exist_ok=True)
    Path(TMP_DIR).mkdir(parents=True, exist_ok=True)

def convert_glb_to_stl(input_path: str, tmp_dir: str = TMP_DIR) -> str:
    in_path = Path(input_path)
    if not in_path.exists():
        raise FileNotFoundError(f"Input not found: {in_path}")

    mesh = trimesh.load(in_path, force='mesh')
    if isinstance(mesh, trimesh.Scene):
        print("[convert] Input is a Scene; concatenating geometry into single mesh...")
        mesh = trimesh.util.concatenate([m for m in mesh.geometry.values()])

    if not mesh.is_watertight:
        print("[convert] Mesh is NOT watertight. Attempting simple repair...")
        try:
            mesh.fill_holes()
            if mesh.is_watertight:
                print("[convert] Mesh repaired to watertight.")
            else:
                print("[convert] Mesh still not watertight after fill_holes(). Slicer may fail.")
        except Exception as e:
            print("[convert] Repair attempt failed:", e)

    input_name = f"tmp_{in_path.stem}".replace(" ", "_")
    out_stl = Path(tmp_dir) / f"{input_name}.stl"
    mesh.export(out_stl)
    if not out_stl.exists() or out_stl.stat().st_size == 0:
        raise RuntimeError("STL export failed or file empty")
    print("[convert] Exported STL to:", out_stl)
    return str(out_stl)

def is_exe_available(name):
    return shutil.which(name) is not None

def run_subprocess(cmd):
    """Run command, stream stdout/stderr, return returncode."""
    print("[run] " + " ".join(shlex_quote(c) for c in cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.stdout:
        print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode

def shlex_quote(s):
    # simple quoting for printing readability; subprocess gets raw args list so no need to quote there
    return f"'{s}'" if " " in s else s

def slice_with_prusaslicer(stl_path: str, gcode_out: str) -> bool:
    # find prusa binary
    candidates = [PRUSASLICER_BIN, "prusa-slicer", "PrusaSlicer"]
    prusa = next((c for c in candidates if is_exe_available(c)), None)
    if prusa is None:
        print("[slice:prusa] PrusaSlicer CLI not found (searched):", candidates)
        return False

    # Build the command (use --export-gcode action)
    cmd = [
        prusa,
        "--export-gcode",
        "--output", str(gcode_out),
        "--fill-density", str(INFILL_FRACTION),
        "--fill-pattern", str(INFILL_PATTERN),
        "--scale", str(SCALE),
    ]
    if ENABLE_SUPPORTS:
        cmd.append("--support-material")

    cmd.append(str(stl_path))

    print("[slice:prusa] Running:", " ".join(shlex_quote(c) for c in cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.stdout:
        print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)

    if proc.returncode == 0 and Path(gcode_out).exists():
        print("[slice:prusa] PrusaSlicer produced gcode at:", gcode_out)
        return True

    print("[slice:prusa] PrusaSlicer failed (return code {}).".format(proc.returncode))
    return False

def main():
    ensure_dirs()
    inp = Path(INPUT_FILE)
    if not inp.exists():
        print("Input file not found:", inp)
        sys.exit(2)

    working_stl = None
    if inp.suffix.lower() in (".glb", ".gltf", ".obj", ".ply"):
        try:
            tmp_stl = convert_glb_to_stl(str(inp), TMP_DIR)
        except Exception as e:
            print("[main] Conversion failed:", e)
            sys.exit(3)
        working_stl = tmp_stl
    elif inp.suffix.lower() == ".stl":
        working_stl = str(inp)
    else:
        print("[main] Unsupported input extension:", inp.suffix, "— provide .glb/.gltf/.stl/.obj")
        sys.exit(4)

    safe_base = inp.stem.replace(" ", "_")
    gcode_out_path = Path(SAVE_DIR) / f"printer3d_{safe_base}.gcode"

    success = slice_with_prusaslicer(working_stl, str(gcode_out_path))

    if not success:
        print("Slicing failed.")
        sys.exit(6)

    print("Slicing succeeded. Output G-code:", gcode_out_path.resolve())
    print("Tip: Open output in PrusaSlicer preview or upload to OctoPrint for inspection/printing.")

    if tmp_stl:
        try:
            Path(tmp_stl).unlink(missing_ok=True)
            print("[main] Cleaned temp STL:", tmp_stl)
        except Exception as e:
            print("Warning: could not remove temp STL:", e)

if __name__ == "__main__":
    main()
