import cv2
import numpy as np
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import os

class OCRHandler:
    """OCR para PDFs escaneados - fallback quando pdfplumber falha"""
    
    def __init__(self):
        # Tenta configurar caminho do tesseract se estiver no Windows e nao no PATH
        # Mas assume que está no PATH ou configurado externamente para simplificar
        pass
    
    def pdf_para_texto(self, caminho_pdf: str, dpi: int = 300) -> str:
        """Converte PDF → Imagem → OCR"""
        texto_completo = ""
        try:
            doc = fitz.open(caminho_pdf)
            # Processar apenas a primeira página para performance (guias geralmente são 1 pag)
            if len(doc) > 0:
                pagina = doc[0]
                
                # Renderizar em alta resolução
                matriz = fitz.Matrix(dpi/72, dpi/72)
                pix = pagina.get_pixmap(matrix=matriz)
                
                # Converter para numpy array
                img_bytes = pix.tobytes("png")
                nparr = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # Pré-processamento
                img_processada = self._preprocessar_imagem(img)
                
                # OCR em português
                texto = pytesseract.image_to_string(
                    img_processada,
                    lang='por',
                    config='--oem 3 --psm 6'
                )
                texto_completo = texto
                
            doc.close()
            return texto_completo
            
        except Exception as e:
            print(f"Erro OCR: {e}")
            return ""
    
    def _preprocessar_imagem(self, img):
        """Melhora qualidade para OCR"""
        # Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Threshold adaptativo
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Remover ruído
        denoised = cv2.fastNlMeansDenoising(thresh, h=10)
        
        return denoised
