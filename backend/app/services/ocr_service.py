import pytesseract
from PIL import Image
import pdf2image
import io
import logging
from typing import Optional, Tuple
import numpy as np

# OpenCV é opcional - melhora pré-processamento
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("opencv-python não disponível - pré-processamento de imagem será limitado")

# OCRmyPDF é opcional - pode ter problemas de compatibilidade
try:
    import ocrmypdf
    OCRMYPDF_AVAILABLE = True
except ImportError:
    OCRMYPDF_AVAILABLE = False
    logging.warning("ocrmypdf não disponível - funcionalidade de OCR em PDF será limitada")

logger = logging.getLogger(__name__)


class OCRService:
    """Service for OCR processing using Tesseract and OCRmyPDF."""
    
    def __init__(self):
        self.tesseract_lang = "por"  # Portuguese
        # Configuração otimizada para boletos brasileiros
        self.tesseract_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,/-:R$ '
    
    def _preprocess_image(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Pré-processa imagem para melhorar qualidade do OCR.
        Aplica: escala de cinza, threshold, denoising, contraste.
        """
        if not CV2_AVAILABLE:
            return None
        
        try:
            # Converter bytes para numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return None
            
            # Converter para escala de cinza
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img
            
            # Aplicar threshold (binarização) - melhora muito o OCR
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Reduzir ruído (opcional - pode ser lento)
            try:
                denoised = cv2.fastNlMeansDenoising(thresh, h=10)
            except:
                denoised = thresh  # Fallback se falhar
            
            # Aumentar contraste (CLAHE)
            try:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(denoised)
            except:
                enhanced = denoised  # Fallback se falhar
            
            # Redimensionar se muito pequeno (melhora OCR)
            height, width = enhanced.shape
            if height < 1000:
                scale = 1000 / height
                new_width = int(width * scale)
                new_height = int(height * scale)
                enhanced = cv2.resize(enhanced, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Erro no pré-processamento de imagem: {e}")
            return None
    
    def extract_text_from_image(self, image_bytes: bytes) -> Tuple[str, float]:
        """
        Extract text from image using Tesseract with preprocessing.
        Returns: (text, confidence)
        """
        try:
            # Tentar pré-processar imagem
            preprocessed = self._preprocess_image(image_bytes)
            
            if preprocessed is not None and CV2_AVAILABLE:
                # Usar imagem pré-processada
                image = Image.fromarray(preprocessed)
                logger.info("Usando imagem pré-processada para OCR")
            else:
                # Usar imagem original
                image = Image.open(io.BytesIO(image_bytes))
                logger.info("Usando imagem original para OCR (sem pré-processamento)")
            
            # Extrair texto com configuração otimizada
            data = pytesseract.image_to_data(
                image,
                lang=self.tesseract_lang,
                config=self.tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            text_lines = []
            confidences = []
            
            for i, word in enumerate(data['text']):
                if word.strip():
                    text_lines.append(word)
                    conf = float(data['conf'][i]) if data['conf'][i] != -1 else 0.0
                    confidences.append(conf)
            
            full_text = ' '.join(text_lines)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Log para debug
            logger.info(f"OCR extraiu {len(text_lines)} palavras com confiança média de {avg_confidence:.1f}%")
            
            return full_text, avg_confidence / 100.0  # Normalize to 0-1
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}", exc_info=True)
            return "", 0.0
    
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> Tuple[str, float]:
        """
        Extract text from PDF using OCRmyPDF and Tesseract.
        Returns: (text, confidence)
        """
        try:
            # First, try to extract text directly (if PDF has text layer)
            try:
                images = pdf2image.convert_from_bytes(pdf_bytes)
                text_parts = []
                confidences = []
                
                for image in images:
                    img_bytes = io.BytesIO()
                    image.save(img_bytes, format='PNG')
                    text, conf = self.extract_text_from_image(img_bytes.getvalue())
                    text_parts.append(text)
                    confidences.append(conf)
                
                full_text = '\n'.join(text_parts)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                
                return full_text, avg_confidence
                
            except Exception as e:
                logger.warning(f"Direct PDF extraction failed: {e}")
                # Fallback to OCRmyPDF se disponível
                if OCRMYPDF_AVAILABLE:
                    try:
                        output_pdf = io.BytesIO()
                        ocrmypdf.ocr(io.BytesIO(pdf_bytes), output_pdf, language='por')
                        output_pdf.seek(0)
                    except Exception as ocr_error:
                        logger.error(f"OCRmyPDF também falhou: {ocr_error}")
                        return "", 0.0
                else:
                    logger.warning("OCRmyPDF não disponível, usando apenas Tesseract nas páginas convertidas")
                    return "", 0.0
                
                images = pdf2image.convert_from_bytes(output_pdf.read())
                text_parts = []
                confidences = []
                
                for image in images:
                    img_bytes = io.BytesIO()
                    image.save(img_bytes, format='PNG')
                    text, conf = self.extract_text_from_image(img_bytes.getvalue())
                    text_parts.append(text)
                    confidences.append(conf)
                
                full_text = '\n'.join(text_parts)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                
                return full_text, avg_confidence
                
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return "", 0.0
    
    def extract_text(self, file_bytes: bytes, content_type: str) -> Tuple[str, float]:
        """
        Extract text from file (PDF or image).
        Returns: (text, confidence)
        """
        if content_type.startswith('image/'):
            return self.extract_text_from_image(file_bytes)
        elif content_type == 'application/pdf':
            return self.extract_text_from_pdf(file_bytes)
        else:
            logger.warning(f"Unsupported content type: {content_type}")
            return "", 0.0


ocr_service = OCRService()

