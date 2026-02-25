"""
VOC Sensor Visualization Script
--------------------------------
Generates scatterplots and radar plots from VOC sensor data.

1. Scatterplot: Shows which sensor readings match between verification and registered users
2. Radar Plot: Compares sensor profiles for all users
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import warnings
warnings.filterwarnings('ignore')

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
CSV_FILE = "voc_data_curated.csv"

# Sensor columns to analyze
SENSOR_COLUMNS = [
    'mq137_1', 'mq137_2',
    'mems_ethanol_1', 'mems_ethanol_2',
    'mq135_1', 'mq135_2',
    'mems_nh3_1', 'mems_nh3_2',
    'mq6_1', 'mq6_2',
    'mems_odor_1', 'mems_odor_2',
    'dht_temp', 'dht_hum'
]

# Sensor display names for plots
SENSOR_LABELS = [
    'MQ137-1', 'MQ137-2',
    'Ethanol-1', 'Ethanol-2',
    'MQ135-1', 'MQ135-2',
    'NH3-1', 'NH3-2',
    'MQ6-1', 'MQ6-2',
    'Odor-1', 'Odor-2',
    'Temp', 'Humidity'
]

# Matching threshold (15% relative difference)
MATCH_THRESHOLD = 0.15

# Color scheme
BG_DARK = "#0D1117"
BG_CARD = "#161B22"
ACCENT = "#58A6FF"
ACCENT2 = "#3FB950"
ACCENT_WARN = "#D29922"
TEXT_PRIMARY = "#E6EDF3"
TEXT_MUTED = "#8B949E"
BORDER = "#30363D"


# ─── DATA LOADING ─────────────────────────────────────────────────────────────
def load_and_prepare_data(csv_file):
    """Load CSV and prepare user profiles."""
    print(f"Loading data from {csv_file}...")
    df = pd.read_csv(csv_file)
    
    # Remove rows with missing sensor data
    df_clean = df.dropna(subset=['name', 'user_id'])
    
    # Group by user and calculate mean sensor values
    user_profiles = {}
    
    for user_id in df_clean['user_id'].unique():
        user_data = df_clean[df_clean['user_id'] == user_id]
        user_name = user_data['name'].iloc[0]
        
        # Calculate mean for each sensor
        sensor_means = []
        for sensor in SENSOR_COLUMNS:
            if sensor in user_data.columns:
                values = pd.to_numeric(user_data[sensor], errors='coerce')
                mean_val = values.mean()
                sensor_means.append(mean_val if not pd.isna(mean_val) else 0.0)
            else:
                sensor_means.append(0.0)
        
        user_profiles[user_id] = {
            'name': user_name,
            'sensors': sensor_means,
            'num_samples': len(user_data)
        }
    
    print(f"Loaded {len(user_profiles)} unique users")
    print(f"Users: {[v['name'] for v in user_profiles.values()]}")
    
    return user_profiles


# ─── SCATTERPLOT: SENSOR MATCHING ────────────────────────────────────────────
def create_scatterplot_matching(user_profiles, verification_user_id=None):
    """
    Create scatterplot showing which sensors match across users.
    
    If verification_user_id is provided, it's compared against all other users.
    Otherwise, the last user is used as the "verification" subject.
    """
    if not user_profiles or len(user_profiles) < 2:
        print("Need at least 2 users for comparison scatterplot")
        return
    
    # Select verification user (last one if not specified)
    if verification_user_id is None or verification_user_id not in user_profiles:
        verification_user_id = list(user_profiles.keys())[-1]
    
    ver_profile = user_profiles[verification_user_id]
    ver_name = ver_profile['name']
    ver_sensors = ver_profile['sensors']
    
    # Get all other users for comparison
    registered_users = {uid: prof for uid, prof in user_profiles.items() 
                       if uid != verification_user_id}
    
    if not registered_users:
        print("Need at least one other registered user for comparison")
        return
    
    # Calculate match scores for each user
    user_match_scores = []
    
    for uid, profile in registered_users.items():
        reg_sensors = profile['sensors']
        match_count = 0
        total_similarity = 0.0
        
        for reg_val, ver_val in zip(reg_sensors, ver_sensors):
            if reg_val == 0 and ver_val == 0:
                continue  # Skip if both are zero (missing data)
            
            # Calculate relative difference
            denom = max(abs(reg_val), abs(ver_val), 1e-9)
            rel_diff = abs(reg_val - ver_val) / denom
            
            if rel_diff <= MATCH_THRESHOLD:
                match_count += 1
                # Similarity score: closer to 1 is better
                similarity = 1.0 - rel_diff
                total_similarity += similarity
        
        # Score based on both number of matches and average similarity
        avg_similarity = total_similarity / match_count if match_count > 0 else 0
        score = match_count * avg_similarity
        
        user_match_scores.append({
            'user_id': uid,
            'name': profile['name'],
            'match_count': match_count,
            'score': score
        })
    
    # Sort by score and take top 10
    user_match_scores.sort(key=lambda x: x['score'], reverse=True)
    top_10_users = user_match_scores[:10]
    
    # Create a mapping for top 10 users
    top_user_ids = [u['user_id'] for u in top_10_users]
    person_names = [u['name'] for u in top_10_users]
    
    # Find matches only for top 10 users
    matches = []  # (person_idx, sensor_idx)
    
    for person_idx, user_id in enumerate(top_user_ids):
        profile = user_profiles[user_id]
        reg_sensors = profile['sensors']
        
        for sensor_idx, (reg_val, ver_val) in enumerate(zip(reg_sensors, ver_sensors)):
            if reg_val == 0 and ver_val == 0:
                continue  # Skip if both are zero (missing data)
            
            # Calculate relative difference
            denom = max(abs(reg_val), abs(ver_val), 1e-9)
            rel_diff = abs(reg_val - ver_val) / denom
            
            if rel_diff <= MATCH_THRESHOLD:
                matches.append((person_idx, sensor_idx))
    
    # Create scatterplot
    fig, ax = plt.subplots(figsize=(16, 10), facecolor=BG_CARD)
    ax.set_facecolor(BG_DARK)
    
    if matches:
        x_vals = [m[0] for m in matches]
        y_vals = [m[1] for m in matches]
        
        # Plot matches
        ax.scatter(x_vals, y_vals, c=ACCENT, s=150, alpha=0.7, 
                  edgecolors=TEXT_PRIMARY, linewidths=1.5, zorder=5)
        
        # Add grid lines
        for x in range(len(person_names)):
            ax.axvline(x, color=BORDER, linewidth=0.5, alpha=0.5, zorder=1)
        for y in range(len(SENSOR_LABELS)):
            ax.axhline(y, color=BORDER, linewidth=0.5, alpha=0.5, zorder=1)
    
    # Configure axes
    ax.set_xticks(range(len(person_names)))
    ax.set_xticklabels(person_names, fontsize=11, color=TEXT_MUTED, rotation=45, ha='right')
    ax.set_yticks(range(len(SENSOR_LABELS)))
    ax.set_yticklabels(SENSOR_LABELS, fontsize=10, color=TEXT_MUTED)
    
    ax.set_xlim(-0.7, max(len(person_names)-1, 0)+0.7)
    ax.set_ylim(-0.7, max(len(SENSOR_LABELS)-1, 0)+0.7)
    
    ax.set_xlabel("Registered Users", fontsize=13, color=TEXT_PRIMARY, labelpad=10)
    ax.set_ylabel("VOC Sensors", fontsize=13, color=TEXT_PRIMARY, labelpad=10)
    ax.set_title(f"Sensor Matching: {ver_name} (Verification) vs Top 10 Best Matches\n"
                 f"Points indicate sensor readings within {MATCH_THRESHOLD*100:.0f}% match",
                 fontsize=14, color=TEXT_PRIMARY, pad=20)
    
    ax.spines['top'].set_color(BORDER)
    ax.spines['bottom'].set_color(BORDER)
    ax.spines['left'].set_color(BORDER)
    ax.spines['right'].set_color(BORDER)
    ax.tick_params(colors=TEXT_MUTED)
    
    plt.tight_layout()
    plt.savefig('voc_scatterplot_matching.png', dpi=150, facecolor=BG_CARD, 
                edgecolor=BORDER, bbox_inches='tight')
    print(f"\n✓ Scatterplot saved: voc_scatterplot_matching.png")
    print(f"  Showing top 10 best matches for {ver_name}")
    print(f"  Total matching sensors across top 10: {len(matches)}")
    if top_10_users:
        print(f"  Best match: {top_10_users[0]['name']} ({top_10_users[0]['match_count']} sensors matched)")
    plt.close()


# ─── RADAR PLOTS: ALL USERS ───────────────────────────────────────────────────
def create_radar_plots(user_profiles):
    """Create radar plots for all users showing their sensor profiles."""
    if not user_profiles:
        print("No user profiles to visualize")
        return
    
    num_users = len(user_profiles)
    
    # Determine grid layout
    if num_users <= 4:
        rows, cols = 2, 2
    elif num_users <= 6:
        rows, cols = 2, 3
    elif num_users <= 9:
        rows, cols = 3, 3
    elif num_users <= 12:
        rows, cols = 3, 4
    else:
        rows, cols = 4, 4
    
    fig = plt.figure(figsize=(6*cols, 5*rows), facecolor=BG_CARD)
    fig.suptitle('VOC Sensor Profiles - All Users', 
                 fontsize=18, color=TEXT_PRIMARY, y=0.995)
    
    # Prepare angular coordinates for radar
    num_sensors = len(SENSOR_LABELS)
    angles = np.linspace(0, 2 * np.pi, num_sensors, endpoint=False).tolist()
    angles += angles[:1]  # Close the plot
    
    for idx, (user_id, profile) in enumerate(user_profiles.items()):
        if idx >= rows * cols:
            break
            
        ax = fig.add_subplot(rows, cols, idx + 1, projection='polar')
        ax.set_facecolor(BG_DARK)
        
        # Get sensor values and normalize
        sensor_values = profile['sensors']
        max_val = max(sensor_values) if max(sensor_values) > 0 else 1
        normalized = [v / max_val for v in sensor_values]
        normalized += normalized[:1]  # Close the plot
        
        # Plot
        ax.plot(angles, normalized, 'o-', linewidth=2.5, color=ACCENT2, 
               markersize=6, label=profile['name'])
        ax.fill(angles, normalized, alpha=0.25, color=ACCENT2)
        
        # Configure
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(SENSOR_LABELS, size=8, color=TEXT_MUTED)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(['25%', '50%', '75%', '100%'], size=7, color=TEXT_MUTED)
        ax.grid(color=BORDER, linewidth=0.8, alpha=0.6)
        ax.spines['polar'].set_color(BORDER)
        
        # Title
        ax.set_title(f"{profile['name']}\n({profile['num_samples']} samples)", 
                    size=11, color=TEXT_PRIMARY, pad=15, weight='bold')
    
    # Hide unused subplots
    for idx in range(num_users, rows * cols):
        ax = fig.add_subplot(rows, cols, idx + 1)
        ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('voc_radar_all_users.png', dpi=150, facecolor=BG_CARD,
                edgecolor=BORDER, bbox_inches='tight')
    print(f"\n✓ Radar plots saved: voc_radar_all_users.png")
    print(f"  Generated {num_users} user profiles")
    plt.close()


# ─── RADAR COMPARISON: REGISTRATION VS VERIFICATION ──────────────────────────
def create_radar_comparison(user_profiles, user_id_1, user_id_2=None):
    """
    Create radar plot comparing two users (e.g., registration vs verification).
    
    If user_id_2 is None, compares the specified user with the average of all others.
    """
    if user_id_1 not in user_profiles:
        print(f"User {user_id_1} not found")
        return
    
    profile_1 = user_profiles[user_id_1]
    
    if user_id_2 and user_id_2 in user_profiles:
        profile_2 = user_profiles[user_id_2]
        title = f"Comparison: {profile_1['name']} vs {profile_2['name']}"
        label_2 = profile_2['name']
    else:
        # Compare with average of all other users
        other_users = [prof for uid, prof in user_profiles.items() if uid != user_id_1]
        if not other_users:
            print("No other users for comparison")
            return
        
        avg_sensors = np.mean([prof['sensors'] for prof in other_users], axis=0)
        profile_2 = {'name': 'Average Others', 'sensors': avg_sensors.tolist()}
        title = f"Comparison: {profile_1['name']} vs Average of Others"
        label_2 = "Average Others"
    
    # Prepare data
    num_sensors = len(SENSOR_LABELS)
    angles = np.linspace(0, 2 * np.pi, num_sensors, endpoint=False).tolist()
    angles += angles[:1]
    
    # Normalize both profiles together for fair comparison
    all_values = profile_1['sensors'] + profile_2['sensors']
    max_val = max(all_values) if max(all_values) > 0 else 1
    
    values_1 = [v / max_val for v in profile_1['sensors']] + [profile_1['sensors'][0] / max_val]
    values_2 = [v / max_val for v in profile_2['sensors']] + [profile_2['sensors'][0] / max_val]
    
    # Create plot
    fig = plt.figure(figsize=(10, 9), facecolor=BG_CARD)
    ax = fig.add_subplot(111, projection='polar')
    ax.set_facecolor(BG_DARK)
    
    # Plot both profiles
    ax.plot(angles, values_1, 'o-', linewidth=2.5, color=ACCENT, 
           markersize=7, label=profile_1['name'], alpha=0.9)
    ax.fill(angles, values_1, alpha=0.2, color=ACCENT)
    
    ax.plot(angles, values_2, 's-', linewidth=2.5, color=ACCENT2, 
           markersize=7, label=label_2, alpha=0.9)
    ax.fill(angles, values_2, alpha=0.2, color=ACCENT2)
    
    # Configure
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(SENSOR_LABELS, size=10, color=TEXT_MUTED)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['25%', '50%', '75%', '100%'], size=9, color=TEXT_MUTED)
    ax.grid(color=BORDER, linewidth=1, alpha=0.6)
    ax.spines['polar'].set_color(BORDER)
    
    # Legend and title
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), 
             framealpha=0.9, edgecolor=BORDER, fontsize=11, 
             facecolor=BG_CARD, labelcolor=TEXT_PRIMARY)
    
    plt.title(title, size=14, color=TEXT_PRIMARY, pad=30, weight='bold')
    
    plt.tight_layout()
    plt.savefig('voc_radar_comparison.png', dpi=150, facecolor=BG_CARD,
                edgecolor=BORDER, bbox_inches='tight')
    print(f"\n✓ Radar comparison saved: voc_radar_comparison.png")
    print(f"  Comparing: {profile_1['name']} vs {label_2}")
    plt.close()


# ─── MAIN EXECUTION ───────────────────────────────────────────────────────────
def main():
    """Main execution function."""
    print("=" * 70)
    print("VOC SENSOR VISUALIZATION SYSTEM")
    print("=" * 70)
    
    # Load data
    user_profiles = load_and_prepare_data(CSV_FILE)
    
    if not user_profiles:
        print("Error: No valid user data found in CSV")
        return
    
    print("\n" + "=" * 70)
    print("GENERATING VISUALIZATIONS")
    print("=" * 70)
    
    # 1. Scatterplot: Sensor matching
    print("\n[1/3] Creating scatterplot - Sensor Matching...")
    create_scatterplot_matching(user_profiles)
    
    # 2. Radar plots: All users
    print("\n[2/3] Creating radar plots - All Users...")
    create_radar_plots(user_profiles)
    
    # 3. Radar comparison: Two users
    print("\n[3/3] Creating radar comparison...")
    user_ids = list(user_profiles.keys())
    if len(user_ids) >= 2:
        create_radar_comparison(user_profiles, user_ids[-1], user_ids[0])
    else:
        print("Skipping comparison - need at least 2 users")
    
    print("\n" + "=" * 70)
    print("VISUALIZATION COMPLETE!")
    print("=" * 70)
    print("\nGenerated files:")
    print("  • voc_scatterplot_matching.png - Sensor matching between users")
    print("  • voc_radar_all_users.png - Individual profiles for all users")
    print("  • voc_radar_comparison.png - Side-by-side comparison")
    print()


if __name__ == "__main__":
    main()
