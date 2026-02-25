"""
VOC Biometric System - Complete Automation Workflow
Master script for automating the entire registration -> training -> deployment pipeline
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil
import json
from datetime import datetime


class WorkflowAutomation:
    """Manage the complete VOC biometric workflow."""
    
    def __init__(self):
        self.workflow_log = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def log(self, message: str, level: str = "INFO"):
        """Log workflow messages."""
        prefix = {
            "INFO": "ℹ",
            "SUCCESS": "✓",
            "WARNING": "⚠",
            "ERROR": "✗",
            "STEP": "▶"
        }
        
        formatted = f"[{prefix.get(level, '•')}] {message}"
        print(formatted)
        self.workflow_log.append(formatted)
    
    def print_header(self, title: str):
        """Print a formatted header."""
        width = 70
        print("\n" + "=" * width)
        print(title.center(width))
        print("=" * width + "\n")
    
    def print_section(self, title: str):
        """Print a formatted section."""
        print(f"\n{'─' * 70}")
        print(f"  {title}")
        print(f"{'─' * 70}\n")
    
    def phase_registration(self):
        """Phase 1: Registration on Raspberry Pi."""
        self.print_section("PHASE 1: REGISTRATION (Raspberry Pi)")
        
        self.log("Launch VOC biometric system", "STEP")
        self.log("Follow these steps on Raspberry Pi:")
        print("""
          1. Run the executable or: python voc_main_updated.py
          2. Select 'NEW USER REGISTRATION'
          3. Enter user information
          4. Follow biometric capture prompts
          5. System automatically packages data after registration
          6. Transfer the generated ZIP file to your main device
        """)
        
        self.log("Data will be packaged at: data_exports/registration_*.zip", "SUCCESS")
        self.log("Ready to proceed to training phase", "SUCCESS")
    
    def phase_training(self, zip_file: str = None):
        """Phase 2: Model training on main device."""
        self.print_section("PHASE 2: AUTOMATED TRAINING (Main Device)")
        
        if not zip_file:
            self.log("Enter path to registration data ZIP file:", "STEP")
            zip_file = input("  Path: ").strip()
        
        if not os.path.exists(zip_file):
            self.log(f"File not found: {zip_file}", "ERROR")
            return None
        
        self.log(f"Starting training pipeline with: {zip_file}", "INFO")
        
        try:
            # Run auto_train.py
            result = subprocess.run(
                [sys.executable, "auto_train.py", zip_file],
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if result.returncode == 0:
                self.log("Model training completed successfully", "SUCCESS")
                
                # Extract deployment package path from output
                for line in result.stdout.split('\n'):
                    if 'trained_models_' in line and '.zip' in line:
                        deploy_zip = line.split()[-1]
                        self.log(f"Deployment package: {deploy_zip}", "SUCCESS")
                        return deploy_zip
                
                # If not found in output, try to find the latest
                deploy_files = sorted(Path('.').glob('trained_models_*.zip'))
                if deploy_files:
                    return str(deploy_files[-1])
            else:
                self.log("Training failed!", "ERROR")
                print(result.stderr)
                return None
        
        except Exception as e:
            self.log(f"Training process failed: {e}", "ERROR")
            return None
    
    def phase_deployment(self, deploy_zip: str = None):
        """Phase 3: Model deployment on Raspberry Pi."""
        self.print_section("PHASE 3: MODEL DEPLOYMENT (Raspberry Pi)")
        
        if not deploy_zip:
            self.log("Enter path to trained models ZIP file:", "STEP")
            deploy_zip = input("  Path: ").strip()
        
        if not os.path.exists(deploy_zip):
            self.log(f"File not found: {deploy_zip}", "ERROR")
            return False
        
        self.log(f"Instructions for Raspberry Pi:", "INFO")
        print(f"""
          1. Transfer: {deploy_zip}
          2. Run: python model_deploy.py {os.path.basename(deploy_zip)}
          3. Verify output shows: ✓ All model files present
          4. System ready for IDENTITY VERIFICATION
        """)
        
        self.log("Model deployment ready", "SUCCESS")
        return True
    
    def phase_verification(self):
        """Phase 4: Identity verification."""
        self.print_section("PHASE 4: IDENTITY VERIFICATION (Raspberry Pi)")
        
        self.log("After model deployment, you can now:", "INFO")
        print("""
          1. Run the VOC biometric system
          2. Select 'IDENTITY VERIFICATION'
          3. Scan fingerprint and sensor readings
          4. System will:
             - Compare fingerprint
             - Extract sensor readings
             - Compute radar profile similarity
             - Make multi-factor decision
        """)
        
        self.log("System ready for production use", "SUCCESS")
    
    def run_interactive_workflow(self):
        """Run the complete workflow interactively."""
        self.print_header("VOC BIOMETRIC SYSTEM - COMPLETE WORKFLOW")
        
        print("""
        This automated workflow guides you through:
        1. Registration Phase (Raspberry Pi)
        2. Training Phase (Main Device)
        3. Deployment Phase (Raspberry Pi)
        4. Verification Phase (Raspberry Pi)
        """)
        
        while True:
            print("\n" + "─" * 70)
            print("Select workflow phase:")
            print("  1. Phase 1: Registration Instructions")
            print("  2. Phase 2: Automated Training")
            print("  3. Phase 3: Model Deployment Instructions")
            print("  4. Phase 4: Verification Instructions")
            print("  5. Run All Phases (with user input)")
            print("  0. Exit")
            print("─" * 70)
            
            choice = input("\nEnter choice (0-5): ").strip()
            
            if choice == "1":
                self.phase_registration()
            elif choice == "2":
                deploy_zip = self.phase_training()
                if deploy_zip:
                    print(f"\n✓ Trained models ready: {deploy_zip}")
            elif choice == "3":
                self.phase_deployment()
            elif choice == "4":
                self.phase_verification()
            elif choice == "5":
                self.phase_registration()
                input("\n⏳ Press ENTER after transferring ZIP to main device...")
                deploy_zip = self.phase_training()
                if deploy_zip:
                    input("\n⏳ Press ENTER after transferring trained models to Raspberry Pi...")
                    self.phase_deployment(deploy_zip)
                    self.phase_verification()
            elif choice == "0":
                self.log("Exiting workflow", "INFO")
                break
            else:
                self.log("Invalid choice", "WARNING")
    
    def print_quick_reference(self):
        """Print quick reference guide."""
        self.print_header("QUICK REFERENCE GUIDE")
        
        print("""
        REGISTRATION (Raspberry Pi):
        $ python voc_main_updated.py
        → Select NEW USER REGISTRATION
        → Collect biometrics
        → Data auto-packaged to: data_exports/registration_*.zip
        
        TRAINING (Main Device):
        $ python auto_train.py registration_*.zip
        → Automatically trains all 6 models
        → Creates: trained_models_*.zip
        
        DEPLOYMENT (Raspberry Pi):
        $ python model_deploy.py trained_models_*.zip
        → Deploys trained models
        → Ready for verification
        
        VERIFICATION (Raspberry Pi):
        $ python voc_main_updated.py
        → Select IDENTITY VERIFICATION
        → System uses trained models
        
        CREATING EXECUTABLE:
        $ pyinstaller voc_main.spec
        → Creates: dist/VOC_Biometric_System/VOC_Biometric_System.exe
        """)


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--quick-ref":
            workflow = WorkflowAutomation()
            workflow.print_quick_reference()
            return 0
        elif sys.argv[1] == "--train":
            if len(sys.argv) < 3:
                print("Usage: python workflow.py --train <registration_zip>")
                return 1
            workflow = WorkflowAutomation()
            deploy_zip = workflow.phase_training(sys.argv[2])
            if deploy_zip:
                print(f"\n✓ Trained models: {deploy_zip}")
                return 0
            return 1
    
    # Interactive mode
    workflow = WorkflowAutomation()
    workflow.run_interactive_workflow()
    return 0


if __name__ == "__main__":
    sys.exit(main())
