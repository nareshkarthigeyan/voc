import threading
import tkinter as tk
from fingerprint import FingerprintSensor
from sensors import VOCSensor
from train_model import train_all_with_logs
from ml_model import predict_user
from xml_handler import get_user_by_finger_id
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import xml.etree.ElementTree as ET

# TFT display
import board
import busio
import digitalio
import adafruit_rgb_display.st7735 as st7735

# ------------------- TFT SETUP -------------------
spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI)
tft_cs = digitalio.DigitalInOut(board.D27)
tft_dc = digitalio.DigitalInOut(board.D24)
tft_rst = digitalio.DigitalInOut(board.D25)
disp = st7735.ST7735R(spi, cs=tft_cs, dc=tft_dc, rst=tft_rst,
                       width=128, height=160)
disp.rotation = 270

def update_display(text):
    image = Image.new("RGB", (160, 128), "black")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    lines = text.split("\n")
    y = (160 - len(lines) * 22) // 2
    for line in lines:
        w, _ = draw.textbbox((0,0), line, font=font)[2:]
        x = (128 - w) // 2
        draw.text((x, y), line, font=font, fill="white")
        y += 25
    disp.image(image)

# ------------------- SENSOR INIT -------------------
try:
    fprint = FingerprintSensor()
    print("✅ Fingerprint sensor initialized")
except Exception as e:
    print(f"⚠️ Failed to initialize fingerprint sensor: {e}")
    fprint = None

voc = VOCSensor()

# ------------------- DASHBOARD -------------------
def launch_user_dashboard():
    update_display("Welcome\nUser Panel")
    root = tk.Tk()
    root.title("User Dashboard")
    root.geometry("800x800")
    root.configure(bg="#f0f0f0")

    matched_user = {}

    output = tk.Text(root, height=12, width=60, font=("Helvetica", 12))
    output.pack(pady=10)

    img_label = tk.Label(root)
    img_label.pack(pady=10)

    # Train classifiers at start
    train_all_with_logs()

    def log(msg):
        output.insert(tk.END, msg + "\n")
        output.see(tk.END)
        print(msg)

    def reset_ui():
        nonlocal matched_user
        matched_user = {}
        output.delete(1.0, tk.END)
        img_label.config(image="")
        img_label.image = None
        voc_dropdown.config(state=tk.NORMAL)
        voc_button.config(state=tk.NORMAL)
        update_display("Ready\nNext User")
        train_all_with_logs()

    # ------------------- Fingerprint -------------------
    def authenticate_fp():
        nonlocal matched_user
        reset_ui()
        if fprint is None:
            log("Fingerprint sensor not initialized.")
            update_display("Fingerprint\nError")
            return

        update_display("Place Finger")
        result = fprint.authenticate()

        if result.get("status") == "authenticated":
            user = get_user_by_finger_id(result["finger_id"])
            if user:
                matched_user = user
                log(f"Fingerprint result: {result}")
                log(f"Name: {user.get('name','Unknown')} (User ID: {user.get('user_id')})")
                voc_dropdown.config(state=tk.NORMAL)
                voc_button.config(state=tk.NORMAL)
                update_display("1st Auth\nSuccess")
            else:
                log("No user mapped to this fingerprint.")
                update_display("1st Auth\nFailed")
        else:
            log("Fingerprint not recognized.")
            update_display("1st Auth\nFailed")

    # ------------------- VOC -------------------
    def authenticate_voc():
        def task():
            try:
                voc_data = voc.read_sensors()
                print(voc_data)
            except Exception as e:
                log(f"VOC Sensor read error: {e}")
                update_display("VOC Sensor\nError")
                return

            selected_clf = classifier_var.get()
            try:
                predicted_id = predict_user(voc_data, classifier=selected_clf)
            except ValueError:
                log("VOC model not found or not trained.")
                update_display("VOC Model\nMissing")
                return

            log(f"VOC Prediction ID: {predicted_id} (Classifier: {selected_clf})")

            # XML matching
            try:
                tree = ET.parse("users.xml")
                root_xml = tree.getroot()
                matched = None
                for user in root_xml.findall("user"):
                    user_id_elem = user.find("user_id")
                    if user_id_elem is not None:
                        user_id = str(user_id_elem.text).strip().lower()
                        if str(predicted_id).strip().lower() == user_id:
                            matched = user
                            break

                if matched:
                    log(f"VOC Authentication Success! User: {matched.find('name').text}")
                    update_display(f"2nd Auth\nSuccess\n{matched.find('name').text}")
                else:
                    log(f"VOC Authentication Failed: No matching user for VOC ID {predicted_id}")
                    update_display("2nd Auth\nFailed")

            except Exception as e:
                log(f"Error reading users.xml: {e}")
                update_display("Error\nCheck Logs")

            root.after(5000, reset_ui)  # reset after 5 sec

        threading.Thread(target=task, daemon=True).start()

    # ------------------- Back Button -------------------
    def back_to_main():
        from main_gui import main_menu
        root.destroy()
        update_display("Welcome\nMain Menu")
        main_menu()

    # ------------------- UI Buttons -------------------
    tk.Button(root, text="Authenticate Fingerprint", command=authenticate_fp,
              font=("Helvetica", 14), bg="#38ada9", fg="white", padx=10, pady=5).pack(pady=10)

    tk.Label(root, text="Select VOC Classifier:", font=("Helvetica", 14)).pack(pady=5)
    classifiers = ["Random Forest", "SVM", "XGBoost", "Decision Tree", "Logistic Regression", "Nearest Neighbour"]
    classifier_var = tk.StringVar(value=classifiers[0])
    voc_dropdown = tk.OptionMenu(root, classifier_var, *classifiers)
    voc_dropdown.pack(pady=5)
    voc_dropdown.config(state=tk.NORMAL)

    voc_button = tk.Button(root, text="Authenticate VOC", command=authenticate_voc,
                           font=("Helvetica", 14), bg="#218c74", fg="white", padx=10, pady=5, state=tk.NORMAL)
    voc_button.pack(pady=10)

    tk.Button(root, text="Back to Main Menu", command=back_to_main,
              font=("Helvetica", 14), bg="#60a3bc", fg="white", padx=10, pady=5).pack(pady=20)

    root.mainloop()

# ------------------- RUN DASHBOARD -------------------
if __name__ == "__main__":
    launch_user_dashboard()
