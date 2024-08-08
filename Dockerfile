# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables
# Prevents Python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# install the required basic tools to ensure sources.list is available
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# use aliyun mirror to speed up the installation
RUN echo "deb https://mirrors.aliyun.com/debian/ bookworm main contrib non-free" > /etc/apt/sources.list \
    && echo "deb https://mirrors.aliyun.com/debian/ bookworm-updates main contrib non-free" >> /etc/apt/sources.list \
    && echo "deb https://mirrors.aliyun.com/debian/ bookworm-backports main contrib non-free" >> /etc/apt/sources.list \
    && echo "deb https://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list

# install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# install Poetry and set the timeout to 120 seconds
RUN pip install --no-cache-dir --default-timeout=120 poetry==1.8.3 -i https://mirrors.aliyun.com/pypi/simple/

# copy the Poetry lock file and the pyproject.toml
COPY pyproject.toml poetry.lock /app/

# install dependencies via poetry
RUN poetry config repositories.aliyun https://mirrors.aliyun.com/pypi/simple/ \
#    && poetry config installer.max_retries 5 \
    && poetry config installer.timeout 120 \
    && poetry install --no-interaction --no-ansi --no-dev

# copy the rest of the application code
COPY . /app
# expose the port
EXPOSE 8000

# run
CMD ["poetry","run","poe","webserver"]