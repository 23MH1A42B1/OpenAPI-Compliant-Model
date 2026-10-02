from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="Model Inference API",
    version="1.0.0",
    description="A simple API for text classification inference.",
)


class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text string for inference")


class PredictResponse(BaseModel):
    label: str = Field(..., description="Predicted label")
    score: float = Field(..., description="Confidence score")


class HealthResponse(BaseModel):
    status: str = Field("ok", description="Service health status")


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint used by Docker to ensure backend is ready."""
    return {"status": "ok"}


@app.post("/v1/predict", response_model=PredictResponse)
def predict(payload: PredictRequest):
    """Predict label and score from text input."""
    text_lower = payload.text.lower()

    # Rule-based sentiment classification stub
    positive_keywords = {
        "good", "great", "excellent", "happy", "love",
        "wonderful", "awesome", "positive", "best", "delighted"
    }
    negative_keywords = {
        "bad", "poor", "terrible", "sad", "hate",
        "awful", "horrible", "negative", "worst", "broken"
    }

    words = set(text_lower.split())
    has_pos = any(w in words or w in text_lower for w in positive_keywords)
    has_neg = any(w in words or w in text_lower for w in negative_keywords)

    if has_pos and not has_neg:
        label = "positive"
        score = 0.95
    elif has_neg and not has_pos:
        label = "negative"
        score = 0.92
    else:
        label = "neutral"
        score = 0.75

    return PredictResponse(label=label, score=score)
