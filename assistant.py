import speech_recognition as sr
import librosa
import os
from assistanttools.actions import get_llm_response, message_history, preload_model
from assistanttools.generate_gguf import generate_gguf_stream
from assistanttools.transcribe_gguf import transcribe_gguf
from assistanttools.display import DisplayManager
import soundfile as sf
import re
import json
import uuid
import RPi.GPIO as GPIO
import time
import pyaudio
import wave
import threading

class ButtonListener:
    def __init__(self,
                 timeout,
                 sounds_path,
                 whisper_cpp_path,
                 whisper_model_path,
                 message_history,
                 store_conversations,
                 ollama_model):
        
        self.timeout = timeout
        self.sounds_path = sounds_path
        self.whisper_cpp_path = whisper_cpp_path
        self.whisper_model_path = whisper_model_path
        self.message_history = message_history
        self.store_conversations = store_conversations
        self.ollama_model = ollama_model
        self.conversation_id = str(uuid.uuid4())
        self.listening = False
        self.audio_thread = None
        
        self.yellowled = 11
        self.greenled = 13
        self.redled = 15

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(10,GPIO.RISING,callback=self.on_button_press, bouncetime=300)
        
        GPIO.setup(self.yellowled,GPIO.OUT)
        GPIO.setup(self.greenled,GPIO.OUT)
        GPIO.setup(self.redled,GPIO.OUT)
        
        GPIO.output(self.yellowled,GPIO.LOW)
        GPIO.output(self.greenled,GPIO.LOW)
        GPIO.output(self.redled,GPIO.LOW)
        
        
        
        
        self.display_manager = DisplayManager()
        # time.sleep(2)
        self.display_manager.update_status("Ready")
    

    def on_button_press(self, channel):
        
        if self.listening:
            self.listening = False
            GPIO.output(self.redled,GPIO.LOW)
        else:
            self.listening = True
            print("setting: listening")
            
            GPIO.output(self.redled,GPIO.HIGH)
            GPIO.output(self.greenled,GPIO.LOW)
            GPIO.output(self.yellowled,GPIO.LOW)
            self.display_manager.update_status("Listening...")
            
            if self.audio_thread is None or not self.audio_thread.is_alive():
                self.audio_thread = threading.Thread(target=self.record_audio)
                self.audio_thread.start()
            
   
    def record_audio(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        input=True,
                        frames_per_buffer=1024)
        print("Recording...")
        
        frames = []

        while self.listening:
            data = stream.read(1024)
            frames.append(data)

        print("Finished recording.")
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        wave_file_path = f"{self.sounds_path}command.wav"
        wf = wave.open(wave_file_path, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        print(f"Audio saved to {wave_file_path}")
        
        self.process_audio()
    
    def process_audio(self):
        try:
            
            speech, rate = librosa.load(
                        f"{self.sounds_path}command.wav", sr=16000)
            sf.write(f"{self.sounds_path}command.wav", speech, rate)

            self.display_manager.update_status("Transcribing...")        
            
            transcription = transcribe_gguf(whisper_cpp_path=self.whisper_cpp_path,
                                                    model_path=self.whisper_model_path,
                                                    file_path=f"{self.sounds_path}command.wav")
                    
            self.display_manager.add_human_input(transcription)
            print(transcription)
            self.display_manager.update_status("LLM Thinking...") 
            # update_main_screen_text(self.image, self.draw, "Human: "+transcription+"... [LLM thinking]")
            GPIO.output(self.redled,GPIO.LOW)
            GPIO.output(self.greenled,GPIO.LOW)
            GPIO.output(self.yellowled,GPIO.HIGH)
                    
            response, self.message_history = get_llm_response(
                        transcription, self.message_history, model_name=self.ollama_model)
                    
            print(response)
            
            GPIO.output(self.redled,GPIO.HIGH)
            GPIO.output(self.yellowled,GPIO.LOW)
            GPIO.output(self.greenled,GPIO.LOW)
            time.sleep(0.2)
            GPIO.output(self.redled,GPIO.HIGH)
            GPIO.output(self.yellowled,GPIO.HIGH)
            GPIO.output(self.greenled,GPIO.LOW)
            time.sleep(0.2)
            GPIO.output(self.redled,GPIO.HIGH)
            GPIO.output(self.yellowled,GPIO.HIGH)
            GPIO.output(self.greenled,GPIO.HIGH)
            time.sleep(0.2)
            
            GPIO.output(self.redled,GPIO.LOW)
            GPIO.output(self.yellowled,GPIO.LOW)
            GPIO.output(self.greenled,GPIO.HIGH)
            self.display_manager.add_response(response)
                    
            if self.store_conversations:
                with open(f"storage/{self.conversation_id}.json", "w") as f:
                    json.dump(self.message_history, f, indent=4)
        
        except sr.UnknownValueError:
            print("Could not understand audio")
         
    
    def wait_to_listen(self):
        print("waiting to listen!")
        self.display_manager.update_status("Ready")
        while True:
            time.sleep(0.1)  # Prevent CPU overload by adding a small sleep

            


if __name__ == "__main__":
    from config import SOUNDS_PATH, WAKE_WORD, WHISPER_CPP_PATH, \
        WHISPER_MODEL_PATH, LLAMA_CPP_PATH, MOONDREAM_MMPROJ_PATH, \
        MOONDREAM_MODEL_PATH, LOCAL_MODEL, STORE_CONVERSATIONS


    preload_model(LOCAL_MODEL)

    
    button_listener = ButtonListener(
        timeout = 2,
        sounds_path=SOUNDS_PATH,
        whisper_cpp_path=WHISPER_CPP_PATH,
        whisper_model_path=WHISPER_MODEL_PATH,
        store_conversations=STORE_CONVERSATIONS,
        message_history=message_history,
        ollama_model=LOCAL_MODEL
    )

    button_listener.wait_to_listen()
