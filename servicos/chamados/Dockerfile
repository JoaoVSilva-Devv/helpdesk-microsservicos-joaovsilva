FROM python:3.12-slim

RUN useradd --create-home --uid 10001 helpdesk && mkdir /dados && chown helpdesk /dados

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY chamados ./chamados

USER helpdesk
ENV DATABASE_URL=sqlite:////dados/chamados.db \
    USUARIOS_URL=http://usuarios:8000 \
    INVENTARIO_URL=http://inventario:8000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "chamados.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
