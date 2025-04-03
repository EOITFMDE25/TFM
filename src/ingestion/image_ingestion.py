# src/ingestion/image_ingestion.py
import gridfs
from pymongo import MongoClient
from typing import Optional

class ImageIngestion:
    def __init__(self, mongo_uri: str, db_name: str = "tickets_db"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.fs = gridfs.GridFS(self.db)

    def save_image_to_mongo(self, image_path: str, meta: Optional[dict] = None) -> str:
        """
        Guarda la imagen en GridFS y retorna el ID.
        meta puede incluir campos como 'user_id', 'timestamp', etc.
        """
        with open(image_path, 'rb') as f:
            file_data = f.read()
        metadata = meta if meta else {}
        file_id = self.fs.put(file_data, filename=image_path, **metadata)
        return str(file_id)
