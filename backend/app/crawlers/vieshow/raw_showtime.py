import json
import re
import time
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


class RawShowtimeCrawler:
    def __init__(self):
        BASE_DIR = Path(__file__).resolve().parents[3]  # backend

        self.cinema_path = BASE_DIR / "data" / "raw" / "vieshow" / "vieshow_cinema.json"
        self.output_path = BASE_DIR / "data" / "raw" / "vieshow" / "vieshow_showtime.json"

        self.all_showtimes = []

    # =========================
    # Entry
    # =========================
    def run(self):
        print("=" * 60)
        print("🎬 開始爬取威秀場次（raw_showtime）")
        print("=" * 60)

        cinemas = self._load_cinemas()
        self._crawl_all_cinemas(cinemas)
        self._save()

        print("=" * 60)
        print(f"✅ raw_showtime 完成，共 {len(self.all_showtimes)} 筆")
        print("=" * 60)

    # =========================
    # Cinema list
    # =========================
    def _load_cinemas(self):
        with open(self.cinema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _crawl_all_cinemas(self, cinemas):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                locale="zh-TW",
            )

            for idx, cinema in enumerate(cinemas, 1):
                print(f"\n🏢 [{idx}/{len(cinemas)}] {cinema['name']}")
                showtimes = self._crawl_cinema(context, cinema)
                print(f"  ✅ {len(showtimes)} 筆場次")
                self.all_showtimes.extend(showtimes)

            browser.close()

    # =========================
    # Cinema detail
    # =========================
    def _crawl_cinema(self, context, cinema):
        page = context.new_page()

        page.goto(cinema["detail_url"], timeout=60000)
        time.sleep(2)

        soup = BeautifulSoup(page.content(), "html.parser")
        page.close()

        # 1️⃣ 先抓「上方日期列」對應的 article id
        date_map = {}
        for a in soup.select("#sliderDate a.haveTime"):
            date_text = a.get_text(strip=True)  # 12/14 (日)
            href = a.get("href", "")
            if href.startswith("#"):
                date_map[href[1:]] = date_text

        if not date_map:
            return []

        showtimes = []

        # 2️⃣ 只 parse 上方有列到的 article
        for article_id, date_text in date_map.items():
            article = soup.find("article", id=article_id)
            if not article:
                continue

            showtimes.extend(self._parse_article(article, cinema, date_text))

        return showtimes

    # =========================
    # Parse showtime
    # =========================
    def _parse_article(self, article, cinema, date_text):
        results = []

        cinema_id = cinema.get("cinema_id") or cinema.get("id")

        movie_cn = None
        movie_en = None
        rating = None
        current_screen_type = None

        for el in article.find_all(["h1", "h2", "h4", "ul"], recursive=True):

            # 🎬 中文名 + 分級
            if el.name == "h1":
                movie_cn = el.contents[0].strip() if el.contents else ""
                span = el.find("span")
                rating = span.get("class", [None])[0] if span else None

            # 🇬🇧 英文名
            elif el.name == "h2":
                movie_en = el.get_text(strip=True)

            # 🖥️ screen type
            elif el.name == "h4":
                current_screen_type = el.get_text(strip=True)

            # 🕒 場次
            elif el.name == "ul" and "bookList" in el.get("class", []):
                if not (movie_cn and current_screen_type):
                    continue

                for li in el.find_all("li"):
                    a = li.find("a")
                    if not a:
                        continue

                    time_text = a.get_text(strip=True)
                    is_next_day = "(隔日)" in time_text
                    time_text = time_text.replace("(隔日)", "").strip()

                    booking_href = a.get("href", "")
                    session_id = self._extract_session_id(booking_href)

                    # 🔍 往後找對應的座位查詢連結
                    seat_url = None
                    for sib in li.next_siblings:
                        if getattr(sib, "name", None) == "a":
                            href = sib.get("href", "")
                            if "SessionSeats.aspx" in href:
                                seat_url = href
                                break
                        elif getattr(sib, "name", None) == "li":
                            break  # 已經到下一場次，停止

                    results.append(
                        {
                            "cinema_id": cinema_id,
                            "cinema_name": cinema["name"],
                            "movie_title_cn": movie_cn,
                            "movie_title_en": movie_en,
                            "rating": rating,
                            "date": date_text,
                            "time": time_text,
                            "is_next_day": is_next_day,
                            "screen_type": current_screen_type,
                            "session_id": session_id,
                            "booking_url": booking_href,
                            "seat_query_url": seat_url,
                            "crawled_at": datetime.now().isoformat(),
                        }
                    )

        return results

    # =========================
    # Utils
    # =========================
    def _extract_session_id(self, url):
        m = re.search(r"txtSessionId=(\d+)", url)
        return m.group(1) if m else None

    # =========================
    # Save
    # =========================
    def _save(self):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(self.all_showtimes, f, ensure_ascii=False, indent=2)

        print(f"\n💾 已存檔：{self.output_path.resolve()}")


if __name__ == "__main__":
    RawShowtimeCrawler().run()
