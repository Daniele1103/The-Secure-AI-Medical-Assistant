from datetime import datetime
from fastapi import APIRouter, Body, HTTPException, Header, Depends
import os
from db import users, appointments
from bson import ObjectId, errors

router = APIRouter(prefix="/tool", tags=["Tool"])

def verify_letta_token(x_letta_token: str = Header(...)):
    """
    Controlla che l'header X-Letta-Token sia corretto.
    """
    expected_token = os.getenv("LETTA_TOOL_TOKEN")  # token che hai impostato come variabile globale in Letta
    if x_letta_token != expected_token:
        raise HTTPException(status_code=403, detail="Token per usare api non valido")

@router.post("/appointments", dependencies=[Depends(verify_letta_token)])
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
    
    existing = appointments.find_one({
        "user_id": user_id,
        "date": date,
        "time": time
    })

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Hai già un appuntamento il {date} alle {time}"
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

@router.get("/appointments", dependencies=[Depends(verify_letta_token)])
def get_appointments():
    result = []

    for appt in appointments.find():
        appt.pop("_id", None)  # Rimuove l'ObjectId
        appt["created_at"] = appt["created_at"].isoformat() if "created_at" in appt else None       #devo fare così perchè sto modificando direttamente il file di mongo BSON
        result.append(appt)

    return {"appointments": result}


@router.get("/appointments/{user_id}", dependencies=[Depends(verify_letta_token)])
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

@router.delete("/appointments/{appointment_id}", dependencies=[Depends(verify_letta_token)])
def delete_appointment(appointment_id: str, data: dict = Body(...)):
    user_id = data.get("user_id")

    try:
        oid = ObjectId(appointment_id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="appointment_id non valido")

    appt = appointments.find_one({"_id": oid})

    if not appt:
        raise HTTPException(status_code=404, detail="Appuntamento non trovato")

    if appt.get("user_id") != user_id:
        raise HTTPException(
            status_code=403,
            detail="Non puoi cancellare un appuntamento che non ti appartiene"
        )

    appointments.delete_one({"_id": oid})

    return {
        "status": "success",
        "message": "Appuntamento eliminato correttamente",
        "appointment_id": appointment_id
    }


@router.put("/appointments/{appointment_id}", dependencies=[Depends(verify_letta_token)])
def update_appointment(appointment_id: str, data: dict = Body(...)):
    user_id = data.get("user_id")
    date = data.get("date")
    time = data.get("time")

    if not user_id:
        raise HTTPException(
            status_code=400,
            detail="user_id è obbligatorio"
        )

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

    if appt.get("user_id") != user_id:
        raise HTTPException(
            status_code=403,
            detail="Non puoi modificare un appuntamento che non ti appartiene"
        )

    update_data = {}
    if date:
        update_data["date"] = date
    if time:
        update_data["time"] = time

    update_data["updated_at"] = datetime.utcnow()

    appointments.update_one({"_id": oid}, {"$set": update_data})

    return {
        "status": "success",
        "message": "Appuntamento aggiornato correttamente",
        "appointment_id": appointment_id
    }