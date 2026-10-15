import os
import cloudinary
import cloudinary.api
from cloudinary.search import Search

class CloudinaryService:
    def __init__(self):
        self.cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
        self.api_key = os.getenv("CLOUDINARY_API_KEY")
        self.api_secret = os.getenv("CLOUDINARY_API_SECRET")

        if not self.cloud_name or not self.api_key or not self.api_secret:
            raise RuntimeError("Configure CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY e CLOUDINARY_API_SECRET no arquivo .env.")

        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True
        )

    def list_folder_or_prefix(self, prefix=""):
        """Busca todas as mídias da pasta/prefixo usando o Search API do Cloudinary."""
        prefix = prefix.strip().strip("/")
        
        # Se não informar prefixo, busca tudo. Se informar, busca por pasta ou prefixo do public_id
        if prefix:
            expression = f"folder:{prefix}/* OR public_id:{prefix}/* OR public_id:{prefix}*"
        else:
            expression = "resource_type:image OR resource_type:video"

        all_resources = []
        next_cursor = None

        while True:
            search_query = Search()\
                .expression(expression)\
                .max_results(500)
            
            if next_cursor:
                search_query = search_query.next_cursor(next_cursor)
                
            result = search_query.execute()
            resources = result.get("resources", [])
            all_resources.extend(resources)

            next_cursor = result.get("next_cursor")
            if not next_cursor:
                break

        return all_resources