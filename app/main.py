from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine
from app.controllers import municipio_controller, prediccion_controller, alerta_controller, gemini_controller

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Acuífero-Data SCZ API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(municipio_controller.router)
app.include_router(prediccion_controller.router)
app.include_router(alerta_controller.router)
app.include_router(gemini_controller.router)

@app.get("/")
def root():
    return {"status": "online", "proyecto": "Acuífero-Data SCZ"}
