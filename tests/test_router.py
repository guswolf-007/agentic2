"""Pruebas de enrutamiento con Gemini y tolerancia a 2 errores de 15."""

import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from dotenv import load_dotenv

from src.router.graph import graph


load_dotenv()
CASOS = json.loads(
    (Path(__file__).with_name("casos_router.json")).read_text(encoding="utf-8")
)


@pytest.fixture(scope="session")
def resultados_router():
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.skip("Configura GOOGLE_API_KEY en .env para probar el router con Gemini.")

    resultados = []
    yield resultados

    aciertos = sum(obtenido == caso["esperado"] for caso, obtenido, _ in resultados)
    fallados = [
        f"{caso['mensaje']!r}: esperado={caso['esperado']}, obtenido={obtenido}"
        for caso, obtenido, _ in resultados
        if obtenido != caso["esperado"]
    ]
    assert len(resultados) == len(CASOS), (
        f"Se ejecutaron {len(resultados)}/{len(CASOS)} casos; deben ejecutarse todos."
    )
    assert aciertos >= 13, (
        f"El router acertó {aciertos}/{len(CASOS)}; se requieren al menos 13. "
        f"Fallados: {fallados}"
    )


@pytest.mark.parametrize("caso", CASOS, ids=[caso["mensaje"] for caso in CASOS])
def test_router_clasifica_casos(caso, resultados_router):
    resultado = graph.invoke(
        {"mensaje": caso["mensaje"]},
        config={"configurable": {"thread_id": f"pytest-{uuid4()}"}},
    )
    obtenido = resultado["ruta"]
    resultados_router.append((caso, obtenido, resultado["motivo"]))

    assert obtenido in {"preventa", "postventa", "generica"}
    assert resultado["respuesta"]
    assert resultado["motivo"]
