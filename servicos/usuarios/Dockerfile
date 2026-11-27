FROM python:3.12-slim

# Contêiner roda como usuário sem privilégios; o banco fica em /dados (volume).
RUN useradd --create-home --uid 10001 helpdesk && mkdir /dados && chown helpdesk /dados

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY usuarios ./usuarios

USER helpdesk
ENV DATABASE_URL=sqlite:////dados/usuarios.db \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "usuarios.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
