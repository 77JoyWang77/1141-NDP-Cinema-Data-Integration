from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uvicorn
import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

sys.path.append(str(Path(__file__).parent / "app" / "crawlers"))

from config import (
    MONGODB_URL,
    MONGODB_DB,
    CORS_ORIGINS,
    API_HOST,
    API_PORT,
    API_TITLE,
    API_VERSION,
)

# ✅ Redis 快取（可選）
REDIS_AVAILABLE = False
redis_client = None

try:
    import redis.asyncio as redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_AVAILABLE = True
    print(f"✓ Redis 快取已啟用")
except ImportError:
    print(f"⚠️  Redis 未安裝，將不使用快取（pip install redis）")

# ✅ 威秀座位爬蟲(異步 + 持久化瀏覽器)
VIESHOW_SEATS_AVAILABLE = False
vieshow_provider = None

try:
    from app.crawlers.vieshow.seat_status_provider_async import SeatStatusProvider as VieshowSeatProvider
    vieshow_provider = VieshowSeatProvider()  # ✅ 單例模式，只創建一次
    VIESHOW_SEATS_AVAILABLE = True
    print(f"✓ 威秀座位爬蟲已初始化（持久化瀏覽器）")
except ImportError as e:
    print(f"⚠️  無法導入威秀座位爬蟲: {e}")
except Exception as e:
    print(f"⚠️  威秀爬蟲初始化錯誤: {e}")

# ✅ 秀泰座位爬蟲(異步版本)
SHOWTIME_SEATS_AVAILABLE = False
showtime_provider = None

try:
    from app.crawlers.showtime.seat_status_provider_async import ShowtimeSeatStatusProvider
    
    SHOWTIME_PHONE = os.getenv("SHOWTIME_PHONE")
    SHOWTIME_PASSWORD = os.getenv("SHOWTIME_PASSWORD")
    
    if SHOWTIME_PHONE and SHOWTIME_PASSWORD:
        print(f"✓ 已讀取秀泰帳密: {SHOWTIME_PHONE[:4]}****")
        showtime_provider = ShowtimeSeatStatusProvider(
            phone=SHOWTIME_PHONE,
            password=SHOWTIME_PASSWORD
        )
        SHOWTIME_SEATS_AVAILABLE = True
        print(f"✓ 秀泰座位爬蟲已初始化（持久化瀏覽器）")
    else:
        print(f"⚠️  .env 缺少 SHOWTIME_PHONE 或 SHOWTIME_PASSWORD")
        
except ImportError as e:
    print(f"⚠️  無法導入秀泰座位爬蟲: {e}")
except Exception as e:
    print(f"⚠️  秀泰爬蟲初始化錯誤: {e}")


# Pydantic 模型
class Cinema(BaseModel):
    name: str
    chain: Optional[str] = None
    chain_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    ticket_prices: Optional[List[Dict[str, Any]]] = None
    ticket_extra_rules: Optional[str] = None

class Movie(BaseModel):
    title_cn: str
    title_en: Optional[str] = None
    runtime_min: Optional[int] = None
    rating: Optional[str] = None
    release_date: Optional[str] = None
    genres: Optional[List[str]] = None
    director: Optional[str] = None
    actors: Optional[List[str]] = None
    synopsis: Optional[str] = None
    sources: Optional[List[str]] = None
    available_cinemas: Optional[List[str]] = None
    showtime: Optional[Dict[str, Any]] = None
    vieshow: Optional[Dict[str, Any]] = None

class Showtime(BaseModel):
    chain: Optional[str] = None
    chain_name: Optional[str] = None
    cinema_name: str
    movie_id: str
    movie_title_cn: str
    movie_title_en: Optional[str] = None
    date: str
    weekday: Optional[str] = None
    time_range: Optional[str] = None
    show_time: str
    screen_number: Optional[str] = None
    screen_type: Optional[str] = None
    session_id: Optional[str] = None
    cinema_code: Optional[str] = None
    booking_url: Optional[str] = None
    seat_query_url: Optional[str] = None

class Booking(BaseModel):
    user_id: Optional[str] = None
    showtime_id: str
    movie_id: str
    cinema_name: str
    ticket_type: str
    quantity: int
    unit_price: int
    surcharge: int = 0


# FastAPI 應用
app = FastAPI(title=API_TITLE, version=API_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局數據庫連接
db = None

@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    global db, showtime_provider, SHOWTIME_SEATS_AVAILABLE, redis_client
    
    # MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB]
    
    try:
        await client.admin.command('ping')
        print(f"✓ 已連接到 MongoDB: {MONGODB_DB}")
    except Exception as e:
        print(f"✗ MongoDB 連接失敗: {e}")
    
    # Redis（可選）
    if REDIS_AVAILABLE:
        try:
            redis_client = await redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await redis_client.ping()
            print(f"✓ Redis 快取已連接")
        except Exception as e:
            print(f"⚠️  Redis 連接失敗（將不使用快取）: {e}")
            redis_client = None
    
    # 威秀爬蟲
    if VIESHOW_SEATS_AVAILABLE:
        print(f"✓ 威秀座位查詢服務: 可用")
    else:
        print(f"✗ 威秀座位查詢服務: 不可用")
    
    # 秀泰爬蟲
    if SHOWTIME_SEATS_AVAILABLE and showtime_provider:
        print(f"🚀 正在啟動秀泰座位查詢服務...")
        try:
            if await showtime_provider.login():
                print(f"✓ 秀泰座位查詢服務: 已登入並可用")
            else:
                print(f"✗ 秀泰登入失敗")
                SHOWTIME_SEATS_AVAILABLE = False
        except Exception as e:
            print(f"✗ 秀泰登入錯誤: {e}")
            SHOWTIME_SEATS_AVAILABLE = False
    else:
        print(f"✗ 秀泰座位查詢服務: 不可用")

@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    global db, showtime_provider, redis_client
    
    if db:
        db.client.close()
        print("✓ MongoDB 連接已關閉")
    
    if redis_client:
        await redis_client.close()
        print("✓ Redis 連接已關閉")
    
    # ✅ 關閉秀泰瀏覽器
    if showtime_provider:
        await showtime_provider.close()
        print("✓ 秀泰瀏覽器已關閉")
    
    # ✅ 關閉威秀瀏覽器
    if vieshow_provider:
        await vieshow_provider.close()
        print("✓ 威秀瀏覽器已關閉")

@app.get("/")
async def root():
    """根端點"""
    return {
        "message": "電影票訂系統 API",
        "version": API_VERSION,
        "services": {
            "mongodb": "已連接" if db else "未連接",
            "redis_cache": "已啟用" if redis_client else "未啟用",
            "vieshow_seats": "可用" if VIESHOW_SEATS_AVAILABLE else "不可用",
            "showtime_seats": "可用" if SHOWTIME_SEATS_AVAILABLE else "不可用"
        },
    }


# ==================== 快取輔助函數 ====================

async def get_cache(key: str) -> Optional[Dict]:
    """從 Redis 獲取快取"""
    if not redis_client:
        return None
    
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        print(f"⚠️  快取讀取失敗: {e}")
    
    return None

async def set_cache(key: str, value: Dict, expire: int = 60):
    """設置 Redis 快取"""
    if not redis_client:
        return
    
    try:
        await redis_client.setex(
            key,
            expire,
            json.dumps(value, ensure_ascii=False)
        )
    except Exception as e:
        print(f"⚠️  快取寫入失敗: {e}")


# ==================== 座位查詢端點（加入快取）====================

@app.get("/api/seats/{showtime_id}")
async def get_seats(showtime_id: str, force_refresh: bool = False):
    """
    獲取場次的即時座位資訊（帶快取）
    
    Args:
        showtime_id: 場次 ID
        force_refresh: 強制刷新（跳過快取）
    """
    try:
        # ✅ 檢查快取（除非強制刷新）
        if not force_refresh:
            cache_key = f"seats:{showtime_id}"
            cached_data = await get_cache(cache_key)
            
            if cached_data:
                print(f"💨 使用快取資料: {showtime_id}")
                cached_data["from_cache"] = True
                return cached_data
        
        # 查詢場次資料
        showtime = await db.showtimes.find_one({"_id": showtime_id})
        
        if not showtime:
            raise HTTPException(status_code=404, detail="場次不存在")
        
        chain = showtime.get('chain', 'unknown')
        seat_query_url = showtime.get('seat_query_url')
        
        print(f"\n{'='*60}")
        print(f"座位查詢請求")
        print(f"{'='*60}")
        print(f"場次 ID: {showtime_id}")
        print(f"影城鏈: {chain}")
        print(f"電影: {showtime.get('movie_title_cn')}")
        print(f"影城: {showtime.get('cinema_name')}")
        
        # ✅ 威秀座位
        if chain == 'vieshow' and VIESHOW_SEATS_AVAILABLE and seat_query_url:
            print(f"✓ 使用威秀座位爬蟲（異步）")
            # ✅ 使用全域 provider（持久化瀏覽器）
            provider = vieshow_provider
            cinema_code = showtime.get('cinema_code', '1')
            referer_url = f"https://www.vscinemas.com.tw/theater/detail.aspx?id={cinema_code}"
            
            try:
                print(f"🔍 開始爬取座位資料...")
                data = await provider.fetch(
                    seat_query_url=seat_query_url,
                    referer_url=referer_url
                )
                
                if not data:
                    raise Exception("爬蟲返回空資料")
                
                stats = provider.get_seat_stats(data['seats'])
                
                print(f"✓ 成功獲取座位資料")
                print(f"  總座位: {stats['total']}")
                print(f"  可售: {stats['available']}")
                print(f"  已售: {stats['sold']}")
                print(f"{'='*60}\n")
                
                result = {
                    "showtime_id": showtime_id,
                    "has_real_data": True,
                    "chain": chain,
                    "movie_name": data.get('movie_name'),
                    "cinema": data.get('cinema'),
                    "screen": data.get('screen'),
                    "datetime": data.get('datetime'),
                    "seats": data['seats'],
                    "stats": stats,
                    "from_cache": False
                }
                
                # ✅ 寫入快取（60秒）
                await set_cache(f"seats:{showtime_id}", result, expire=60)
                
                return result
                
            except Exception as e:
                print(f"❌ 爬取失敗: {e}")
                return generate_mock_response(showtime_id, f"威秀座位查詢失敗: {str(e)}")
        
        # ✅ 秀泰座位
        elif chain == 'showtime' and SHOWTIME_SEATS_AVAILABLE and showtime_provider:
            print(f"✓ 使用秀泰座位爬蟲（異步）")
            
            try:
                print(f"🔍 開始爬取座位資料...")
                data = await showtime_provider.fetch_single_showtime(showtime)
                
                if not data or not data.get('seats'):
                    raise Exception("爬蟲返回空資料")
                
                print(f"✓ 成功獲取座位資料")
                print(f"  總座位: {data['total']}")
                print(f"  可售: {data['available']}")
                print(f"  已售: {data['sold']}")
                print(f"{'='*60}\n")
                
                # ✅ 直接使用秀泰的原始格式（不需要轉換）
                result = {
                    "showtime_id": showtime_id,
                    "has_real_data": True,
                    "chain": chain,
                    "movie_name": data.get('movie_title_cn'),
                    "cinema": data.get('cinema_name'),
                    "screen": data.get('screen_number'),
                    "datetime": f"{data.get('date')} {data.get('time_range')}",
                    "seats": data['seats'],  # ✅ 直接使用，保留 seat_id, seat_number, row, position
                    "stats": {
                        "total": data['total'],
                        "available": data['available'],
                        "sold": data['sold'],
                        "occupancy_rate": data['occupancy_rate']
                    },
                    "from_cache": False
                }
                
                # ✅ 寫入快取（30秒，秀泰更新較慢）
                await set_cache(f"seats:{showtime_id}", result, expire=30)
                
                return result
                
            except Exception as e:
                print(f"❌ 爬取失敗: {e}")
                return generate_mock_response(showtime_id, f"秀泰座位查詢失敗: {str(e)}")
        
        # 沒有座位查詢功能
        else:
            reason = "此場次沒有座位查詢URL" if not seat_query_url else f"{chain} 座位查詢服務不可用"
            print(f"⚠️  {reason}，使用模擬資料")
            print(f"{'='*60}\n")
            return generate_mock_response(showtime_id, reason)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 座位查詢錯誤: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"座位查詢失敗: {str(e)}")


def generate_mock_response(showtime_id: str, message: str):
    """生成模擬座位響應"""
    import random
    seats = []
    for row in range(8):
        for col in range(12):
            seat_id = f"{chr(65 + row)}{col + 1}"
            seats.append({
                "seat_id": seat_id,
                "row": chr(65 + row),
                "number": col + 1,
                "status": "sold" if random.random() > 0.7 else "available"
            })
    
    total = len(seats)
    sold = sum(1 for s in seats if s['status'] == 'sold')
    available = total - sold
    
    return {
        "showtime_id": showtime_id,
        "has_real_data": False,
        "message": message,
        "seats": seats,
        "stats": {
            "total": total,
            "available": available,
            "sold": sold,
            "occupancy_rate": round(sold / total * 100, 2)
        },
        "from_cache": False
    }

# ==================== 影城端點 ====================

@app.get("/api/cinemas")
async def get_cinemas(chain: Optional[str] = None):
    """獲取所有影城"""
    try:
        query = {}
        if chain:
            query["chain"] = chain
            
        cinemas = await db.cinemas.find(query).to_list(None)
        
        for cinema in cinemas:
            cinema["_id"] = str(cinema["_id"])
        
        return cinemas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cinemas/{name}")
async def get_cinema(name: str):
    """根據名稱獲取影城詳細資訊"""
    try:
        cinema = await db.cinemas.find_one({"_id": name})
        if not cinema:
            raise HTTPException(status_code=404, detail="影城未找到")
        
        cinema["_id"] = str(cinema["_id"])
        return cinema
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 電影端點 ====================

@app.get("/api/movies")
async def get_movies(
    skip: int = Query(0, ge=0), 
    limit: int = Query(20, ge=1, le=100),
    chain: Optional[str] = None
):
    """獲取電影列表(分頁)"""
    try:
        query = {}
        if chain:
            query["sources"] = chain
        
        movies = await db.movies.find(query).skip(skip).limit(limit).to_list(None)
        
        for movie in movies:
            movie["_id"] = str(movie["_id"])
        
        return movies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/movies/{movie_id}")
async def get_movie(movie_id: str):
    """根據 ID 獲取電影詳細資訊"""
    try:
        movie = await db.movies.find_one({"_id": movie_id})
        
        if not movie:
            movie = await db.movies.find_one({
                "$or": [
                    {"showtime.id": movie_id},
                    {"vieshow.id": movie_id}
                ]
            })
        
        if not movie:
            raise HTTPException(status_code=404, detail="電影未找到")
        
        movie["_id"] = str(movie["_id"])
        return movie
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 放映場次端點 ====================

@app.get("/api/showtimes")
async def get_showtimes(
    cinema_name: Optional[str] = None,
    movie_id: Optional[str] = None,
    movie_title: Optional[str] = None,
    chain: Optional[str] = None,
    date: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """獲取放映場次(支持篩選)"""
    try:
        query = {}
        if cinema_name:
            query["cinema_name"] = cinema_name
        if movie_id:
            query["movie_id"] = movie_id
        if movie_title:
            query["movie_title_cn"] = movie_title
        if chain:
            query["chain"] = chain
        if date:
            query["date"] = {"$regex": date}

        showtimes = await db.showtimes.find(query).skip(skip).limit(limit).to_list(None)
        
        for showtime in showtimes:
            showtime["_id"] = str(showtime["_id"])
        
        return showtimes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/showtimes/cinema/{cinema_name}")
async def get_cinema_showtimes(cinema_name: str, date: Optional[str] = None):
    """獲取特定影城的放映場次"""
    try:
        query = {"cinema_name": cinema_name}
        if date:
            query["date"] = {"$regex": date}

        showtimes = await db.showtimes.find(query).to_list(None)
        
        for showtime in showtimes:
            showtime["_id"] = str(showtime["_id"])
        
        return showtimes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/showtimes/movie/{movie_id}")
async def get_movie_showtimes(movie_id: str):
    """獲取特定電影的所有放映場次"""
    try:
        showtimes = await db.showtimes.find({
            "$or": [
                {"movie_id": movie_id},
                {"movie_title_cn": movie_id}
            ]
        }).to_list(None)
        
        for showtime in showtimes:
            showtime["_id"] = str(showtime["_id"])
        
        return showtimes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 座位查詢端點 ====================

@app.get("/api/seats/{showtime_id}")
async def get_seats(showtime_id: str):
    """獲取場次的即時座位資訊"""
    try:
        showtime = await db.showtimes.find_one({"_id": showtime_id})
        
        if not showtime:
            raise HTTPException(status_code=404, detail="場次不存在")
        
        chain = showtime.get('chain', 'unknown')
        seat_query_url = showtime.get('seat_query_url')
        
        print(f"\n{'='*60}")
        print(f"座位查詢請求")
        print(f"{'='*60}")
        print(f"場次 ID: {showtime_id}")
        print(f"影城鏈: {chain}")
        print(f"電影: {showtime.get('movie_title_cn')}")
        print(f"影城: {showtime.get('cinema_name')}")
        
        # ✅ 威秀座位(異步)
        if chain == 'vieshow' and VIESHOW_SEATS_AVAILABLE and seat_query_url:
            print(f"座位查詢 URL: {seat_query_url}")
            print(f"✓ 使用威秀座位爬蟲(異步)")
            provider = VieshowSeatProvider()
            cinema_code = showtime.get('cinema_code', '1')
            referer_url = f"https://www.vscinemas.com.tw/theater/detail.aspx?id={cinema_code}"
            
            try:
                print(f"🔍 開始爬取座位資料...")
                data = await provider.fetch(
                    seat_query_url=seat_query_url,
                    referer_url=referer_url
                )
                
                if not data:
                    raise Exception("爬蟲返回空資料")
                
                stats = provider.get_seat_stats(data['seats'])
                
                print(f"✓ 成功獲取座位資料")
                print(f"  總座位: {stats['total']}")
                print(f"  可售: {stats['available']}")
                print(f"  已售: {stats['sold']}")
                print(f"{'='*60}\n")
                
                return {
                    "showtime_id": showtime_id,
                    "has_real_data": True,
                    "chain": chain,
                    "movie_name": data.get('movie_name'),
                    "cinema": data.get('cinema'),
                    "screen": data.get('screen'),
                    "datetime": data.get('datetime'),
                    "seats": data['seats'],
                    "stats": stats
                }
                
            except Exception as e:
                print(f"❌ 爬取失敗: {e}")
                print(f"使用模擬資料替代")
                print(f"{'='*60}\n")
                
                return generate_mock_response(showtime_id, f"威秀座位查詢失敗: {str(e)}")
        
        # ✅ 秀泰座位(異步版本)
        elif chain == 'showtime' and SHOWTIME_SEATS_AVAILABLE and showtime_provider:
            print(f"✓ 使用秀泰座位爬蟲(異步)")
            
            try:
                print(f"🔍 開始爬取座位資料...")
                data = await showtime_provider.fetch_single_showtime(showtime)
                
                if not data or not data.get('seats'):
                    raise Exception("爬蟲返回空資料")
                
                print(f"✓ 成功獲取座位資料")
                print(f"  總座位: {data['total']}")
                print(f"  可售: {data['available']}")
                print(f"  已售: {data['sold']}")
                print(f"{'='*60}\n")
                
                # 轉換秀泰格式到統一格式
                unified_seats = []
                for seat in data['seats']:
                    unified_seats.append({
                        "seat_id": seat['seat_number'],
                        "row": seat['seat_number'][0] if seat['seat_number'] else 'A',
                        "number": int(''.join(filter(str.isdigit, seat['seat_number']))) if seat['seat_number'] else 0,
                        "status": seat['status']
                    })
                
                return {
                    "showtime_id": showtime_id,
                    "has_real_data": True,
                    "chain": chain,
                    "movie_name": data.get('movie_title_cn'),
                    "cinema": data.get('cinema_name'),
                    "screen": data.get('screen_number'),
                    "datetime": f"{data.get('date')} {data.get('time_range')}",
                    "seats": unified_seats,
                    "stats": {
                        "total": data['total'],
                        "available": data['available'],
                        "sold": data['sold'],
                        "occupancy_rate": data['occupancy_rate']
                    }
                }
                
            except Exception as e:
                print(f"❌ 爬取失敗: {e}")
                print(f"使用模擬資料替代")
                print(f"{'='*60}\n")
                
                return generate_mock_response(showtime_id, f"秀泰座位查詢失敗: {str(e)}")
        
        # 沒有座位查詢功能
        else:
            reason = "此場次沒有座位查詢URL" if not seat_query_url else f"{chain} 座位查詢服務不可用"
            print(f"⚠️ {reason},使用模擬資料")
            print(f"{'='*60}\n")
            return generate_mock_response(showtime_id, reason)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 座位查詢錯誤: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"座位查詢失敗: {str(e)}")


def generate_mock_response(showtime_id: str, message: str):
    """生成模擬座位響應"""
    import random
    seats = []
    for row in range(8):
        for col in range(12):
            seat_id = f"{chr(65 + row)}{col + 1}"
            seats.append({
                "seat_id": seat_id,
                "row": chr(65 + row),
                "number": col + 1,
                "status": "sold" if random.random() > 0.7 else "available"
            })
    
    total = len(seats)
    sold = sum(1 for s in seats if s['status'] == 'sold')
    available = total - sold
    
    return {
        "showtime_id": showtime_id,
        "has_real_data": False,
        "message": message,
        "seats": seats,
        "stats": {
            "total": total,
            "available": available,
            "sold": sold,
            "occupancy_rate": round(sold / total * 100, 2)
        }
    }


# ==================== 其他端點(搜尋、訂票、統計)====================

@app.get("/api/showtimes")
async def get_showtimes(
    cinema_name: Optional[str] = None,
    movie_id: Optional[str] = None,
    movie_title: Optional[str] = None,
    chain: Optional[str] = None,  # 這裡參數名稱保持 chain（前端傳來的）
    date: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(None, ge=1, le=200),
):
    """獲取放映場次(支持篩選)"""
    try:
        query = {}
        if cinema_name:
            query["cinema_name"] = cinema_name
        if movie_id:
            query["movie_id"] = movie_id
        if movie_title:
            query["movie_title_cn"] = movie_title
        if chain:
            query["chain_name"] = chain  # ✅ 改這裡！資料庫欄位是 chain_name
        if date:
            query["date"] = date  # ✅ 改這裡！改為精確匹配（不用 regex）

        showtimes = await db.showtimes.find(query).skip(skip).limit(limit).to_list(None)
        
        for showtime in showtimes:
            showtime["_id"] = str(showtime["_id"])
        
        return showtimes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/showtimes/all")
async def get_all_showtimes():
    """取得所有放映場次（未來 7 天，用於前端篩選）"""
    try:
        from datetime import datetime, timedelta
        
        # 生成未來 7 天的日期
        today = datetime.now()
        dates = []
        for i in range(7):
            date = today + timedelta(days=i)
            dates.append(f"{date.month}月{date.day}日")
        
        # 只查詢未來 7 天的場次
        query = {"date": {"$in": dates}}
        
        showtimes = await db.showtimes.find(query).to_list(None)
        
        for showtime in showtimes:
            showtime["_id"] = str(showtime["_id"])
        
        return showtimes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bookings")
async def create_booking(booking: Booking):
    """建立訂票"""
    try:
        booking_doc = booking.dict()
        booking_doc["total_price"] = (
            booking.unit_price * booking.quantity + booking.surcharge
        )
        booking_doc["status"] = "pending"
        booking_doc["created_at"] = datetime.now()
        booking_doc["order_number"] = f"ORD-{int(datetime.now().timestamp())}"

        result = await db.bookings.insert_one(booking_doc)
        booking_doc["_id"] = str(result.inserted_id)

        return {
            "success": True,
            "order_id": str(result.inserted_id),
            "order_number": booking_doc["order_number"],
            "total_price": booking_doc["total_price"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bookings/{order_number}")
async def get_booking(order_number: str):
    """根據訂單號獲取訂票"""
    try:
        booking = await db.bookings.find_one({"order_number": order_number})
        if not booking:
            raise HTTPException(status_code=404, detail="訂單未找到")
        booking["_id"] = str(booking["_id"])
        return booking
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """獲取詳細統計數據"""
    try:
        stats = {
            "cinemas": {
                "total": await db.cinemas.count_documents({}),
                "showtime": await db.cinemas.count_documents({"chain": "showtime"}),
                "vieshow": await db.cinemas.count_documents({"chain": "vieshow"})
            },
            "movies": {
                "total": await db.movies.count_documents({}),
                "both": await db.movies.count_documents({"sources": {"$size": 2}}),
                "showtime_only": await db.movies.count_documents({"sources": ["showtime"]}),
                "vieshow_only": await db.movies.count_documents({"sources": ["vieshow"]})
            },
            "showtimes": {
                "total": await db.showtimes.count_documents({}),
                "showtime": await db.showtimes.count_documents({"chain": "showtime"}),
                "vieshow": await db.showtimes.count_documents({"chain": "vieshow"})
            },
            "bookings": await db.bookings.count_documents({}),
            "timestamp": datetime.now().isoformat(),
        }
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host=API_HOST, port=API_PORT)