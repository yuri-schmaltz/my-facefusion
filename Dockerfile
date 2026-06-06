# Usar imagem oficial NVIDIA CUDA runtime baseada no Ubuntu 22.04
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Evitar prompts interativos durante instalação de pacotes do apt
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependências do sistema necessárias (Python, FFMPEG, Curl, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3-dev \
    ffmpeg \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Vincular python e python3
RUN ln -s /usr/bin/python3 /usr/bin/python

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do Python necessárias para o FaceFusion e API FastAPI
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    gradio==5.44.1 \
    gradio-rangeslider==0.0.8 \
    numpy==2.2.1 \
    onnx==1.21.0 \
    opencv-python-headless==4.10.0.84 \
    tqdm==4.67.3 \
    scipy==1.14.1 \
    fastapi==0.110.0 \
    uvicorn[standard]==0.28.0 \
    sqlalchemy==2.0.28 \
    python-multipart==0.0.9

# Instalar ONNX Runtime com suporte a aceleração por GPU (CUDA)
RUN pip install --no-cache-dir onnxruntime-gpu==1.16.3

# Copiar os arquivos do código-fonte (excluindo itens do .dockerignore)
COPY . /app

# Expor a porta da API
EXPOSE 8000

# Definir variáveis de ambiente e rodar o servidor FastAPI
ENV PYTHONPATH=/app
CMD ["python", "facefusion/api/main.py"]
