import pathlib
import os
import json
import tempfile
from PIL import Image

# Intenta importar pillow_heif para soportar HEIC
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    print("WARNING: pillow-heif no está instalado. Para abrir imágenes HEIC, "
          "instálalo usando 'pip install pillow-heif'.")

import google.generativeai as genai

# Lee la API KEY desde variable de entorno (recomendado),
# o colócala directamente aquí como fallback:
api_key = os.getenv('GEMINI_API_KEY')  # O "GEMINI_API_KEY_XXX"
if not api_key:
    raise ValueError("La variable de entorno GEMINI_API_KEY no está configurada.")

genai.configure(api_key=api_key)

# Modelo de Gemini (puede variar si hay versiones nuevas)
model = genai.GenerativeModel('gemini-2.0-flash')

def process_image_file(image_path):
    """
    Procesa una imagen para asegurarse de que esté en formato JPG o PNG.
    Si la imagen no lo está (por ejemplo, HEIC), la convierte a .jpg en un archivo temporal.
    Retorna la ruta del archivo convertido.
    """
    image_path = pathlib.Path(image_path)
    if image_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
        return str(image_path)
    else:
        try:
            img = Image.open(image_path)
        except Exception as e:
            raise ValueError(f"Error al abrir la imagen {image_path}: {e}")
        # Convertimos a RGB si es RGBA o modo P
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        # Guardamos la imagen convertida en un archivo temporal .jpg
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        temp_file_name = temp_file.name
        temp_file.close()
        img.save(temp_file_name, format="JPEG")
        return temp_file_name

def ocr_image(image_path):
    """
    Realiza OCR usando Gemini Flash 2.0 en la imagen dada.
    Retorna un dict con la información extraída, o None en caso de error.
    """
    try:
        processed_path = process_image_file(image_path)

        # Subimos el archivo a la API de Google generative
        file_ref = genai.upload_file(processed_path)

        # Construimos el prompt.
        # Ajusta si deseas otro formato JSON.
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

        response = model.generate_content(
            [prompt, file_ref],
            stream=False,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        response.resolve()

        # Extraemos solo la parte JSON de la respuesta.
        text = response.text
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            print("No se ha encontrado el bloque JSON en la respuesta de Gemini.")
            print("Respuesta completa:", text)
            return None

        json_text = text[json_start:json_end]
        data = json.loads(json_text)
        return data

    except Exception as e:
        print(f"Error durante el OCR: {e}")
        return None

# Pequeña función de prueba local:
if __name__ == '__main__':
    test_path = "IMG_7833.HEIC"
    result = ocr_image(test_path)
    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("No se pudo extraer un JSON válido.")
