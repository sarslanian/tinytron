from utils import hex_to_rgb_bytes
from adafruit_display_shapes.rect import Rect

# SHAPE RENDERING FUNCTIONS
def renderRectangle(item):
    rect = Rect(item["start_x"], item["start_y"], item["width"], item["height"], fill = hex_to_rgb_bytes(item["fill"]))  # Example color
    return rect

def renderShape(item):
    if item["shape"] == "rect":
        return renderRectangle(item)
    else:
        print("Unsupported shape found")
        return None
   
    
# TEXT RENDERING FUNCTIONS
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font

# Load a font file (adjust path if needed)
font_path = "/small_font.bdf"  # Replace with correct font file path
font = bitmap_font.load_font(font_path)  # Corrected usage of load_font()

def render_basic_text(item):
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


