"""Picture edits of VeltOS Photos (Windows 11 Photos' "Edit image"): crop,
rotate in 90° steps, flip, brightness, contrast, saturation and warmth,
and the plain rotation of the viewer. Done with Pillow; the picture is
turned upright first (EXIF orientation), the EXIF data is kept with the
orientation reset, JPEG pictures are saved at quality 95.
"""

from pathlib import Path

ADJUSTMENTS = ("brightness", "contrast", "saturation", "warmth")


def _open(path):
    from PIL import Image, ImageOps
    image = Image.open(path)
    exif = image.getexif()
    image = ImageOps.exif_transpose(image)
    if 0x0112 in exif:
        exif[0x0112] = 1
    return image, exif


def apply(image, crop=None, rotation=0, flip=False, brightness=0, contrast=0, saturation=0, warmth=0):
    """The edited picture. `crop` is (left, top, right, bottom) in parts of
    the upright picture (0..1) after rotation; the adjustments go from
    -100 to 100 (0 changes nothing)."""
    from PIL import Image, ImageEnhance
    rotation %= 360
    if rotation:
        image = image.rotate(-rotation, expand=True)
    if flip:
        image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if crop:
        left, top, right, bottom = (max(0.0, min(1.0, float(v))) for v in crop)
        if right - left > 0.001 and bottom - top > 0.001 and (left, top, right, bottom) != (0, 0, 1, 1):
            w, h = image.size
            image = image.crop((round(left * w), round(top * h), round(right * w), round(bottom * h)))
    has_alpha = image.mode in ("RGBA", "LA", "PA")
    if any((brightness, contrast, saturation, warmth)):
        alpha = image.getchannel("A") if has_alpha else None
        rgb = image.convert("RGB")
        if brightness:
            rgb = ImageEnhance.Brightness(rgb).enhance(1 + brightness / 100)
        if contrast:
            rgb = ImageEnhance.Contrast(rgb).enhance(1 + contrast / 100)
        if saturation:
            rgb = ImageEnhance.Color(rgb).enhance(1 + saturation / 100)
        if warmth:
            shift = warmth / 100 * 0.12
            r, g, b = rgb.split()
            r = r.point(lambda v: min(255, max(0, round(v * (1 + shift)))))
            b = b.point(lambda v: min(255, max(0, round(v * (1 - shift)))))
            rgb = Image.merge("RGB", (r, g, b))
        image = rgb
        if alpha is not None:
            image.putalpha(alpha.resize(image.size))
    return image


def save(source, target=None, **edits):
    """Edit `source` and write it to `target` (the source itself when None,
    i.e. "Save"; another path for "Save as copy"). Returns the path."""
    source = Path(source)
    target = Path(target) if target else source
    image, exif = _open(source)
    fmt = image.format or (source.suffix.lstrip(".").upper() or "PNG")
    image = apply(image, **edits)
    options = {}
    suffix = target.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        options.update(quality=95, subsampling=0)
        fmt = "JPEG"
    elif suffix == ".png":
        fmt = "PNG"
    elif suffix == ".webp":
        options.update(quality=95)
        fmt = "WEBP"
    if exif and fmt in ("JPEG", "PNG", "WEBP"):
        options["exif"] = exif.tobytes()
    tmp = target.with_name(f".{target.name}.veltos-tmp")
    try:
        image.save(tmp, fmt, **options)
        tmp.replace(target)
    finally:
        tmp.unlink(missing_ok=True)
    return str(target)


def copy_name(path, word="Copy"):
    """"photo - Copy.jpg", "photo - Copy (2).jpg", ... like Windows (the
    word in the user's language: "Kopya" in Turkish)."""
    path = Path(path)
    stem, suffix = path.stem, path.suffix
    candidate = path.with_name(f"{stem} - {word}{suffix}")
    n = 2
    while candidate.exists():
        candidate = path.with_name(f"{stem} - {word} ({n}){suffix}")
        n += 1
    return candidate


def info(path):
    """Facts for the file information panel: size in pixels, camera,
    exposure, as far as the picture tells."""
    result = {"width": 0, "height": 0, "camera": "", "lens": "", "exposure": "", "iso": "", "focal": ""}
    try:
        from PIL import Image, ImageOps
        with Image.open(path) as image:
            exif = image.getexif()
            upright = ImageOps.exif_transpose(image)
            result["width"], result["height"] = upright.size
            make, model = str(exif.get(0x010F) or "").strip(), str(exif.get(0x0110) or "").strip()
            result["camera"] = model if model.lower().startswith(make.lower()) else f"{make} {model}".strip()
            sub = exif.get_ifd(0x8769)
            exposure = sub.get(0x829A)
            if exposure:
                value = float(exposure)
                result["exposure"] = f"1/{round(1 / value)} s" if 0 < value < 1 else f"{value:g} s"
            if sub.get(0x8827):
                result["iso"] = f"ISO {sub.get(0x8827)}"
            if sub.get(0x920A):
                result["focal"] = f"{float(sub.get(0x920A)):g} mm"
            result["lens"] = str(sub.get(0xA434) or "").strip()
    except Exception:  # not a picture Pillow knows (or broken): fewer facts
        pass
    return result
