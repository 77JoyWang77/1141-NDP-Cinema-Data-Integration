import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path

from app.loaders.load_movies import load_movies
from config import MONGODB_URL, MONGODB_DB


async def main():
    # 1. 連 MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB]

    # 2. 讀爬蟲產生的 movie json
    showtime_movies = json.loads(
        Path("data/raw/showtime/showtime_movie.json").read_text(encoding="utf-8")
    )

    vieshow_movies = json.loads(
        Path("data/raw/vieshow/vieshow_movie.json").read_text(encoding="utf-8")
    )

    # 3. 呼叫 loader
    await load_movies(
        db=db,
        showtime_movies=showtime_movies,
        vieshow_movies=vieshow_movies,
    )

    print("✅ movies collection 更新完成")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
