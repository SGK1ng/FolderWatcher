import os
import shutil
import tempfile
import zipfile
from ads import list_ads_files

def create_snapshot(directory, use_ads):
    snapshot_dir = tempfile.mkdtemp()

    for root, dirs, files in os.walk(directory):
        for dir_name in dirs:
            src_dir = os.path.join(root, dir_name)
            rel_path = os.path.relpath(src_dir, directory)
            dest_dir = os.path.join(snapshot_dir, rel_path)
            os.makedirs(dest_dir, exist_ok=True)

        for file_name in files:
            src_file = os.path.join(root, file_name)
            rel_path = os.path.relpath(src_file, directory)
            dest_file = os.path.join(snapshot_dir, rel_path)
            shutil.copy2(src_file, dest_file)
            
            if use_ads:
                ads_files = list_ads_files(src_file)
                for ads_file, ads_size in ads_files:
                    ads_rel_path = os.path.relpath(ads_file, directory)
                    ads_dest_file = os.path.join(snapshot_dir, ads_rel_path)
                    shutil.copy2(ads_file, ads_dest_file)

    snapshot_zip = tempfile.mktemp(suffix='.zip')
    shutil.make_archive(snapshot_zip.replace('.zip', ''), 'zip', snapshot_dir)

    shutil.rmtree(snapshot_dir)

    return snapshot_zip

def save_snapshot(snapshot_zip, filepath):
    shutil.move(snapshot_zip, filepath)

def load_snapshot(filepath, target_directory):
    with zipfile.ZipFile(filepath, 'r') as zip_ref:
        zip_ref.extractall(target_directory)
