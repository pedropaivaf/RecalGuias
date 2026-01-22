import os
import sys
import subprocess

def build():
    print("--- BUILDING WITH NUITKA ---")
    
    # Clean previous
    if os.path.exists('dist'):
        print("Cleaning dist...")
        # os.rmdir('dist') # Careful with rmdir
        
    cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile", 
        "--mingw64",
        "--enable-plugin=tk-inter",
        "--include-package-data=customtkinter",
        "--include-package-data=tkinterdnd2",
        "--windows-disable-console",
        "--include-data-dir=database=database",
        "--include-data-file=license.lic=license.lic", 
        "--include-data-file=public_key.pem=public_key.pem",
        "--include-data-dir=assets=assets",
        "--windows-icon-from-ico=assets/icon.ico",
        "--output-dir=dist",
        "--remove-output",
        "main.py"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
        print("\nBUILD SUCCESSFUL! Check 'dist/main.dist'")
    except subprocess.CalledProcessError as e:
        print(f"\nBUILD FAILED: {e}")

if __name__ == "__main__":
    build()
