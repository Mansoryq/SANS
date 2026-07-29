import os
import logging
from typing import Optional
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)

class SupabaseStorageService:
    def __init__(self):
        self.client: Optional[Client] = None
        self.bucket_name = "sans_assets"
        
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                logger.info("Supabase Storage client initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
        else:
            logger.warning("Supabase credentials not found. Storage service disabled.")

    def upload_file(self, file_path: str, file_name: str, content_type: str = "application/octet-stream") -> Optional[str]:
        if not self.client:
            logger.warning("Upload skipped: Supabase client not initialized.")
            return None
            
        try:
            with open(file_path, 'rb') as f:
                res = self.client.storage.from_(self.bucket_name).upload(
                    path=file_name,
                    file=f,
                    file_options={"content-type": content_type}
                )
            
            # Return public URL if upload succeeded
            return self.client.storage.from_(self.bucket_name).get_public_url(file_name)
        except Exception as e:
            logger.error(f"Supabase upload failed: {e}")
            return None

storage_service = SupabaseStorageService()
