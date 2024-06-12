import os
import time
import hashlib
import stat
from pyads import ADS

def calculate_directory_size(path):
    total_size = 0
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            total_size += calculate_directory_size(entry.path)
        else:
            total_size += entry.stat(follow_symlinks=False).st_size
    return total_size

def get_file_attributes(path):
    stats = os.stat(path)
    attrs = stats.st_file_attributes
    attrs_to_test = [
            (stat.FILE_ATTRIBUTE_ARCHIVE, 'a'), # Архивный файл
            (stat.FILE_ATTRIBUTE_READONLY, 'r'), # Файл только для чтения
            (stat.FILE_ATTRIBUTE_SYSTEM, 's'), # Системный файл
            (stat.FILE_ATTRIBUTE_HIDDEN, 'h'), # Скрытый файл
            (stat.FILE_ATTRIBUTE_NOT_CONTENT_INDEXED, 'i') # Файл не индексируется для поиска
        ]
    return ''.join([ch if attrs & attr else "-" for attr, ch in attrs_to_test])

def get_last_modified(path):
    last_modified_timestamp = os.path.getmtime(path)
    last_modified_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_modified_timestamp))
    return last_modified_time

def list_ads_files(file_path):
    ads_files = []
    try:
        ads_instance = ADS(file_path)
        if ads_instance.has_streams():
            for stream in ads_instance:
                stream_name = ads_instance.full_filename(stream)
                stream_size = len(ads_instance.get_stream_content(stream))
                ads_files.append((stream_name, stream_size))
    except Exception as e:
        print(f"Error accessing ADS: {e}")
    return ads_files

def calculate_file_hash(file_path, chunk_size=8192):
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hash_sha256.update(chunk)
    except Exception as e:
        print(f"Error calculating hash: {e}")
        return None
    return hash_sha256.hexdigest()

def compare_directories(dir1, dir2):
    entries1 = {e.name: e for e in os.scandir(dir1)}
    entries2 = {e.name: e for e in os.scandir(dir2)}

    files1 = {f: {
        'size': os.path.getsize(os.path.join(dir1, f)),
        'attributes': get_file_attributes(os.path.join(dir1, f)),
        'last_modified': get_last_modified(os.path.join(dir1, f)),
        'ads': list_ads_files(os.path.join(dir1, f)),
        'hash': calculate_file_hash(os.path.join(dir1, f))
    } for f in entries1 if not entries1[f].is_dir()}

    files2 = {f: {
        'size': os.path.getsize(os.path.join(dir2, f)),
        'attributes': get_file_attributes(os.path.join(dir2, f)),
        'last_modified': get_last_modified(os.path.join(dir2, f)),
        'ads': list_ads_files(os.path.join(dir2, f)),
        'hash': calculate_file_hash(os.path.join(dir2, f))
    } for f in entries2 if not entries2[f].is_dir()}

    dirs1 = {d: calculate_directory_size(os.path.join(dir1, d)) for d in entries1 if entries1[d].is_dir()}
    dirs2 = {d: calculate_directory_size(os.path.join(dir2, d)) for d in entries2 if entries2[d].is_dir()}

    size_diff_files = {
        f: {
            'size': files1[f]['size'] != files2[f]['size'],
            'attributes': files1[f]['attributes'] != files2[f]['attributes'],
            'last_modified': files1[f]['last_modified'] != files2[f]['last_modified'],
            'ads': files1[f]['ads'] != files2[f]['ads'],
            'hash': files1[f]['hash'] != files2[f]['hash']
        }
        for f in files1 if f in files2 and (
            files1[f]['size'] != files2[f]['size'] or
            files1[f]['attributes'] != files2[f]['attributes'] or
            files1[f]['last_modified'] != files2[f]['last_modified'] or
            files1[f]['ads'] != files2[f]['ads'] or
            files1[f]['hash'] != files2[f]['hash']
        )
    }

    size_diff_dirs = {d for d in dirs1 if d in dirs2 and dirs1[d] != dirs2[d]}
    only_in1_files = set(files1.keys()) - set(files2.keys())
    only_in2_files = set(files2.keys()) - set(files1.keys())
    only_in1_dirs = set(dirs1.keys()) - set(dirs2.keys())
    only_in2_dirs = set(dirs2.keys()) - set(dirs1.keys())

    return size_diff_files, only_in1_files, only_in2_files, only_in1_dirs, only_in2_dirs, size_diff_dirs

