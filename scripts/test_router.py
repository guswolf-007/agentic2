"""Evalúa los casos de tests/casos_router.json contra el agente router."""

import json
import os
import sys
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.router.graph import graph


def cargar_casos() -> list[dict[str, str]]:
    ruta = ROOT / "tests" / "casos_router.json"
    return json.loads(ruta.read_text(encoding="utf-8"))


def evaluar(casos: list[dict[str, str]]) -> list[dict[str, str]]:
    resultados = []
    for caso in casos:
        try:
            resultado = graph.invoke(
                {"mensaje": caso["mensaje"]},
                config={"configurable": {"thread_id": f"script-{uuid4()}"}},
            )
            obtenido = resultado["ruta"]
            motivo = resultado["motivo"]
        except Exception as error:
            obtenido = "ERROR"
            motivo = f"{type(error).__name__}: {error}"

        resultados.append(
            {
                "mensaje": caso["mensaje"],
                "esperado": caso["esperado"],
                "obtenido": obtenido,
                "estado": "✔" if obtenido == caso["esperado"] else "✘",
                "motivo": motivo,
            }
        )
    return resultados


def imprimir_tabla(resultados: list[dict[str, str]]) -> None:
    columnas = ["mensaje", "esperado", "obtenido", "estado", "motivo"]
    anchos = {
        columna: max(len(columna), *(len(fila[columna]) for fila in resultados))
        for columna in columnas
    }

    def imprimir_fila(fila: dict[str, str]) -> None:
        print(" | ".join(f"{fila[col]:<{anchos[col]}}" for col in columnas))

    imprimir_fila({col: col for col in columnas})
    print("-+-".join("-" * anchos[col] for col in columnas))
    for fila in resultados:
        imprimir_fila(fila)


def main() -> int:
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        print("Falta GOOGLE_API_KEY. Configúrala en .env para ejecutar las pruebas.", file=sys.stderr)
        return 2

    resultados = evaluar(cargar_casos())
    imprimir_tabla(resultados)

    aciertos = sum(fila["estado"] == "✔" for fila in resultados)
    total = len(resultados)
    porcentaje = (aciertos / total * 100) if total else 0
    print(f"\nAciertos: {aciertos}/{total} ({porcentaje:.1f}%)")

    fallados = [fila for fila in resultados if fila["estado"] == "✘"]
    if fallados:
        print("Fallados:")
        for fila in fallados:
            print(
                f"- {fila['mensaje']} — esperado: {fila['esperado']}, "
                f"obtenido: {fila['obtenido']}; motivo: {fila['motivo']}"
            )
    else:
        print("Fallados: ninguno")

    return 0 if aciertos >= 13 else 1


if __name__ == "__main__":
    sys.exit(main())
