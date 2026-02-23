import tkinter as tk
from tkinter import ttk
from admin_dashboard import admin_login_screen
from user_dashboard import launch_user_dashboard
from PIL import Image, ImageTk

import board
import busio
import digitalio
import adafruit_rgb_display.st7735 as st7735
from PIL import ImageDraw, ImageFont

spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI)
tft_cs = digitalio.DigitalInOut(board.D27)
tft_dc = digitalio.DigitalInOut(board.D24)
tft_rst = digitalio.DigitalInOut(board.D25)
disp = st7735.ST7735R(
    spi, cs=tft_cs, dc=tft_dc, rst=tft_rst,
    width=128, height=160
)
disp.rotation = 270


def update_display(text):
    image = Image.new("RGB", (160, 128), "black")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16
    )
    lines = text.split("\n")
    y = (160 - len(lines) * 22) // 2
    for line in lines:
        w, _ = draw.textbbox((0, 0), line, font=font)[2:]
        x = (128 - w) // 2
        draw.text((x, y), line, font=font, fill="white")
        y += 25
    disp.image(image)

def main_menu():
    update_display("Multi Modal \n   Secure Biometric \n Auth System")
    root = tk.Tk()
    root.title("Authentication System")
    root.geometry("800x800")
    root.configure(bg="#f4f6f8")  # Light professional background

    # --- Header Frame ---
    header_frame = tk.Frame(root, bg="#2c3e50", height=120)
    header_frame.pack(fill="x")

    tk.Label(
        header_frame, 
        text="Multi Modal Secure Biometric\nAuthentication System", 
        font=("Helvetica", 28, "bold"), 
        bg="#2c3e50", 
        fg="white"
    ).pack(pady=35)

    # --- Content Frame ---
    content_frame = tk.Frame(root, bg="#f4f6f8")
    content_frame.pack(expand=True, fill="both")

    # Center Frame for buttons with shadow effect
    card_frame = tk.Frame(content_frame, bg="white", bd=2, relief="groove")
    card_frame.place(relx=0.5, rely=0.5, anchor="center", width=500, height=300)

    tk.Label(
        card_frame, 
        text="Choose an Option", 
        font=("Helvetica", 20, "bold"), 
        bg="white", 
        fg="#34495e"
    ).pack(pady=30)

    # --- Style Buttons ---
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TButton', font=('Helvetica', 16, 'bold'), foreground='white')
    
    # Admin button
    admin_btn = tk.Button(
        card_frame, text="Admin Login", bg="#3498db", fg="white", activebackground="#2980b9",
        font=("Helvetica", 16, "bold"), relief="flat", command=lambda: [root.destroy(), admin_login_screen()]
    )
    admin_btn.pack(pady=20, ipadx=20, ipady=10)

    # User button
    user_btn = tk.Button(
        card_frame, text="User Dashboard", bg="#1abc9c", fg="white", activebackground="#16a085",
        font=("Helvetica", 16, "bold"), relief="flat", command=lambda: [root.destroy(), launch_user_dashboard()]
    )
    user_btn.pack(pady=10, ipadx=20, ipady=10)

    # Footer Frame
    footer_frame = tk.Frame(root, bg="#ecf0f1", height=40)
    footer_frame.pack(fill="x", side="bottom")
    tk.Label(footer_frame, text="© 2025", font=("Helvetica", 10), bg="#ecf0f1", fg="#7f8c8d").pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main_menu()
