"""Helper script to download EdgeDriver manually."""
import os
import requests
import zipfile
import subprocess
import re
import shutil
from pathlib import Path


def get_edge_version():
    """Get installed Edge version."""
    edge_paths = [
        os.path.join(os.environ.get('ProgramFiles', ''), 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
        os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
    ]
    
    for edge_path in edge_paths:
        if os.path.exists(edge_path):
            try:
                result = subprocess.run([edge_path, '--version'], capture_output=True, text=True, timeout=5)
                version_match = re.search(r'(\d+)\.(\d+)\.(\d+)\.(\d+)', result.stdout)
                if version_match:
                    major_version = int(version_match.group(1))
                    return major_version, version_match.group(0)
            except:
                pass
    
    return None, None


def download_edgedriver(version=None):
    """Download EdgeDriver for the specified version or auto-detect."""
    print("=" * 60)
    print("EdgeDriver Downloader")
    print("=" * 60)
    print()
    
    if not version:
        major_version, full_version = get_edge_version()
        if major_version:
            print(f"✅ Обнаружена версия Edge: {full_version}")
            print(f"   Скачивание драйвера для версии {major_version}...")
        else:
            print("⚠️  Не удалось определить версию Edge автоматически")
            version_input = input("Введите версию Edge (например, 120): ")
            try:
                major_version = int(version_input)
            except:
                print("❌ Неверный формат версии")
                return False
    else:
        major_version = version
    
    # Download from Microsoft
    base_url = f"https://msedgedriver.azureedge.net/{major_version}.0.0.0/edgedriver_win64.zip"
    
    print(f"📥 Скачивание с: {base_url}")
    
    try:
        response = requests.get(base_url, stream=True, timeout=30)
        response.raise_for_status()
        
        zip_path = Path("edgedriver_temp.zip")
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("✅ Загрузка завершена")
        print("📦 Распаковка...")
        
        # Extract
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall('.')
        
        # Remove zip
        zip_path.unlink()
        
        # Check if extracted
        driver_path = Path('msedgedriver.exe')
        if driver_path.exists():
            print(f"✅ EdgeDriver успешно установлен: {driver_path.absolute()}")
            print()
            print("Теперь вы можете запустить: python save_cookies.py")
            return True
        else:
            print("❌ Файл msedgedriver.exe не найден после распаковки")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при загрузке: {e}")
        print(f"\n💡 Попробуйте скачать вручную:")
        print(f"   https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


if __name__ == '__main__':
    import sys
    version = None
    if len(sys.argv) > 1:
        try:
            version = int(sys.argv[1])
        except:
            print("Использование: python download_edgedriver.py [версия]")
            sys.exit(1)
    
    success = download_edgedriver(version)
    sys.exit(0 if success else 1)

