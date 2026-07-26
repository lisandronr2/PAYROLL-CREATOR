# PAYROLL CREATOR (MVP)

Motor de cálculo jurídico-laboral para generar nóminas mensuales en España.

Ver [docs/LEGAL_DISCLAIMER.md](docs/LEGAL_DISCLAIMER.md) antes de usar en producción:
los parámetros legales (SMI, tipos de cotización, tramos IRPF) y algunas tablas de
convenio son orientativos/de ejemplo y deben verificarse con una asesoría.

## Estructura

- `backend/` — API FastAPI + motor de cálculo (Python).
- `frontend/` — App Next.js (gestión de empresas/trabajadores/contratos y generación de nóminas).
- `docs/` — Documentación, incluido el aviso legal.

## Puesta en marcha (desarrollo local)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
python -m app.seed.run_seed   # carga convenios, parámetros legales y tabla IRPF de ejemplo
uvicorn app.main:app --reload --port 8000
```

Por defecto usa SQLite (`backend/payroll.db`). Para Postgres/Supabase en producción,
define `DATABASE_URL` en `backend/.env` (ver `backend/.env.example`).

Tests del motor de cálculo:
```bash
cd backend
pytest tests/ -v
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Configurar `frontend/.env.local` con `NEXT_PUBLIC_API_URL` apuntando al backend
(por defecto `http://127.0.0.1:8000`).

## Convenios cargados de ejemplo

- **Metal Madrid** — tabla salarial 2026 **real**, tomada del BOCM núm. 59 (11/03/2026).
- **Construcción** y **Comercio Madrid** — estructura de grupos con salarios de
  **EJEMPLO**, a sustituir por las tablas oficiales antes de usar en producción.

## Despliegue

- Frontend → Vercel.
- Backend → Render/Railway (free tier; necesita un proceso Python persistente).
- Base de datos → Supabase Postgres (free tier).

## Fuera de alcance en esta versión

Asistente de IA conversacional, exportación SILTRA/Sistema RED, control horario,
gestión de bajas médicas con partes reales, actualización automática de convenios.
Ver el plan completo en `docs/LEGAL_DISCLAIMER.md` para las simplificaciones del
motor de cálculo.
