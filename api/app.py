"""FastAPI para el chat del ecommerce y la integración futura con Telegram."""

import logging
import os
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from src.router.graph import graph


load_dotenv()
logger = logging.getLogger(__name__)
MODELO = os.getenv("MODELO", "gemini-3.5-flash-lite")

# El módulo del agente compila el grafo una vez al importarse. Esta misma
# instancia (incluido su MemorySaver) se reutiliza en todas las solicitudes.
router_graph = graph


class ChatRequest(BaseModel):
    """Mensaje de un usuario para el chat del ecommerce."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "cliente-123",
                "texto": "¿Tienen la polera azul en talla M?",
            }
        }
    )

    user_id: str = Field(
        description="Identificador estable del usuario; se usa como thread_id de la memoria.",
        examples=["cliente-123"],
    )
    texto: str = Field(
        description="Mensaje que se enviará al router del ecommerce.",
        examples=["¿Tienen la polera azul en talla M?"],
    )


class ChatResponse(BaseModel):
    """Clasificación del mensaje y respuesta del agente destino."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ruta": "preventa",
                "motivo": "Pregunta por la disponibilidad y talla de un producto.",
                "respuesta": "Soy el agente de preventa. Recibí: ¿Tienen la polera azul en talla M?. Pronto podré ayudarte con productos y compras.",
            }
        }
    )

    ruta: Literal["preventa", "postventa", "generica"] = Field(
        description="Ruta elegida por el router.",
        examples=["preventa"],
    )
    motivo: str = Field(
        description="Motivo breve de la clasificación.",
        examples=["Pregunta por la disponibilidad y talla de un producto."],
    )
    respuesta: str = Field(
        description="Respuesta del agente destino.",
        examples=[
            "Soy el agente de preventa. Recibí: ¿Tienen la polera azul en talla M?. Pronto podré ayudarte con productos y compras."
        ],
    )


class HealthResponse(BaseModel):
    ok: bool = Field(description="Indica que la API está disponible.", examples=[True])
    modelo: str = Field(description="Modelo configurado para el router.", examples=[MODELO])


app = FastAPI(
    title="Ecommerce Router API",
    version="1.0.0",
    description=(
        "API del chat de ecommerce. El router dirige cada mensaje a una de tres rutas: "
        "`preventa`, `postventa` o `generica`."
    ),
    openapi_tags=[
        {"name": "salud", "description": "Estado y configuración del servicio."},
        {"name": "chat", "description": "Enrutamiento de mensajes del ecommerce."},
        {"name": "telegram", "description": "Webhook reservado para la integración con Telegram."},
    ],
)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["salud"],
    summary="Comprobar el estado de la API",
    description="Devuelve el estado del servicio y el nombre del modelo configurado.",
)
def health() -> HealthResponse:
    return HealthResponse(ok=True, modelo=MODELO)


@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["chat"],
    summary="Enrutar un mensaje del chat",
    description=(
        "Invoca el grafo router y conserva la memoria de conversación asociada al `user_id`. "
        "Las rutas posibles son `preventa`, `postventa` y `generica`."
    ),
    responses={
        200: {"description": "Mensaje clasificado y respuesta del agente destino."},
        422: {
            "description": "El cuerpo no cumple el esquema; por ejemplo, falta `texto` o `user_id`.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "texto"],
                                "msg": "Field required",
                                "type": "missing",
                            }
                        ]
                    }
                }
            },
        },
        502: {
            "description": "El modelo o el grafo no pudo procesar el mensaje.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "El modelo no está disponible en este momento. Inténtalo de nuevo."
                    }
                }
            },
        },
    },
)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = router_graph.invoke(
            {"mensaje": request.texto},
            config={"configurable": {"thread_id": request.user_id}},
        )
        return ChatResponse(
            ruta=result["ruta"],
            motivo=result["motivo"],
            respuesta=result["respuesta"],
        )
    except Exception as exc:
        logger.exception("Error al invocar el grafo router")
        raise HTTPException(
            status_code=502,
            detail="El modelo no está disponible en este momento. Inténtalo de nuevo.",
        ) from exc


@app.post(
    "/telegram",
    tags=["telegram"],
    include_in_schema=False,
    summary="Webhook provisional de Telegram",
)
async def telegram(payload: Any = Body(...)) -> dict[str, bool]:
    """Acepta provisionalmente cualquier cuerpo JSON; se completará más adelante."""
    return {"ok": True}
