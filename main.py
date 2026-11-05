"""Ejecutor de agentes definidos en src/{nombre_agente}/graph.py."""

import argparse
import importlib
import sys
import uuid


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecuta un agente LangGraph.")
    parser.add_argument("agente", help="Nombre del paquete dentro de src/")
    parser.add_argument("mensaje", nargs="?", help="Mensaje para el agente")
    parser.add_argument("--saltos", action="store_true", help="Muestra nodos y motivo")
    parser.add_argument("--diagrama", action="store_true", help="Imprime el Mermaid")
    parser.add_argument("--thread-id", help="Identificador para reutilizar memoria")
    args = parser.parse_args()

    try:
        module = importlib.import_module(f"src.{args.agente}.graph")
    except ModuleNotFoundError as exc:
        if exc.name == f"src.{args.agente}" or exc.name == f"src.{args.agente}.graph":
            parser.error(f"No se encontró el agente '{args.agente}' en src/{args.agente}/")
        raise

    agent_graph = module.graph
    if args.diagrama:
        print(agent_graph.get_graph().draw_mermaid())
        return 0
    if args.mensaje is None:
        parser.error("mensaje es obligatorio, excepto cuando se usa --diagrama")

    config = {"configurable": {"thread_id": args.thread_id or str(uuid.uuid4())}}
    result: dict = {}
    final_node = None
    for update in agent_graph.stream(
        {"mensaje": args.mensaje}, config=config, stream_mode="updates"
    ):
        for node_name, values in update.items():
            result.update(values)
            if node_name != "router":
                final_node = node_name

    if args.saltos:
        motivo = result.get("motivo", "")
        print(f"router → {final_node}; motivo: {motivo}")
    print(result.get("respuesta", ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
