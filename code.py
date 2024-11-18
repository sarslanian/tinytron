import time
import board
import displayio
from adafruit_display_shapes.rect import Rect
from adafruit_display_text.label import Label
from adafruit_matrixportal.matrixportal import MatrixPortal
from cta_helper import fetch_cta_data
from adafruit_bitmap_font import bitmap_font  # Correct import
import gc

# --- MatrixPortal Setup --- #
matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=True)

# --- Display Setup --- #
SCROLL_DELAY = 0.03

# Positions for both messages
hello_world_y_position = 4  # Position for the "Hello World" message
cta_data_y_position = 17    # Position for the CTA data
greeting_y_position = 13    # Position for the greeting message

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

# --- Add Shapes (Optional) --- #
# Add a blue rectangle as an example shape
rect = Rect(0, 7, 64, 11, fill=0x0000ff) # Brown color
# rect2 = Rect(0, 7, 64, 1, fill=0xffffff) # Brown color

group.append(rect)
# group.append(rect2)


# --- Create Text Labels --- #
# "Hello World" Label (example)
hello_world_label = Label(font, text="Booting up...")
hello_world_label.color = 0xFFFFFF  # White color
hello_world_label.x = 1
hello_world_label.y = hello_world_y_position
group.append(hello_world_label)

# CTA Data Label (initially empty, will update later)
cta_data_label = Label(font, text="Loading CTA Data...")
cta_data_label.color = 0x8B4513  # Brown color
cta_data_label.x = 1
cta_data_label.y = cta_data_y_position
group.append(cta_data_label)

# CTA Data Label (initially empty, will update later)
greeting_label = Label(font, text="HAVE A GOOD DAY!")
greeting_label.color = 0x000000  # Brown color
greeting_label.x = 1
greeting_label.y = greeting_y_position
group.append(greeting_label)


# --- Add the Display Group to MatrixPortal --- #
matrixportal.display.root_group = group  # This displays everything on the display

# --- Functions for Time and Formatting --- #

def convert_to_12hr_format(hour, minute):
    """Converts a 24-hour time to 12-hour format with AM/PM."""
    period = "a"
    if hour >= 12:
        period = "p"
    if hour == 0:
        hour = 12  # Midnight case
    elif hour > 12:
        hour -= 12  # Convert hour to 12-hour format

    # Format minute to ensure it's always 2 digits
    return f"{hour:02}:{minute:02}{period}"

def format_date_time(times):
    """Formats the date and time into 'MM/DD/YY hh:mm AM/PM'."""
    year = int(times[2:4])
    month = int(times[5:7])
    day = int(times[8:10])
    hour = int(times[11:13])
    minute = int(times[14:16])

    # Convert to 12-hour format
    formatted_time = convert_to_12hr_format(hour, minute)

    # Format the final output as 'MM/DD/YY hh:mm AM/PM'
    return f"{month}/{day}     {formatted_time}"


def fetch_weather(matrixportal):
    """Fetch data from the CTA API."""
    
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude=41.89536&longitude=13.41&current=temperature_2m,apparent_temperature&temperature_unit=fahrenheit&wind_speed_unit=mph"  # Ensure BASE_API_URL is defined
        print(f"Fetching data from {url}")

        # Making the HTTP request using adafruit_requests
        response = matrixportal.network.requests.get(url)
        print(f"resy {response}")

        if response.status_code == 200:
            print("here")
            # Only parse JSON if the response was successful
            data = response
            print(data)  # Optionally, log or print the data for debugging
            return data  # Return the JSON data if successful
        else:
            print(f"Error fetching data: HTTP {response.status_code} - {response.reason}")
            return None

    except Exception as e:
        # Catch any network or other errors
        print(f"An error occurred: {e}")
        return None

# --- Main Loop --- #
refresh_time = None
while True:
    if (not refresh_time) or (time.monotonic() - refresh_time) > 60:  # Refresh every 30 seconds
        try:
            print("Obtaining time from the server...")
            times = matrixportal.get_local_time()
            print(times)
            cta_msg = fetch_cta_data(matrixportal)  # Fetch the CTA data

            # Format the date and time to display
            formatted_date_time = format_date_time(times)
            print(formatted_date_time)  # Output: "11/10/24 03:30 PM"

            # Only update the text labels (avoid recreating them)
            hello_world_label.text = formatted_date_time
            cta_data_label.text = cta_msg

            del times  # Clear times data after it's no longer needed
            del formatted_date_time  # Clear formatted date time data
            del cta_msg  # Clear CTA data after it's no longer needed
            gc.collect()  # Force garbage collection
    
            # Update the refresh time to manage the loop interval
            refresh_time = time.monotonic()

        except RuntimeError as e:
            print("Unable to obtain time from the server, retrying - ", e)
            continue

    time.sleep(0.05)
