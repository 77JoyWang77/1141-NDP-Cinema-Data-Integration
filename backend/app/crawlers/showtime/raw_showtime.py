# raw_showtime.py (秀泰版本 - 移除 seat_status)

import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


class ShowtimeRawShowtimeCrawler:
    def __init__(self):
        BASE_DIR = Path(__file__).resolve().parents[3]  # backend
        self.movie_path = BASE_DIR / "data" / "raw" / "showtime" / "showtime_movie.json"
        self.output_path = BASE_DIR / "data" / "raw" / "showtime" / "showtime_showtime.json"
        self.all_showtimes = []

    # =========================
    # Entry
    # =========================
    def run(self):
        print("=" * 60)
        print("🎬 開始爬取秀泰場次資訊（raw_showtime）")
        print("=" * 60)

        movies = self._load_movies()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                locale="zh-TW",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            )
            page = context.new_page()

            for idx, movie in enumerate(movies, 1):
                print(f"\n🎬 [{idx}/{len(movies)}] {movie['title_cn']}")
                
                showtimes = self._crawl_movie_showtimes(page, movie)
                
                if showtimes:
                    print(f"  ✅ {len(showtimes)} 筆場次")
                    self.all_showtimes.extend(showtimes)
                
                time.sleep(2)

            browser.close()

        self._save()

        print("\n" + "=" * 60)
        print(f"✅ raw_showtime 完成，共 {len(self.all_showtimes)} 個場次")
        print("=" * 60)

    # =========================
    # Load movies
    # =========================
    def _load_movies(self):
        with open(self.movie_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # =========================
    # Crawl movie showtimes
    # =========================
    def _crawl_movie_showtimes(self, page, movie):
        """爬取單部電影的場次"""
        url = movie["detail_url"]
        all_showtimes = []
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            
            # 等待影城按鈕載入
            page.wait_for_selector("button.sc-bypJrT", timeout=10000)
            
            # 取得所有影城按鈕
            cinema_buttons = page.locator("button.sc-bypJrT").all()
            print(f"  找到 {len(cinema_buttons)} 家影城")
            
            # 爬取所有影城
            for cinema_idx in range(len(cinema_buttons)):
                try:
                    # 重新定位按鈕
                    buttons = page.locator("button.sc-bypJrT").all()
                    cinema_button = buttons[cinema_idx]
                    cinema_name = cinema_button.inner_text()
                    
                    print(f"    [{cinema_idx+1}] {cinema_name}")
                    
                    # 點擊影城
                    cinema_button.click()
                    time.sleep(2)
                    
                    # 取得所有日期按鈕
                    date_divs = page.locator("div.sc-ijDOKB").all()
                    print(f"      找到 {len(date_divs)} 個日期")
                    
                    # 爬取所有日期
                    for date_idx in range(len(date_divs)):
                        try:
                            # 重新定位日期按鈕
                            date_divs = page.locator("div.sc-ijDOKB").all()
                            date_div = date_divs[date_idx]
                            
                            # 取得日期文字
                            date_spans = date_div.locator("span").all()
                            if len(date_spans) >= 2:
                                date_text = date_spans[0].inner_text()  # "12月17日"
                                weekday = date_spans[1].inner_text()     # "周三"
                                
                                print(f"        點擊日期: {date_text} {weekday}")
                                
                                # 點擊日期
                                date_div.click()
                                time.sleep(2)
                                
                                # 解析場次
                                html = page.content()
                                soup = BeautifulSoup(html, "html.parser")
                                
                                session_showtimes = self._parse_showtimes(
                                    soup,
                                    movie,
                                    cinema_name, 
                                    date_text, 
                                    weekday
                                )
                                
                                all_showtimes.extend(session_showtimes)
                                print(f"          ✅ 找到 {len(session_showtimes)} 個場次")
                        
                        except Exception as e:
                            print(f"          ❌ 爬取日期失敗: {e}")
                            continue
                    
                except Exception as e:
                    print(f"      ❌ 爬取影城失敗: {e}")
                    continue
            
        except Exception as e:
            print(f"  ❌ 爬取失敗: {e}")
        
        return all_showtimes

    # =========================
    # Parse showtimes
    # =========================
    def _parse_showtimes(self, soup, movie, cinema_name, date_text, weekday):
        """解析場次資訊"""
        showtimes = []
        
        # 找到所有場次卡片
        showtime_cards = soup.select("div.grid > div.border-brand-700")
        
        for card in showtime_cards:
            try:
                # 廳別和語言：「7廳 | HFR 英語」
                screen_info_elem = card.select_one("div.text-sm")
                if not screen_info_elem:
                    continue
                
                screen_info = screen_info_elem.get_text(strip=True)
                parts = [p.strip() for p in screen_info.split("|")]
                screen_number = parts[0] if len(parts) > 0 else None
                screen_type = parts[1] if len(parts) > 1 else None
                
                # 時間：「10:00 ~ 13:17」
                time_elem = card.select_one("div.text-lg")
                if not time_elem:
                    continue
                
                time_range = time_elem.get_text(strip=True)
                
                # 🔥 移除 seat_status 判斷（因為 bg-brand-100/50 不準確）
                showtimes.append({
                    # 電影資訊
                    "movie_id": movie["movie_id"],
                    "movie_title_cn": movie["title_cn"],
                    "movie_title_en": movie["title_en"],
                    
                    # 影城資訊
                    "cinema_name": cinema_name,
                    
                    # 場次資訊
                    "date": date_text,
                    "weekday": weekday,
                    "time_range": time_range,
                    
                    # 廳別資訊
                    "screen_number": screen_number,
                    "screen_type": screen_type,
                    
                    # 爬取時間
                    "crawled_at": datetime.now().isoformat(),
                })
                
            except Exception as e:
                continue
        
        return showtimes

    # =========================
    # Save
    # =========================
    def _save(self):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(self.all_showtimes, f, ensure_ascii=False, indent=2)

        print(f"\n💾 已存檔：{self.output_path.resolve()}")


if __name__ == "__main__":
    ShowtimeRawShowtimeCrawler().run()