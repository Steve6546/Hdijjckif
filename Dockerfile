FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN npm install -g eslint prettier
COPY .eslintrc.json .
COPY .prettierrc .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]