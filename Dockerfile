# 베이스 이미지를 선택합니다.
FROM python:3.11.3

# 의존성 목록을 복사하고 설치합니다.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 소스 코드를 복사합니다.
COPY . .

# 컨테이너 실행 시 uvicorn을 이용해 FastAPI 애플리케이션을 실행합니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
