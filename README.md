# Ecommerce Router

Agente LangGraph para enrutar mensajes de un chat de ecommerce a `preventa`,
`postventa` o `generica`. Incluye una API FastAPI, memoria de conversación por
`thread_id`, una suite de 15 casos de clasificación y una colección Bruno.

## Requisitos y configuración local

Se requiere Python 3.12 y una clave de Google AI para las llamadas al modelo.
Los secretos no se guardan en el código ni se suben al repositorio.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
```

Edita `.env` y configura `GOOGLE_API_KEY`. `MODELO` usa por defecto
`gemini-3.5-flash-lite`. No rellenes valores reales en `.env.example`.

## Ejecutar el router en local

Desde la raíz del proyecto:

```bash
python main.py router "¿Tienen la polera azul en talla M?"
```

Para mostrar los nodos visitados y el motivo de clasificación:

```bash
python main.py router "Mi pedido llegó roto" --saltos
```

Para imprimir el diagrama Mermaid sin invocar el modelo:

```bash
python main.py router --diagrama
```

Se puede reutilizar memoria pasando el mismo `--thread-id` en llamadas sucesivas:

```bash
python main.py router "Busco una polera" --thread-id cliente-123
python main.py router "¿La tienen en talla M?" --thread-id cliente-123
```

## Levantar la API

Desde la raíz, con el entorno virtual activo:

```bash
uvicorn api.app:app --reload --port 8000
```

Swagger/OpenAPI está disponible en <http://localhost:8000/docs> y la comprobación
de salud en <http://localhost:8000/health>.

Ejemplo de llamada a `/chat`:

```bash
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"cliente-123","texto":"¿Tienen la polera azul en talla M?"}'
```

`user_id` se utiliza como `thread_id`; enviar el mismo valor conserva la memoria de
esa conversación. `/telegram` es, por ahora, un webhook provisional que acepta el
JSON y devuelve `{"ok":true}`.

## Pruebas del router

Las pruebas consultan el modelo real y requieren `GOOGLE_API_KEY` en `.env`. Hay
15 casos (5 por ruta); pytest acepta al menos 13 aciertos.

```bash
python scripts/test_router.py
pytest -q
```

El script imprime la tabla de mensajes, ruta esperada/obtenida, resultado y motivo,
y termina con el porcentaje y la lista de fallos. Los casos están en
`tests/casos_router.json`.

## Desplegar en Heroku

Instala y autentícate con Heroku CLI. Desde la raíz del proyecto, define un nombre
único para la app y créala una sola vez:

```bash
heroku login
export HEROKU_APP=nombre-unico-para-tu-app
heroku create "$HEROKU_APP"
```

Configura `.env` localmente con los secretos y el nombre del modelo. Luego carga la
configuración de la app y despliega la rama `main`:

```bash
set -a
source .env
set +a
export PUBLIC_URL="https://${HEROKU_APP}.herokuapp.com"
heroku config:set \
  GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  MODELO="$MODELO" \
  TELEGRAM_TOKEN="$TELEGRAM_TOKEN" \
  TELEGRAM_SECRET="$TELEGRAM_SECRET" \
  PUBLIC_URL="$PUBLIC_URL" \
  --app "$HEROKU_APP"
git push heroku main
```

El `Procfile`, `.python-version` y `requirements.txt` configuran el proceso web y
Python 3.12. Comprueba el despliegue con:

```bash
curl "${PUBLIC_URL}/health"
```

Si el repositorio todavía no tiene un remoto Heroku, `heroku create` lo configura.
En despliegues posteriores basta con actualizar las variables necesarias y ejecutar
`git push heroku main`.

## Conectar Telegram

Crea el bot con [BotFather](https://t.me/BotFather), guarda su token como
`TELEGRAM_TOKEN` en `.env` y configura `TELEGRAM_SECRET` con un secreto propio.
Tras desplegar en una URL HTTPS, asegúrate de que `PUBLIC_URL` sea esa URL y carga
las variables de entorno de Heroku como se indica arriba.

Con `.env` cargado en la terminal, registra el webhook:

```bash
set -a
source .env
set +a
curl --fail-with-body --request POST \
  "https://api.telegram.org/bot${TELEGRAM_TOKEN}/setWebhook" \
  --data-urlencode "url=${PUBLIC_URL}/telegram" \
  --data-urlencode "secret_token=${TELEGRAM_SECRET}"
```

Para comprobar el registro:

```bash
curl "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getWebhookInfo"
```

**Estado actual:** `/telegram` solo acepta el JSON y responde `{"ok":true}`. Aún no
valida el encabezado secreto ni procesa actualizaciones o envía respuestas al bot;
la configuración del webhook por sí sola no activa el chat de Telegram.
