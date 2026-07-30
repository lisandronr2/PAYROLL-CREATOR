# Despliegue — PAYROLL CREATOR

Arquitectura de producción: **Vercel** (frontend Next.js) + **Render**
(backend FastAPI) + **Supabase** (Postgres). Sigue los pasos en orden — cada
uno depende del anterior.

## 1. Supabase (base de datos)

1. Entra en https://supabase.com y crea un proyecto nuevo (requiere tu
   cuenta; elige región Europa para menor latencia desde España).
2. En **Project Settings → Database → Connection string**, copia la cadena
   modo **Session pooler** (funciona mejor con conexiones persistentes como
   las de Render) y sustituye `[YOUR-PASSWORD]` por la contraseña del
   proyecto.
3. Guarda esa cadena — la necesitarás como `DATABASE_URL` en el paso 2.

## 2. Render (backend)

1. Entra en https://render.com y conecta tu cuenta de GitHub (o sube el
   repo). El repo debe tener el `render.yaml` que ya está en
   `backend/render.yaml`.
2. **New → Blueprint**, selecciona el repo. Render leerá `render.yaml` y
   pedirá los valores marcados `sync: false`:
   - `DATABASE_URL`: la cadena de Supabase del paso 1.
   - `CORS_ORIGINS`: de momento pon `["http://localhost:3000"]`, lo
     actualizarás en el paso 4 con la URL real de Vercel.
   - `ADMIN_DEFAULT_EMAIL` / `ADMIN_DEFAULT_PASSWORD`: credenciales del
     primer usuario admin (cámbialas después del primer login).
   - `JWT_SECRET` se genera automáticamente (`generateValue: true`).
   - `FRONTEND_URL`: la URL de Vercel (paso 3) — se usa para construir el
     enlace del correo de "recuperar contraseña". Puedes dejarla pendiente y
     volver a este valor después del paso 3.
   - `RESEND_API_KEY`: para enviar el correo de recuperación de contraseña.
     Crea una cuenta gratis en https://resend.com y una API Key en
     https://resend.com/api-keys. Se usa la API HTTP de Resend (no SMTP)
     porque Render, en su plan gratuito, bloquea las conexiones salientes
     por los puertos SMTP (25/465/587) — un intento con SMTP directo
     (Gmail, etc.) falla siempre con "Network is unreachable". Si dejas
     `RESEND_API_KEY` vacío, el flujo sigue funcionando pero el enlace solo
     queda en los logs de Render (no se envía correo real).
3. Despliega. Al arrancar, el backend crea las tablas y carga los datos
   semilla (convenios, parámetros legales, tabla IRPF, usuario admin) de
   forma automática (`app/main.py` → `on_startup`).
4. Copia la URL pública que te da Render (algo como
   `https://payroll-creator-backend.onrender.com`).
5. Verifica: `curl https://TU-URL.onrender.com/health` debe responder
   `{"status":"ok"}`.

## 3. Vercel (frontend)

Desde `frontend/`:

```bash
npx vercel login
npx vercel link
npx vercel env add NEXT_PUBLIC_API_URL production
# pega la URL de Render del paso 2 cuando lo pida
npx vercel --prod
```

`vercel login` abre un flujo de autenticación en tu navegador/email — solo
tú puedes completarlo. Una vez logueado, los siguientes comandos ya pueden
ejecutarse sin más intervención.

## 4. Cerrar el círculo de CORS

Copia la URL final de Vercel (`https://tu-proyecto.vercel.app`) y actualiza
la variable `CORS_ORIGINS` en Render:

```
CORS_ORIGINS=["https://tu-proyecto.vercel.app"]
```

Guarda y deja que Render redepliegue el backend.

## 5. Verificación final

1. Abre la URL de Vercel, entra con el usuario admin (`ADMIN_DEFAULT_EMAIL`
   / `ADMIN_DEFAULT_PASSWORD`), y **cambia la contraseña por defecto** desde
   `/admin/usuarios` (o vía `PATCH /admin/usuarios/{id}` con una nueva
   contraseña).
2. Crea un usuario operador de prueba y confirma que no puede acceder a
   `/admin/*`.
3. Da de alta una empresa, un trabajador y un contrato, genera una nómina y
   descarga el PDF — igual que en el flujo verificado en local.

## Notas

- El almacenamiento de PDFs es efímero (se regeneran en cada descarga desde
  `backend/app/pdf/generador.py`), por lo que el plan free de Render no
  necesita disco persistente para esto.
- Si cambias `JWT_SECRET` en producción, todos los tokens emitidos antes
  dejan de ser válidos (los usuarios tendrán que volver a iniciar sesión).
- Antes de dar el sistema por operativo con datos reales, revisa
  [docs/LEGAL_DISCLAIMER.md](LEGAL_DISCLAIMER.md).
