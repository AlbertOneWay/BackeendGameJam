from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # Importar el middleware CORS
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List
from pymongo import ASCENDING
import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

# Inicializar la aplicación
app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas las orígenes (puedes cambiarlo por dominios específicos)
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos HTTP (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Permitir todos los encabezados
)

# Conexión a MongoDB usando la cadena de conexión de MongoDB Atlas
client = AsyncIOMotorClient(MONGO_URI)
db = client["game_db"]  # Base de datos
collection = db["positions"]  # Colección

# Modelo de datos
class Position(BaseModel):
    name: str
    time: int
    position: int = 0  # Inicializamos la posición, que se calculará más tarde

# Función para insertar datos en la base de datos
@app.post("/add_position")
async def add_position(position: Position):
    # Insertar el nuevo registro en la base de datos
    document = position.dict()
    result = await collection.insert_one(document)

    # Recuperamos todos los registros y los ordenamos por tiempo
    all_positions = await collection.find().sort("time", ASCENDING).to_list(length=None)
    
    # Reasignamos las posiciones basadas en el tiempo
    for i, p in enumerate(all_positions):
        await collection.update_one(
            {"_id": p["_id"]},
            {"$set": {"position": i + 1}}  # Asignar la posición, el más rápido es el 1
        )

    return {"id": str(result.inserted_id), "position": position.position}

# Función para consultar todas las posiciones ordenadas
@app.get("/positions", response_model=List[Position])
async def get_positions():
    positions = []
    # Obtener todos los registros ordenados por "time" de menor a mayor
    async for position in collection.find().sort("time", ASCENDING):
        positions.append(Position(
            name=position["name"],
            time=position["time"],
            position=position["position"]  # La posición ya está guardada en la base de datos
        ))
    return positions

# Punto de entrada para ejecutar la aplicación
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
