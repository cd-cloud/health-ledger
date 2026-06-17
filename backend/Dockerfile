FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖：
# - poppler-utils: pdf2image 需要 pdftoppm/pdftocairo
# - tesseract-ocr + chi-sim: Tesseract OCR 兜底
# - paddleocr 运行/编译所需的系统库
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖（含 OCR 与测试）
COPY requirements.txt requirements-ocr.txt ./
RUN pip install --no-cache-dir -r requirements-ocr.txt

# 复制后端代码
COPY . /app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
