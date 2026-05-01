FROM ghcr.io/astral-sh/uv:debian

RUN apt-get update && apt-get install -y bash-completion openssh-client

RUN useradd -m -s /bin/bash feed_ursus
USER feed_ursus

# Don't use ./.venv; it can conflict with host system
ENV UV_PROJECT_ENVIRONMENT="/home/feed_ursus/venv"

# Activate virtualenv
ENV VIRTUAL_ENV=$UV_PROJECT_ENVIRONMENT
ENV PATH="$UV_PROJECT_ENVIRONMENT/bin:$PATH"

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Install project from postCreateCommand in devcontainer.json
