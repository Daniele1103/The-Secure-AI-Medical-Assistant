from datetime import datetime
from fastapi import APIRouter, Body, HTTPException
import db
from services.ai_service import ask_gpt

router = APIRouter(prefix="/tool", tags=["Tool"])

@router.post("/ask")
def ask(data: dict):
    message = data.get("message")

    if message is None:
        return {"error": "Serve il campo 'message'"}

    return {"response": ask_gpt(str(message))}

@router.post("/create")
def create_appointment(data: dict = Body(...)):

    user_id = data.get("user_id")
    email = data.get("email")
    date = data.get("date")
    time = data.get("time")

    if not user_id or not email or not date or not time:
        raise HTTPException(status_code=400, detail="user_id, email, date e time sono obbligatori")

    user = db.users.find_one({"_id": user_id, "email": email})

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User ID ed email non corrispondono ad alcun utente"
        )

    appointment = {
        "user_id": user_id,
        "email": email,
        "date": date,
        "time": time,
        "created_at": datetime.utcnow()
    }

    db.appointments.insert_one(appointment)

    return {
        "message": "Appuntamento salvato correttamente",
        "appointment": appointment
    }