FROM python:slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 6565
CMD ["python", "main.py"]