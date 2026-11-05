"""Grafo LangGraph del agente router."""

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from src.router.prompts import (
    GENERICO_PROMPT,
    POSTVENTA_PROMPT,
    PREVENTA_PROMPT,
    ROUTER_PROMPT,
)
from src.router.tools import get_router_model


class Decision(BaseModel):
    ruta: Literal["preventa", "postventa", "generica"] = Field(
        description="A qué agente va el mensaje."
    )
    motivo: str = Field(description="Una frase: por qué esa ruta.")


class RouterState(TypedDict, total=False):
    mensaje: str
    ruta: Literal["preventa", "postventa", "generica"]
    motivo: str
    respuesta: str
    messages: Annotated[list[AnyMessage], add_messages]


def router_node(state: RouterState) -> dict:
    """Clasifica el mensaje más reciente, considerando el historial del hilo."""
    history = list(state.get("messages", []))
    history.append(HumanMessage(content=state["mensaje"]))
    structured_llm = get_router_model().with_structured_output(Decision)
    decision = structured_llm.invoke(
        [SystemMessage(content=ROUTER_PROMPT), *history]
    )
    return {
        "ruta": decision.ruta,
        "motivo": decision.motivo,
        "messages": [HumanMessage(content=state["mensaje"])],
    }


def agente_preventa_node(state: RouterState) -> dict:
    respuesta = PREVENTA_PROMPT.format(mensaje=state["mensaje"])
    return {"respuesta": respuesta, "messages": [AIMessage(content=respuesta)]}


def agente_postventa_node(state: RouterState) -> dict:
    respuesta = POSTVENTA_PROMPT.format(mensaje=state["mensaje"])
    return {"respuesta": respuesta, "messages": [AIMessage(content=respuesta)]}


def respuesta_generica_node(state: RouterState) -> dict:
    # Respuesta estática: este nodo no invoca ningún modelo.
    respuesta = GENERICO_PROMPT
    return {"respuesta": respuesta, "messages": [AIMessage(content=respuesta)]}


def ruta_destino(state: RouterState) -> str:
    return state["ruta"]


builder = StateGraph(RouterState)
builder.add_node("router", router_node)
builder.add_node("agente_preventa", agente_preventa_node)
builder.add_node("agente_postventa", agente_postventa_node)
builder.add_node("respuesta_generica", respuesta_generica_node)
builder.add_edge(START, "router")
builder.add_conditional_edges(
    "router",
    ruta_destino,
    {
        "preventa": "agente_preventa",
        "postventa": "agente_postventa",
        "generica": "respuesta_generica",
    },
)
builder.add_edge("agente_preventa", END)
builder.add_edge("agente_postventa", END)
builder.add_edge("respuesta_generica", END)

graph = builder.compile(checkpointer=MemorySaver())
