import os
from pathlib import Path

# Project files
BASE_DIR = Path(__file__).resolve().parent
ASSET_DIR = BASE_DIR / "card_assets"
ASSET_DIR.mkdir(exist_ok=True)
game_html = "tangogame.html"

# MediaPipe model path
# Put pose_landmarker.task in this folder, or set POSE_MODEL_PATH from Terminal.
model_path = os.getenv("POSE_MODEL_PATH", str(BASE_DIR / "pose_landmarker.task"))

# Server and camera settings
http_port = 8000
ws_port = 8765
camera_index = 0
camera_width = 640
camera_height = 480

# Game rules
input_confirm = 1.0
answer_hold = 15.0
round_session = 10
pose_index = {"LEFT": 0, "RIGHT": 1, "UP": 2, "DOWN": 3}

# Pose detection threshold
ELBOW_T = 160

# Cloudflare credentials
# The first names are the natural names used in this project.
# The second names are also accepted for compatibility with the old README.
cloudflare_ID = os.getenv("cloudflare_ID", os.getenv("CLOUDFLARE_ID", os.getenv("CLOUDFLARE_ACCOUNT_ID", ""))).strip()
cloudflare_API = os.getenv("cloudflare_API", os.getenv("CLOUDFLARE_TOKEN", os.getenv("CLOUDFLARE_API_TOKEN", ""))).strip()

# AI models
CF_TEXT_MODEL = os.getenv("CF_TEXT_MODEL", os.getenv("QUESTION_AI_MODEL", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"))
CF_IMAGE_MODEL = os.getenv("CF_IMAGE_MODEL", os.getenv("CARD_IMAGE_MODEL", "@cf/black-forest-labs/flux-1-schnell"))

cloudflare = bool(cloudflare_ID and cloudflare_API)
