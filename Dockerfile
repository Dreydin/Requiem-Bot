FROM python:3.12-slim
WORKDIR /ap
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD
