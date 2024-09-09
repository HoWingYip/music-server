FROM python:3.12.5-alpine3.20

# Install requirements before copying to better utilize build cache
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["python3", "main.py"]
