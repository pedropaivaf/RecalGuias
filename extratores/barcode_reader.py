import cv2
import numpy as np
from pyzbar.pyzbar import decode, ZBarSymbol
import fitz

class BarcodeReader:
    """Lê código de barras Interleaved 2 of 5 de PDFs"""
    
    def ler_codigo_pdf(self, caminho_pdf: str) -> str:
        """Extrai código de barras do PDF"""
        try:
            doc = fitz.open(caminho_pdf)
            
            # Renderizar em alta resolução para barcode
            matriz = fitz.Matrix(4, 4)  # 4x zoom
            pix = doc[0].get_pixmap(matrix=matriz)
            
            # Converter para opencv
            img_bytes = pix.tobytes("png")
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            
            doc.close()
            
            # Threshold para melhorar contraste
            _, thresh = cv2.threshold(img, 0, 255, 
                                     cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Tentar ler código
            codigos = decode(thresh, symbols=[ZBarSymbol.I25])
            if codigos:
                return codigos[0].data.decode('utf-8')
            
            # Fallback: inverter imagem (barcode branco em fundo preto)
            inv = cv2.bitwise_not(thresh)
            codigos = decode(inv, symbols=[ZBarSymbol.I25])
            
            return codigos[0].data.decode('utf-8') if codigos else None
            
        except Exception as e:
            print(f"Erro Barcode: {e}")
            return None
