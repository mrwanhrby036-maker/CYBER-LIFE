#!/usr/bin/env python3
"""Convert white-background artwork into true transparent WebP images.

The image model returns RGB files on a white plate. This removes only the
white region connected to the border (so white details inside the artwork
survive), un-premultiplies the white fringe on anti-aliased edges, trims the
empty margin and writes a real RGBA WebP with an alpha channel.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

WHITE_LOW = 228          # pixels above this on every channel are background candidates
FRINGE_LOW, FRINGE_HIGH = 205, 250   # soft alpha ramp for edge pixels
MAX_SIDE = 520
PAD = 12


def make_transparent(path: Path) -> dict:
    src = Image.open(path).convert("RGB")
    rgb = np.asarray(src).astype(np.float32)
    min_channel = rgb.min(axis=2)

    # 1. Candidate background = near-white pixels.
    candidate = min_channel >= WHITE_LOW
    labels, count = ndimage.label(candidate)
    border_labels = set(np.unique(np.concatenate([
        labels[0, :], labels[-1, :], labels[:, 0], labels[:, -1]])))
    border_labels.discard(0)
    background = np.isin(labels, list(border_labels)) if border_labels else np.zeros_like(candidate)

    # 2. Hard alpha, then a soft ramp on the 2-pixel ring around the cutout so
    #    anti-aliased edges do not keep a white halo.
    alpha = np.where(background, 0.0, 1.0)
    ring = ndimage.binary_dilation(background, iterations=2) & ~background
    ramp = np.clip((FRINGE_HIGH - min_channel) / (FRINGE_HIGH - FRINGE_LOW), 0.0, 1.0)
    alpha[ring] = np.minimum(alpha[ring], ramp[ring])
    alpha = ndimage.gaussian_filter(alpha, sigma=0.4)
    alpha[background] = 0.0

    # 3. Remove white contamination from semi-transparent edge pixels.
    a = alpha[..., None]
    safe = np.maximum(a, 1e-3)
    cleaned = np.clip((rgb - (1.0 - a) * 255.0) / safe, 0, 255)
    cleaned = np.where(a > 0.02, cleaned, 0)

    out = np.dstack([cleaned, alpha * 255.0]).astype(np.uint8)
    image = Image.fromarray(out, "RGBA")

    # 4. Trim transparent margin.
    bbox = image.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    if bbox:
        left, upper, right, lower = bbox
        left = max(0, left - PAD)
        upper = max(0, upper - PAD)
        right = min(image.width, right + PAD)
        lower = min(image.height, lower + PAD)
        image = image.crop((left, upper, right, lower))

    if max(image.size) > MAX_SIDE:
        ratio = MAX_SIDE / max(image.size)
        image = image.resize((round(image.width * ratio), round(image.height * ratio)), Image.LANCZOS)

    # WebP keeps the alpha channel and is ~95% smaller than PNG for this artwork.
    out_path = path.with_suffix(".webp")
    image.save(out_path, "WEBP", quality=86, method=6)
    if out_path != path:
        path.unlink()
    coverage = float((np.asarray(image.getchannel("A")) > 8).mean())
    return {"file": out_path.name, "size": image.size, "mode": image.mode,
            "opaque_ratio": round(coverage, 3), "bytes": out_path.stat().st_size}


def main() -> None:
    targets = [Path(p) for p in sys.argv[1:]]
    if not targets:
        root = Path(__file__).resolve().parents[1] / "frontend" / "assets"
        targets = sorted(root.glob("service-*.png")) + sorted(root.glob("character-*.png"))
        if not targets:
            targets = sorted(root.glob("service-*.webp")) + sorted(root.glob("character-*.webp"))
    for path in targets:
        print(make_transparent(path))


if __name__ == "__main__":
    main()
