FROM ubuntu:noble
# noble == Ubuntu 14.04 LTS, the most recent LTS release supported by the docker-outside-of-docker devcontainer feature. Once they support 26.04 LTS "Resolute" we should switch to that.

RUN apt-get update && apt-get install -y \
    bash-completion \
    openssh-client

# Install uv (to export from uv.lock)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN useradd --create-home --shell /bin/bash devcontainer
USER devcontainer

# Don't use ./.venv; it can conflict with host system
ENV UV_PROJECT_ENVIRONMENT="/home/devcontainer/venv"

# Activate virtualenv
ENV VIRTUAL_ENV=$UV_PROJECT_ENVIRONMENT
ENV PATH="$UV_PROJECT_ENVIRONMENT/bin:$PATH"

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --all-groups --no-install-project

# Install project from postCreateCommand in devcontainer.json
