from pyads import ADS

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