"""Construcción diferida del modelo usado por el nodo router."""

from functools import lru_cache
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


@lru_cache(maxsize=1)
def get_router_model() -> ChatGoogleGenerativeAI:
    """Crea el modelo configurado por MODELO; la clave se lee del entorno."""
    load_dotenv()
    model_name = os.getenv("MODELO", "gemini-3.5-flash-lite")
    return ChatGoogleGenerativeAI(model=model_name)
