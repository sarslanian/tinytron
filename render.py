from utils import hex_to_rgb_bytes
from adafruit_display_shapes.rect import Rect

# SHAPE RENDERING FUNCTIONS
def renderRectangle(item):
    rect = Rect(item["start_x"], item["start_y"], item["width"], item["height"], fill=hex_to_rgb_bytes(item["fill"]))
    return rect

def renderShape(item):
    if item["shape"] == "rect":
        return renderRectangle(item)
    else:
        print("Unsupported shape found")
        return None


# TEXT RENDERING FUNCTIONS
from adafruit_display_text.label import Label

_font = None

def get_font():
    global _font
    if _font is None:
        try:
            from adafruit_bitmap_font import bitmap_font
            _font = bitmap_font.load_font("/small_font.bdf")
        except Exception as e:
            print(f"Font load failed: {e}")
    return _font

def render_basic_text(item):
    font = get_font()
    label = Label(font, text=item["text"])
    label.color = hex_to_rgb_bytes(item["color"])
    label.x = item["x"]
    label.y = item["y"]
    return label

def renderText(item):
    return render_basic_text(item)


# IMAGE RENDERING FUNCTIONS
import displayio

def renderImage(item):
    # Load the sprite sheet (bitmap)
    bitmap = displayio.OnDiskBitmap(item["path"])

    # Create the sprite TileGrid
    sprite = displayio.TileGrid(
        bitmap,
        pixel_shader=bitmap.pixel_shader,
        x=item["x"],
        y=item["y"]
    )

    sprite_group = displayio.Group()
    sprite_group.append(sprite)

    return sprite_group
