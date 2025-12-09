from datetime import datetime
from fastapi import APIRouter, Body, HTTPException
from db import users, appointments
from services.ai_service import ask_gpt
from bson import ObjectId, errors

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
    try:
        oid = ObjectId(user_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="user_id non valido")

    user = users.find_one({"_id": oid, "email": email})

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

    appointments.insert_one(appointment)

    return {
        "message": "Appuntamento salvato correttamente"
    }

@router.get("/appointments")
def get_appointments():
    result = []

    for appt in appointments.find():
        appt.pop("_id", None)  # Rimuove l'ObjectId
        appt["created_at"] = appt["created_at"].isoformat() if "created_at" in appt else None
        result.append(appt)

    return {"appointments": result}


@router.get("/appointments/user/{user_id}")
def get_user_appointments(user_id: str):

    appts = appointments.find({"user_id": user_id}).sort("created_at", 1)

    result = []
    for appt in appts:
        appt_dict = {
            "appointment_id": str(appt["_id"]), 
            "user_id": appt["user_id"],
            "email": appt["email"],
            "date": appt["date"],
            "time": appt["time"],
            "created_at": appt["created_at"].isoformat() if "created_at" in appt else None
        }
        result.append(appt_dict)

    return {"appointments": result}

@router.delete("/appointments/{appointment_id}")
def delete_appointment(appointment_id: str):
    try:
        oid = ObjectId(appointment_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="appointment_id non valido")

    deleted = appointments.find_one_and_delete({"_id": oid})

    if not deleted:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")

    return {
        "status": "success",
        "message": "Appuntamento eliminato correttamente",
        "appointment_id": appointment_id
    }

@router.put("/appointments/{appointment_id}")
def update_appointment(appointment_id: str, data: dict = Body(...)):
    date = data.get("date")
    time = data.get("time")

    if not date and not time:
        raise HTTPException(
            status_code=400,
            detail="Devi fornire almeno uno tra 'date' o 'time'"
        )

    try:
        oid = ObjectId(appointment_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="appointment_id non valido")

    appt = appointments.find_one({"_id": oid})
    if not appt:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")

    update_data = {}
    if date:
        update_data["date"] = date
    if time:
        update_data["time"] = time

    update_data["updated_at"] = datetime.utcnow()

    appointments.update_one({"_id": oid}, {"$set": update_data})

    updated = appointments.find_one({"_id": oid})

    updated.pop("_id", None)
    updated["created_at"] = updated["created_at"].isoformat() if "created_at" in updated else None
    updated["updated_at"] = updated["updated_at"].isoformat() if "updated_at" in updated else None

    return {
        "message": "Appuntamento aggiornato correttamente",
        "appointment": updated
    }