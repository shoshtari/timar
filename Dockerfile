FROM python:3.13

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /src

COPY requirements.txt /src/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /src/

CMD ["python", "main.py"]
