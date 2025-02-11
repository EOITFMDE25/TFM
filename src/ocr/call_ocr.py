import pathlib
import os
import json
import tempfile
from PIL import Image

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    print("WARNING: pillow-heif no está instalado. Para HEIC, instálalo con 'pip install pillow-heif'.")

import google.generativeai as genai

# Leer la API Key desde variable de entorno (recomendado)
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("Falta la variable de entorno GEMINI_API_KEY.")
genai.configure(api_key=api_key)

# Selecciona el modelo
model = genai.GenerativeModel('gemini-2.0-flash')

def process_image_file(image_path):
    """
    Convierte la imagen a JPG si no lo está (por ej. HEIC -> JPG).
    Retorna la ruta del archivo (temporal) convertido.
    """
    p = pathlib.Path(image_path)
    if p.suffix.lower() in [".jpg", ".jpeg", ".png"]:
        return str(p)

    try:
        img = Image.open(str(p))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
    except Exception as e:
        print(f"Error abriendo {image_path}: {e}")
        return None

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    tmp_name = tmp.name
    tmp.close()
    img.save(tmp_name, "JPEG")
    return tmp_name

def ocr_image(image_path):
    """
    Sube la imagen a Gemini y obtiene un JSON estructurado con la info del ticket.
    Retorna dict o None en caso de error.
    """
    processed_path = process_image_file(image_path)
    if not processed_path:
        return None

    try:
        file_ref = genai.upload_file(processed_path)

        # Prompt definido en el prompt original (estructura de JSON).
        prompt = """
        Extract the important information from this image of a supermarket receipt.
        Return the data in JSON format, structured as follows:

        {
          "supermarket": "Name of the supermarket",
          "date": "YYYY-MM-DD",
          "time": "HH:MM:SS",
          "location": "Address or city of the supermarket",
          "items": [
            {
              "name": "Product name",
              "quantity": 1,
              "unit_price": 2.99,
              "total_price": 2.99,
              "discount": 0.50,
              "original_price": 3.49
            }
          ],
          "subtotal": 15.99,
          "taxes": [
              {"name": "VAT", "amount": 1.60}
          ],
          "total": 17.59,
          "payment_method": "Card",
          "currency": "EUR"
        }

        If any information is not present, use null as the value.
        Don't include additional text, only JSON.
        """

        response = model.generate_content([prompt, file_ref], stream=False)
        response.resolve()
        text = response.text

        # Extraer el bloque JSON
        start = text.find('{')
        end = text.rfind('}') + 1
        if start == -1 or end == 0:
            print("No se encontró JSON en la respuesta de Gemini.")
            return None
        json_text = text[start:end]
        data = json.loads(json_text)
        return data

    except Exception as e:
        print(f"Ocurrió un error con la API de Gemini: {e}")
        return None
