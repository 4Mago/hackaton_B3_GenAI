import pyaudio
import websocket
import threading
import json
import wave
import numpy as np
import requests
from retell import Retell
import os
from dotenv import load_dotenv
import inspect
import traceback

# Load environment variables from .env file
load_dotenv()

class VoiceInterface:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
        self.call = None
        self.audio_detected = False
        self.selected_device_index = 1  # Adjust as needed
        self.audio_level = 0
        self.audio_threshold = 100  # Adjust as needed

        # Load API key and Agent ID
        retell_api_key = os.getenv('RETELL_API_KEY')
        self.retell_agent_id = os.getenv('RETELL_AGENT_ID')

        if not retell_api_key or not self.retell_agent_id:
            raise ValueError("RETELL_API_KEY and RETELL_AGENT_ID must be set in the .env file")

        self.retell_client = Retell(api_key=retell_api_key)
        self.call = None
        self.audio_stream = None

    def start_recording(self):
        self.input_stream = self.p.open(format=pyaudio.paInt16,
                                        channels=1,
                                        rate=16000,
                                        input=True,
                                        input_device_index=self.selected_device_index,
                                        frames_per_buffer=1024,
                                        stream_callback=self.audio_callback)
        self.input_stream.start_stream()
        print(f"Recording started with device index {self.selected_device_index}")

    def start_playback(self):
        self.output_stream = self.p.open(format=pyaudio.paInt16,
                                         channels=1,
                                         rate=16000,
                                         output=True,
                                         frames_per_buffer=1024)

    def audio_callback(self, in_data, frame_count, time_info, status):
        try:
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            self.audio_level = np.abs(audio_data).mean()
            print(f"Audio level: {self.audio_level}")
            self.audio_detected = self.audio_level > self.audio_threshold

            if self.call:
                self.call.send_audio(in_data)
        except Exception as e:
            print(f"Error processing audio data: {e}")
        return (None, pyaudio.paContinue)

    def connect_websocket(self):
        try:
            # Create a new web call
            self.call = self.retell_client.call.create_web_call(
                agent_id=self.retell_agent_id,
                metadata={
                    "customer_id": "example_customer_123"  # Optional
                }
            )
            print(f"Web call created with ID: {self.call.call_id}")

            # Start the audio stream
            self.audio_stream = self.call.stream_audio()
            self.start_recording()
            self.start_playback()
            threading.Thread(target=self.handle_audio_stream).start()
        except Exception as e:
            print(f"Error creating web call: {e}")
            traceback.print_exc()

    def handle_audio_stream(self):
        try:
            for chunk in self.audio_stream:
                if chunk and self.output_stream:
                    self.output_stream.write(chunk)
        except Exception as e:
            print(f"Error in audio stream: {e}")
            traceback.print_exc()

    def stop(self):
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        if self.call:
            self.call.end_call()
            print(f"Call ended: {self.call.call_id}")
        self.p.terminate()

    def is_audio_detected(self):
        return self.audio_detected

    def get_audio_level(self):
        return self.audio_level

    def is_connected(self):
        return self.call and self.call.is_connected()

    def handle_webhook(self, webhook_data):
        event_type = webhook_data.get('event')
        call_data = webhook_data.get('call')

        if event_type == 'call_started':
            print(f"Call started: {call_data['call_id']}")
        elif event_type == 'call_ended':
            print(f"Call ended: {call_data['call_id']}")
            print(f"Disconnection reason: {call_data['disconnection_reason']}")
            # Process transcript or other call data here
        elif event_type == 'call_analyzed':
            print(f"Call analyzed: {call_data['call_id']}")
            # Process analysis results here

# GUI code
import tkinter as tk
from tkinter import messagebox

class VoiceInterfaceGUI:
    def __init__(self, voice_interface):
        self.voice_interface = voice_interface
        self.root = tk.Tk()
        self.root.title("Voice Interface")
        self.root.geometry("300x250")

        self.start_button = tk.Button(self.root, text="Start Call", command=self.start_call)
        self.start_button.pack(pady=20)

        self.stop_button = tk.Button(self.root, text="End Call", command=self.stop_call, state=tk.DISABLED)
        self.stop_button.pack(pady=20)

        self.audio_status = tk.Label(self.root, text="")
        self.audio_status.pack(pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_call(self):
        self.voice_interface.connect_websocket()
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        messagebox.showinfo("Call Started", "The call has been initiated.")
        self.update_audio_status()

    def stop_call(self):
        self.voice_interface.stop()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.audio_status.config(text="")
        messagebox.showinfo("Call Ended", "The call has been terminated.")

    def update_audio_status(self):
        if self.voice_interface.is_connected():
            audio_level = self.voice_interface.get_audio_level()
            status = f"Detected (Level: {audio_level:.2f})" if self.voice_interface.is_audio_detected() else f"Not detected (Level: {audio_level:.2f})"
            self.audio_status.config(text=f"Audio Status: {status}")
            self.root.after(100, self.update_audio_status)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.voice_interface.stop()
            self.root.destroy()

    def run(self):
        self.root.mainloop()

# Create and run the GUI
interface = VoiceInterface()
gui = VoiceInterfaceGUI(interface)
gui.run()

interface.stop()
