import customtkinter as ctk
import threading
import time
from tkinter import messagebox

from sensors.sensor_reader import VOCSensor
from sensors.hand_controller import HandController
from core.feature_extractor import extract_features
from database.logger import log_voc
from database.feature_dao import store_features
from core.verification_controller import verify_user
from sensors.fan_manager import get_fan

import os
import subprocess
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------- CONFIG ----------------
SAMPLE_COUNT = 10
SENSOR_MODE = int(os.environ.get("VOC_SENSOR_MODE", "6"))
ROUNDS = 6 if SENSOR_MODE == 12 else 10

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

    # ================= SAFE UI UPDATE =================
    def safe_ui(self, func):
        self.after(0, func)

    # ================= MAIN MENU =================
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
            text="Train / Update Ensemble Models",
            height=60,
            width=400,
            fg_color="orange",
            hover_color="darkorange",
            command=self.training_mode
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

    # ================= TRAINING MODE =================
    def training_mode(self):
        self.clear()

        ctk.CTkLabel(
            self.frame,
            text="Ensemble Model Training",
            font=("Arial", 28, "bold")
        ).pack(pady=20)

        status_label = ctk.CTkLabel(self.frame, text="Initializing training pipeline...", text_color="orange")
        status_label.pack(pady=10)

        log_box = ctk.CTkTextbox(self.frame, width=900, height=400, font=("Courier", 12))
        log_box.pack(pady=20)

        def run_training():
            try:
                # Resolve script path
                script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "train.sh"))
                
                # Start the training process
                process = subprocess.Popen(
                    [script_path, "--sensors", str(SENSOR_MODE)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                # Stream output live
                for line in iter(process.stdout.readline, ""):
                    self.safe_ui(lambda l=line: log_box.insert("end", l))
                    self.safe_ui(lambda: log_box.see("end"))

                process.stdout.close()
                return_code = process.wait()

                if return_code == 0:
                    self.safe_ui(lambda: status_label.configure(text="Training Complete! Models updated.", text_color="green"))
                else:
                    self.safe_ui(lambda: status_label.configure(text="Training Failed. Check logs above.", text_color="red"))
            except Exception as e:
                self.safe_ui(lambda err=e: log_box.insert("end", f"Error launching training script: {err}\n"))
                self.safe_ui(lambda: status_label.configure(text="Critical Execution Error", text_color="red"))

        # Launch training in background

        threading.Thread(target=run_training, daemon=True).start()

        ctk.CTkButton(
            self.frame,
            text="Back to Menu",
            command=self.show_main_menu
        ).pack(pady=20)

    # ================= CAPTURE MODE =================
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
            name_entry = ctk.CTkEntry(self.frame, width=350,
                                      placeholder_text="Enter User Name")
            name_entry.pack(pady=5)

            id_entry = ctk.CTkEntry(self.frame, width=350,
                                    placeholder_text="Enter User ID")
            id_entry.pack(pady=5)

        # ================= START CAPTURE =================
        def start_capture():

            status, voc, _ = self.sensor.read_sensors()

            if status != "OK":
                self.safe_ui(lambda: messagebox.showerror(
                    "Sensors Not Active",
                    "VOC sensors not responding."
                ))
                return

            if mode == "registration":
                user_name = name_entry.get().strip()
                user_id = id_entry.get().strip()

                if not user_name or not user_id:
                    self.safe_ui(lambda: messagebox.showwarning(
                        "Missing Info",
                        "Enter User Name and ID"
                    ))
                    return

            self.safe_ui(lambda: status_label.configure(text="Waiting for hand..."))

            while not self.hand.hand_present():
                time.sleep(0.2)

            self.hand.start_sampling()

            total_steps = ROUNDS * SAMPLE_COUNT
            current_step = 0

            # ================= REGISTRATION =================
            if mode == "registration":

                for round_no in range(1, ROUNDS + 1):

                    samples = []

                    for _ in range(SAMPLE_COUNT):

                        if not self.hand.hand_present():
                            self.safe_ui(lambda: status_label.configure(
                                text="Hand removed! Waiting..."
                            ))
                            while not self.hand.hand_present():
                                time.sleep(0.2)

                        status, voc, _ = self.sensor.read_sensors()
                        if status != "OK":
                            continue

                        samples.append(voc)
                        current_step += 1

                        progress_value = current_step / total_steps
                        text_value = f"Round {round_no}/{ROUNDS} - Sample {len(samples)}/{SAMPLE_COUNT}"

                        self.safe_ui(lambda v=progress_value: progress.set(v))
                        self.safe_ui(lambda t=text_value: status_label.configure(text=t))

                        time.sleep(0.3)

                    features = extract_features(samples)
                    store_features(user_id, features, round_no)

                    self.safe_ui(lambda r=round_no:
                                 result_box.insert("end", f"Round {r} saved\n"))

                self.hand.stop_sampling()

                log_voc("REGISTRATION", user_name, user_id, samples)

                self.safe_ui(lambda:
                             result_box.insert("end", "\nRegistration completed\n"))
                '''
                # FAN FLUSH
                threading.Thread(
                    target=get_fan().flush,
                    args=(20,),
                    daemon=True
                ).start()

                self.safe_ui(lambda: self.ask_next_registration())
                '''
                get_fan().flush(20)
                self.safe_ui(lambda: self.ask_next_registration())
            # ================= VERIFICATION =================
            else:

                all_round_features = []

                for round_no in range(1, ROUNDS + 1):

                    samples = []

                    for _ in range(SAMPLE_COUNT):

                        if not self.hand.hand_present():
                            self.safe_ui(lambda:
                                         status_label.configure(text="Hand removed! Waiting..."))
                            while not self.hand.hand_present():
                                time.sleep(0.2)

                        status, voc, _ = self.sensor.read_sensors()
                        if status != "OK":
                            return

                        samples.append(voc)
                        current_step += 1

                        progress_value = current_step / total_steps
                        text_value = f"Round {round_no}/{ROUNDS} - Sample {len(samples)}/{SAMPLE_COUNT}"

                        self.safe_ui(lambda v=progress_value: progress.set(v))
                        self.safe_ui(lambda t=text_value: status_label.configure(text=t))

                        time.sleep(0.3)

                    features = extract_features(samples)
                    all_round_features.append(features)

                self.hand.stop_sampling()

                self.safe_ui(lambda:
                             status_label.configure(text="Processing..."))

                result = verify_user(all_round_features)

                def show_result():
                    result_box.delete("1.0", "end")

                    if result["status"] == "VERIFIED":
                        result_box.insert(
                            "end",
                            f"✅ VERIFIED\n\n"
                            f"Name: {result['user_name']}\n"
                            f"Overall Confidence: {result['confidence']}%\n"
                        )
                        threading.Thread(
                            target=get_fan().flush,
                            args=(20,),
                            daemon=True
                        ).start()
                    else:
                        result_box.insert(
                            "end",
                            f"❌ NOT VERIFIED\n\n"
                            f"Overall Confidence: {result['confidence']}%\n"
                        )

                    # Log detailed voting
                    result_box.insert("end", "\n--- Final Round Detailed Votes ---\n")
                    last_round = result["round_details"][-1]["votes"]
                    models, confidences = [], []
                    for model, vote in last_round.items():
                        result_box.insert(
                            "end",
                            f"{model}: {vote['user_name']} ({vote['confidence']}%)\n"
                        )
                        models.append(model)
                        confidences.append(vote['confidence'])

                    ### GRAPH PLOTTING ###
                    fig, ax = plt.subplots(figsize=(6, 3), dpi=100)
                    ax.bar(models, confidences, color=['blue', 'green', 'orange', 'purple', 'red'])
                    ax.set_ylim(0, 100)
                    ax.set_ylabel('Confidence (%)')
                    ax.set_title('Final Round Model Probabilities')
                    
                    canvas = FigureCanvasTkAgg(fig, master=self.frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(pady=10)
                    
                    # ---------------- FLAG AS INCORRECT ----------------
                    def flag_as_wrong():
                        dialog = ctk.CTkInputDialog(
                            text="Prediction was wrong? Enter the CORRECT User ID to reinforce the model:",
                            title="Flag Incorrect / Reinforce"
                        )
                        correct_id = dialog.get_input()
                        
                        if correct_id and correct_id.strip():
                            correct_id = correct_id.strip()
                            try:
                                for r_idx, f_dict in enumerate(all_round_features):
                                    store_features(correct_id, f_dict, r_idx + 1)
                                
                                messagebox.showinfo(
                                    "Data Added", 
                                    f"Added new fingerprint for User ID '{correct_id}'.\nPlease run the 'Train / Update' pipeline from the main menu to learn this signature!"
                                )
                                self.show_main_menu()
                            except Exception as e:
                                messagebox.showerror("Database Error", f"Failed to save corrected features: {e}")
                    
                    ctk.CTkButton(
                        self.frame,
                        text="Flag Incorrect (Reinforce Model)",
                        fg_color="crimson",
                        hover_color="darkred",
                        command=flag_as_wrong
                    ).pack(pady=10)

                    status_label.configure(text="Verification Completed")

                self.safe_ui(show_result)

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

    # ================= ASK NEXT =================
    def ask_next_registration(self):
        if messagebox.askyesno("Register Another?", "Register another user?"):
            self.registration_mode()
        else:
            self.show_main_menu()

    # ================= CLEAR FRAME =================
    def clear(self):
        for w in self.frame.winfo_children():
            w.destroy()


if __name__ == "__main__":
    app = MainGUI()
    app.mainloop()