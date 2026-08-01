#!/usr/bin/env python3
"""Generate the original Divine Elytra equipment and inventory textures."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
WING_TEXTURES = ROOT / "assets" / "minecraft" / "textures" / "entity" / "equipment" / "wings"
ITEM_TEXTURES = ROOT / "assets" / "minecraft" / "textures" / "item"

TRANSPARENT = (0, 0, 0, 0)
SHADOW = (77, 72, 58, 255)
FEATHER_SHADE = (161, 157, 143, 255)
FEATHER = (226, 224, 210, 255)
IVORY = (250, 249, 239, 255)
HIGHLIGHT = (255, 255, 252, 255)
GOLD_SHADOW = (111, 76, 19, 255)
GOLD = (205, 159, 48, 255)
GOLD_LIGHT = (255, 225, 131, 255)
CYAN = (82, 227, 239, 255)


def row_bounds(image: Image.Image, y: int) -> tuple[int, int] | None:
    visible = [x for x in range(image.width) if image.getpixel((x, y))[3] > 0]
    if not visible:
        return None
    return min(visible), max(visible)


def make_worn_wings() -> None:
    """Keep vanilla's wing silhouette while painting layered ivory feathers."""
    source = Image.open(WING_TEXTURES / "elytra.png").convert("RGBA")
    result = Image.new("RGBA", source.size, TRANSPARENT)

    for y in range(source.height):
        bounds = row_bounds(source, y)
        if bounds is None:
            continue
        left, right = bounds
        width = right - left + 1
        for x in range(left, right + 1):
            alpha = source.getpixel((x, y))[3]
            if not alpha:
                continue
            local_x = x - left
            leading_edge = local_x <= 1
            trailing_edge = local_x >= width - 2
            feather_seam = y >= 5 and y % 4 == 0
            inner_rib = local_x == max(2, width // 3) and y >= 3

            color = FEATHER
            if feather_seam:
                color = FEATHER_SHADE
            elif (local_x + y) % 7 == 0:
                color = IVORY
            if y >= 5 and local_x == max(2, width // 3) + 1:
                color = HIGHLIGHT
            if leading_edge or inner_rib:
                color = GOLD
            if leading_edge and y % 3 == 0:
                color = GOLD_LIGHT
            if trailing_edge:
                color = SHADOW
            if y <= 2:
                color = GOLD_SHADOW if y == 0 else GOLD
            result.putpixel((x, y), (*color[:3], alpha))

    # The small cyan setting reads as a divine clasp at the shoulder.
    for point in ((35, 2), (36, 2), (35, 3)):
        if source.getpixel(point)[3] > 0:
            result.putpixel(point, CYAN)
    result.save(WING_TEXTURES / "tyraels_elytra.png")


def paint_wing(image: Image.Image, points: tuple[tuple[int, int], ...], mirror: bool) -> None:
    for x, y in points:
        draw_x = 15 - x if mirror else x
        color = IVORY
        if x in (2, 3) or y in (4, 8, 12):
            color = FEATHER_SHADE
        if x == 4:
            color = GOLD
        image.putpixel((draw_x, y), color)


def make_inventory_icons() -> None:
    icon = Image.new("RGBA", (16, 16), TRANSPARENT)
    wing_points = (
        (4, 2),
        (3, 3), (4, 3), (5, 3),
        (2, 4), (3, 4), (4, 4), (5, 4),
        (2, 5), (3, 5), (4, 5), (5, 5),
        (1, 6), (2, 6), (3, 6), (4, 6),
        (1, 7), (2, 7), (3, 7), (4, 7),
        (1, 8), (2, 8), (3, 8), (4, 8),
        (2, 9), (3, 9), (4, 9),
        (2, 10), (3, 10), (4, 10),
        (3, 11), (4, 11),
        (3, 12),
    )
    paint_wing(icon, wing_points, mirror=False)
    paint_wing(icon, wing_points, mirror=True)
    icon.putpixel((7, 2), GOLD_LIGHT)
    icon.putpixel((8, 2), GOLD_LIGHT)
    icon.putpixel((7, 3), CYAN)
    icon.putpixel((8, 3), CYAN)
    icon.save(ITEM_TEXTURES / "tyraels_elytra.png")

    broken = icon.copy()
    muted = {
        IVORY: FEATHER_SHADE,
        FEATHER_SHADE: SHADOW,
        GOLD: GOLD_SHADOW,
        GOLD_LIGHT: GOLD,
        CYAN: SHADOW,
    }
    broken.putdata([muted.get(pixel, pixel) for pixel in broken.getdata()])
    for point in ((1, 7), (14, 7), (2, 10), (13, 10), (3, 12), (12, 12)):
        broken.putpixel(point, TRANSPARENT)
    broken.save(ITEM_TEXTURES / "tyraels_elytra_broken.png")


def main() -> None:
    make_worn_wings()
    make_inventory_icons()


if __name__ == "__main__":
    main()
