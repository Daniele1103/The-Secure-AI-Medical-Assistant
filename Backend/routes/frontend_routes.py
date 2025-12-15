from fastapi import APIRouter, Cookie
from auth import get_user_id_from_token
from db import appointments
from bson import ObjectId

router = APIRouter(prefix="/frontend", tags=["Frontend"])

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
