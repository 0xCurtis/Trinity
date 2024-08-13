FROM python:3.9

WORKDIR /website

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .
COPY ../common /website/common

EXPOSE 5000

CMD ["python", "app.py"]
