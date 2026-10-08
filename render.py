from utils import hex_to_rgb_bytes
from adafruit_display_shapes.rect import Rect

# SHAPE RENDERING FUNCTIONS
def renderRectangle(item):
    rect = Rect(item["x"], item["y"], item["w"], item["h"], fill=hex_to_rgb_bytes(item["f"]))
    return rect

def renderShape(item):
    return renderRectangle(item)


# TEXT RENDERING FUNCTIONS
from adafruit_display_text.label import Label

_font = None
_bold_font = None

def get_font():
    global _font
    if _font is None:
        try:
            from adafruit_bitmap_font import bitmap_font
            _font = bitmap_font.load_font("/small_font.bdf")
        except Exception as e:
            print(f"Font load failed: {e}")
    return _font

def get_bold_font():
    global _bold_font
    if _bold_font is None:
        try:
            from adafruit_bitmap_font import bitmap_font
            _bold_font = bitmap_font.load_font("/squeezed_bold_7.bdf")
        except Exception as e:
            print(f"Bold font load failed: {e}")
            _bold_font = get_font()
    return _bold_font

def render_basic_text(item):
    font = get_bold_font() if item.get("b") else get_font()
    label = Label(font, text=item["v"])
    label.color = hex_to_rgb_bytes(item["c"])
    label.x = item["x"]
    label.y = item["y"]
    return label

def renderText(item):
    return render_basic_text(item)


# IMAGE RENDERING FUNCTIONS
import displayio

def renderImage(item):
    bitmap = displayio.OnDiskBitmap(item["path"])
    sprite = displayio.TileGrid(
        bitmap,
        pixel_shader=bitmap.pixel_shader,
        x=item["x"],
        y=item["y"]
    )
    sprite_group = displayio.Group()
    sprite_group.append(sprite)
    return sprite_group


# ANIMATION RENDERING FUNCTIONS
def renderAnimation(item):
    """Load a vertical sprite sheet into RAM and return a TileGrid showing frame 0.

    Payload: {"t":"a","p":"/nyan.bmp","n":8,"ms":100} — n frames of the full
    64x32 panel stacked top-to-bottom. Frames are advanced by code.py's main
    loop, so the server publishes this once and the device animates locally.
    Uses imageload (in-RAM) rather than OnDiskBitmap so each frame change is a
    cheap index swap instead of a flash read.
    """
    import adafruit_imageload
    bitmap, palette = adafruit_imageload.load(
        item["p"], bitmap=displayio.Bitmap, palette=displayio.Palette
    )
    return displayio.TileGrid(
        bitmap,
        pixel_shader=palette,
        tile_width=bitmap.width,
        tile_height=bitmap.height // item["n"],
    )
