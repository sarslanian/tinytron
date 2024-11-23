import time
import board
import displayio
from adafruit_display_shapes.rect import Rect
from adafruit_display_text.label import Label
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_bitmap_font import bitmap_font  # Correct import
import json

# --- MatrixPortal Setup --- #
matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=True)

# Load a font file (adjust path if needed)
font_path = "/small_font.bdf"  # Replace with correct font file path
font = bitmap_font.load_font(font_path)  # Corrected usage of load_font()

# Create a display group for shapes and text
group = displayio.Group()

# --- Add Background Color --- #
# Add background (Black color background)
color_bitmap = displayio.Bitmap(64, 32, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x000000  # Black color
bg_sprite = displayio.TileGrid(color_bitmap, x=0, y=0, pixel_shader=color_palette)
group.append(bg_sprite)

# Open the file and load the data
with open('payload.json', 'r') as file:
    payload = json.load(file)

print(payload)


def hex_to_rgb_bytes(hex_color):
    # Strip the "0x" prefix and convert to an integer
    hex_color = hex_color[2:]  # Remove the '0x' prefix
    rgb = int(hex_color, 16)
    
    # Extract the red, green, and blue components (each is an integer between 0 and 255)
    red = (rgb >> 16) & 0xFF
    green = (rgb >> 8) & 0xFF
    blue = rgb & 0xFF
    
    # Return as a tuple of RGB bytes
    return (red, green, blue)


# --- Download and Display a Remote BMP Image --- #
# URL of the image you want to download
image_url = "https://people.math.sc.edu/Burkardt/data/bmp/blackbuck.bmp"  # Replace with your image URL

# Define the local path to save the downloaded image
image_path = "/downloaded_image.bmp"

# Download the image
try:
    matrixportal.network.download(image_url, image_path)
    print("Image downloaded successfully!")
except Exception as e:
    print(f"Failed to download image: {e}")

# Open the downloaded image file and convert it to a Bitmap
bitmap = displayio.OnDiskBitmap(image_path)

# Create a TileGrid to display the image
image_sprite = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
group.append(image_sprite)




for item in payload["data"]:
    if item["type"] == "shape":
        rect = Rect(item["start_x"], item["start_y"], item["width"], item["height"], fill=0X0000ff) # Brown color
        group.append(rect)
        print(f"Shape found with fill color {item['fill']} at ({item['start_x']}, {item['start_y']}) with dimensions {item['width']}x{item['height']}")
    elif item["type"] == "text":
        label = Label(font, text=item["text"])
        label.color = hex_to_rgb_bytes(item["color"])
        label.x = item["x"]
        label.y = item["y"]
        group.append(label)
        print(f"Text found: '{item['text']}' at ({item['x']}, {item['y']}) with color {item['color']}")




# --- Add the Display Group to MatrixPortal --- #
matrixportal.display.root_group = group  # This displays everything on the display

# --- Main Loop --- #
refresh_time = None
while True:
    if (not refresh_time) or (time.monotonic() - refresh_time) > 60:  # Refresh every 30 seconds
        try:
            
            refresh_time = time.monotonic()

        except RuntimeError as e:
            print("Unable to obtain time from the server, retrying - ", e)
            continue

    time.sleep(0.05)
