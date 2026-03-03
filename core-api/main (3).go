from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
import asyncpg
import uuid
import os

app = FastAPI(title="Project Sentinel - Ingestion API")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/sentinel"
)

# --- Connection Pool ---

@app.on_event("startup")
async def startup():
    app.state.pool = await asyncpg.create_pool(DATABASE_URL)

@app.on_event("shutdown")
async def shutdown():
    await app.state.pool.close()

# --- Pydantic Models (Master JSON Contract) ---

class Payload(BaseModel):
    username_attempted: Optional[str] = None
    password_attempted: Optional[str] = None
    commands_executed: Optional[List[Any]] = None
    files_dropped: Optional[List[Any]] = None

class SecurityEvent(BaseModel):
    event_id: uuid.UUID
    timestamp: datetime
    sensor_id: str = Field(..., max_length=50)
    sensor_location: Optional[str] = Field(None, max_length=50)
    source_ip: str = Field(..., max_length=45)
    vector: str = Field(..., max_length=20)
    interaction_level: Optional[str] = Field(None, max_length=10)
    payload: Optional[Payload] = None

# --- Ingest Endpoint ---

@app.post("/api/v1/ingest")
async def ingest_event(event: SecurityEvent):
    payload = event.payload or Payload()

    sql = """
        INSERT INTO security_events (
            event_id, timestamp, sensor_id, sensor_location,
            source_ip, vector, interaction_level,
            username_attempted, password_attempted,
            commands_executed, files_dropped
        ) VALUES (
            $1, $2, $3, $4,
            $5, $6, $7,
            $8, $9,
            $10::jsonb, $11::jsonb
        )
        ON CONFLICT (event_id) DO NOTHING
    """

    import json

    try:
        async with app.state.pool.acquire() as conn:
            await conn.execute(
                sql,
                event.event_id,
                event.timestamp,
                event.sensor_id,
                event.sensor_location,
                event.source_ip,
                event.vector,
                event.interaction_level,
                payload.username_attempted,
                payload.password_attempted,
                json.dumps(payload.commands_executed) if payload.commands_executed is not None else "[]",
                json.dumps(payload.files_dropped) if payload.files_dropped is not None else "[]",
            )
    except asyncpg.PostgresError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"status": "success", "event_id": str(event.event_id)}


# --- Health Check ---

@app.get("/health")
async def health():
    return {"status": "ok"}
