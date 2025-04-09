
# Copyright (c) Microsoft Corporation. All rights reserved.
# Dockerfile
# https://eng.ms/docs/more/containers-secure-supply-chain/approved-images
FROM mcr.microsoft.com/oryx/python:3.11

RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
RUN apt-get update -y

# Install dependencies
WORKDIR ./
COPY . .
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH="${PATH}:/root/.local/bin"
RUN poetry config virtualenvs.in-project true
RUN poetry install --no-root

# Run application
EXPOSE 8501
ENTRYPOINT ["poetry","run","streamlit", "run", "./app/home_page.py"]