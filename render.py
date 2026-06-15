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
