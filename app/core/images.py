"""Procesado das fotos de perfil: valida, endereita, recorta en cadrado e garda como WebP sen metadatos."""
import io
import re
import secrets
from pathlib import Path

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

# 800 px: nítida en pantallas retina e se máis adiante a mostramos en grande
PHOTO_SIZE = 800
MAX_PIXELS = 40_000_000  # ~ foto de 40 MP; máis é sospeitoso (bomba de descompresión)
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
PHOTO_NAME = re.compile(r"^[0-9a-f]{32}\.webp$")


def process_photo(data: bytes) -> bytes:
    """Devolve a foto lista para gardar (WebP 800×800). Nunca garda o EXIF (GPS, móbil…)."""
    try:
        img = Image.open(io.BytesIO(data))
        if img.format not in ALLOWED_FORMATS:
            raise HTTPException(status_code=415, detail="image_format")
        w, h = img.size
        if w * h > MAX_PIXELS or w < 64 or h < 64:
            raise HTTPException(status_code=422, detail="image_invalid")
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(status_code=422, detail="image_invalid")

    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "transparency" in img.info or img.mode in ("LA", "P") else "RGB")
    if img.mode == "RGBA":
        # Fondo branco para PNG con transparencia
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.getchannel("A"))
        img = bg
    # Recorte cadrado lixeiramente cara arriba: nas fotos verticais a cara adoita estar no terzo superior
    img = ImageOps.fit(img, (PHOTO_SIZE, PHOTO_SIZE), Image.Resampling.LANCZOS, centering=(0.5, 0.35))

    out = io.BytesIO()
    img.save(out, format="WEBP", quality=90, method=6)
    return out.getvalue()


def new_photo_name() -> str:
    return f"{secrets.token_hex(16)}.webp"


def photo_path(media_dir: str, name: str) -> Path:
    if not PHOTO_NAME.match(name):
        raise HTTPException(status_code=404, detail="photo_not_found")
    return Path(media_dir) / "athletes" / name


def write_photo(media_dir: str, name: str, data: bytes) -> Path:
    path = photo_path(media_dir, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)
    return path


def delete_photo(media_dir: str, name: str | None) -> None:
    if not name:
        return
    try:
        photo_path(media_dir, name).unlink(missing_ok=True)
    except HTTPException:
        pass
