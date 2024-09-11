FROM python:3.12.5-bookworm

RUN apt-get update && apt-get install -y ffmpeg tree

# Install pip requirements before copying other files to better utilize build cache
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

RUN pip cache purge
RUN apt-get clean autoclean
RUN apt-get autoremove -y

CMD ["python3", "main.py"]
