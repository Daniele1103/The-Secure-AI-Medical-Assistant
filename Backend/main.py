from fastapi import FastAPI
import traceback

print("Main.py avviato!")
try:
    app = FastAPI()

    @app.get("/")
    async def root():
        return {"message": "Benvenuto nel Medical Assistant!"}
except Exception:
    traceback.print_exc()

print("Main.py avviato!")
