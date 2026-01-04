#!/usr/bin/env python3
"""Script to upload cookies.json to Render server via SSH."""
import subprocess
import json
import sys
from pathlib import Path

# Render SSH connection details
SSH_HOST = "srv-d5crfrtactks73csled0@ssh.oregon.render.com"
REMOTE_PATH = "/app/data/cookies.json"
LOCAL_COOKIES = Path("cookies.json")

def upload_cookies():
    """Upload cookies.json to Render server."""
    if not LOCAL_COOKIES.exists():
        print(f"❌ Error: {LOCAL_COOKIES} not found!")
        return False
    
    # Read local cookies
    try:
        with open(LOCAL_COOKIES, 'r', encoding='utf-8') as f:
            cookies_data = json.load(f)
        print(f"[OK] Read {len(cookies_data)} cookies from {LOCAL_COOKIES}")
    except Exception as e:
        print(f"[ERROR] Error reading cookies.json: {e}")
        return False
    
    # Create the JSON content
    cookies_json = json.dumps(cookies_data, indent=2, ensure_ascii=False)
    
    # Method 1: Try using SSH with heredoc
    print(f"\n[UPLOAD] Uploading cookies to {SSH_HOST}:{REMOTE_PATH}")
    print("=" * 60)
    
    # Create SSH command with heredoc
    ssh_command = f'''ssh {SSH_HOST} << 'EOF'
mkdir -p /app/data
cat > {REMOTE_PATH} << 'COOKIES_EOF'
{cookies_json}
COOKIES_EOF
cat {REMOTE_PATH} | wc -l
ls -lh {REMOTE_PATH}
EOF'''
    
    try:
        result = subprocess.run(
            ssh_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("[SUCCESS] Cookies uploaded successfully!")
            print(result.stdout)
            return True
        else:
            print("[ERROR] Error uploading cookies:")
            print(result.stderr)
            print("\n" + "=" * 60)
            print("[INFO] Manual upload instructions:")
            print("=" * 60)
            print(f"1. Connect: ssh {SSH_HOST}")
            print(f"2. Run: mkdir -p /app/data")
            print(f"3. Create file: nano {REMOTE_PATH}")
            print("4. Paste the contents of cookies.json")
            print("5. Save (Ctrl+O, Enter, Ctrl+X)")
            print("=" * 60)
            return False
            
    except subprocess.TimeoutExpired:
        print("[ERROR] SSH connection timeout")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        print("\n" + "=" * 60)
        print("[INFO] Please upload cookies manually via Render Dashboard:")
        print("=" * 60)
        print("1. Go to: https://dashboard.render.com/web/srv-d5crfrtactks73csled0")
        print("2. Click 'Shell' in the left menu")
        print(f"3. Run: mkdir -p /app/data && nano {REMOTE_PATH}")
        print("4. Paste cookies.json content and save")
        print("=" * 60)
        return False

if __name__ == "__main__":
    print("Render Cookies Upload Script")
    print("=" * 60)
    
    if upload_cookies():
        print("\n[SUCCESS] Done! Restart the service in Render Dashboard if needed.")
        sys.exit(0)
    else:
        print("\n[WARNING] Upload failed. Please follow manual instructions above.")
        sys.exit(1)

