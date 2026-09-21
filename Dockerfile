FROM python3.12-slim
WORKDIR /ap
COPY . .
RUN pipinstall-r requirements.txt
CMD ["python", "chameleon.py"]
