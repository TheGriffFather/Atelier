"""Original procedural colour studies for Atelier's synthetic demonstration.

These graphics are sample artwork, not reproductions or works by a real artist.
They are generated locally with Pillow and are covered by the repository MIT license.
"""

from pathlib import Path
import math
import random
from PIL import Image, ImageDraw

PALETTES = [
    ("#eee5d4", "#bd634b", "#223c49", "#d2ac62", "#456568"),
    ("#d9ddd0", "#375c58", "#182d3c", "#d9ad6c", "#779289"),
    ("#e9e1d5", "#d4a358", "#b76143", "#293b48", "#877464"),
    ("#dfd5c5", "#344b61", "#80908c", "#c98857", "#212c38"),
]


def make_study(path: Path, index: int) -> tuple[int, int]:
    """Create one textured geometric study with a repeatable seed."""
    sizes = [(720, 920), (800, 650), (720, 840), (760, 760)]
    w, h = sizes[index % 4]
    rng = random.Random(20260918 + index)
    paper, terracotta, ink, gold, sage = PALETTES[(index + index // 6) % len(PALETTES)]
    image = Image.new("RGB", (w, h), paper)
    draw = ImageDraw.Draw(image)
    margin = int(w * 0.08)
    kind = index % 6
    if kind == 0:  # Solar landscape; layered cut-paper contours.
        draw.ellipse((w * 0.55, h * 0.13, w * 0.84, h * 0.13 + w * 0.29), fill=gold)
        for layer, color in enumerate([sage, ink, terracotta]):
            points = [(margin, h - margin)]
            for x in range(margin, w - margin + 1, 6):
                y = h * (0.53 + layer * 0.13) + math.sin(x / w * 5 + layer * 1.1) * h * 0.065
                points.append((x, y))
            points.extend([(w - margin, h - margin)])
            draw.polygon(points, fill=color)
        draw.line((margin, h * 0.38, w * 0.43, h * 0.38), fill=ink, width=2)
    elif kind == 1:  # Woven field of drifting colour bands.
        for j in range(9):
            x = margin + j * (w - 2 * margin) / 9
            points = [(x, margin), (x + w * 0.073, margin)]
            points += [
                (x + w * 0.073 + math.sin(y / h * 5 + j * 0.55) * w * 0.023, y)
                for y in range(margin, h - margin, 5)
            ]
            points += [
                (x + math.sin(y / h * 5 + j * 0.55) * w * 0.023, y)
                for y in range(h - margin, margin, -5)
            ]
            draw.polygon(points, fill=[ink, terracotta, sage, gold][j % 4])
    elif kind == 2:  # Architectural arches and a quiet sun.
        draw.rectangle((margin, h * 0.38, w * 0.62, h - margin), fill=terracotta)
        draw.pieslice((margin, h * 0.13, w * 0.62, h * 0.13 + w * 0.54), 180, 360, fill=terracotta)
        draw.rectangle((w * 0.27, h * 0.4, w * 0.46, h - margin), fill=paper)
        draw.pieslice((w * 0.27, h * 0.27, w * 0.46, h * 0.27 + w * 0.19), 180, 360, fill=paper)
        draw.ellipse((w * 0.66, h * 0.19, w * 0.85, h * 0.19 + w * 0.19), fill=gold)
        draw.rectangle((w * 0.62, h * 0.66, w - margin, h - margin), fill=ink)
        for j in range(8):
            y = h * 0.48 + j * 13
            draw.line((w * 0.69, y, w * 0.85, y), fill=sage, width=3)
    elif kind == 3:  # Botanical silhouette, rendered as a screen print.
        draw.rectangle((margin, margin, w - margin, h - margin), fill=ink)
        draw.ellipse((w * 0.51, h * 0.14, w * 0.84, h * 0.14 + w * 0.33), fill=gold)
        stem = [
            (w * 0.42, h * 0.86),
            (w * 0.48, h * 0.69),
            (w * 0.42, h * 0.51),
            (w * 0.49, h * 0.27),
        ]
        draw.line(stem, fill=paper, width=6)
        for j in range(7):
            y = h * (0.34 + j * 0.07)
            x = w * 0.45
            side = 1 if j % 2 else -1
            draw.polygon(
                [
                    (x, y + h * 0.09),
                    (x + side * w * 0.2, y - h * 0.025),
                    (x + side * w * 0.23, y + h * 0.045),
                    (x, y + h * 0.09),
                ],
                fill=sage if j % 3 else terracotta,
            )
    elif kind == 4:  # Orbital forms, thin offset registration lines.
        for j, color in enumerate([ink, terracotta, gold, sage]):
            x = w * (0.12 + (j % 2) * 0.39)
            y = h * (0.14 + (j // 2) * 0.39)
            draw.ellipse((x, y, x + w * 0.36, y + w * 0.36), fill=color)
            draw.rectangle((x, y + w * 0.18, x + w * 0.36, y + w * 0.36), fill=paper)
        for j in range(10):
            y = h * 0.48 + j * 8
            draw.line((w * 0.12, y, w * 0.87, y), fill=ink, width=1)
    else:  # Still life of a carafe and two bowls.
        draw.rectangle((margin, h * 0.67, w - margin, h - margin), fill=sage)
        draw.rectangle((w * 0.23, h * 0.23, w * 0.39, h * 0.49), fill=terracotta)
        draw.rounded_rectangle((w * 0.17, h * 0.4, w * 0.45, h * 0.8), radius=45, fill=terracotta)
        draw.ellipse((w * 0.51, h * 0.52, w * 0.84, h * 0.79), fill=ink)
        draw.rectangle((w * 0.50, h * 0.5, w * 0.85, h * 0.65), fill=paper)
        draw.ellipse((w * 0.52, h * 0.58, w * 0.83, h * 0.65), fill=gold)
        draw.ellipse((w * 0.57, h * 0.21, w * 0.76, h * 0.21 + w * 0.19), fill=gold)
    # Fine deterministic grain gives the flat shapes a printed-paper finish.
    grain = Image.frombytes("L", (w, h), rng.randbytes(w * h)).convert("RGB")
    image = Image.blend(image, grain, 0.055)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, quality=93, optimize=True)
    return w, h
