import subprocess
import sys
import os
import time

def install_pyinstaller():
    print("Installing PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build():
    # 1. Install PyInstaller if missing
    try:
        import PyInstaller
    except ImportError:
        install_pyinstaller()

    print("--- BUILDING WITH PYINSTALLER ---")
    print("Reason: Nuitka freezes on Python 3.14 with PyMuPDF.")
    
    # 2. Clean previous
    if os.path.exists('dist'):
        import shutil
        try:
            shutil.rmtree('dist')
        except:
            pass

    # 3. Define arguments
    # Note: We use --collect-all for libraries that often have hidden imports or data assets
    args = [
        "main.py",
        "--name=RecalGuias",
        "--onefile",
        "--windowed", # Start hidden (no console)
        "--clean",
        "--noconfirm",
        
        # Embedded Assets (Internal)
        # However, our security_core looks for them next to the exe, 
        # so embedding them here just ensures they exist for fallback, 
        # but the code expects external files for License/DB.
        # We'll just rely on the external files as per previous instructions.
        # But for 'customtkinter', we need its internal data.
        
        "--collect-all=customtkinter",
        "--collect-all=tkinterdnd2",
        "--collect-all=pymupdf",
        
        # If we wanted to Embed the public key strictly inside:
        # "--add-data=public_key.pem;." 
        # But we will stick to the 'external' strategy for simplicity and consistency with previous turn.
    ]
    
    print(f"Running PyInstaller with args: {args}")
    
    # 4. Run
    from PyInstaller.__main__ import run
    try:
        run(args)
        print("\nBUILD SUCCESSFUL! Executable: 'dist/RecalGuias.exe'")
    except Exception as e:
        print(f"\nBUILD FAILED: {e}")

if __name__ == "__main__":
    build()
