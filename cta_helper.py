import time
import adafruit_requests as requests
import secrets
import gc

# --- Configuration for API --- #
BASE_API_URL = "https://lapi.transitchicago.com/api/1.0/ttarrivals.aspx?"
API_KEY = secrets.CTA_API_KEY
LIMIT = 6
MAP_ID = 40710
ROUTE = "brn"
DESTINATION_ABBREVIATIONS = {
    "Kimball": "KMBL",
    "Loop": "LOOP",
    # Add other destinations here as needed
}


def log_memory_usage():
    """Logs the memory usage (used, free, total)."""
    print(f"Memory used: {gc.mem_alloc()} bytes")
    print(f"Memory free: {gc.mem_free()} bytes")
    print(f"Total memory: {gc.mem_alloc() + gc.mem_free()} bytes")

def force_garbage_collection():
    gc.collect()
    print(f"Memory after GC: Used: {gc.mem_alloc()} bytes, Free: {gc.mem_free()} bytes")

def fetch_data_from_api(matrixportal):
    """Fetch data from the CTA API."""
    log_memory_usage()  # Log memory usage before fetching data
    try:
        url = f"{BASE_API_URL}mapid={MAP_ID}&max={LIMIT}&key={API_KEY}&rt={ROUTE}"
        print(f"Fetching data from {url}")
        response = matrixportal.network.requests.get(url)

        if response.status_code == 200:
            log_memory_usage()  # Log memory usage after fetching data
            return response.text  # Return the XML data if successful
        else:
            print(f"Error fetching data: HTTP {response.status_code} - {response.reason}")
            return None

    except Exception as e:
        print(f"An error occurred while fetching data: {e}")
        return None

def parse_cta_xml(xml_data):
    """Parse the CTA XML data and extract relevant information."""
    arrivals = []
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

    # Clean up XML data after parsing
    del xml_data
    gc.collect()

    return arrivals


def process_arrival_times(arrivals):
    """Process the arrival times and prepare them for display."""
    loop_arr = []
    kmbl_arr = []

    for train in arrivals[:6]:  # Limit to the next 6 trains
        dest = DESTINATION_ABBREVIATIONS.get(train['destNm'], train['destNm'])
        arr_time_str = train['arrT']
        arr_date_str, arr_time_str = arr_time_str.split(' ')
        year = int(arr_date_str[0:4])
        month = int(arr_date_str[4:6])
        day = int(arr_date_str[6:8])
        hour, minute, second = map(int, arr_time_str.split(':'))

        arr_time = time.mktime((year, month, day, hour, minute, second, 0, 0, 0))
        current_time = time.time()
        time_diff = arr_time - current_time
        minutes_until_arrival = int(time_diff / 60)

        if minutes_until_arrival < 0:
            minutes_until_arrival += 60  # Adjust for negative times

        # Format destination and arrival time
        minutes_until_arrival_str = "DUE" if minutes_until_arrival == 0 else str(minutes_until_arrival)

        if dest == "LOOP":
            loop_arr.append(minutes_until_arrival_str)
        if dest == "KMBL":
            kmbl_arr.append(minutes_until_arrival_str)

    # Clean trailing commas
    loop_arr = ','.join(loop_arr)
    kmbl_arr = ','.join(kmbl_arr)

    return loop_arr, kmbl_arr


def build_message(loop_arr, kmbl_arr):
    """Build the message to display on the MatrixPortal."""
    kmbl_chars = len(kmbl_arr)
    loop_chars = len(loop_arr)

    message = f"\nKMBL{'.' * (12 - kmbl_chars)}{kmbl_arr}\nLOOP{'.' * (12 - loop_chars)}{loop_arr}"
    return message


def fetch_cta_data(matrixportal):
    """Fetch and parse CTA train data."""
    log_memory_usage()  # Log memory before processing
    xml_data = fetch_data_from_api(matrixportal)
    
    if xml_data:
        arrivals = parse_cta_xml(xml_data)
        loop_arr, kmbl_arr = process_arrival_times(arrivals)
        message = build_message(loop_arr, kmbl_arr)

        log_memory_usage()  # Log memory after processing
        print(message)  # For debugging

        # Clean up memory
        del xml_data  # Dereference large XML data
        del arrivals  # Dereference arrivals data
        gc.collect()   # Force garbage collection

        return message
    else:
        log_memory_usage()  # Log memory if there's an error
        force_garbage_collection()  # Force garbage collection if there's an error
        return "Error fetching data"