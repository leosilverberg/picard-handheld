import board
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_sharpmemorydisplay
import time
from queue import Queue
import threading

import sys

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from displayhatmini import DisplayHATMini

import ST7789

class DisplayManager:
    def __init__(self):
     
        # spi = busio.SPI(board.SCK, MOSI=board.MOSI)
        # scs = digitalio.DigitalInOut(board.D6)  
        # self.display = ST7789.ST7789(
        # height=240,
        # width=320,
        # rotation=180,
        # port=0,
        # cs=1,
        # dc=9,
        # backlight=13,
        # spi_speed_hz=60 * 1000 * 1000,
        # offset_left=0,
        # offset_top=0
        # )
        # self.display = adafruit_sharpmemorydisplay.SharpMemoryDisplay(spi, scs, 400, 240)
        self.width = DisplayHATMini.WIDTH
        self.height = DisplayHATMini.HEIGHT
        self.image = Image.new("RGB", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        self.display = DisplayHATMini(self.image)
        self.display.set_led(0, 0, 0)
        

        # Colors
        self.BLACK = 0
        self.WHITE = (255,255,255)
        self.FONTSIZE = 18

        # Load font
        self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", self.FONTSIZE)
        self.smallfont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

       

        # Queues for updating status and conversation
        self.status_queue = Queue()
        self.conversation_queue = Queue()

        # Conversation history
        self.conversation_history = []

        # Scroll position
        self.scroll_position = 0

        # Start the display thread
        self.display_thread = threading.Thread(target=self.run_display)
        self.display_thread.daemon = True
        self.display_thread.start()

    def create_blank_image(self):
        image = Image.new("RGB", (self.width, self.height))
        draw = ImageDraw.Draw(image)
        return image, draw

    def run_display(self):
        while True:
            self.update_display()
            time.sleep(0.1)  # Update the display at regular intervals

    def update_display(self):
        status_updated = False
        conversation_updated = False

       

        # Check if there is a new conversation message
        if not self.conversation_queue.empty():
            message = self.conversation_queue.get_nowait()
            self.conversation_history.append(message)
            print(f"Displaying conversation: {message}")
            self.adjust_scroll_position()
            self.display_conversation()
            conversation_updated = True
            
         # Check if there is a new status
        if not self.status_queue.empty():
            status = self.status_queue.get_nowait()
            print(f"Displaying status: {status}")
            self.display_status(status)
            status_updated = True

        self.display.set_led(0, 0, 0)
        self.display.display()
        
        
    def display_corner(self, text, x, y):
        
        self.draw.text((x, y), text, font=self.smallfont, fill=self.BLACK)

    def display_status(self, status):
        bar_height = 30

        self.draw.rectangle([(0, 0), (self.width, bar_height)], fill=self.WHITE)
        bbox = self.font.getbbox(status)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (self.width - text_width) // 2
        text_y = (bar_height - text_height) // 2
 
        self.draw.text((text_x, text_y), status, font=self.font, fill=self.BLACK)
        self.display_corner("\u2023 picard", 7, 1)
        self.display_corner("local:mistral-7b-0.3", 7, 13)

    def display_conversation(self):
        bar_height = 30
        text_x = 10
        text_y = bar_height + 10 - self.scroll_position
        max_width = self.width - 20  # 10px padding on each side

        
        self.draw.rectangle([(0, bar_height), (self.width, self.height)], fill=self.BLACK)

        for message in self.conversation_history:
            lines = self.wrap_text(message, max_width)
            for line in lines:
                if text_y + self.font.getbbox(line)[3] - self.font.getbbox(line)[1] >= self.height:
                    break
                self.draw.text((text_x, text_y), line, font=self.font, fill=self.WHITE)
                text_y += self.font.getbbox(line)[3] - self.font.getbbox(line)[1] + 5  # Add a small margin between lines

    def wrap_text(self, text, max_width):
        lines = []
        words = text.split()

        while words:
            line = ''
            while words and self.font.getbbox(line + words[0])[2] <= max_width:
                line += (words.pop(0) + ' ')
            lines.append(line.strip())

        return lines

    def adjust_scroll_position(self):
        # Determine the total height of the conversation
        total_height = 0
        max_width = self.width - 20  # 10px padding on each side
        for message in self.conversation_history:
            lines = self.wrap_text(message, max_width)
            for line in lines:
                total_height += self.font.getbbox(line)[3] - self.font.getbbox(line)[1] + 5

        # Adjust scroll position if the total height exceeds the display height
        bar_height = 30
        available_height = self.height - bar_height - 10
        if total_height > available_height:
            self.scroll_position = total_height - available_height
        else:
            self.scroll_position = 0

    def update_status(self, status):
        self.status_queue.put(status)

    def add_human_input(self, text):
        self.conversation_queue.put(f"Human: {text}")

    def add_response(self, text):
        self.conversation_queue.put(f"AI: {text}")


if __name__ == "__main__":
    display_manager = DisplayManager()

    # Example status updates
    print("update status")
    display_manager.update_status("Listening...")
    time.sleep(2)
    display_manager.add_human_input("Hello, how are you?")
    time.sleep(2)
    display_manager.add_response("I am fine, thank you.")
    time.sleep(2)

    # Keep the main thread alive to allow the display thread to run
    while True:
        time.sleep(1)
