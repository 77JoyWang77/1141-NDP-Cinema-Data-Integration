"""應用配置文件"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 項目根目錄
BASE_DIR = Path(__file__).parent

# MongoDB 配置
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "movie_booking")

# FastAPI 配置
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
API_TITLE = "電影票訂系統 API"
API_VERSION = "1.0.0"

# Gemini API 配置
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# 資料文件路徑
DATA_DIR = BASE_DIR / "data" / "raw"
CINEMA_FILE = DATA_DIR / "showtime" / "cinema.json"
MOVIE_FILE = DATA_DIR / "vieshow" / "movie.json"
SHOWTIME_FILE = DATA_DIR / "showtime" / "showtime.json"

# CORS 配置
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
