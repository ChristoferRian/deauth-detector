from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.start_service import router as deauth_router

app = FastAPI(
    title="Deauth Detection API",
    description="API untuk mendeteksi paket deauthentication",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(deauth_router)

@app.get("/")
async def root():
    return {"message": "Deauth Detection API - /docs untuk dokumentasi"}