import pyaudio
import websocket
import threading
import json
import wave
import numpy as np

class VoiceInterface:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
        self.ws = None
        self.audio_detected = False
        self.selected_device_index = 1  # Always use Index 1
        self.audio_level = 0
        self.audio_threshold = 100  # Adjust this value as needed

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

            if self.ws and self.ws.sock and self.ws.sock.connected:
                self.ws.send(in_data, opcode=websocket.ABNF.OPCODE_BINARY)
        except Exception as e:
            print(f"Error processing audio data: {e}")
        return (None, pyaudio.paContinue)

    def is_audio_detected(self):
        return self.audio_detected

    def get_audio_level(self):
        return self.audio_level

    def connect_websocket(self):
        self.ws = websocket.WebSocketApp("ws://localhost:8765",  # Changed this line
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws.on_open = self.on_open
        threading.Thread(target=self.ws.run_forever).start()

    def on_message(self, ws, message):
        try:
            # Check if the message is JSON (text) or binary (audio)
            json.loads(message)
            print(f"Received text message: {message}")
        except json.JSONDecodeError:
            # If it's not JSON, assume it's audio data
            if self.output_stream:
                self.output_stream.write(message)

    def on_error(self, ws, error):
        print(f"Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket connection closed")

    def on_open(self, ws):
        print("WebSocket connection opened")
        self.start_recording()
        self.start_playback()

    def stop(self):
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        if self.ws:
            self.ws.close()
        self.p.terminate()

    def is_connected(self):
        return self.ws and self.ws.sock and self.ws.sock.connected

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
