import pytesseract
from PIL import Image
import pdf2image
import io
import logging
from typing import Optional, Tuple

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
    
    def extract_text_from_image(self, image_bytes: bytes) -> Tuple[str, float]:
        """
        Extract text from image using Tesseract.
        Returns: (text, confidence)
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            data = pytesseract.image_to_data(image, lang=self.tesseract_lang, output_type=pytesseract.Output.DICT)
            
            text_lines = []
            confidences = []
            
            for i, word in enumerate(data['text']):
                if word.strip():
                    text_lines.append(word)
                    conf = float(data['conf'][i]) if data['conf'][i] != -1 else 0.0
                    confidences.append(conf)
            
            full_text = ' '.join(text_lines)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return full_text, avg_confidence / 100.0  # Normalize to 0-1
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
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

