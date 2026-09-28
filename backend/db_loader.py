"""MongoDB 數據載入模組（整合版：秀泰 + 威秀）"""

import json
from pathlib import Path
from typing import List, Dict, Any
from pymongo import MongoClient
from datetime import datetime


class MongoDBLoader:
    def __init__(self, uri: str = None, db_name: str = None):
        # 使用環境變數或預設值
        self.uri = uri or "mongodb://localhost:27017/"
        self.db_name = db_name or "movie_booking"
        self.client = None
        self.db = None

        # 資料路徑
        self.BASE_DIR = Path(__file__).resolve().parent
        self.DATA_DIR = self.BASE_DIR / "data" / "raw"

        # 分級對應表
        self.RATING_MAP = {
            "general": "普遍級",
            "childview": "保護級",
            "bigchild": "輔12級",
            "teenager": "輔15級",
            "adult": "限制級",
            "needCheck": "未分級",
            "普遍級": "普遍級",
            "保護級": "保護級",
            "輔12級": "輔12級",
            "輔15級": "輔15級",
            "限制級": "限制級",
        }

        self.WEEKDAY_MAP = {
            0: "周一",
            1: "周二", 
            2: "周三",
            3: "周四",
            4: "周五",
            5: "周六",
            6: "周日"
        }

    def normalize_rating(self, rating: str) -> str:
        """將分級轉換為統一格式"""
        if not rating:
            return "普遍級"  # 預設值

        rating = rating.strip().upper()

        # 直接查表
        if rating in self.RATING_MAP:
            return self.RATING_MAP[rating]

        # 模糊匹配（如果查不到）
        rating_lower = rating.lower()
        for key, value in self.RATING_MAP.items():
            if key.lower() in rating_lower or rating_lower in key.lower():
                return value

        # 都找不到，返回原值
        return rating if rating else "普遍級"

    def normalize_release_date(self, date_str: str, source: str = "showtime") -> str:
        """將發行日期統一為 YYYY-MM-DD 格式

        秀泰格式: 2025/12/17
        威秀格式: 2025-12-17
        """
        if not date_str:
            return None

        date_str = date_str.strip()

        # 如果已是標準格式 YYYY-MM-DD，直接返回
        if len(date_str) == 10 and date_str[4] == "-" and date_str[7] == "-":
            return date_str

        # 秀泰格式: YYYY/MM/DD → YYYY-MM-DD
        if "/" in date_str:
            parts = date_str.split("/")
            if len(parts) == 3:
                return f"{parts[0]}-{parts[1]}-{parts[2]}"

        # 威秀格式: 已經是 YYYY-MM-DD
        if "-" in date_str:
            return date_str

        return date_str
    
    def parse_vieshow_date(self, date_str: str) -> tuple:
        """解析威秀日期格式並獲取星期"""
        if not date_str:
            return (None, None)
        
        try:
            # 提取日期部分 "12/22 (一)" -> "12/22"
            date_part = date_str.split(" ")[0] if " " in date_str else date_str
            
            # 解析日期（假設當前年份）
            current_year = datetime.now().year
            month, day = date_part.split("/")
            date_obj = datetime(current_year, int(month), int(day))
            
            # 格式化為 "12月22日"
            formatted_date = f"{int(month)}月{int(day)}日"
            
            # 獲取星期
            weekday_num = date_obj.weekday()
            weekday = self.WEEKDAY_MAP.get(weekday_num, "")
            
            return (formatted_date, weekday)
        except Exception as e:
            print(f"  ⚠️  解析日期失敗: {date_str}, {e}")
            return (None, None)


    def calculate_time_range(self, start_time: str, runtime_min: int) -> str:
        """計算場次的時間範圍"""
        if not start_time or not runtime_min:
            return None
        
        try:
            from datetime import timedelta
            
            # 解析開始時間
            start = datetime.strptime(start_time, "%H:%M")
            
            # 計算結束時間
            end = start + timedelta(minutes=runtime_min)
            
            # 格式化
            return f"{start.strftime('%H:%M')} ~ {end.strftime('%H:%M')}"
        except Exception as e:
            print(f"  ⚠️  計算時間範圍失敗: {e}")
            return None

    def clean_movie_data(self, movie: dict, source: str) -> dict:
        """清理電影數據

        1. 移除 release_date_detail，只保留 release_date
        2. 標準化日期格式
        3. 標記電影ID來源
        """
        # 標準化發行日期
        if "release_date" in movie:
            movie["release_date"] = self.normalize_release_date(
                movie["release_date"], source
            )

        # 刪除不需要的欄位
        if "release_date_detail" in movie:
            del movie["release_date_detail"]

        return movie

    def get_available_cinemas_for_movie(
        self, movie_id_or_title: str, source: str, is_title: bool = False
    ) -> list:
        """從 showtimes 獲取特定電影的上映影城列表

        Args:
            movie_id_or_title: 電影ID (秀泰) 或片名 (威秀)
            source: "showtime" 或 "vieshow"
            is_title: 是否按片名查詢 (威秀用)

        Returns:
            影城名稱列表，已排序去重
        """
        try:
            showtimes_file = self.DATA_DIR / source / f"{source}_showtime.json"
            if showtimes_file.exists():
                with open(showtimes_file, "r", encoding="utf-8") as f:
                    showtimes = json.load(f)
                    cinemas = set()

                    for showtime in showtimes:
                        match = False

                        if is_title:
                            # 威秀：按 movie_title_cn 查詢
                            if showtime.get("movie_title_cn") == movie_id_or_title:
                                match = True
                        else:
                            # 秀泰：按 movie_id 查詢
                            if showtime.get("movie_id") == movie_id_or_title:
                                match = True

                        if match:
                            cinema_name = showtime.get("cinema_name")
                            if cinema_name:
                                cinemas.add(cinema_name)

                    return sorted(list(cinemas))
        except Exception as e:
            pass
        return []

    def connect(self):
        """連接到 MongoDB"""
        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]
        # 測試連接
        self.db.command("ping")
        print("✓ MongoDB 連接成功")

    def disconnect(self):
        """斷開 MongoDB 連接"""
        if self.client:
            self.client.close()
            print("✓ MongoDB 連接已關閉")

    def clear_collections(self):
        """清空所有集合（準備重新載入數據）"""
        collections = self.db.list_collection_names()
        for collection in collections:
            self.db[collection].delete_many({})
        print(f"✓ 已清空 {len(collections)} 個集合")

    def load_cinemas(self) -> int:
        """載入影城數據（秀泰 + 威秀）"""
        try:
            all_cinemas = []

            # 載入秀泰影城
            showtime_cinema_path = self.DATA_DIR / "showtime" / "showtime_cinema.json"
            if showtime_cinema_path.exists():
                with open(showtime_cinema_path, "r", encoding="utf-8") as f:
                    showtime_cinemas = json.load(f)
                    for cinema in showtime_cinemas:
                        cinema["_id"] = cinema.get("name")
                        cinema["chain"] = "showtime"
                        cinema["chain_name"] = "秀泰影城"
                        all_cinemas.append(cinema)
                print(f"  ✓ 載入秀泰影城: {len(showtime_cinemas)} 間")

            # 載入威秀影城
            vieshow_cinema_path = self.DATA_DIR / "vieshow" / "vieshow_cinema.json"
            if vieshow_cinema_path.exists():
                with open(vieshow_cinema_path, "r", encoding="utf-8") as f:
                    vieshow_cinemas = json.load(f)
                    for cinema in vieshow_cinemas:
                        cinema["_id"] = cinema.get("name")
                        cinema["chain"] = "vieshow"
                        cinema["chain_name"] = "威秀影城"
                        all_cinemas.append(cinema)
                print(f"  ✓ 載入威秀影城: {len(vieshow_cinemas)} 間")

            if all_cinemas:
                result = self.db.cinemas.insert_many(all_cinemas)
                print(f"✓ 總計載入 {len(result.inserted_ids)} 間影城")
                return len(result.inserted_ids)

            return 0
        except Exception as e:
            print(f"✗ 載入影城失敗: {e}")
            import traceback

            traceback.print_exc()
            return 0

    def load_movies(self) -> int:
        """載入電影數據（用 title_cn 去重合併，清楚標記來源）

        結構：
        {
          "_id": "片名中文",
          "title_cn": "片名中文",
          "title_en": "English Title",
          "rating": "限制級",
          "release_date": "2025-12-17",
          "genres": ["動作", "冒險"],
          "runtime_min": 130,
          "actors": ["演員1", "演員2"],
          "director": "導演名字",
          "synopsis": "劇情簡介",
          "sources": ["showtime", "vieshow"],
          "available_cinemas": ["影城A", "影城B"],  ← 所有上映影城的合併列表
          "showtime": {
            "id": "秀泰電影ID",
            "release_date": "2025/12/17",
            "available_cinemas": ["秀泰影城A", "秀泰影城B"]  ← 秀泰專屬
          },
          "vieshow": {
            "id": "威秀電影ID",
            "release_date": "2025-12-17",
            "available_cinemas": ["威秀影城A", "威秀影城B"]  ← 威秀專屬
          }
        }
        """
        try:
            movies_dict = {}  # key: title_cn, value: movie data

            # 載入秀泰電影
            showtime_movie_path = self.DATA_DIR / "showtime" / "showtime_movie.json"
            if showtime_movie_path.exists():
                with open(showtime_movie_path, "r", encoding="utf-8") as f:
                    showtime_movies = json.load(f)
                    for movie in showtime_movies:
                        title_cn = movie.get("title_cn")
                        if title_cn:
                            movie = self.clean_movie_data(movie, "showtime")

                            if "rating" in movie:
                                movie["rating"] = self.normalize_rating(movie["rating"])

                            # 獲取秀泰的上映影城
                            showtime_cinemas = self.get_available_cinemas_for_movie(
                                movie.get("movie_id"), "showtime"
                            )

                            if title_cn not in movies_dict:
                                # 第一次看到這部電影
                                base_movie = {
                                    "_id": title_cn,
                                    "title_cn": title_cn,
                                    "sources": ["showtime"],
                                    "available_cinemas": showtime_cinemas.copy(),  # 先用秀泰的
                                    "showtime": {
                                        "id": movie.get("movie_id"),
                                        "release_date": movie.get("release_date"),
                                        "available_cinemas": showtime_cinemas,
                                    },
                                    "vieshow": {},
                                }

                                # 複製公共欄位
                                if movie.get("title_en"):
                                    base_movie["title_en"] = movie["title_en"]
                                if movie.get("release_date"):
                                    base_movie["release_date"] = movie["release_date"]
                                if movie.get("rating"):
                                    base_movie["rating"] = movie["rating"]
                                if movie.get("genres"):
                                    base_movie["genres"] = (
                                        movie["genres"]
                                        if isinstance(movie["genres"], list)
                                        else [movie["genres"]]
                                    )
                                if movie.get("runtime_min"):
                                    base_movie["runtime_min"] = movie["runtime_min"]
                                if movie.get("director"):
                                    base_movie["director"] = movie["director"]
                                if movie.get("cast"):
                                    base_movie["actors"] = (
                                        movie["cast"]
                                        if isinstance(movie["cast"], list)
                                        else [movie["cast"]]
                                    )
                                if movie.get("synopsis"):
                                    base_movie["synopsis"] = movie["synopsis"]

                                movies_dict[title_cn] = base_movie
                            else:
                                # 電影已存在，添加秀泰資料
                                if "showtime" not in movies_dict[title_cn]["sources"]:
                                    movies_dict[title_cn]["sources"].append("showtime")

                                movies_dict[title_cn]["showtime"] = {
                                    "id": movie.get("movie_id"),
                                    "release_date": movie.get("release_date"),
                                    "available_cinemas": showtime_cinemas,
                                }

                                # 合併外層 available_cinemas
                                existing = set(
                                    movies_dict[title_cn]["available_cinemas"]
                                )
                                existing.update(showtime_cinemas)
                                movies_dict[title_cn]["available_cinemas"] = sorted(
                                    list(existing)
                                )

                                # 補充缺失的公共欄位
                                if not movies_dict[title_cn].get(
                                    "title_en"
                                ) and movie.get("title_en"):
                                    movies_dict[title_cn]["title_en"] = movie[
                                        "title_en"
                                    ]
                                if not movies_dict[title_cn].get(
                                    "genres"
                                ) and movie.get("genres"):
                                    movies_dict[title_cn]["genres"] = (
                                        movie["genres"]
                                        if isinstance(movie["genres"], list)
                                        else [movie["genres"]]
                                    )
                                if not movies_dict[title_cn].get(
                                    "runtime_min"
                                ) and movie.get("runtime_min"):
                                    movies_dict[title_cn]["runtime_min"] = movie[
                                        "duration"
                                    ]
                                if not movies_dict[title_cn].get(
                                    "actors"
                                ) and movie.get("cast"):
                                    movies_dict[title_cn]["actors"] = (
                                        movie["cast"]
                                        if isinstance(movie["cast"], list)
                                        else [movie["cast"]]
                                    )

                print(f"  ✓ 載入秀泰電影: {len(showtime_movies)} 部")

            # 載入威秀電影
            vieshow_movie_path = self.DATA_DIR / "vieshow" / "vieshow_movie.json"
            if vieshow_movie_path.exists():
                with open(vieshow_movie_path, "r", encoding="utf-8") as f:
                    vieshow_movies = json.load(f)
                    for movie in vieshow_movies:
                        title_cn = movie.get("title_cn")
                        if title_cn:
                            movie = self.clean_movie_data(movie, "vieshow")

                            if "rating" in movie:
                                movie["rating"] = self.normalize_rating(movie["rating"])

                            # 從威秀 showtime 數據獲取可用影城（按片名查詢）
                            vieshow_cinemas = self.get_available_cinemas_for_movie(
                                title_cn, "vieshow", is_title=True
                            )

                            if title_cn not in movies_dict:
                                # 第一次看到這部電影
                                base_movie = {
                                    "_id": title_cn,
                                    "title_cn": title_cn,
                                    "sources": ["vieshow"],
                                    "available_cinemas": vieshow_cinemas.copy(),  # 先用威秀的
                                    "showtime": {},
                                    "vieshow": {
                                        "id": movie.get("movie_id"),
                                        "release_date": movie.get("release_date"),
                                        "available_cinemas": vieshow_cinemas,
                                    },
                                }

                                # 複製公共欄位
                                if movie.get("title_en"):
                                    base_movie["title_en"] = movie["title_en"]
                                if movie.get("release_date"):
                                    base_movie["release_date"] = movie["release_date"]
                                if movie.get("rating"):
                                    base_movie["rating"] = movie["rating"]
                                if movie.get("genres"):
                                    base_movie["genres"] = (
                                        movie["genres"]
                                        if isinstance(movie["genres"], list)
                                        else [movie["genres"]]
                                    )
                                if movie.get("runtime_min"):
                                    base_movie["runtime_min"] = movie["runtime_min"]
                                if movie.get("director"):
                                    base_movie["director"] = movie["director"]
                                if movie.get("cast"):
                                    base_movie["actors"] = (
                                        movie["cast"]
                                        if isinstance(movie["cast"], list)
                                        else [movie["cast"]]
                                    )
                                if movie.get("synopsis"):
                                    base_movie["synopsis"] = movie["synopsis"]

                                movies_dict[title_cn] = base_movie
                            else:
                                # 電影已存在，添加威秀資料
                                if "vieshow" not in movies_dict[title_cn]["sources"]:
                                    movies_dict[title_cn]["sources"].append("vieshow")

                                movies_dict[title_cn]["vieshow"] = {
                                    "id": movie.get("movie_id"),
                                    "release_date": movie.get("release_date"),
                                    "available_cinemas": vieshow_cinemas,
                                }

                                # 合併外層 available_cinemas
                                existing = set(
                                    movies_dict[title_cn]["available_cinemas"]
                                )
                                existing.update(vieshow_cinemas)
                                movies_dict[title_cn]["available_cinemas"] = sorted(
                                    list(existing)
                                )

                                # 補充缺失的公共欄位，genres 和 actors 需要合併
                                if not movies_dict[title_cn].get(
                                    "title_en"
                                ) and movie.get("title_en"):
                                    movies_dict[title_cn]["title_en"] = movie[
                                        "title_en"
                                    ]

                                # 合併 genres
                                if movie.get("genres"):
                                    new_genres = (
                                        movie["genres"]
                                        if isinstance(movie["genres"], list)
                                        else [movie["genres"]]
                                    )
                                    if "genres" in movies_dict[title_cn]:
                                        existing_genres = set(
                                            movies_dict[title_cn]["genres"]
                                        )
                                        existing_genres.update(new_genres)
                                        movies_dict[title_cn]["genres"] = sorted(
                                            list(existing_genres)
                                        )
                                    else:
                                        movies_dict[title_cn]["genres"] = new_genres

                                if not movies_dict[title_cn].get(
                                    "runtime_min"
                                ) and movie.get("runtime_min"):
                                    movies_dict[title_cn]["runtime_min"] = movie[
                                        "duration"
                                    ]

                                # 合併 actors
                                if movie.get("cast"):
                                    new_actors = (
                                        movie["cast"]
                                        if isinstance(movie["cast"], list)
                                        else [movie["cast"]]
                                    )
                                    if "actors" in movies_dict[title_cn]:
                                        existing_actors = set(
                                            movies_dict[title_cn]["actors"]
                                        )
                                        existing_actors.update(new_actors)
                                        movies_dict[title_cn]["actors"] = sorted(
                                            list(existing_actors)
                                        )
                                    else:
                                        movies_dict[title_cn]["actors"] = new_actors

                print(f"  ✓ 載入威秀電影: {len(vieshow_movies)} 部")

            movies_list = list(movies_dict.values())

            if movies_list:
                result = self.db.movies.insert_many(movies_list)
                print(f"✓ 總計載入 {len(result.inserted_ids)} 部電影（已去重）")
                return len(result.inserted_ids)

            return 0
        except Exception as e:
            print(f"✗ 載入電影失敗: {e}")
            import traceback

            traceback.print_exc()
            return 0

    def load_showtimes(self) -> int:
        """載入放映場次數據（秀泰 + 威秀）"""
        try:
            all_showtimes = []
            counter = 0

            # 載入秀泰場次
            showtime_path = self.DATA_DIR / "showtime" / "showtime_showtime.json"

            if showtime_path.exists():
                with open(showtime_path, "r", encoding="utf-8") as f:
                    showtime_showtimes = json.load(f)
                    for showtime in showtime_showtimes:
                        # 解析時間
                        time_range = showtime.get("time_range", "")
                        show_time = None
                        if time_range and "~" in time_range:
                            show_time = time_range.split("~")[0].strip()

                        processed_showtime = {
                            "_id": f"showtime_{counter}",
                            "chain": "showtime",
                            "chain_name": "秀泰影城",
                            **showtime,
                            "show_time": show_time,
                            "created_at": showtime.get(
                                "crawled_at", datetime.now().isoformat()
                            ),
                        }
                        all_showtimes.append(processed_showtime)
                        counter += 1
                print(f"  ✓ 載入秀泰場次: {len(showtime_showtimes)} 場")

            # 載入威秀場次
            vieshow_showtime_path = self.DATA_DIR / "vieshow" / "vieshow_showtime.json"
            if vieshow_showtime_path.exists():
                with open(vieshow_showtime_path, "r", encoding="utf-8") as f:
                    vieshow_showtimes = json.load(f)
                    
                    for showtime in vieshow_showtimes:
                        # 威秀的時間格式：time = "08:45"
                        show_time = showtime.get("time")
                        
                        # ✅ 解析日期和星期
                        date_str = showtime.get("date", "")  # "12/22 (一)"
                        formatted_date, weekday = self.parse_vieshow_date(date_str)
                        
                        # ✅ 獲取電影時長並計算 time_range
                        movie_title_cn = showtime.get("movie_title_cn")
                        runtime_min = None
                        time_range = None
                        
                        if movie_title_cn:
                            # 從 movies collection 查詢電影時長
                            movie = self.db.movies.find_one(
                                {"title_cn": movie_title_cn},
                                {"runtime_min": 1}
                            )
                            if movie and movie.get("runtime_min"):
                                runtime_min = movie["runtime_min"]
                                time_range = self.calculate_time_range(show_time, runtime_min)
                        
                        # ✅ 建立精簡格式的場次資料
                        processed_showtime = {
                            "_id": f"vieshow_{counter}",
                            "chain": "vieshow",
                            "chain_name": "威秀影城",
                            "cinema_name": showtime.get("cinema_name"),
                            "movie_title_cn": movie_title_cn,
                            "movie_title_en": showtime.get("movie_title_en"),
                            "date": formatted_date,
                            "weekday": weekday,
                            "show_time": show_time,
                            "time_range": time_range,
                            "screen_type": showtime.get("screen_type"),
                            "session_id": showtime.get("session_id"),
                            "booking_url": showtime.get("booking_url"),
                            "seat_query_url": showtime.get("seat_query_url"),
                            "created_at": showtime.get("crawled_at", datetime.now().isoformat()),
                        }
                        all_showtimes.append(processed_showtime)
                        counter += 1
                
                print(f"  ✓ 載入威秀場次: {len(vieshow_showtimes)} 場")

            if all_showtimes:
                result = self.db.showtimes.insert_many(all_showtimes)
                print(f"✓ 總計載入 {len(result.inserted_ids)} 場放映場次")
                return len(result.inserted_ids)

            return 0
        except Exception as e:
            print(f"✗ 載入放映場次失敗: {e}")
            import traceback

            traceback.print_exc()
            return 0

    def create_indexes(self):
        """建立索引以提高查詢性能"""
        try:
            # 影城索引
            self.db.cinemas.create_index("name")
            self.db.cinemas.create_index("chain")

            # 電影索引
            self.db.movies.create_index("title_cn")
            self.db.movies.create_index("title_en")
            self.db.movies.create_index("sources")
            self.db.movies.create_index("showtime.id")
            self.db.movies.create_index("vieshow.id")

            # 放映場次索引
            self.db.showtimes.create_index("chain")
            self.db.showtimes.create_index("cinema_name")
            self.db.showtimes.create_index("movie_id")
            self.db.showtimes.create_index("movie_title_cn")
            self.db.showtimes.create_index("date")
            self.db.showtimes.create_index([("date", 1), ("cinema_name", 1)])
            self.db.showtimes.create_index([("movie_title_cn", 1), ("chain", 1)])

            # 訂票記錄索引
            self.db.bookings.create_index("order_number", unique=True)
            self.db.bookings.create_index("user_id")
            self.db.bookings.create_index("showtime_id")

            print("✓ 已建立數據庫索引")
        except Exception as e:
            print(f"⚠ 建立索引部分失敗: {e}")

    def show_summary(self):
        """顯示數據庫摘要"""
        try:
            # 影城統計
            cinema_count = self.db.cinemas.count_documents({})
            showtime_cinema_count = self.db.cinemas.count_documents(
                {"chain": "showtime"}
            )
            vieshow_cinema_count = self.db.cinemas.count_documents({"chain": "vieshow"})

            # 電影統計
            movie_count = self.db.movies.count_documents({})
            both_sources = self.db.movies.count_documents({"sources": {"$size": 2}})
            only_showtime = self.db.movies.count_documents({"sources": ["showtime"]})
            only_vieshow = self.db.movies.count_documents({"sources": ["vieshow"]})

            # 場次統計
            showtime_count = self.db.showtimes.count_documents({})
            showtime_showtime_count = self.db.showtimes.count_documents(
                {"chain": "showtime"}
            )
            vieshow_showtime_count = self.db.showtimes.count_documents(
                {"chain": "vieshow"}
            )

            # 訂票統計
            booking_count = self.db.bookings.count_documents({})

            print("\n" + "=" * 60)
            print("【MongoDB 數據摘要】")
            print("=" * 60)
            print(f"\n📍 影城: {cinema_count} 間")
            print(f"   ├─ 秀泰: {showtime_cinema_count} 間")
            print(f"   └─ 威秀: {vieshow_cinema_count} 間")

            print(f"\n🎬 電影: {movie_count} 部")
            print(f"   ├─ 兩邊都有: {both_sources} 部")
            print(f"   ├─ 僅秀泰: {only_showtime} 部")
            print(f"   └─ 僅威秀: {only_vieshow} 部")

            print(f"\n🎞️  放映場次: {showtime_count} 場")
            print(f"   ├─ 秀泰: {showtime_showtime_count} 場")
            print(f"   └─ 威秀: {vieshow_showtime_count} 場")

            print(f"\n🎫 訂票記錄: {booking_count} 筆")
            print("=" * 60)

            # 顯示範例電影
            sample_movie = self.db.movies.find_one({"sources": {"$size": 2}})
            if sample_movie:
                print(f"\n📋 範例電影（兩邊都有）:")
                print(f"   片名: {sample_movie['title_cn']}")
                print(f"   秀泰 ID: {sample_movie['showtime'].get('id', 'N/A')}")
                print(f"   威秀 ID: {sample_movie['vieshow'].get('id', 'N/A')}")
                print(f"   來源: {', '.join(sample_movie['sources'])}")

        except Exception as e:
            print(f"✗ 顯示摘要失敗: {e}")
            import traceback

            traceback.print_exc()

    def init_all(self):
        """執行完整初始化流程"""
        print("=" * 60)
        print("🚀 開始 MongoDB 初始化（秀泰 + 威秀整合）")
        print("=" * 60)
        print()

        self.connect()
        print()

        self.clear_collections()
        print()

        self.load_cinemas()
        print()

        self.load_movies()
        print()

        self.load_showtimes()
        print()

        self.create_indexes()
        print()

        self.show_summary()
        print()

        self.disconnect()


def main():
    """主程序"""
    loader = MongoDBLoader()
    loader.init_all()


if __name__ == "__main__":
    main()