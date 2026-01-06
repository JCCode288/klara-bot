ARG PYTHON_VER=3.13.5
ARG PYTHON_TAGS=${PYTHON_VER}-alpine

FROM python:${PYTHON_TAGS}

WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install -r ./requirements.txt

# Copy the rest of the application code
COPY . .

CMD ["python", "-u", "./main.py"]

