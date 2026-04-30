from fastapi import FastAPI
from p_models import BookInput, NormalizedOutput
from logic import NormalizerLogic

app = FastAPI(title="Normalization Service")

@app.post("/normalize", response_model=NormalizedOutput)
async def normalize_data(data: BookInput):
    return NormalizedOutput(
        title=NormalizerLogic.format_title(data.title),
        author=NormalizerLogic.format_author(data.author),
        publisher=data.publisher.upper() if data.publisher else "UNKNOWN",
        year=NormalizerLogic.extract_year(data.published_date),
        description=NormalizerLogic.clean_description(data.description),
        cover_url=data.cover_url
    )