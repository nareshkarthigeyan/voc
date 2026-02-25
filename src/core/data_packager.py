import os
import shutil
import zipfile
from datetime import datetime

class DataPackager:
    def __init__(self, export_dir="data_exports"):
        self.export_dir = export_dir
        os.makedirs(self.export_dir, exist_ok=True)

    def create_registration_package(self):
        """
        Packages current registration data (SQL db and CSV) for transfer.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"registration_{timestamp}.zip"
        zip_path = os.path.join(self.export_dir, zip_filename)
        
        # Files to include
        files_to_zip = []
        if os.path.exists("data/voc_biometrics.db"):
            files_to_zip.append("data/voc_biometrics.db")
        if os.path.exists("voc_data_curated.csv"):
            files_to_zip.append("voc_data_curated.csv")
            
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in files_to_zip:
                if os.path.exists(file):
                    zipf.write(file, os.path.basename(file))
                    
        return os.path.abspath(zip_path)
