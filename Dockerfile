FROM python:3.8-bullseye
COPY . .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python", "-u", "main.py"]