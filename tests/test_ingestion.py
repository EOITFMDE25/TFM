# tests/test_ingestion.py

import pytest
import os
from pymongo.errors import ConnectionFailure
from src.ingestion.image_ingestion import ImageIngestion

def test_mongo_connection_failure():
    """
    Probar que se maneja correctamente cuando la URI de Mongo es inválida.
    """
    with pytest.raises(ConnectionFailure):
        ingestion = ImageIngestion("mongodb://usuario_incorrecto:pass@localhost:9999")
        ingestion.save_image_to_mongo("tests/data/test_img.jpg")

def test_image_ingestion_valid(mocker, tmp_path):
    """
    Testea guardar una imagen simulada usando una URI de Mongo mock.
    """
    # Creamos un archivo temporal fingiendo una imagen
    test_file = tmp_path / "fake.jpg"
    test_file.write_bytes(b"fake_image_data")

    # Mock de la clase que evite la conexión real a Mongo
    mock_fs = mocker.Mock()
    mocker.patch("gridfs.GridFS", return_value=mock_fs)

    ingestion = ImageIngestion("mongodb://fake:fake@localhost:27017")
    file_id = ingestion.save_image_to_mongo(str(test_file), meta={"test": True})

    # Verificar que se llamó a fs.put
    mock_fs.put.assert_called_once()
    assert file_id is not None
