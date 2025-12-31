from datetime import datetime
from fastapi import APIRouter, Body, Cookie
from auth import get_user_id_from_token
from db import appointments, messages
from bson import ObjectId

router = APIRouter(prefix="/frontend", tags=["Frontend"])

# Restituisce tutti gli appunatmenti di un utente
@router.get("/my-appointments")
def my_appointments(access_token: str = Cookie(None)):
    if not access_token:
        return {"error": "Token mancante"}
    
    user_id = get_user_id_from_token(access_token)

    if not user_id:
        return {"error": "Token non valido"}

    try:
        appts_cursor = appointments.find({"user_id": user_id}).sort("created_at", 1)
        appointments_list = []
        for appt in appts_cursor:
            appointments_list.append({
                "appointment_id": str(appt["_id"]),
                "date": appt.get("date"),
                "time": appt.get("time")
            })
        return {"appointments": appointments_list}

    except Exception as e:
        return {"error": "Errore nel recupero appuntamenti"}

# Salva un messaggio nel db
@router.post("/messages")
def save_message(
    message: dict = Body(...),
    access_token: str = Cookie(None)
):
    if not access_token:
        return {"error": "Token mancante"}

    user_id = get_user_id_from_token(access_token)
    if not user_id:
        return {"error": "Token non valido"}

    try:
        doc = {
            "user_id": user_id,
            "role": message.get("role"),
            "content": message.get("content"),
            "created_at": datetime.utcnow()
        }

        messages.insert_one(doc)

        return {"status": "ok"}

    except Exception as e:
        return {"error": "Errore nel salvataggio messaggio"}

# Ottiene lo storico dei messaggi di un utente
@router.get("/messages")
def get_messages(access_token: str = Cookie(None)):
    if not access_token:
        return {"error": "Token mancante"}

    user_id = get_user_id_from_token(access_token)
    if not user_id:
        return {"error": "Token non valido"}

    try:
        cursor = messages.find(
            {"user_id": user_id}
        ).sort("created_at", 1)

        messages_list = []
        for msg in cursor:
            messages_list.append({
                "message_id": str(msg["_id"]),
                "role": msg.get("role"),
                "content": msg.get("content"),
                "created_at": msg.get("created_at")
            })

        return {"messages": messages_list}

    except Exception:
        return {"error": "Errore nel recupero messaggi"}