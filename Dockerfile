FROM registry.access.redhat.com/ubi9/python-311:9.5-1733172699@sha256:3d9ce0a19b0edc6f7a60a933ea9e53a809282972fde30003ce686437affde070 as base
COPY --from=ghcr.io/astral-sh/uv:0.5.8@sha256:0bc959d4cc56e42cbd9aa9b63374d84481ee96c32803eea30bd7f16fd99d8d56 /uv /bin/uv

COPY LICENSE /licenses/

ENV \
    # use venv from ubi image
    UV_PROJECT_ENVIRONMENT=$APP_ROOT \
    # disable uv cache. it doesn't make sense in a container
    UV_NO_CACHE=true

COPY pyproject.toml uv.lock ./
# Test lock file is up to date
RUN uv lock --locked
# other project related files
COPY README.md Makefile ./
# the source code
COPY qontract_development_cli ./qontract_development_cli

# Install dependencies
RUN uv sync --frozen

FROM base AS test
RUN make test

FROM test AS pypi
# Secrets are owned by root and are not readable by others :(
USER root
RUN --mount=type=secret,id=app-sre-pypi-credentials/token make -s pypi
