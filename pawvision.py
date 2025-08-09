#!/usr/bin/env python3
import os
import random
import subprocess
import threading
import time
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, jsonify

# ---------------- DEV MODE CONFIG ----------------
DEV_MODE = True  # Set to False when running on Pi
# -------------------------------------------------

if not DEV_MODE:
    from gpiozero import Button, OutputDevice

# ---------------- CONFIG ----------------
BUTTON_PIN = 17
if DEV_MODE:
    VIDEO_DIRS = ["./videos"]
    SETTINGS_FILE = "./pawvision_settings.json"
    PORT = 5001  # Use different port for development to avoid AirPlay conflict
else:
    VIDEO_DIRS = ["/home/pi/videos", "/media/usb"]
    SETTINGS_FILE = "/home/pi/pawvision_settings.json"
    PORT = 5000  # Standard port for production
# -----------------------------------------

# Load or create settings
DEFAULT_SETTINGS = {
    "timeout_minutes": 30,
    "volume": 50,
    "night_mode_start": 22,
    "night_mode_end": 6,
    "button_enabled": True,
    "button_disable_start": None,
    "button_disable_end": None,
    "second_press_stops": True,
    "monitor_gpio": None,
    "play_schedule": []
}

if not os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(DEFAULT_SETTINGS, f)

with open(SETTINGS_FILE, "r") as f:
    settings = json.load(f)

app = Flask(__name__)
current_process = None
monitor_relay = None

if not DEV_MODE and settings.get("monitor_gpio") is not None:
    monitor_relay = OutputDevice(settings["monitor_gpio"])

def save_settings():
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)

def is_night_mode():
    hour = datetime.now().hour
    return settings["night_mode_start"] <= hour or hour < settings["night_mode_end"]

def is_button_allowed():
    if not settings["button_enabled"]:
        return False
    start = settings["button_disable_start"]
    end = settings["button_disable_end"]
    if start is None or end is None:
        return True
    hour = datetime.now().hour
    if start < end:
        return start <= hour < end
    else:
        return hour >= start or hour < end

def get_all_videos():
    videos = []
    for vdir in VIDEO_DIRS:
        if os.path.exists(vdir):
            for f in os.listdir(vdir):
                if f.lower().endswith((".mp4", ".mkv", ".avi", ".mov")):
                    videos.append(os.path.join(vdir, f))
    return videos

def get_video_duration(path):
    try:
        result = subprocess.run(
            ["mediainfo", "--Inform=Video;%Duration%", path],
            capture_output=True, text=True
        )
        ms = int(result.stdout.strip())
        return ms / 1000
    except:
        return None

def turn_monitor_on():
    if DEV_MODE:
        print("DEV_MODE: Would turn monitor on")
        return
    if monitor_relay:
        monitor_relay.on()
    else:
        subprocess.run("vcgencmd display_power 1", shell=True)

def turn_monitor_off():
    if DEV_MODE:
        print("DEV_MODE: Would turn monitor off")
        return
    if monitor_relay:
        monitor_relay.off()
    else:
        subprocess.run("vcgencmd display_power 0", shell=True)

def play_random_video():
    global current_process
    videos = get_all_videos()
    if not videos:
        print("No videos found.")
        return
    video = random.choice(videos)
    duration = get_video_duration(video)
    if not duration:
        print("Could not get duration.")
        return
    timeout_sec = settings["timeout_minutes"] * 60
    if duration <= timeout_sec:
        start_sec = 0
    else:
        start_sec = random.randint(0, int(duration - timeout_sec))
    volume_arg = "--volume=0" if is_night_mode() else f"--volume={settings['volume']}"
    turn_monitor_on()
    current_process = subprocess.Popen(
        ["mpv", f"--start={start_sec}", volume_arg, video]
    )
    threading.Thread(target=stop_after_timeout, args=(timeout_sec,)).start()

def stop_after_timeout(timeout_sec):
    global current_process
    time.sleep(timeout_sec)
    if current_process and current_process.poll() is None:
        current_process.terminate()
        turn_monitor_off()

def button_pressed():
    global current_process
    if not is_button_allowed():
        print("Button disabled by schedule/settings.")
        return
    if current_process and current_process.poll() is None:
        if settings["second_press_stops"]:
            current_process.terminate()
            turn_monitor_off()
    else:
        play_random_video()

# ---------------- SCHEDULER ----------------
def scheduler_loop():
    last_checked = None
    while True:
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        if current_time_str != last_checked:
            last_checked = current_time_str
            if current_time_str in settings["play_schedule"]:
                print(f"Scheduled play at {current_time_str}")
                play_random_video()
        time.sleep(10)

# ---------------- WEB INTERFACE ----------------
@app.route("/")
def index():
    videos = get_all_videos()
    return render_template("index.html", videos=videos, settings=settings)

@app.route("/upload", methods=["POST"])
def upload_video():
    file = request.files["file"]
    if file:
        file.save(os.path.join(VIDEO_DIRS[0], file.filename))
    return redirect("/")

@app.route("/delete", methods=["POST"])
def delete_video():
    path = request.form["path"]
    if os.path.exists(path):
        os.remove(path)
    return redirect("/")

@app.route("/settings", methods=["POST"])
def update_settings():
    settings["timeout_minutes"] = int(request.form["timeout"])
    settings["volume"] = int(request.form["volume"])
    settings["night_mode_start"] = int(request.form["night_start"])
    settings["night_mode_end"] = int(request.form["night_end"])
    settings["button_enabled"] = "button_enabled" in request.form
    settings["second_press_stops"] = "second_press_stops" in request.form
    settings["button_disable_start"] = (
        int(request.form["button_disable_start"]) if request.form["button_disable_start"] else None
    )
    settings["button_disable_end"] = (
        int(request.form["button_disable_end"]) if request.form["button_disable_end"] else None
    )
    schedule_str = request.form["play_schedule"].strip()
    settings["play_schedule"] = [t.strip() for t in schedule_str.split(",") if t.strip()]
    save_settings()
    return redirect("/")

# ---------------- API FOR HOME ASSISTANT ----------------
@app.route("/api/play", methods=["POST"])
def api_play():
    play_random_video()
    return jsonify({"status": "playing"})

@app.route("/api/stop", methods=["POST"])
def api_stop():
    global current_process
    if current_process and current_process.poll() is None:
        current_process.terminate()
        turn_monitor_off()
    return jsonify({"status": "stopped"})

# ---------------- MAIN ----------------
if __name__ == "__main__":
    if not DEV_MODE:
        button = Button(BUTTON_PIN, pull_up=True)
        button.when_pressed = button_pressed
    else:
        print("DEV_MODE: GPIO button disabled")
    
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=PORT)).start()
    threading.Thread(target=scheduler_loop).start()
    print(f"PawVision ready. Web UI on http://localhost:{PORT}")
    while True:
        time.sleep(1)