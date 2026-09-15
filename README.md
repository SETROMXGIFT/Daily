# Diario de Ruta — versión en la nube

## Qué cambió

Tu app dejó de depender de un archivo SQLite guardado en una sola computadora.
Ahora hay dos piezas:

1. **`backend/`** — un servidor (FastAPI) que guarda todo en una base de datos
   Postgres **en la nube**. Reemplaza a tu antiguo `database.py`.
2. **`frontend/`** — una sola app web (funciona en el navegador de tu PC y de
   tu celular, y se puede "instalar" en ambos como si fuera una app nativa).

**Por qué esto resuelve la sincronización:** tanto tu PC como tu celular
hablan con el mismo servidor, que lee y escribe en la misma base de datos.
Ya no hay un archivo `.db` atrapado en una sola máquina — todo vive en un
solo lugar central.

El backend ya viene preparado para servir el frontend él mismo, así que al
desplegar solo tienes **un servicio, una URL**.

---

## Paso 1 — Crear la base de datos (gratis, 3 minutos)

1. Ve a **https://supabase.com** → crea una cuenta gratis.
2. **New Project** → ponle un nombre, elige una contraseña (guárdala, la
   necesitas en el paso 3) y la región más cercana a ti.
3. Espera ~2 minutos a que el proyecto termine de crearse.
4. Ve a **Project Settings → Database → Connection string** → copia la que
   dice **URI** (formato `postgresql://postgres:[TU-PASSWORD]@...`).
   Reemplaza `[TU-PASSWORD]` por la contraseña real que elegiste.
   Guarda esta línea completa — es tu `DATABASE_URL`.

## Paso 2 — Elegir tu clave API

Es la "contraseña" que van a usar tu PC y tu celular para hablar con tu
servidor. Escribe cualquier texto largo y difícil de adivinar (por ejemplo
30 caracteres al azar). Guárdalo — es tu `API_KEY`.

## Paso 3 — Subir el código a GitHub (sin usar la terminal)

1. Crea una cuenta gratis en **https://github.com** si no tienes.
2. **New repository** → nómbralo, por ejemplo, `diario-ruta` → **Create repository**.
3. En la página del repo: **Add file → Upload files**.
4. Arrastra las carpetas `backend/` y `frontend/` completas (con todo su
   contenido) a la ventana. Confirma el commit.

## Paso 4 — Desplegar en Render (gratis)

1. Ve a **https://render.com** → crea una cuenta (puedes entrar con GitHub).
2. **New + → Web Service** → conecta el repositorio `diario-ruta` que subiste.
3. Configura:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free
4. En **Environment Variables**, agrega:
   - `DATABASE_URL` = el connection string de Supabase (Paso 1)
   - `API_KEY` = la clave que elegiste (Paso 2)
5. **Create Web Service** y espera el despliegue (2–3 minutos).
6. Al terminar te da una URL como `https://diario-ruta.onrender.com` — esa es
   tu app, ya en vivo.

> **Nota sobre el plan gratis de Render:** el servidor "se duerme" tras 15
> minutos sin uso, y tarda unos 20–30 segundos en despertar la primera vez
> que lo abres después de estar dormido. Es normal, no es que esté roto. Si
> quieres que esté siempre despierto, el plan pagado empieza en $7/mes.

## Paso 5 — Conectar tu PC y tu celular

1. Abre la URL de Render (`https://diario-ruta.onrender.com`) en el
   navegador de tu PC.
2. Te va a pedir **URL del servidor** (pega esa misma URL) y **Clave API**
   (la del Paso 2). Dale **Conectar**.
3. Repite exactamente lo mismo en el navegador de tu celular.
4. A partir de ahí, cualquier cosa que registres desde un dispositivo
   aparece automáticamente en el otro (solo tienes que recargar/cambiar de
   pestaña).

**Instalarla como app (opcional pero recomendado):**
- **Celular (Android/iOS):** menú del navegador → "Agregar a pantalla de inicio" / "Instalar app".
- **PC (Chrome/Edge):** ícono de instalar en la barra de direcciones, o menú → "Instalar Diario de Ruta".

Con esto te queda un ícono como el de cualquier otra app, pero que abre tu
Diario de Ruta ya sincronizado.

---

## Desarrollo local (opcional, para probar antes de desplegar)

```bash
cd backend
pip install -r requirements.txt
API_KEY=cualquier-clave uvicorn main:app --reload
```

Abre `http://127.0.0.1:8000` en tu navegador. Sin `DATABASE_URL`, usa un
sqlite local (`diario_local.db`) solo para pruebas — en producción siempre
usa Postgres (Paso 1) para que la sincronización funcione.

---

## Seguridad y respaldos

- Tu `API_KEY` es lo único que protege tus datos — no la compartas ni la
  subas a un repositorio público junto con el código.
- Supabase hace respaldos automáticos en su plan gratis, pero de forma
  limitada. Si quieres un respaldo extra por tu cuenta, en Supabase puedes
  ir a **Database → Backups** y descargar uno manualmente de vez en cuando.
