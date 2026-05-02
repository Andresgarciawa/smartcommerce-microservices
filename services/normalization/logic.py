import re
from typing import Optional

class NormalizerLogic:
    @staticmethod
    def format_author(author_str: Optional[str]) -> str:
        if not author_str or author_str.lower() in ["unknown", "n/a"]:
            return "Unknown Author"
        
        # Tomamos el primer autor si vienen varios (separados por coma)
        main_author = author_str.split(',')[0].strip()
        parts = main_author.split()
        
        if len(parts) >= 2:
            # Formato: G. GARCIA MARQUEZ
            initial = f"{parts[0][0].upper()}."
            last_name = " ".join(parts[1:]).upper()
            return f"{initial} {last_name}"
        
        return main_author.upper()

    @staticmethod
    def format_title(title: Optional[str]) -> str:
        if not title: return "Untitled"
        # Capitaliza la primera letra de cada palabra (Title Case)
        return title.strip().title()

    @staticmethod
    def extract_year(date_str: Optional[str]) -> int:
        if not date_str: return 0
        # Busca 4 números seguidos (el año) en cualquier parte del string
        match = re.search(r'\d{4}', date_str)
        return int(match.group()) if match else 0

    @staticmethod
    def clean_description(text: Optional[str]) -> str:
        if not text: return ""
        # Elimina etiquetas HTML como <p> o <b> que vienen de Google Books
        return re.sub(r'<.*?>', '', text).strip()