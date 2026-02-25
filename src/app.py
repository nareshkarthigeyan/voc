import customtkinter as ctk
import threading
import time
import os
import subprocess
import numpy as np
from tkinter import messagebox
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Internal Imports
from sensors.sensor_reader import VOCSensor
from sensors.hand_controller import HandController
from core.feature_extractor import extract_features
from database.logger import log_voc as log_voc_encrypted
from database.logger_simple import log_voc as log_voc_simple
from database.feature_dao import store_features, store_radar_profile, get_radar_profile
from database.user_dao import insert_user
from core.verification_controller import verify_user
from sensors.fan_manager import get_fan
from core.radar_handler import RadarHandler
from core.data_packager import DataPackager

# Optional Fingerprint (only for 12 sensor version)
FingerprintSensor = None
SENSOR_MODE = int(os.environ.get("VOC_SENSOR_MODE", "6"))
if SENSOR_MODE == 12:
    try:
        from sensors.fingerprint_sensor import FingerprintSensor
    except ImportError:
        print("[WARN] Fingerprint library (pyfingerprint) not found.")

# ---------------- CONFIG ----------------
SAMPLE_COUNT = 10
ROUNDS = 10
SENSOR_NAMES = ["Ethanol", "Methane", "CO2", "Ammonia", "H2S", "Toluene"]

# ─── THEME ────────────────────────────────────────────────────────────────────
BG_DARK      = "#0D1117"
BG_CARD      = "#161B22"
BG_HOVER     = "#1C2128"
ACCENT       = "#58A6FF"
ACCENT2      = "#3FB950"
ACCENT_RED   = "#F85149"
ACCENT_WARN  = "#D29922"
TEXT_PRIMARY = "#E6EDF3"
TEXT_MUTED   = "#8B949E"
BORDER       = "#30363D"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ─── MATPLOTLIB DARK THEME ────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor":  BG_CARD,
    "axes.facecolor":    BG_DARK,
    "axes.edgecolor":    BORDER,
    "axes.labelcolor":   TEXT_MUTED,
    "xtick.color":       TEXT_MUTED,
    "ytick.color":       TEXT_MUTED,
    "text.color":        TEXT_PRIMARY,
    "grid.color":        BORDER,
    "grid.alpha":        0.6,
    "font.family":       "monospace",
})

class VisualizationWindow(ctk.CTkToplevel):
    """Floating analytics window with scatter + radar charts."""
    def __init__(self, master, scatter_data=None, radar_data=None):
        super().__init__(master)
        self.title("Analytics Dashboard")
        self.geometry("1280x760")
        self.configure(fg_color=BG_DARK)

        # Header
        hdr = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr, text="◈  VOC ANALYTICS DASHBOARD",
            font=("Courier New", 16, "bold"),
            text_color=ACCENT
        ).pack(side="left", padx=24, pady=14)

        # Tab row
        tab = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=42)
        tab.pack(fill="x")
        tab.pack_propagate(False)

        self.scatter_frame = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self.radar_frame   = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)

        def show_scatter():
            self.radar_frame.pack_forget()
            self.scatter_frame.pack(fill="both", expand=True)
            scatter_btn.configure(text_color=ACCENT, fg_color=BG_HOVER)
            radar_btn.configure(text_color=TEXT_MUTED, fg_color="transparent")

        def show_radar():
            self.scatter_frame.pack_forget()
            self.radar_frame.pack(fill="both", expand=True)
            radar_btn.configure(text_color=ACCENT, fg_color=BG_HOVER)
            scatter_btn.configure(text_color=TEXT_MUTED, fg_color="transparent")

        scatter_btn = ctk.CTkButton(tab, text="SCATTER — Match Matrix", fg_color=BG_HOVER, 
                                   text_color=ACCENT, font=("Courier New", 11, "bold"), 
                                   height=42, corner_radius=0, command=show_scatter)
        scatter_btn.pack(side="left")

        radar_btn = ctk.CTkButton(tab, text="RADAR — Biometric Profile", fg_color="transparent", 
                                 text_color=TEXT_MUTED, font=("Courier New", 11, "bold"), 
                                 height=42, corner_radius=0, command=show_radar)
        radar_btn.pack(side="left")

        self._build_scatter(self.scatter_frame, scatter_data)
        self._build_radar(self.radar_frame, radar_data)
        show_radar()

    def _build_scatter(self, parent, data):
        fig = Figure(figsize=(10, 5), dpi=100)
        ax = fig.add_subplot(111)
        if data:
            persons = data.get("persons", [])
            sensors = data.get("sensors", SENSOR_NAMES)
            matches = data.get("matches", [])
            verified = data.get("verified_person")
            
            x_vals, y_vals, colors, sizes = [], [], [], []
            for (pi, si) in matches:
                x_vals.append(pi)
                y_vals.append(si)
                is_verified = (verified and persons[pi] == verified)
                colors.append(ACCENT2 if is_verified else ACCENT)
                sizes.append(200 if is_verified else 100)

            if x_vals:
                ax.scatter(x_vals, y_vals, c=colors, s=sizes, alpha=0.8)
            
            ax.set_xticks(range(len(persons)))
            ax.set_xticklabels(persons)
            ax.set_yticks(range(len(sensors)))
            ax.set_yticklabels(sensors)
        else:
            ax.text(0.5, 0.5, "No data yet", ha="center")
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _build_radar(self, parent, data):
        fig = Figure(figsize=(6, 6), dpi=100)
        if data:
            labels = data.get("labels", SENSOR_NAMES)
            reg_v  = data.get("registration", [])
            ver_v  = data.get("verification", [])
            name   = data.get("user_name", "User")
            N = len(labels)
            angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
            angles += angles[:1]
            
            reg_n = [v/max(reg_v + [1]) for v in reg_v] + [reg_v[0]/max(reg_v + [1])]
            ver_n = [v/max(ver_v + [1]) for v in ver_v] + [ver_v[0]/max(ver_v + [1])]

            ax = fig.add_subplot(111, polar=True)
            ax.set_facecolor(BG_DARK)
            ax.plot(angles, reg_n, color=ACCENT, linewidth=2, label="Registered")
            ax.fill(angles, reg_n, color=ACCENT, alpha=0.1)
            ax.plot(angles, ver_n, color=ACCENT2, linewidth=2, label="Current")
            ax.fill(angles, ver_n, color=ACCENT2, alpha=0.1)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(labels)
            ax.legend(loc="upper right", bbox_to_anchor=(1.1, 1.1))
            fig.suptitle(f"VOC Radar Profile: {name}")
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

class MainGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VOC Biometric Intelligence")
        self.geometry("1280x900")
        self.configure(fg_color=BG_DARK)

        self.sensor = VOCSensor()
        self.hand   = HandController()
        
        self.fp_sensor = None
        if SENSOR_MODE == 12 and FingerprintSensor:
            self.fp_sensor = FingerprintSensor()

        self._scatter_data = None
        self._radar_data   = None
        self._registered_profiles = {}

        self._build_sidebar()
        self.frame = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self.frame.pack(side="right", fill="both", expand=True)
        
        self.show_main_menu()

    def _build_sidebar(self):
        side = ctk.CTkFrame(self, width=220, fg_color=BG_CARD, corner_radius=0)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        ctk.CTkLabel(side, text="◈ VOC SYSTEM", font=("Courier New", 18, "bold"), text_color=ACCENT).pack(pady=30)
        
        def _side_btn(text, cmd):
            return ctk.CTkButton(side, text=text, fg_color="transparent", text_color=TEXT_MUTED, 
                                 hover_color=BG_HOVER, anchor="w", command=cmd).pack(fill="x", padx=10, pady=2)

        _side_btn("Dashboard", self.show_main_menu)
        _side_btn("Registration", self.registration_mode)
        _side_btn("Verification", self.verification_mode)
        _side_btn("Model Training", self.training_mode)
        _side_btn("Analytics", self._open_analytics)
        
        ctk.CTkLabel(side, text=f"Mode: {SENSOR_MODE}-Sensor", font=("Courier New", 10), text_color=TEXT_MUTED).pack(side="bottom", pady=20)

    def _open_analytics(self):
        VisualizationWindow(self, self._scatter_data, self._radar_data)

    def clear(self):
        for w in self.frame.winfo_children(): w.destroy()

    def safe_ui(self, func): self.after(0, func)

    def show_main_menu(self):
        self.clear()
        outer = ctk.CTkFrame(self.frame, fg_color="transparent")
        outer.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(outer, text="VOC BIOMETRIC PLATFORM", font=("Courier New", 32, "bold"), text_color=TEXT_PRIMARY).pack(pady=10)
        ctk.CTkLabel(outer, text="Multimodal Gas-Phase Identity Verification", font=("Courier New", 14), text_color=TEXT_MUTED).pack(pady=(0, 40))

        btn_container = ctk.CTkFrame(outer, fg_color="transparent")
        btn_container.pack()

        def _big_btn(text, subtitle, clr, cmd):
            card = ctk.CTkFrame(btn_container, fg_color=BG_CARD, border_width=1, border_color=BORDER, width=400, height=100)
            card.pack(pady=10)
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=text, font=("Courier New", 16, "bold"), text_color=clr).place(x=20, y=25)
            ctk.CTkLabel(card, text=subtitle, font=("Courier New", 11), text_color=TEXT_MUTED).place(x=20, y=55)
            ctk.CTkButton(card, text="→", width=50, height=50, fg_color=clr, text_color=BG_DARK, command=cmd).place(x=330, y=25)

        _big_btn("USER ENROLLMENT", "Register new biometric profile", ACCENT, self.registration_mode)
        _big_btn("IDENTITY CHECK", "Verify existing user identity", ACCENT2, self.verification_mode)
        _big_btn("SYSTEM TRAINING", "Update ML ensemble parameters", "orange", self.training_mode)

    def training_mode(self):
        self.clear()
        ctk.CTkLabel(self.frame, text="Neural Network & Ensemble Training", font=("Courier New", 24, "bold")).pack(pady=20)
        log_box = ctk.CTkTextbox(self.frame, width=900, height=500, font=("Courier New", 12))
        log_box.pack(pady=10)

        def run_t():
            script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "train.sh"))
            proc = subprocess.Popen([script, "--sensors", str(SENSOR_MODE)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in iter(proc.stdout.readline, ""):
                self.safe_ui(lambda l=line: log_box.insert("end", l))
                self.safe_ui(lambda: log_box.see("end"))
            proc.stdout.close()
        
        threading.Thread(target=run_t, daemon=True).start()
        ctk.CTkButton(self.frame, text="Return to Menu", command=self.show_main_menu).pack(pady=10)

    def registration_mode(self): self.capture_mode("registration")
    def verification_mode(self): self.capture_mode("verification")

    def capture_mode(self, mode):
        self.clear()
        t_clr = ACCENT if mode=="registration" else ACCENT2
        
        left = ctk.CTkFrame(self.frame, fg_color="transparent", width=400)
        left.pack(side="left", fill="y", padx=30, pady=30)
        
        ctk.CTkLabel(left, text=mode.upper(), font=("Courier New", 24, "bold"), text_color=t_clr).pack(anchor="w")
        
        name_e = id_e = None
        if mode == "registration":
            name_e = ctk.CTkEntry(left, placeholder_text="Name", width=340); name_e.pack(pady=10)
            id_e = ctk.CTkEntry(left, placeholder_text="User ID", width=340); id_e.pack(pady=10)

        prog = ctk.CTkProgressBar(left, width=340, progress_color=t_clr); prog.pack(pady=20); prog.set(0)
        status_l = ctk.CTkLabel(left, text="Ready", text_color=TEXT_MUTED); status_l.pack()

        log_box = ctk.CTkTextbox(self.frame, width=700, height=700, fg_color=BG_CARD)
        log_box.pack(side="right", fill="both", padx=30, pady=30)

        def start():
            if SENSOR_MODE == 12 and self.fp_sensor:
                self.safe_ui(lambda: status_l.configure(text="Place finger on scanner..."))
                res = self.fp_sensor.enroll("user", "id") if mode=="registration" else self.fp_sensor.authenticate()
                if res["status"] != "success" and res["status"] != "authenticated":
                    self.safe_ui(lambda: messagebox.showerror("FP Error", "Fingerprint failed"))
                    return

            uid = id_e.get() if mode=="registration" else "unknown"
            uname = name_e.get() if mode=="registration" else "unknown"

            # Pre-check sensor connectivity
            self.safe_ui(lambda: status_l.configure(text="Validating sensors..."))
            ch_status, _, _ = self.sensor.read_sensors()
            if ch_status != "OK":
                self.safe_ui(lambda: messagebox.showerror("Sensor Error", f"Hardware Feedback: {ch_status}"))
                self.safe_ui(lambda: status_l.configure(text="Ready"))
                return

            self.safe_ui(lambda: status_l.configure(text="Waiting for hand..."))
            while not self.hand.hand_present(): time.sleep(0.1)
            
            self.hand.start_sampling()
            all_samples = []
            
            for r in range(1, ROUNDS + 1):
                samples = []
                for s in range(SAMPLE_COUNT):
                    # Check if hand is still present during sampling
                    if not self.hand.hand_present():
                        self.safe_ui(lambda: status_l.configure(text="Hand removed! Waiting..."))
                        while not self.hand.hand_present(): time.sleep(0.2)
                        
                    self.safe_ui(lambda v=(len(all_samples)/(ROUNDS*SAMPLE_COUNT)), r=r, s=s: 
                                 [prog.set(v), status_l.configure(text=f"Scanning Round {r}/{ROUNDS} - Sample {s+1}/{SAMPLE_COUNT}")])
                    
                    res, voc, _ = self.sensor.read_sensors()
                    if res == "OK": 
                        samples.append(voc)
                        all_samples.append(voc)
                    time.sleep(0.2)
                
                if len(samples) > 0:
                    features = extract_features(samples)
                    if mode=="registration": store_features(uid, features, r)
                else:
                    self.safe_ui(lambda: messagebox.showerror("Read Error", f"Round {r} collected no valid readings. Retrying..."))
            
            self.hand.stop_sampling()
            
            if len(all_samples) == 0:
                self.safe_ui(lambda: messagebox.showerror("Failure", "No valid data collected."))
                self.safe_ui(lambda: status_l.configure(text="Ready"))
                return
                
            if mode=="registration":
                # Store user name in users table (critical for verification name lookup)
                insert_user(uid, uname)
                log_voc_simple("REGISTRATION", uname, uid, all_samples)
                RadarHandler().generate_radar_plot(uid, np.mean([list(s.values()) for s in all_samples], axis=0), uname)
                self.safe_ui(lambda: status_l.configure(text="Registration Packaged!"))
                self.safe_ui(lambda: messagebox.showinfo("Success", "Registration packaged!"))
            else:
                self.safe_ui(lambda: status_l.configure(text="Processing Verification..."))
                chunks = [extract_features(all_samples[i:i+SAMPLE_COUNT]) for i in range(0, len(all_samples), SAMPLE_COUNT) if len(all_samples[i:i+SAMPLE_COUNT]) > 0]
                result = verify_user(chunks)
                self._show_ver_result(result, all_samples, log_box)
                self.safe_ui(lambda: status_l.configure(text="Verification Complete!"))

        ctk.CTkButton(left, text="BEGIN", height=50, width=340, fg_color=t_clr, text_color=BG_DARK, 
                      command=lambda: threading.Thread(target=start, daemon=True).start()).pack(pady=20)

    def _show_ver_result(self, result, samples, log_box):
        # ── Print per-model predictions per round ──
        def _render_results():
            log_box.insert("end", "\n" + "═"*60 + "\n")
            log_box.insert("end", "  VERIFICATION RESULTS\n")
            log_box.insert("end", "═"*60 + "\n\n")
            
            round_details = result.get('round_details', [])
            for rd in round_details:
                log_box.insert("end", f"── Round {rd['round']} ──\n")
                for model_name, vote in rd['votes'].items():
                    log_box.insert("end", f"  {model_name:>4s}: {vote['user_name']}  [{vote['confidence']}%]\n")
                log_box.insert("end", "\n")
            
            log_box.insert("end", "═"*60 + "\n")
            status_color = "[VERIFIED]" if result['status'] == "VERIFIED" else "[NOT VERIFIED]"
            log_box.insert("end", f"  {status_color} FINAL RESULT: {result['status']}\n")
            log_box.insert("end", f" Name : {result['user_name']}\n")
            log_box.insert("end", f" ID   : {result['user_id']}\n")
            log_box.insert("end", f" Score: {result['confidence']}%\n")
            log_box.insert("end", "═"*60 + "\n")
            log_box.see("end")
        
        self.safe_ui(_render_results)
        
        if result['status'] == "VERIFIED":
            threading.Thread(target=get_fan().flush, args=(20,), daemon=True).start()
        
        # Build Radar Data for Analytics
        v_means = np.mean([list(s.values()) for s in samples], axis=0)
        try:
            profile = get_radar_profile(result['user_id'])
        except Exception:
            profile = None
        if profile:
            self._radar_data = {
                "labels": SENSOR_NAMES,
                "registration": profile["registration_readings"],
                "verification": v_means,
                "user_name": result["user_name"]
            }
        
        # ── Flag Incorrect / Reinforcement Button ──
        def reinforce():
            dialog = ctk.CTkInputDialog(
                text="Verification was wrong.\nEnter CORRECT Name:",
                title="Flag Incorrect — Enter Correct Name"
            )
            correct_name = dialog.get_input()
            if not correct_name:
                return
            
            dialog2 = ctk.CTkInputDialog(
                text=f"Name: {correct_name}\nEnter CORRECT User ID:",
                title="Flag Incorrect — Enter Correct ID"
            )
            correct_id = dialog2.get_input()
            if not correct_id:
                return
            
            # Store correct user in users table
            insert_user(correct_id, correct_name)
            
            # Store features under the correct user ID for reinforcement
            for i in range(ROUNDS):
                chunk = samples[i*SAMPLE_COUNT:(i+1)*SAMPLE_COUNT]
                if len(chunk) > 0:
                    store_features(correct_id, extract_features(chunk), i+1)
            
            self.safe_ui(lambda: log_box.insert("end", f"\n[REINFORCEMENT] Data stored for {correct_name} ({correct_id}).\nRe-train models to apply.\n"))
            self.safe_ui(lambda: log_box.see("end"))
            messagebox.showinfo("Reinforcement Saved", f"Data added for {correct_name} ({correct_id}).\n\nRun Model Training to update the models.")

        self.safe_ui(lambda: ctk.CTkButton(self.frame, text="⚠ Flag Incorrect — Reinforce", fg_color=ACCENT_RED, 
                                           hover_color="#DA3633", text_color="white", height=40,
                                           font=("Courier New", 13, "bold"), command=reinforce).pack(pady=10))

if __name__ == "__main__":
    app = MainGUI()
    app.mainloop()