import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime
from database.feature_dao import store_radar_profile

class RadarHandler:
    def __init__(self, output_dir="data/radar_plots"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.sensor_names = ["Ethanol", "Methane", "CO2", "Ammonia", "H2S", "Toluene"]

    def generate_radar_plot(self, user_id, registration_readings, user_name):
        """
        Generates a radar plot for a user's registration profile
        and stores it in the database.
        """
        N = len(self.sensor_names)
        
        # Ensure we have enough readings
        readings = list(registration_readings)
        if len(readings) < N:
            readings += [0.0] * (N - len(readings))
        readings = readings[:N]
        
        # Normalize
        max_val = max(readings) if max(readings) > 0 else 1.0
        normalized = [v / max_val for v in readings]
        
        # Radar plot angles
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        angles += angles[:1]
        
        plot_vals = normalized + [normalized[0]]
        
        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(111, polar=True)
        
        ax.plot(angles, plot_vals, color='#58A6FF', linewidth=2)
        ax.fill(angles, plot_vals, color='#58A6FF', alpha=0.25)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(self.sensor_names)
        
        plt.title(f"VOC Profile: {user_name} ({user_id})")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"radar_{user_id}_{timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        plt.savefig(filepath)
        plt.close()
        
        # Store radar profile in database for verification lookup
        store_radar_profile(user_id, user_name, filepath, readings)
        
        return filepath, normalized

