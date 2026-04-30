import uuid
import httpx
import asyncio

async def test():
    base_catalog = "http://catalog-service:8001"
    base_enrich  = "http://localhost:8000"
    unique_name = f"Ficcion-{uuid.uuid4().hex[:6]}"

    async with httpx.AsyncClient(timeout=40) as client:
        # 1. Crear categoria con nombre unico
        r = await client.post(f"{base_catalog}/api/catalog/categories",
                              json={"name": unique_name, "description": ""})
        cat = r.json()
        print("Cat ID:", cat["id"])

        # 2. Crear libro
        r2 = await client.post(f"{base_catalog}/api/catalog/books", json={
            "title": "The Great Gatsby",
            "author": "F. Scott Fitzgerald",
            "publisher": "Scribner",
            "publication_year": 1925,
            "isbn": "9780743273565",
            "category_id": cat["id"]
        })
        book = r2.json()
        print("Book ID:", book["id"])
        print("Enriched inicial:", book["enriched_flag"])

        # 3. Llamar al enrichment con book_id
        book_id = book["id"]
        r3 = await client.post(
            f"{base_enrich}/enrichment/process?book_id={book_id}",
            json={"book_reference": "9780743273565"}
        )
        enrich = r3.json()
        print("Source:", enrich["metadata_json"]["source"])
        print("Titulo normalizado:", enrich["normalized_title"])

        # 4. Verificar el libro en el Catalog
        r4 = await client.get(f"{base_catalog}/api/catalog/books/{book_id}")
        updated = r4.json()
        print("=== Catalog DESPUES del enriquecimiento ===")
        print("Enrichment status:", updated.get("enrichment_status"))
        print("Enriched flag:    ", updated.get("enriched_flag"))
        print("Cover URL:        ", updated.get("cover_url", "")[:60])
        print("Source provider:  ", updated.get("source_provider"))

asyncio.run(test())
