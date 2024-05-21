import board
import busio
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_sharpmemorydisplay
import time
from queue import Queue
import threading

class DisplayManager:
    def __init__(self):
        # init display
        spi = busio.SPI(board.SCK, MOSI=board.MOSI)
        scs = digitalio.DigitalInOut(board.D6)  
        self.display = adafruit_sharpmemorydisplay.SharpMemoryDisplay(spi, scs, 400, 240)

        # colors
        self.BLACK = 0
        self.WHITE = 255
        self.FONTSIZE = 20

        self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", self.FONTSIZE)

        # blank image
        self.image, self.draw = self.create_blank_image()
        
        # queue setup
        self.status_queue = Queue()
        self.conversation_queue = Queue()
        
        self.conversation_history = []
        
        self.display_thread = threading.Thread(target=self.run_display)
        self.display_thread.daemon = True
        self.display_thread.start()

    def create_blank_image(self):
        image = Image.new("1", (self.display.width, self.display.height))
        draw = ImageDraw.Draw(image)
        return image, draw

    def run_display(self):
        while True:
            self.update_display()
            time.sleep(0.1)  

    def update_display(self):

        
        
        if not self.status_queue.empty():
            status = self.status_queue.get_nowait()
            print(f"Displaying status: {status}")
            self.display_status(status)
        
       
        if not self.conversation_queue.empty():
            message = self.conversation_queue.get_nowait()
            self.conversation_history.append(message)
            print(f"Displaying conv: {message}")
            self.display_conversation()
        
        
        
        
        self.display.image(self.image)
        self.display.show()

    def display_status(self, status):
        bar_height = 30
        self.draw.rectangle([(0, 0), (self.display.width, bar_height)], fill=self.WHITE)
        bbox = self.font.getbbox(status)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (self.display.width - text_width) // 2
        text_y = (bar_height - text_height) // 2
        self.draw.text((text_x, text_y), status, font=self.font, fill=self.BLACK)

    def display_conversation(self):
        bar_height = 30
        text_x = 10
        text_y = bar_height + 10
        max_width = self.display.width - 20 
        
        for message in self.conversation_history:
            lines = self.wrap_text(message, max_width)
            for line in lines:
                if text_y + self.font.getbbox(line)[3] - self.font.getbbox(line)[1] >= self.display.height:
                    break
                self.draw.text((text_x, text_y), line, font=self.font, fill=self.WHITE)
                text_y += self.font.getbbox(line)[3] - self.font.getbbox(line)[1] + 2  # Add a small margin between lines

    def wrap_text(self, text, max_width):
        lines = []
        words = text.split()
        
        while words:
            line = ''
            while words and self.font.getbbox(line + words[0])[2] <= max_width:
                line += (words.pop(0) + ' ')
            lines.append(line.strip())
        
        return lines

    def update_status(self, status):
        self.status_queue.put(status)

    def add_human_input(self, text):
        self.conversation_queue.put(f"Human: {text}")

    def add_response(self, text):
        self.conversation_queue.put(f"AI: {text}")
        
        
if __name__ == "__main__":
    display_manager = DisplayManager()

    
    print("Updating status to Listening...")
    display_manager.update_status("Listening...")

    time.sleep(2) 
    print("Updating status to heard...")
    display_manager.update_status("heard")
    
    print("Adding conversation")
    display_manager.add_human_input("Hello, how are you?")
    time.sleep(2)
    display_manager.add_response("I am an AI. How can I assist you today?")
    time.sleep(2)
    display_manager.add_human_input("What's the weather like?")
    time.sleep(2)
    display_manager.add_response("The weather is sunny with a slight chance of rain.")

    
    while True:
        time.sleep(1)
