import easyocr
import logging
import ssl
import certifi

# Fix for macOS SSL certificate verify failed
# EasyOCR uses urllib to download models, which often fails on macOS due to missing certs.
try:
    # Set default SSL context to use certifi's bundle
    default_context = ssl.create_default_context(cafile=certifi.where())
    ssl._create_default_https_context = lambda: default_context
except Exception as e:
    logging.warning(f"Could not apply SSL certificate fix: {e}")

# Initialize the reader once to avoid reloading the model on every request
# 'ru' for Russian, 'en' for English
try:
    reader = easyocr.Reader(['ru', 'en'], gpu=False) # Set gpu=True if you have CUDA
except Exception as e:
    logging.error(f"Error initializing EasyOCR: {e}")
    reader = None

def text_from_image(image_path):
    """
    Reads text from the image at the given path.
    Returns a list of detected text strings.
    """
    if reader is None:
        return ["OCR System not initialized."]
    
    try:
        # detail=0 returns just the text list
        result = reader.readtext(image_path, detail=0)
        return result
    except Exception as e:
        logging.error(f"Error reading text from image: {e}")
        return []