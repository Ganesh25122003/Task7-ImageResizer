import os
from pathlib import Path
from PIL import Image, ImageOps

# ==== Settings you can change easily ====
INPUT_FOLDER = "images"            # where your original images are
OUTPUT_FOLDER = "resized_images"   # where resized images will go
TARGET_SIZE = (800, 800)           # (width, height) in pixels
PAD_TO_EXACT_SIZE = True           # True = letterbox/pad to exact size
BACKGROUND_COLOR = (255, 255, 255) # padding color (white)

# Convert format? Options: None (keep original), "JPEG", "PNG", "WEBP"
CONVERT_TO_FORMAT = None           # e.g., "PNG" to force PNG output

# JPEG quality (only used if saving JPEG)
JPEG_QUALITY = 90
# =======================================

def ensure_dirs():
    Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)

def output_extension():
    if not CONVERT_TO_FORMAT:
        return None
    mapping = {"JPG": ".jpg", "JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
    return mapping.get(CONVERT_TO_FORMAT.upper(), f".{CONVERT_TO_FORMAT.lower()}")

def resize_with_aspect(img: Image.Image, size, pad=False, bg=(255, 255, 255)) -> Image.Image:
    """Resize while keeping aspect ratio. Optionally pad to exact size."""
    img = ImageOps.exif_transpose(img)  # correct orientation from EXIF
    if pad:
        # Fit inside and pad to exact size (letterbox effect)
        fitted = ImageOps.contain(img, size, method=Image.LANCZOS)
        # Choose base mode (keep alpha only if not saving JPEG)
        needs_alpha = (img.mode in ("RGBA", "LA")) and (CONVERT_TO_FORMAT not in ("JPG", "JPEG"))
        base_mode = "RGBA" if needs_alpha else "RGB"
        base = Image.new(base_mode, size, (bg[0], bg[1], bg[2], 0) if needs_alpha else bg)
        base.paste(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2), fitted if needs_alpha else None)
        return base
    else:
        # Fit inside box, size may be smaller than target in one dimension
        return ImageOps.contain(img, size, method=Image.LANCZOS)

def save_image(img: Image.Image, dest_path: Path, original_ext: str):
    # Decide format & extension
    if CONVERT_TO_FORMAT:
        fmt = CONVERT_TO_FORMAT.upper()
        ext = output_extension()
    else:
        fmt = None  # keep original
        ext = original_ext.lower()

    # Handle JPEG mode (JPEG doesn’t support alpha)
    if (fmt in ("JPG", "JPEG")) or (ext in (".jpg", ".jpeg")):
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

    dest = dest_path.with_suffix(ext)
    save_kwargs = {}
    if (fmt in ("JPG", "JPEG")) or (ext in (".jpg", ".jpeg")):
        save_kwargs.update(dict(quality=JPEG_QUALITY, optimize=True))

    img.save(dest, format=fmt, **save_kwargs)
    return dest

def main():
    ensure_dirs()
    input_dir = Path(INPUT_FOLDER)
    output_dir = Path(OUTPUT_FOLDER)

    supported = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")
    count = 0

    for name in os.listdir(input_dir):
        if not name.lower().endswith(supported):
            continue
        src = input_dir / name
        try:
            with Image.open(src) as im:
                resized = resize_with_aspect(im, TARGET_SIZE, pad=PAD_TO_EXACT_SIZE, bg=BACKGROUND_COLOR)
                dest = output_dir / Path(name).stem  # we'll add extension in save_image
                out_path = save_image(resized, dest, original_ext=Path(name).suffix)
                print(f"✔ Resized → {out_path}")
                count += 1
        except Exception as e:
            print(f"✖ Error processing {name}: {e}")

    print(f"\n✅ Done. Processed {count} image(s).")

if __name__ == "__main__":
    main()