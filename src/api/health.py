from dataclasses import dataclass
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, field_validator
from typing import List
import random

import sqlalchemy
from src.api import auth
from src import database as db

router = APIRouter(
    prefix="/health",
    tags=["health"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/", tags=["meta"])
def read_health() -> dict[str, str]:
    return {"status": "healthy"}