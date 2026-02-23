import tkinter as tk
from tkinter import ttk, messagebox
from xml_handler import save_user_to_xml, load_users_from_xml, delete_user_by_name
from fingerprint import FingerprintSensor
from sensors import VOCSensor
from logger import log_voc
from train_model import train, train_all_with_logs
from PIL import Image, ImageTk
import os
import uuid

# === TFT Display Setup ===
import board
import busio
import digitalio
import adafruit_rgb_display.st7735 as st7735
from PIL import ImageDraw, ImageFont

spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI)
tft_cs = digitalio.DigitalInOut(board.D27)
tft_dc = digitalio.DigitalInOut(board.D24)
tft_rst = digitalio.DigitalInOut(board.D25)
disp = st7735.ST7735R(spi, cs=tft_cs, dc=tft_dc, rst=tft_rst, width=128, height=160)
disp.rotation = 270

def update_display(text):
    image = Image.new("RGB", (160, 128), "black")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    lines = text.split("\n")
    y = (160 - len(lines) * 22) // 3
    for line in lines:
        w, _ = draw.textbbox((0, 0), line, font=font)[2:]
        x = (128 - w) // 3
        draw.text((x, y), line, font=font, fill="white")
        y += 16
    disp.image(image)

fprint = FingerprintSensor()
voc = VOCSensor()

def admin_login_screen():
    update_display("Welcome\nAdmin Login")
    root = tk.Tk()
    root.title("Admin Login")
    root.geometry("600x400")

    tk.Label(root, text="Admin Login", font=("Helvetica", 20, "bold")).pack(pady=20)
    tk.Label(root, text="Username:").pack()
    username_entry = tk.Entry(root)
    username_entry.pack()
    tk.Label(root, text="Password:").pack()
    password_entry = tk.Entry(root, show="*")
    password_entry.pack()

    def attempt_login():
        if username_entry.get() == "admin" and password_entry.get() == "admin":
            update_display("Login\nSuccessful")
            root.destroy()
            launch_admin_dashboard()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")
            update_display("Login\nFailed")

    tk.Button(root, text="Login", command=attempt_login, bg="#38ada9", fg="white", padx=10, pady=5).pack(pady=20)
    root.mainloop()

def launch_admin_dashboard():
    update_display("Admin\nDashboard")
    window = tk.Tk()
    window.title("Admin Dashboard")
    window.geometry("800x800")

    def show_main_menu():
        for widget in window.winfo_children():
            widget.destroy()
        update_display("Admin\nDashboard")

        tk.Label(window, text="Admin Dashboard", font=("Helvetica", 24, "bold")).pack(pady=20)
        tk.Button(window, text="New User Registration", width=30, font=("Helvetica", 16),
                  command=new_user_registration, bg="#04D682", fg="black").pack(pady=20)
        tk.Button(window, text="Existing User", width=30, font=("Helvetica", 16),
                  command=existing_user_page, bg="#D6CF04", fg="black").pack(pady=20)
        tk.Button(window, text="Train Data", width=30, font=("Helvetica", 16),
                  command=train_data_page, bg="#03738A", fg="black").pack(pady=20)
        tk.Button(window, text="Logout", width=30, font=("Helvetica", 16),
                  command=restart_to_main_menu).pack(pady=20)

    def restart_to_main_menu():
        from main_gui import main_menu
        for widget in window.winfo_children():
            widget.destroy()
        update_display("Welcome\nMain Menu")
        window.destroy()
        main_menu()

    def new_user_registration():
        for widget in window.winfo_children():
            widget.destroy()
        update_display("New User\nRegistration")

        name_var = tk.StringVar()
        age_var = tk.StringVar()
        dept_var = tk.StringVar()
        desig_var = tk.StringVar()
        emp_id_var = tk.StringVar()
        images = []
        user_id = str(uuid.uuid4())[:8]
        finger_id = None

        tk.Label(window, text="New User Registration", font=("Helvetica", 22, "bold")).pack(pady=20)
        form_frame = tk.Frame(window)
        form_frame.pack()

        fields = [("Name", name_var), ("Age", age_var), ("Department", dept_var), ("Designation", desig_var), ("Employee ID", emp_id_var)]
        for label_text, var in fields:
            row = tk.Frame(form_frame)
            row.pack(fill="x", pady=5)
            tk.Label(row, text=label_text, width=15, anchor='w').pack(side="left")
            tk.Entry(row, textvariable=var, width=30).pack(side="left")

        def validate_and_next():
            for label, var in fields:
                if var.get().strip() == "":
                    messagebox.showwarning("Validation Error", f"{label} field is required.")
                    update_display("Fill all\nFields")
                    return
            form_frame.destroy()
            show_fingerprint_registration()

        tk.Button(form_frame, text="Next ➡️", command=validate_and_next, bg="#38ada9", fg="white", font=("Helvetica", 14)).pack(pady=20)
        tk.Button(form_frame, text="Back", command=show_main_menu, bg="#60a3bc", fg="white", font=("Helvetica", 14)).pack(pady=10)

        def show_fingerprint_registration():
            update_display("Fingerprint\nRegistration")
            fp_frame = tk.Frame(window)
            fp_frame.pack(pady=10)
            tk.Label(fp_frame, text="Fingerprint Registration", font=("Helvetica", 20, "bold")).pack(pady=10)

            preview_label = tk.Label(fp_frame)
            preview_label.pack(pady=10)

            def register_fp():
                update_display("Place Finger")
                result = fprint.enroll(name_var.get(), emp_id_var.get())

                if result["status"] == "success":
                    nonlocal finger_id
                    finger_id = result["position"]
                    image_path = result["image_path"]
                    images.append(image_path)

                    if image_path and os.path.exists(image_path) and os.path.getsize(image_path) > 0:
                        try:
                            img = Image.open(image_path).resize((100, 100))
                            img_disp = ImageTk.PhotoImage(img)
                            preview_label.config(image=img_disp)
                            preview_label.image = img_disp
                        except Exception as e:
                            messagebox.showerror("Image Error", f"Could not load image: {e}")
                    else:
                        messagebox.showwarning("Image", "Fingerprint image not found or broken.")
                    update_display("Finger\nCaptured")
                elif result["status"] == "exists":
                    messagebox.showinfo("Fingerprint", f"Fingerprint already exists at position {result['position']}.")
                    update_display("Finger\nExists")
                elif result["status"] == "timeout":
                    messagebox.showwarning("Timeout", "Finger not detected in time.")
                    update_display("Timeout")
                else:
                    messagebox.showerror("Error", "Fingerprint enrollment failed.")
                    update_display("Failed")

            tk.Button(fp_frame, text="Register Fingerprint", command=register_fp, bg="#60a3bc", fg="white", font=("Helvetica", 14)).pack(pady=20)
            tk.Button(fp_frame, text="Next ➡️", command=lambda: [fp_frame.destroy(), show_voc_registration()], bg="#38ada9", fg="white", font=("Helvetica", 14)).pack(pady=20)
            tk.Button(fp_frame, text="Back", command=new_user_registration, bg="#60a3bc", fg="white", font=("Helvetica", 14)).pack(pady=10)

        def show_voc_registration():
            update_display("VOC\nRegistration")
            voc_frame = tk.Frame(window)
            voc_frame.pack(pady=10)
            tk.Label(voc_frame, text="VOC Registration", font=("Helvetica", 20, "bold")).pack(pady=10)

            def save_all():
                data = {
                    "user_id": user_id,
                    "name": name_var.get(),
                    "age": age_var.get(),
                    "department": dept_var.get(),
                    "designation": desig_var.get(),
                    "employee_id": emp_id_var.get(),
                    "finger_id": str(finger_id) if finger_id else "0",
                    "fingerprints": images
                }
                voc_data = voc.read_sensors()
                log_voc(data["name"], data["user_id"], voc_data)
                save_user_to_xml(data)
                update_display("User\nRegistered")
                messagebox.showinfo("Success", "User registered and model updated.")
                voc_frame.destroy()
                show_main_menu()

            tk.Button(voc_frame, text="Register VOC & Save ✅", command=save_all, bg="#f6b93b", fg="white", font=("Helvetica", 16)).pack(pady=20)

    def train_data_page():
        for widget in window.winfo_children():
            widget.destroy()
        update_display("Train\nModel")

        tk.Label(window, text="Train Model", font=("Helvetica", 22, "bold")).pack(pady=20)

        classifiers = [
            "SVM",
            "XGBoost",
            "Random Forest",
            "Decision Tree",
            "Logistic Regression",
            "Nearest Neighbour"
        ]

        selected_classifier = tk.StringVar()
        dropdown = ttk.Combobox(window, textvariable=selected_classifier, values=classifiers, state="readonly", width=30)
        dropdown.pack(pady=20)

        def submit_training():
            clf = selected_classifier.get()
            if not clf:
                messagebox.showwarning("Warning", "Please select a classifier first.")
                return
            try:
                train(clf)  # pass selected classifier
                update_display(f"Training\n{clf}")
                messagebox.showinfo("Training Complete", f"✅ Model trained successfully using {clf}")
                show_main_menu()
            except Exception as e:
                messagebox.showerror("Error", f"Training failed: {e}")
                update_display("Training\nFailed")

        tk.Button(window, text="Submit", command=submit_training, bg="#38ada9", fg="white", font=("Helvetica", 14)).pack(pady=10)
        tk.Button(window, text="Back", command=show_main_menu, bg="#60a3bc", fg="white", font=("Helvetica", 14)).pack(pady=10)

    def existing_user_page():
        for widget in window.winfo_children():
            widget.destroy()
        update_display("Existing\nUser")

        tk.Label(window, text="Existing User", font=("Helvetica", 22, "bold")).pack(pady=20)

        users = load_users_from_xml()
        names = [u.get("name", "") for u in users if u.get("name")]

        selected = tk.StringVar()
        dropdown = ttk.Combobox(window, textvariable=selected, values=names, state="readonly")
        dropdown.pack(pady=10)

        info_label = tk.Label(window, text="", justify="left", font=("Courier", 12))
        info_label.pack(pady=10)

        def load_user():
            name = selected.get()
            user = next((u for u in users if u.get("name") == name), None)
            if user:
                info = (
                    f"Name: {user['name']}\n"
                    f"Age: {user['age']}\n"
                    f"Department: {user['department']}\n"
                    f"Designation: {user['designation']}\n"
                    f"Employee ID: {user['employee_id']}\n"
                    f"User ID: {user['user_id']}\n"
                    f"Finger ID: {user['finger_id']}"
                )
                info_label.config(text=info)
                update_display("User\nLoaded")
            else:
                info_label.config(text="User not found.")
                update_display("User\nNot Found")

        def add_fingerprint():
            name = selected.get()
            if not name:
                messagebox.showerror("Error", "Please select a user first.")
                return

            user = next((u for u in users if u.get("name") == name), None)
            if not user:
                messagebox.showerror("Error", "Selected user not found.")
                return

            update_display("Place Finger")
            result = fprint.enroll(user["name"], user["employee_id"])

            if result["status"] == "success":
                finger_id = result["position"]
                user["finger_id"] = str(finger_id)

                #image_path = result["image_path"]
                if "fingerprints" not in user:
                    user["fingerprints"] = []
                user["fingerprints"].append(image_path)

                save_user_to_xml(user)

                info_label.config(text=f"Fingerprint added successfully.\nFinger ID: {finger_id}")
                update_display("Fingerprint\nAdded")
                messagebox.showinfo("Success", f"✅ Fingerprint added for {name}.")
            elif result["status"] == "exists":
                messagebox.showinfo("Fingerprint", f"Fingerprint already exists at position {result['position']}.")
                update_display("Finger\nExists")
            elif result["status"] == "timeout":
                messagebox.showwarning("Timeout", "Finger not detected in time.")
                update_display("Timeout")
            else:
                messagebox.showerror("Error", "Fingerprint enrollment failed.")
                update_display("Failed")

        def add_voc_data():
            name = selected.get()
            if not name:
                messagebox.showerror("Error", "Please select a user first.")
                return

            user = next((u for u in users if u.get("name") == name), None)
            if not user:
                messagebox.showerror("Error", "Selected user not found.")
                return

            update_display("Reading\nVOC Data")
            voc_data = voc.read_sensors()
            log_voc(user["name"], user["user_id"], voc_data)

            voc_lines = []
            for k, v in voc_data.items():
                try:
                    voc_lines.append(f"{k.upper()}: {float(v):.2f}")
                except (ValueError, TypeError):
                    voc_lines.append(f"{k.upper()}: {v}")

            info_text = (
                f"Name: {user['name']}\n"
                f"Age: {user['age']}\n"
                f"Department: {user['department']}\n"
                f"Designation: {user['designation']}\n"
                f"Employee ID: {user['employee_id']}\n"
                f"User ID: {user['user_id']}\n"
                f"Finger ID: {user['finger_id']}\n"
                + "\n".join(voc_lines)
            )

            info_label.config(text=info_text)
            update_display("VOC Data\nLogged")
            messagebox.showinfo("Success", f"✅ VOC data saved for user {name}.")

        def edit_user():
            name = selected.get()
            if not name:
                messagebox.showerror("Error", "Please select a user first.")
                return

            user = next((u for u in users if u.get("name") == name), None)
            if not user:
                messagebox.showerror("Error", "Selected user not found.")
                return

            for widget in window.winfo_children():
                widget.destroy()
            update_display("Edit\nUser")

            tk.Label(window, text="Edit User", font=("Helvetica", 22, "bold")).pack(pady=20)

            vars = {}
            for field in ["name", "age", "department", "designation", "employee_id"]:
                vars[field] = tk.StringVar(value=user[field])

            for field in vars:
                row = tk.Frame(window)
                row.pack(pady=5)
                tk.Label(row, text=field.capitalize(), width=15, anchor='w').pack(side="left")
                tk.Entry(row, textvariable=vars[field], width=30).pack(side="left")

            def save_changes():
                for key in vars:
                    user[key] = vars[key].get()
                save_user_to_xml(user)
                update_display("User\nUpdated")
                messagebox.showinfo("Success", "✅ User information updated and model retrained.")
                show_main_menu()

            tk.Button(window, text="Save Changes", command=save_changes, bg="#38ada9", fg="white", font=("Helvetica", 14)).pack(pady=10)
            tk.Button(window, text="Back", command=existing_user_page, bg="#60a3bc", fg="white", font=("Helvetica", 14)).pack(pady=10)

        def delete_user():
            name = selected.get()
            if not name:
                messagebox.showerror("Error", "Please select a user first.")
                return

            confirm = messagebox.askyesno("Delete", f"Are you sure you want to delete {name}?")
            if not confirm:
                return

            user = next((u for u in users if u.get("name") == name), None)
            if user:
                finger_id = int(user.get("finger_id", "0"))
                if finger_id:
                    try:
                        if fprint.f and fprint.f.deleteTemplate(finger_id):
                            print(f"✅ Fingerprint template {finger_id} deleted.")
                        else:
                            print(f"Could not delete fingerprint template {finger_id}.")
                    except Exception as e:
                        print(f"Error deleting fingerprint template: {e}")

                delete_user_by_name(name)
                update_display("User\nDeleted")
                messagebox.showinfo("Deleted", f"✅ User {name} deleted successfully.")
                show_main_menu()
            else:
                messagebox.showerror("Error", "User not found.")

        tk.Button(window, text="Load Info", command=load_user, bg="#38ada9", fg="white", font=("Helvetica", 14)).pack(pady=5)
        tk.Button(window, text="Add Fingerprint", command=add_fingerprint, bg="#60a3bc", fg="white", font=("Helvetica", 14)).pack(pady=5)
        tk.Button(window, text="Add VOC", command=add_voc_data, bg="#f6b93b", fg="white", font=("Helvetica", 14)).pack(pady=5)
        tk.Button(window, text="Edit User", command=edit_user, bg="#04D682", fg="white", font=("Helvetica", 14)).pack(pady=5)
        tk.Button(window, text="Delete User", command=delete_user, bg="#D64541", fg="white", font=("Helvetica", 14)).pack(pady=5)
        tk.Button(window, text="Back", command=show_main_menu, bg="#60a3bc", fg="white", font=("Helvetica", 14)).pack(pady=10)

    show_main_menu()
    window.mainloop()

if __name__ == "__main__":
    admin_login_screen()
