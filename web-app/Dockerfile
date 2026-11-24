# Python version matches the Pipfile ("3.12")
FROM python:3.12-slim

WORKDIR /app

# install dependencies first so Docker can cache this layer
COPY requirements.txt ./
RUN pip3 install -r requirements.txt

# then copy the rest of the web app code
ADD . .

# team agreed port: 5001
EXPOSE 5001

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=5001"]
