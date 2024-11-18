import board
import terminalio
from adafruit_matrixportal.matrixportal import MatrixPortal

# --- Display Setup --- #
FONT = "/small_font.bdf"
hello_world_y_position = 0  # Position for "Hello World"
cta_data_y_position = 22    # Position for CTA data

def setup_matrix():
    """Sets up the MatrixPortal and adds text fields for display."""
    matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=True)

    # Add "Hello World" text at the top in white
    matrixportal.add_text(
        text_font=FONT,
        text_position=(1, hello_world_y_position),
        text_color=0xFFFFFF,  # White color
        scrolling=False,
    )

    # Add CTA data text in brown below the "Hello World" message
    matrixportal.add_text(
        text_font=FONT,
        text_position=(1, cta_data_y_position),
        text_color=0x8B4513,  # Brown color
        scrolling=False,
    )

    return matrixportal

def update_matrix(matrixportal, message):
    """Updates the second text field (CTA data)."""
    matrixportal.set_text(message, index=1)  # Use index 1 for CTA data (second text object)
    matrixportal.set_text("\n11/10/24", index=0)  # Use index 0 for "Hello World"
