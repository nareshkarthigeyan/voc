import customtkinter as ctk
import threading
import time
from tkinter import messagebox

from sensors.sensor_reader import VOCSensor
from hand_controller import HandController
from Features.feature_extractor import extract_features
from logger import log_voc
from Database.feature_dao import store_features
from verification_controller import verify_user


# ---------------- CONFIG ----------------
SAMPLE_COUNT = 10
ROUNDS = 6
MAX_IO_ERRORS = 3
MAX_INVALID_SAMPLES = 4

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MainGUI(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("VOC Biometric System")
        self.geometry("1200x900")

        self.sensor = VOCSensor()
        self.hand = HandController()

        self.frame = ctk.CTkFrame(self)
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.show_main_menu()

    # ---------------- MAIN MENU ----------------
    def show_main_menu(self):
        self.clear()

        ctk.CTkLabel(
            self.frame,
            text="VOC Biometric System",
            font=("Arial", 32, "bold")
        ).pack(pady=40)

        ctk.CTkButton(
            self.frame,
            text="New User Registration",
            height=60,
            width=400,
            command=self.registration_mode
        ).pack(pady=20)

        ctk.CTkButton(
            self.frame,
            text="Existing User Verification",
            height=60,
            width=400,
            command=self.verification_mode
        ).pack(pady=20)

        ctk.CTkButton(
            self.frame,
            text="Exit",
            height=45,
            fg_color="red",
            command=self.destroy
        ).pack(pady=30)

    def registration_mode(self):
        self.capture_mode(mode="registration")

    def verification_mode(self):
        self.capture_mode(mode="verification")

    # ---------------- CAPTURE MODE ----------------
    def capture_mode(self, mode):

        self.clear()

        title = "Registration" if mode == "registration" else "Verification"

        ctk.CTkLabel(
            self.frame,
            text=f"{title} Mode",
            font=("Arial", 28, "bold")
        ).pack(pady=20)

        status_label = ctk.CTkLabel(self.frame, text="")
        status_label.pack(pady=10)

        progress = ctk.CTkProgressBar(self.frame, width=600)
        progress.pack(pady=20)
        progress.set(0)

        result_box = ctk.CTkTextbox(self.frame, width=900, height=300)
        result_box.pack(pady=20)

        name_entry = id_entry = None

        if mode == "registration":
            name_entry = ctk.CTkEntry(
                self.frame,
                width=350,
                placeholder_text="Enter User Name"
            )
            name_entry.pack(pady=5)

            id_entry = ctk.CTkEntry(
                self.frame,
                width=350,
                placeholder_text="Enter User ID"
            )
            id_entry.pack(pady=5)

        def start_capture():

            status, voc, _ = self.sensor.read_sensors()

            if status != "OK":
                messagebox.showerror(
                    "Sensors Not Active",
                    "VOC sensors not responding.\nPower ON sensors."
                )
                return

            if mode == "registration":
                user_name = name_entry.get().strip()
                user_id = id_entry.get().strip()

                if not user_name or not user_id:
                    messagebox.showwarning(
                        "Missing Info",
                        "Enter User Name and ID"
                    )
                    return

            status_label.configure(text="Waiting for hand...")

            while not self.hand.hand_present():
                time.sleep(0.2)

            self.hand.start_sampling()

            total_steps = ROUNDS * SAMPLE_COUNT
            current_step = 0

            # ================= REGISTRATION =================
            if mode == "registration":

                for round_no in range(1, ROUNDS + 1):

                    samples = []

                    for i in range(SAMPLE_COUNT):

                        if not self.hand.hand_present():
                            status_label.configure(text="Hand removed! Waiting...")
                            while not self.hand.hand_present():
                                time.sleep(0.2)

                        status, voc, _ = self.sensor.read_sensors()

                        if status != "OK":
                            continue

                        samples.append(voc)

                        current_step += 1
                        progress.set(current_step / total_steps)

                        status_label.configure(
                            text=f"Round {round_no}/{ROUNDS} - "
                                 f"Sample {len(samples)}/{SAMPLE_COUNT}"
                        )

                        time.sleep(0.3)

                    features = extract_features(samples)
                    store_features(user_id, features, round_no)

                    result_box.insert(
                        "end",
                        f"✔ Round {round_no} saved\n"
                    )

                self.hand.stop_sampling()

                log_voc("REGISTRATION", user_name, user_id, samples)

                result_box.insert(
                    "end",
                    "\n✅ Registration completed (6 rounds)\n"
                )

                if messagebox.askyesno(
                        "Register Another?",
                        "Register another user?"):
                    self.registration_mode()
                else:
                    self.show_main_menu()

            # ================= VERIFICATION =================
            else:

                all_round_features = []

                for round_no in range(1, ROUNDS + 1):

                    samples = []

                    for i in range(SAMPLE_COUNT):

                        if not self.hand.hand_present():
                            status_label.configure(text="Hand removed! Waiting...")
                            while not self.hand.hand_present():
                                time.sleep(0.2)

                        status, voc, _ = self.sensor.read_sensors()

                        if status != "OK":
                            messagebox.showerror(
                                "Sensor Error",
                                "Sensor not responding. Restart verification."
                            )
                            self.hand.stop_sampling()
                            return

                        samples.append(voc)

                        current_step += 1
                        progress.set(current_step / total_steps)

                        status_label.configure(
                            text=f"Round {round_no}/{ROUNDS} - "
                                 f"Sample {len(samples)}/{SAMPLE_COUNT}"
                        )

                        time.sleep(0.3)

                    features = extract_features(samples)
                    all_round_features.append(features)

                self.hand.stop_sampling()

                status_label.configure(text="Processing...")

                result = verify_user(all_round_features)

                result_box.delete("1.0", "end")

                if result["status"] == "VERIFIED":
                    result_box.insert(
                        "end",
                        f"✅ VERIFIED\n\n"
                        f"Name       : {result['user_name']}\n"
                        f"Confidence : {result['confidence']}%\n\n"
                    )
                else:
                    result_box.insert(
                        "end",
                        f"❌ NOT VERIFIED\n\n"
                        f"Confidence : {result['confidence']}%\n\n"
                    )

                for round_info in result["round_details"]:
                    result_box.insert(
                        "end",
                        f"\n--- Round {round_info['round']} ---\n"
                    )
                    for model, vote in round_info["votes"].items():
                        result_box.insert(
                            "end",
                            f"{model} → "
                            f"{vote['user_name']} "
                            f"({vote['confidence']}%)\n"
                        )

                status_label.configure(text="Verification Completed")

        ctk.CTkButton(
            self.frame,
            text="START" if mode == "registration" else "VERIFY ME",
            height=55,
            width=300,
            command=lambda: threading.Thread(
                target=start_capture,
                daemon=True
            ).start()
        ).pack(pady=20)

        ctk.CTkButton(
            self.frame,
            text="Back",
            command=self.show_main_menu
        ).pack(pady=10)

    def clear(self):
        for w in self.frame.winfo_children():
            w.destroy()


if __name__ == "__main__":
    app = MainGUI()
    app.mainloop()
