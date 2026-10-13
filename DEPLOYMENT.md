# Deployment notes

The included Docker Compose and Django `runserver` commands are intended for
local development. Before deploying to a public environment:

1. Set a unique, secret `SECRET_KEY` and set `DEBUG=False`.
2. Set `ALLOWED_HOSTS` to the exact host names serving the application.
3. Configure HTTPS and secure cookie settings at the application or proxy layer.
4. Provide API keys through the deployment environment; do not commit `.env`.
5. Configure PostgreSQL if multiple application instances or durable shared data
   are needed. SQLite and local FAISS files are suitable for local development.
6. Run database migrations and collect static files as part of deployment.
7. Use a production WSGI/ASGI server and configure persistent storage and backups
   for uploaded files and the FAISS index.

The application reads its settings from environment variables. See
`.env.example` for the supported names and defaults. Docker
Compose currently sets development values directly, so replace those values in
any deployment-specific Compose configuration.
