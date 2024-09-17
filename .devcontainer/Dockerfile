FROM --platform=linux/amd64 python:3.10-slim

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    procps \
    lsb-release \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 - \
    && echo "export PATH=\$PATH:/root/.local/bin" >> ~/.bashrc
    
RUN mkdir /workspace
WORKDIR /workspace

# Update pip to the latest version
RUN pip install --upgrade pip

CMD ["bash"]
