# Backend/routers/letta_router.py
from fastapi import APIRouter, Cookie, Body
from services.agent_service import handle_appointment_message
from auth import get_user_id_from_token, get_email_from_token

router = APIRouter(prefix="/letta", tags=["Letta"])

# Chimata api che riceve il messaggio dell'utente per poi fornire la risposta dell'agente
@router.post("/ask")
def appointment(
    data: dict = Body(...),
    access_token: str = Cookie(None)
):
    print("🔵 ROUTER → CHIAMATO")
    print("🔵 DATA RICEVUTO:", data)
    print("🔵 ACCESS TOKEN:", access_token)

    if not access_token:
        print("🔴 Manca token")
        return {"error": "Token mancante"}

    user_id = get_user_id_from_token(access_token)
    email = get_email_from_token(access_token)
    print("🔵 USER ID:", user_id)
    print("🔵 EMAIL:", email)

    if not user_id or not email:
        print("🔴 Token non valido")
        return {"error": "Token non valido"}

    message = data.get("message")
    print("🔵 MESSAGE:", message)
    if not message:
        print("🔴 Nessun campo 'message'")
        return {"error": "Serve il campo 'message'"}

    print("🟡 Chiamo handle_appointment_message...")
    reply = handle_appointment_message(user_id, email, message)
    print("🟢 RISPOSTA AGENTE:", reply)

    return {"response": reply}
