from fastapi import APIRouter, Request, HTTPException, Response
from db import db
from auth import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
async def register(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email e password richieste")

    existing = db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")

    hashed = hash_password(password)

    new_user = {
        "email": email,
        "password_hash": hashed,
        "mfa_enabled": False,
        "webauthn_credentials": [],
    }

    db.users.insert_one(new_user)
    return {"message": "Registrazione completata"}


@router.post("/login")
async def login(request: Request, response: Response):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email e password richieste")

    db_user = db.users.find_one({"email": email})
    if not db_user or not verify_password(password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenziali errate")

    if db_user.get("mfa_enabled", False):
        return {"mfa_required": True, "user_id": str(db_user["_id"])}

    token = create_access_token({
        "sub": str(db_user["_id"]),
        "email": db_user["email"]
    })

    # Qui usi l'istanza response
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,   # True in produzione con HTTPS (in locale lavoro con http e quindi non funzionerebbe)
        samesite="none",
        max_age=3600
    )

    return {"message": "Login effettuato"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=False
    )
    return {"message": "Logout effettuato"}

@router.get("/me")
async def get_me(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return {"logged_in": False}
    # verifica token qui (decode JWT)
    try:
        payload = decode_access_token(token)  # funzione tua per JWT
        # print(payload)
        return {"logged_in": True, "user": payload}    # invio il payload in questo modo in quanto il client non può leggere il token per motivi di sicurezza
    except:
        return {"logged_in": False}
