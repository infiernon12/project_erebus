import os
import urllib.request
import sys

# Define model URLs and destinations
MODELS = {
    "RWKV-x060-World-1B6-v2.1-20240328-ctx4096.pth": "https://huggingface.co/BlinkDL/rwkv-6-world/resolve/main/RWKV-x060-World-1B6-v2.1-20240328-ctx4096.pth",
    "Qwen2.5-Coder-1.5B-Instruct-GGUF.gguf": "https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"
}

MODELS_DIR = "models"

def progress_bar(block_num, block_size, total_size):
    read_so_far = block_num * block_size
    if total_size > 0:
        percent = min(100, read_so_far * 100 // total_size)
        sys.stdout.write(f"\rDownloading... {percent}% ({read_so_far // (1024*1024)}MB / {total_size // (1024*1024)}MB)")
        sys.stdout.flush()
    else:
        sys.stdout.write(f"\rDownloading... {read_so_far // (1024*1024)}MB")
        sys.stdout.flush()

def download_all():
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    for filename, url in MODELS.items():
        dest_path = os.path.join(MODELS_DIR, filename)
        if os.path.exists(dest_path):
            print(f"Файл {filename} уже существует, пропускаем.")
            continue
            
        print(f"\nЗагрузка {filename} из {url}...")
        try:
            urllib.request.urlretrieve(url, dest_path, progress_bar)
            print(f"\nУспешно скачан: {filename}")
        except Exception as e:
            print(f"\nОшибка при загрузке {filename}: {e}")
            if os.path.exists(dest_path):
                os.remove(dest_path)

if __name__ == "__main__":
    download_all()
