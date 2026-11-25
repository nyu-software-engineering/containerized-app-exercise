FROM python:3.11-slim

# libraries mediapipe needs on the slim image
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# download ASL at build so it doesnt need to be refetched
RUN python -c "from huggingface_hub import hf_hub_download; hf_hub_download('nocontextdoruk/asl-landmark-mlp', 'mlp_asl.onnx')"

COPY . .

# port in app.py
EXPOSE 5000

CMD ["python", "app.py"]