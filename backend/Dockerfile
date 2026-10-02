# Multi-stage Dockerfile para DeskFlow Backend
# Base stage com uv para desenvolvimento e compilação
FROM python:3.12-slim AS base

WORKDIR /app

# Instalar uv e ferramentas de desenvolvimento
RUN pip install --no-cache-dir uv && \
    uv venv .venv && \
    .venv/bin/python -m pip install --no-cache-dir \
    ruff>=0.4 \
    mypy>=1.10

# Possuir PATH do venv
ENV PATH="/app/.venv/bin:$PATH"

# Estágio de instalação de dependências
FROM base AS installer

WORKDIR /app

# Copiar pyproject.toml e uv.lock para instalar dependências
COPY pyproject.toml ./
COPY uv.lock* ./

# Sync com uv (instala em .venv)
RUN uv sync --all-extras --no-dev

# Estágio de desenvolvimento
FROM installer AS dev

# Copiar código fonte
COPY src/ ./src/

# Expor porta
EXPOSE 8000

# Comando padrão
CMD ["uv", "run", "python", "-m", "deskflow"]