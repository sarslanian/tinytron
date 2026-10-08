"""Generate the Nyan Cat screensaver sprite sheet for the 64x32 matrix.

Outputs:
  tinytron/nyan.bmp          8 frames stacked vertically (64x256, 4-bit indexed, ~8 KB) — copy to CIRCUITPY root
  nyan-preview.gif           upscaled LED-style preview (repo root)

Run: python3 tinytron/tools/make_nyan.py
"""
import os
from PIL import Image, ImageDraw

W, H = 64, 32
FRAMES = 8
STAR_SPEED = 8  # px/frame; FRAMES * STAR_SPEED == W so the star field loops seamlessly

# Palette — index order matters (0 is background). Tuned dim-ish for LEDs.
PALETTE = [
    (0x00, 0x10, 0x30),  # 0 background navy
    (0x00, 0x00, 0x00),  # 1 k outline
    (0xFF, 0xCC, 0x99),  # 2 t crust
    (0xFF, 0x66, 0xCC),  # 3 p filling
    (0xFF, 0x00, 0x88),  # 4 m sprinkle
    (0x99, 0x99, 0x99),  # 5 g fur
    (0xFF, 0xFF, 0xFF),  # 6 w white / stars
    (0xFF, 0x88, 0x99),  # 7 c cheek
    (0xFF, 0x00, 0x00),  # 8 rainbow red
    (0xFF, 0x99, 0x00),  # 9 orange
    (0xFF, 0xFF, 0x00),  # 10 yellow
    (0x33, 0xFF, 0x00),  # 11 green
    (0x00, 0x99, 0xFF),  # 12 blue
    (0x66, 0x33, 0xFF),  # 13 violet
]
RAINBOW = [8, 9, 10, 11, 12, 13]
CH = {"k": 1, "t": 2, "p": 3, "m": 4, "g": 5, "w": 6, "c": 7}

HEAD = [
    ".kk.......kk.",
    "kggk.....kggk",
    "kgggkkkkkgggk",
    "kgggggggggggk",
    "kggwkgggwkggk",
    "kggkkgggkkggk",
    "kccgkgkgkgcck",
    "kggggkgkggggk",
    ".kgggggggggk.",
    "..kkkkkkkkk..",
]

SPRINKLES = [(8, 3), (12, 2), (15, 4), (7, 6), (11, 7), (14, 8), (9, 9), (13, 10)]

# Star field: (x, y, phase). Phase picks the twinkle shape, advancing each frame.
STARS = [(4, 3, 0), (22, 1, 2), (40, 4, 1), (58, 2, 3),
         (12, 27, 2), (30, 29, 0), (50, 26, 3), (62, 30, 1)]


def put(img, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        img.putpixel((x, y), c)


def draw_sprite(img, rows, ox, oy):
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != ".":
                put(img, ox + dx, oy + dy, CH[ch])


def draw_star(img, x, y, phase):
    s = phase % 4
    if s == 0:
        put(img, x, y, 6)
    elif s == 1:
        for d in (-1, 1):
            put(img, x + d, y, 6)
            put(img, x, y + d, 6)
    elif s == 2:
        for d in (-2, -1, 1, 2):
            put(img, x + d, y, 6)
            put(img, x, y + d, 6)
    else:
        for d in (-2, 2):
            put(img, x + d, y, 6)
            put(img, x, y + d, 6)
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            put(img, x + dx, y + dy, 6)


def frame(i):
    img = Image.new("P", (W, H), 0)

    for sx, sy, ph in STARS:
        draw_star(img, (sx - i * STAR_SPEED) % W, sy, ph + i)

    bob = 1 if (i // 2) % 2 else 0  # cat bobs 1px every other pair of frames
    cx, cy = 24, 8 + bob             # cat origin (tart top-left outline)

    # Rainbow: 6 stripes x 2px behind the cat, 4px segments alternating up/down
    wave = (i // 2) % 2
    for x in range(0, cx + 4):
        seg_up = ((x // 4) + wave) % 2
        top = 9 + seg_up
        for s, col in enumerate(RAINBOW):
            put(img, x, top + s * 2, col)
            put(img, x, top + s * 2 + 1, col)

    # Tail (wags with the bob)
    ty = cy + 7 - bob
    for dx in range(4):
        put(img, cx - 4 + dx, ty, 1)
        put(img, cx - 4 + dx, ty + 1, 5)
        put(img, cx - 4 + dx, ty + 2, 1)

    # Legs — alternate stride
    stride = i % 2
    for lx in (cx + 2 + stride, cx + 6 + stride, cx + 12 - stride, cx + 16 - stride):
        put(img, lx, cy + 14, 5)
        put(img, lx + 1, cy + 14, 5)
        put(img, lx, cy + 15, 1)
        put(img, lx + 1, cy + 15, 1)

    # Pop-tart body: outline, crust, filling with rounded corners, sprinkles
    tw, th = 19, 14
    d = ImageDraw.Draw(img)
    d.rectangle([cx, cy, cx + tw - 1, cy + th - 1], fill=1)
    d.rectangle([cx + 1, cy + 1, cx + tw - 2, cy + th - 2], fill=2)
    d.rectangle([cx + 3, cy + 2, cx + tw - 4, cy + th - 3], fill=3)
    d.rectangle([cx + 2, cy + 3, cx + tw - 3, cy + th - 4], fill=3)
    for sx, sy in SPRINKLES:
        put(img, cx + sx - 1, cy + sy, 4)

    # Head overlaps the right side of the tart
    draw_sprite(img, HEAD, cx + 12, cy + 4 - bob)
    return img


def palette_bytes():
    flat = [v for rgb in PALETTE for v in rgb]
    return flat + [0] * (768 - len(flat))


def save_bmp4(img, path):
    """Write a 4-bit indexed BMP with a palette of only the colors we use.

    adafruit_imageload sizes the on-device Bitmap from the header's color count,
    so 14 colors -> 4 bits/pixel in RAM (8 KB for the sheet) instead of the
    8-bit/256-color file PIL writes (16 KB + a 256-entry Palette).
    """
    w, h = img.size
    row = w // 2  # 2 px per byte; 64 px -> 32 bytes, already 4-byte aligned
    n = len(PALETTE)
    data_off = 14 + 40 + n * 4
    size = data_off + row * h
    out = bytearray()
    out += b"BM" + size.to_bytes(4, "little") + bytes(4) + data_off.to_bytes(4, "little")
    out += (40).to_bytes(4, "little") + w.to_bytes(4, "little") + h.to_bytes(4, "little")
    out += (1).to_bytes(2, "little") + (4).to_bytes(2, "little") + bytes(4)
    out += (row * h).to_bytes(4, "little") + bytes(8)
    out += n.to_bytes(4, "little") + n.to_bytes(4, "little")
    for r, g, b in PALETTE:
        out += bytes((b, g, r, 0))
    px = img.load()
    for y in range(h - 1, -1, -1):  # BMP rows are bottom-up
        for x in range(0, w, 2):
            out.append((px[x, y] << 4) | px[x + 1, y])
    with open(path, "wb") as f:
        f.write(out)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    device_dir = os.path.dirname(here)
    repo = os.path.dirname(device_dir)

    frames = [frame(i) for i in range(FRAMES)]

    sheet = Image.new("P", (W, H * FRAMES), 0)
    for i, f in enumerate(frames):
        sheet.paste(f, (0, i * H))
    save_bmp4(sheet, os.path.join(device_dir, "nyan.bmp"))

    # LED-style preview: each pixel becomes a round dot on black
    S = 10
    previews = []
    for f in frames:
        f.putpalette(palette_bytes())
        rgb = f.convert("RGB")
        p = Image.new("RGB", (W * S, H * S), (8, 8, 8))
        dd = ImageDraw.Draw(p)
        for y in range(H):
            for x in range(W):
                dd.ellipse([x * S + 1, y * S + 1, x * S + S - 2, y * S + S - 2], fill=rgb.getpixel((x, y)))
        previews.append(p)
    previews[0].save(os.path.join(repo, "nyan-preview.gif"), save_all=True,
                     append_images=previews[1:], duration=100, loop=0)
    print("wrote nyan.bmp and nyan-preview.gif")


if __name__ == "__main__":
    main()
