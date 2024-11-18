import time
import board
import terminalio
from adafruit_matrixportal.matrixportal import MatrixPortal
import adafruit_requests

# --- API Setup --- #
API_URL = "https://lapi.transitchicago.com/api/1.0/ttarrivals.aspx?mapid=40710&max=6&key=c17913e4087c41bb9a5358afd47398f0"

# --- MatrixPortal Setup --- #
matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=True)

# --- Display Setup --- #
SCROLL_DELAY = 0.03
text_y_position = 15

matrixportal.add_text(
    text_font=terminalio.FONT,
    text_position=(2, text_y_position),
    text_color=0x8b4513,
    scrolling=False,
)

# Dictionary to abbreviate destination names
DESTINATION_ABBREVIATIONS = {
    "Kimball": "KMBL",
    "Loop": "LOOP",
    # Add other destinations here as needed
}

# Global message variable to hold the train data message
message = ""

def fetch_cta_data():
    """Fetch and parse CTA train data."""
    global message  # Declare message as global to access it outside the function
    try:
        print("Fetching data from", API_URL)
        response = matrixportal.network.requests.get(API_URL)

        if response.status_code == 200:
            xml_data = response.text
            arrivals = []

            # Parse the XML for eta elements
            start = xml_data.find('<eta>')
            while start != -1:
                end = xml_data.find('</eta>', start)
                if end == -1:
                    break

                arrival_data = xml_data[start:end]
                arrival = {}
                for field in ['rn', 'destNm', 'arrT']:
                    field_start = arrival_data.find(f'<{field}>') + len(field) + 2
                    field_end = arrival_data.find(f'</{field}>', field_start)
                    arrival[field] = arrival_data[field_start:field_end].strip()

                arrivals.append(arrival)
                start = xml_data.find('<eta>', end)

            # Sort arrivals by estimated arrival time
            arrivals.sort(key=lambda x: x['arrT'])

            # Prepare the message for display (display only the next 2 trains)
            message = ""
            for train in arrivals[:6]:  # Display the next two trains
                # Abbreviate destination if possible
                dest = DESTINATION_ABBREVIATIONS.get(train['destNm'], train['destNm'])

                # Get the arrival time (arrT) and manually parse it
                arr_time_str = train['arrT']
                arr_date_str, arr_time_str = arr_time_str.split(' ')
                year = int(arr_date_str[0:4])
                month = int(arr_date_str[4:6])
                day = int(arr_date_str[6:8])
                hour, minute, second = map(int, arr_time_str.split(':'))

                # Convert the arrival time to a timestamp (seconds since the epoch)
                arr_time = time.mktime((year, month, day, hour, minute, second, 0, 0, 0))

                # Get current time
                current_time = time.time()

                # Calculate the time difference in seconds and convert to minutes
                time_diff = arr_time - current_time
                minutes_until_arrival = int(time_diff / 60)

                # Calculate the number of characters needed to format the destination field based on minutes
                if minutes_until_arrival == 0:
                    dest_field = f"{dest:<7}"
                    minutes_until_arrival = "DUE "
                elif minutes_until_arrival < 10:
                    # For single-digit minutes, set a 6-character wide field
                    dest_field = f"{dest:<6}"
                elif minutes_until_arrival > 10:
                    # For double-digit minutes, set a 5-character wide field
                    dest_field = f"{dest:<5}"

                # Format the message with the correct alignment based on the minutes
                message += f"{dest_field}{minutes_until_arrival}min\n"



            print(message)
            matrixportal.set_text(message)  # Update matrix display

        else:
            print(f"Error fetching data: HTTP {response.status_code} - {response.reason}")

    except Exception as e:
        print(f"An error occurred while fetching data: {e}")

def scroll_vertically(message, delay=5):
    """Scroll the message vertically and update every 5 seconds."""
    lines = message.split('\n')  # Split message into lines for vertical scrolling
    line_index = 0

    while True:
        # Display the current two lines
        matrixportal.set_text("\n".join(lines[line_index:line_index + 2]))  # Show 2 lines at a time

        # Wait for 5 seconds before moving to the next two lines
        time.sleep(delay)

        # Update line_index to scroll vertically
        line_index += 2
        if line_index >= len(lines):  # If we've reached the end, start over
            line_index = 0

# --- Main Loop --- #
refresh_time = None
while True:
    if (not refresh_time) or (time.monotonic() - refresh_time) > 120:  # Refresh every 2 minutes
        try:
            print("Obtaining time from the server...")
            matrixportal.get_local_time()
            fetch_cta_data()  # Fetch the CTA data
            refresh_time = time.monotonic()
        except RuntimeError as e:
            print("Unable to obtain time from the server, retrying - ", e)
            continue

    # Scroll the text vertically every 5 seconds
    scroll_vertically(message, delay=5)

    time.sleep(0.05)
