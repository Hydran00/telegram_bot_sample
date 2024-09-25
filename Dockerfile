FROM python:3.10

RUN apt-get update && apt-get install -y \
    python3-pip 
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python3","-u", "telegram_bot.py"]