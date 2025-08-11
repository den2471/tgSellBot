FROM python:3.13.5-slim
WORKDIR /usr/src/app
ENV CONTAINER=docker

RUN apt-get update
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6
COPY . .
CMD ["python", "bot.py"]