# Deploy PairUp API On Render

Render Web Service settings:

- Root Directory: `apps/api`
- Build Command: `bash build.sh`
- Start Command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

Required environment variables:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DATABASE_URL`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`

Recommended values:

- `DEBUG=False`
- `ALLOWED_HOSTS=<your-render-service-hostname>`
- `CORS_ALLOWED_ORIGINS=https://<your-vercel-frontend-domain>`
- `CSRF_TRUSTED_ORIGINS=https://<your-render-service-hostname>,https://<your-vercel-frontend-domain>`

Frontend note:

- Set Vercel `NEXT_PUBLIC_API_BASE_URL=https://<your-render-backend-url>/api/v1`
- After changing Vercel environment variables, trigger a new deployment so the new values take effect
