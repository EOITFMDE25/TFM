# /src/ocr/call_ocr.py
import pathlib
import google.generativeai as genai
import os
import json
import tempfile
from PIL import Image
import pillow_heif

# Modelos de Gemini
model = genai.GenerativeModel('gemini-2.0-flash')
model_cat = genai.GenerativeModel('gemini-2.0-flash')

def process_image_file(image_data):
    """
    Procesa datos de imagen (bytes) para asegurar formato JPG.
    Si es HEIC, lo convierte a JPG. Guarda en archivo temporal.

    Args:
        image_data: Datos binarios de la imagen (BytesIO object).

    Returns:
        Ruta al archivo procesado (formato JPG), o None si hay error.
    """
    pillow_heif.register_heif_opener()  # Registrar HEIF al inicio
    image_data.seek(0)
    try:
        img = Image.open(image_data)
        print(f"[OCR] Imagen abierta: formato={img.format}, tamaño={img.size}, modo={img.mode}")

        if img.format not in ("JPEG", "PNG"):
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_file_name = temp_file.name
                img.save(temp_file_name, "JPEG")
                print(f"[OCR] Imagen convertida a JPEG: {temp_file_name}")
                return temp_file_name
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{img.format.lower()}") as temp_file:
                temp_file_name = temp_file.name
                img.save(temp_file_name)
                print(f"[OCR] Imagen guardada en temporal: {temp_file_name}")
                return temp_file_name

    except Exception as e:
        print(f"[OCR] Error al procesar la imagen: {e}")
        return None

def ocr_image(image_path):
    """
    Realiza OCR en una imagen usando Gemini.

    Args:
        image_path: Ruta a la imagen (str).

    Returns:
        Diccionario JSON con la información, o None si hay error.
    """
    try:
        print(f"[OCR] Iniciando OCR para: {image_path}")
        file_ref = genai.upload_file(image_path)

        prompt = """
        Extrae la información importante de esta imagen de un ticket de supermercado.
        Devuelve los datos en formato JSON, estructurados de la siguiente manera:

        {
          "supermarket": "Nombre del supermercado",
          "date": "AAAA-MM-DD",
          "time": "HH:MM:SS",
          "location": "Dirección o ciudad del supermercado",
          "items": [
            {
              "name": "Nombre del producto",
              "quantity": 1,
              "unit_price": 2.99,
              "total_price": 2.99,
              "discount": 0.50,
              "original_price": 3.49
            }
          ],
          "subtotal": 15.99,
          "taxes": [
              {"name": "IVA", "amount": 1.60}
          ],
          "total": 17.59,
          "payment_method": "Tarjeta",
          "currency": "EUR"
        }

        Si alguna información no está presente, usa "null". Devuelve SOLO el JSON.
        """
        response = model.generate_content([prompt, file_ref], stream=False)
        response.resolve()

        print(f"[OCR] Respuesta cruda de Gemini: {response.text}")
        json_text = response.text
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError:
            json_start = json_text.find('{')
            json_end = json_text.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_text = json_text[json_start:json_end]
                data = json.loads(json_text)
            else:
                print("[OCR] No se encontró JSON válido")
                return None

        print(f"[OCR] JSON procesado: {json.dumps(data, indent=2)}")
        return data

    except Exception as e:
        print(f"[OCR] Error durante el OCR: {e}")
        return None

def categorize_product(product_name):
    """
    Infiera la categoría de un producto usando Gemini.

    Args:
        product_name: Nombre del producto.

    Returns:
        Categoría inferida (str).
    """
    prompt = f"""
    Categoriza el siguiente producto de supermercado: "{product_name}".
    Las categorías posibles son (y solo estas):
    - "Comida"
    - "Bebida"
    - "Lácteos"
    - "Carne"
    - "Pescado"
    - "Fruta"
    - "Verdura"
    - "Panadería"
    - "Congelados"
    - "Limpieza"
    - "Higiene"
    - "Mascotas"
    - "Bebé"
    - "Otros"

    Responde únicamente con el nombre de la categoría, sin explicaciones adicionales.
    """
    try:
        response = model_cat.generate_content(prompt, stream=False)
        response.resolve()
        category = response.text.strip()
        # Validación de la categoría
        valid_categories = [
            "Comida", "Bebida", "Lácteos", "Carne", "Pescado", "Fruta",
            "Verdura", "Panadería", "Congelados", "Limpieza", "Higiene",
            "Mascotas", "Bebé", "Otros"
        ]
        if category not in valid_categories:
            print(f"[Categorización] Categoría inválida: {category}. Se usará 'Otros'.")
            category = "Otros"
        return category
    except Exception as e:
        print(f"[Categorización] Error al categorizar '{product_name}': {e}")
        return "Otros"  # Categoría por defecto en caso de error