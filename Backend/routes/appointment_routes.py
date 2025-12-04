from fastapi import APIRouter
from services.ai_service import ask_gpt

router = APIRouter(prefix="/gpt", tags=["GPT"])

@router.post("/ask")
def ask(data: dict):
    message = data.get("message")

    if message is None:
        return {"error": "Serve il campo 'message'"}

    return {"response": ask_gpt(str(message))}


