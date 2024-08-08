# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables
# Prevents Python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# 安装所需的基础工具以确保 sources.list 可用
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 替换默认的Debian源为阿里云的镜像源以加速apt-get操作
RUN echo "deb https://mirrors.aliyun.com/debian/ bookworm main contrib non-free" > /etc/apt/sources.list \
    && echo "deb https://mirrors.aliyun.com/debian/ bookworm-updates main contrib non-free" >> /etc/apt/sources.list \
    && echo "deb https://mirrors.aliyun.com/debian/ bookworm-backports main contrib non-free" >> /etc/apt/sources.list \
    && echo "deb https://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list

# 安装系统依赖项
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装Poetry，并使用国内的镜像源，设置超时时间为120秒
RUN pip install --no-cache-dir --default-timeout=120 poetry==1.8.3 -i https://mirrors.aliyun.com/pypi/simple/

# 复制Poetry锁文件和pyproject.toml
COPY pyproject.toml poetry.lock /app/

# 配置Poetry使用国内镜像源，并设置合适的安装重试次数和超时时间
RUN poetry config repositories.aliyun https://mirrors.aliyun.com/pypi/simple/ \
    && poetry config installer.max_retries 5 \
    && poetry config installer.timeout 120 \
    && poetry install --no-interaction --no-ansi --no-dev

# 复制应用程序代码
COPY . /app

# 运行应用程序
CMD ["poetry","run","poe","webserver"]