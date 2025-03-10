# src/ocr/call_ocr.py
import pathlib
import google.generativeai as genai
import os
import json
import tempfile
from PIL import Image
import pillow_heif  # Añade esta línea para importar pillow_heif

# Configura la API key desde las variables de entorno
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("La variable de entorno GEMINI_API_KEY no está configurada")
genai.configure(api_key=api_key)

# Selecciona el modelo
model = genai.GenerativeModel('gemini-2.0-flash')

def process_image_file(image_path):
    """
    Procesa una imagen para asegurarse de que esté en formato JPG o PNG.
    Si la imagen no lo está (por ejemplo, HEIC), la abre, la convierte a RGB (si es necesario)
    y la guarda en un archivo temporal en formato JPEG.
    
    Args:
        image_path: Ruta a la imagen (str o pathlib.Path).
    
    Returns:
        La ruta al archivo procesado (formato JPG).
    """
    print(f"[OCR] Procesando archivo: {image_path}")
    image_path = pathlib.Path(image_path)
    if image_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
        return str(image_path)
    else:
        try:
            pillow_heif.register_heif_opener()  # Registra soporte para HEIC
            img = Image.open(image_path)
            print(f"[OCR] Imagen abierta: formato={img.format}, tamaño={img.size}, modo={img.mode}")
        except Exception as e:
            print(f"[OCR] Error al abrir la imagen {image_path}: {e}")
            raise
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        temp_file_name = temp_file.name
        temp_file.close()
        img.save(temp_file_name, format="JPEG")
        print(f"[OCR] Imagen convertida y guardada en: {temp_file_name}")
        return temp_file_name

def ocr_image(image_path):
    """
    Realiza OCR en una imagen usando Gemini mediante la API de archivos.
    
    Args:
        image_path: Ruta a la imagen (str o pathlib.Path).
    
    Returns:
        Un diccionario JSON con la información extraída, o None si ocurre algún error.
    """
    try:
        print(f"[OCR] Iniciando OCR para: {image_path}")
        processed_path = process_image_file(image_path)
        
        file_ref = genai.upload_file(processed_path)
        
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
        
        If any information is not present in the image, use "null" as the value.
        """
        
        response = model.generate_content([prompt, file_ref], stream=False)
        response.resolve()
        
        print(f"[OCR] Respuesta cruda de Gemini: {response.text}")
        json_start = response.text.find('{')
        json_end = response.text.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            print("[OCR] No se encontró JSON en la respuesta de Gemini")
            return None
        json_text = response.text[json_start:json_end]
        data = json.loads(json_text)
        print(f"[OCR] JSON procesado: {json.dumps(data, indent=2)}")
        return data

    except Exception as e:
        print(f"[OCR] Error durante el procesamiento de la imagen: {e}")
        return None