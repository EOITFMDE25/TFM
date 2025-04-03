# tests/test_ocr.py

import pytest
import json
from src.ocr.call_ocr import ocr_image

# Test de ejemplo que verifica que la función no rompe al recibir un archivo inexistente
def test_ocr_non_existent_file():
    with pytest.raises(ValueError):
        # Debe lanzar excepción al no encontrar la imagen
        ocr_image("ruta/que/no/existe.HEIC")

# Test para chequear un mock local
def test_ocr_mock(mocker):
    """
    Supongamos que no queremos llamar a la API real,
    sino simular la respuesta del OCR.
    """
    dummy_response = {
        "supermarket": "MockMarket",
        "date": "2025-02-05",
        "time": "12:00:00",
        "items": [],
        "total": 10.0,
    }
    # Usamos el mocker de pytest para fingir que `ocr_image` hace algo y retorna 'dummy_response'
    # (Si preferimos, podemos mockear la llamada interna a la API de Geminis)
    mocker.patch("src.ocr.call_ocr.ocr_image", return_value=dummy_response)

    result = ocr_image("cualquier_imagen.jpg")
    assert result["supermarket"] == "MockMarket"
    assert result["total"] == 10.0
