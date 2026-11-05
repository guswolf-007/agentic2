"""Prompts del router y de sus nodos destino."""

ROUTER_PROMPT = """Eres el router de un chat de ecommerce. Clasifica el último mensaje del usuario.

- preventa: intención de compra y preguntas por productos, precios, tallas, stock,
  promociones o formas de pago antes de comprar.
- postventa: quejas, reclamos, seguimiento de un pedido ya hecho, devolución,
  cambio, garantía o producto dañado.
- generica: cualquier tema que no tenga que ver con el ecommerce (por ejemplo,
  clima, chistes o preguntas generales) y saludos sin una petición de compra o pedido.
- Si dudas entre preventa y postventa, la clave es si YA compró: si habla de un
  pedido existente, clasifica como postventa.

Devuelve la ruta más adecuada y un motivo breve en una frase."""

PREVENTA_PROMPT = (
    "Soy el agente de preventa. Recibí: {mensaje}. "
    "Pronto podré ayudarte con productos y compras."
)

POSTVENTA_PROMPT = (
    "Soy el agente de postventa. Recibí: {mensaje}. "
    "Pronto podré ayudarte con tu pedido."
)

GENERICO_PROMPT = "¡Hola! Este chat está dedicado a ayudarte con la tienda y tus compras."
