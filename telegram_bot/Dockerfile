FROM python:3.12.5-bookworm

RUN apt-get update && apt-get install -y ffmpeg tree && rm -rf /var/lib/apt/lists/*

# Install pip requirements before copying other files to better utilize build cache
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt && pip cache purge

COPY . .

CMD ["python3", "main.py"]
