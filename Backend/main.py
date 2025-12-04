from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth_routes import router as auth_router
from routes.appointment_routes import router as appointment_routes
from routes.letta_router import router as letta_router

app = FastAPI()

# CORS
origins = [
    "http://127.0.0.1:5173",  # L'URL del mio frontend React
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_router)
app.include_router(appointment_routes)
app.include_router(letta_router)


@app.get("/")
def home():
    return {"status": "Backend attivo"}
