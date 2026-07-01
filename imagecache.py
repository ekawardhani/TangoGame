import base64
from io import BytesIO
from typing import Optional

from PIL import Image

from cardgenerator import cloudflare_run
from gameconfig import ASSET_DIR, CF_IMAGE_MODEL
from utils import rel_path, slugify


def call_ai_image_api(prompt: str) -> Optional[bytes]:
    """Ask FLUX to generate one card image."""
    for attempt in range(1, 4):
        try:
            result = cloudflare_run(
                CF_IMAGE_MODEL,
                {"prompt": prompt, "steps": 4},
                timeout=120,
            )
            encoded = result.get("image", "")
            if encoded.startswith("data:"):
                encoded = encoded.split(",", 1)[1]
            if encoded:
                return base64.b64decode(encoded)
            raise ValueError("Cloudflare returned an empty image")
        except Exception as exc:
            print(f"[AI IMAGE] Attempt {attempt} failed:", exc)
    return None


def ensure_card_image(item: dict) -> str:
    """Return the card image path. Generate it first if it does not exist."""
    filename = f"{slugify(item['romaji'])}_{slugify(item['meaning'])}_visual_v2.png"
    output_path = ASSET_DIR / filename

    if output_path.exists():
        return rel_path(output_path)

    prompt = item.get("image_prompt") or (
        f"A clean, cute educational cartoon illustration of {item['meaning']}, "
        "centered composition, clear visual meaning, bright colors, light background, "
        "no text, no words, no letters"
    )

    image_bytes = call_ai_image_api(prompt)
    if image_bytes:
        try:
            generated = Image.open(BytesIO(image_bytes)).convert("RGB")
            generated.thumbnail((900, 900))

            canvas = Image.new("RGB", (900, 900), (248, 250, 252))
            x = (900 - generated.width) // 2
            y = (900 - generated.height) // 2
            canvas.paste(generated, (x, y))

            canvas.save(output_path)
            return rel_path(output_path)
        except Exception as exc:
            print("[AI SAVE] fallback:", exc)

    raise RuntimeError(f"AI could not generate an image for '{item['meaning']}'")


def build_card_item(item: dict) -> dict:
    """Attach the generated image path to a target vocabulary item."""
    card = dict(item)
    card["image"] = ensure_card_image(item)
    return card
