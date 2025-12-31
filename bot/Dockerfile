ARG PYTHON_VER=3.13.5
ARG PYTHON_TAGS=${PYTHON_VER}-alpine

FROM python:${PYTHON_TAGS}

WORKDIR /app

# Install system dependencies required by yt-dlp
RUN apk update && apk add opus opus-dev ffmpeg

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

CMD ["python", "./bot.py"]

