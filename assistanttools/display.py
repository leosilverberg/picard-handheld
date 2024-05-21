import board
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps
import adafruit_sharpmemorydisplay
import time



# Colors
BLACK = 0
WHITE = 255
FONTSIZE = 25

# Initialize display
spi = busio.SPI(board.SCK, MOSI=board.MOSI)
scs = digitalio.DigitalInOut(board.D6)  # inverted chip select
display = adafruit_sharpmemorydisplay.SharpMemoryDisplay(spi, scs, 400, 240)

# Load a TTF font
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", FONTSIZE)

def create_blank_image():
    image = Image.new("1", (display.width, display.height))
    draw = ImageDraw.Draw(image)
    return image, draw

            
# Function to display a boot image
def display_boot_image(image_path="assets/picard-facepalm.jpg"):
    print("display boot image")
    # Load and process the image
    image = Image.open(image_path)

    # Convert to grayscale
    image = image.convert("L")

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)

    # Convert to 1-bit image
    image = image.convert("1")

    # Resize image to fit display using LANCZOS for high-quality downsampling
    image = image.resize((display.width, display.height), Image.Resampling.LANCZOS)

    #write on the image
    draw = ImageDraw.Draw(image)
    text = "PICARD"
    bbox = font.getbbox(text)
    (font_width, font_height) = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = display.width // 2 - font_width // 2
    y = display.height // 2 - font_height // 2

    # Draw outlined text with adjustable outline thickness
    outline_color = BLACK
    main_color = WHITE
    outline_thickness = 5

    # Draw outline
    for dx in range(-outline_thickness, outline_thickness + 1):
        for dy in range(-outline_thickness, outline_thickness + 1):
            if dx != 0 or dy != 0:  # Skip the center position
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)

    # Draw main text
    draw.text((x, y), text, font=font, fill=main_color)

    # Display the image
    display.image(image)
    display.show()


# Function to create a blank main screen with a top bar
def create_main_screen():
    # Create a blank image for drawing
    image = Image.new("1", (display.width, display.height), color=WHITE)
    draw = ImageDraw.Draw(image)

    # Draw the top bar
    bar_height = 30
    draw.rectangle([(0, 0), (display.width, bar_height)], fill=BLACK)

    # Display the main screen
    display.image(image)
    display.show()
    return image, draw

def wrap_text(text, font, max_width):
    lines = []
    words = text.split()
    
    while words:
        line = ''
        while words and font.getbbox(line + words[0])[2] <= max_width:
            line += (words.pop(0) + ' ')
        lines.append(line.strip())
    
    return lines

def update_main_screen_text(image, draw, text):
    # Clear the main body area
    bar_height = 30
    draw.rectangle([(0, bar_height), (display.width, display.height)], fill=WHITE)

    # Wrap the text
    max_width = display.width - 20  
    lines = wrap_text(text, font, max_width)
    
    # Draw the wrapped text in the main body area
    text_x = 10
    text_y = bar_height + 10
    line_height = font.getbbox('A')[3] - font.getbbox('A')[1]  
    line_height = line_height + 5 #some padding
    
    for line in lines:
        draw.text((text_x, text_y), line, font=font, fill=BLACK)
        text_y += line_height

    # Display the updated image
    display.image(image)
    display.show()


# Example usage
if __name__ == "__main__":
    display_boot_image()
    time.sleep(5)  # Display boot image for 3 seconds

    image, draw = create_main_screen()
    update_main_screen_text(image, draw, "Welcome to the main screen!")
    time.sleep(3)  # Display initial text for 3 seconds

    # Dynamically update text
    for i in range(5):
        update_main_screen_text(image, draw, f"Dynamic update {i+1}")
        time.sleep(2)  # Pause for 2 seconds before the next update