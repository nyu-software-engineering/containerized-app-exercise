#Python img 
FROM python:3.15.2

WORKDIR /app

# Pipenv installation

RUN pip install --no-cache-dir pipenv

COPY Pipfile Pipfile.lock ./

RUN pipenv install --system --deploy

# Flask Copy
COPY . . 

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Port

EXPOSE 5000

CMD [ "", "--bind", "0.0.0.0:5000", "app:app" ]