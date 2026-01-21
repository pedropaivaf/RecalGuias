import PyInstaller.__main__
import os
import shutil

def build():
    # Limpar builds anteriores
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    # Configuração PyInstaller
    PyInstaller.__main__.run([
        'main.py',
        '--name=RecalculoGuias',
        '--onefile',
        '--windowed',  # Sem console
        '--add-data=database:database',
        '--add-data=assets:assets',
        # Dependências hidden por segurança
        '--hidden-import=pdfplumber',
        '--hidden-import=pytesseract',
        '--hidden-import=cv2',
        '--hidden-import=pyzbar',
        '--hidden-import=reportlab',
        '--collect-all=pdfplumber',
        '--collect-all=reportlab',
    ])
    
    print("\n✅ Executável criado em: dist/RecalculoGuias.exe")

if __name__ == '__main__':
    build()
