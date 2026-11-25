FROM python:3.13-slim-trixie

# libraries opencv needs (ultralytics uses opencv)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0t64 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir pipenv
COPY Pipfile Pipfile.lock ./

# install from the lock file, but get torch from the CPU-only index and
# skip the nvidia/triton GPU packages so the image stays small
RUN pipenv requirements | grep -vE '^(nvidia-|triton)' > requirements.txt \
    && pip install --no-cache-dir -r requirements.txt \
       --extra-index-url https://download.pytorch.org/whl/cpu

# download the model weights at build time
RUN python -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"

COPY . .

CMD ["python", "worker.py"]