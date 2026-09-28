import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


class VieshowRawMovieCrawler:
    def __init__(self):
        BASE_DIR = Path(__file__).resolve().parents[3]  # backend
        self.output_path = BASE_DIR / "data" / "raw" / "vieshow" / "vieshow_movie.json"
        self.movies = []

    # =========================
    # Entry
    # =========================
    def run(self):
        print("=" * 60)
        print("🎬 開始爬取威秀電影（raw_movie）")
        print("=" * 60)

        self._crawl_all_pages()
        self._save()

        print("=" * 60)
        print(f"✅ raw_movie 完成，共 {len(self.movies)} 部電影")
        print("=" * 60)

    # =========================
    # Movie list
    # =========================
    def _crawl_all_pages(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                locale="zh-TW",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            )
            page_obj = context.new_page()

            page = 1

            while True:
                print(f"\n📄 爬取第 {page} 頁")
                movies = self._crawl_movie_list_page(page_obj, page)

                if not movies:
                    break

                # 🔥 對每部電影進入詳細頁面爬取額外資訊
                for idx, movie in enumerate(movies, 1):
                    print(f"  [{idx}/{len(movies)}] 進入詳細頁: {movie['title_cn']}")
                    detail_info = self._crawl_movie_detail(page_obj, movie)
                    
                    if detail_info:
                        movie.update(detail_info)
                    
                    time.sleep(1)  # 避免請求過快

                self.movies.extend(movies)
                page += 1
                time.sleep(2)

            browser.close()

    def _crawl_movie_list_page(self, page_obj, page: int):
        """爬取電影列表頁"""
        url = f"https://www.vscinemas.com.tw/film/index.aspx?p={page}"

        try:
            page_obj.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(2)
            html = page_obj.content()
        except Exception as e:
            print(f"  ❌ 載入失敗: {e}")
            return []

        soup = BeautifulSoup(html, "html.parser")
        return self._parse_movie_list(soup)

    def _parse_movie_list(self, soup: BeautifulSoup) -> List[Dict]:
        """解析電影列表"""
        movies = []

        movie_list = soup.select_one("ul.movieList")
        if not movie_list:
            return movies

        for item in movie_list.select("li"):
            try:
                movie = self._parse_movie_item(item)
                if movie:
                    movies.append(movie)
                    print(f"    ✅ {movie['title_cn']}")
            except Exception as e:
                print(f"    ❌ 解析失敗: {e}")
                continue

        return movies

    def _parse_movie_item(self, item) -> Dict:
        """解析列表頁的電影卡片"""
        title_cn_elem = item.select_one(".infoArea h2 a")
        if not title_cn_elem:
            return None

        title_cn = title_cn_elem.text.strip()
        detail_href = title_cn_elem.get("href", "")
        movie_id = detail_href.split("id=")[-1] if "id=" in detail_href else None

        title_en_elem = item.select_one(".infoArea h3")
        release_elem = item.select_one(".infoArea time")

        title_en = title_en_elem.text.strip() if title_en_elem else ""
        release_date = release_elem.text.strip() if release_elem else ""

        # 分級
        rating = None
        for span in item.select("figure span"):
            for cls in span.get("class", []):
                if cls in [
                    "general",
                    "protected",
                    "parental",
                    "childview",
                    "teenager",
                    "bigchild",
                    "adult",
                    "needCheck",
                ]:
                    rating = cls
                    break

        # 放映版本標記
        theater_marks = [
            m.get_text(strip=True)
            for m in item.select(".iconArea .theaterMark")
            if m.get_text(strip=True) and m.get_text(strip=True) != "more"
        ]

        detail_url = (
            f"https://www.vscinemas.com.tw/film/{detail_href}"
            if detail_href and not detail_href.startswith("http")
            else detail_href
        )

        return {
            "movie_id": movie_id,
            "title_cn": title_cn,
            "title_en": title_en,
            "release_date": release_date,
            "rating": rating,
            "theater_marks": theater_marks,
            "detail_url": detail_url,
            "crawled_time": datetime.now().isoformat(),
        }

    # =========================
    # Movie detail (整合的部分)
    # =========================
    def _crawl_movie_detail(self, page_obj, movie: Dict) -> Dict:
        """爬取電影詳細頁面"""
        url = movie["detail_url"]

        try:
            page_obj.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(2)
            soup = BeautifulSoup(page_obj.content(), "html.parser")
            
            return self._parse_movie_detail(soup)
            
        except Exception as e:
            print(f"      ⚠️  詳細頁爬取失敗: {e}")
            return {}

    def _parse_movie_detail(self, soup: BeautifulSoup) -> Dict:
        """解析電影詳細資訊"""
        info = {}

        # 🔥 劇情簡介 (movieStory)
        story_div = soup.select_one(".movieStory .bbsArticle")
        if story_div:
            # 取得所有 <p> 標籤的文字並合併
            paragraphs = [p.get_text(strip=True) for p in story_div.select("p")]
            info["story"] = "\n\n".join(paragraphs) if paragraphs else None
        else:
            # 備用方案：直接取 .movieStory
            story_elem = soup.select_one(".movieInfo .movieStory")
            info["story"] = story_elem.get_text(strip=True) if story_elem else None

        # 🔥 table 資訊（導演、演員、類型、片長）
        for row in soup.select(".movieInfo table tr"):
            cells = row.select("td")
            if len(cells) < 2:
                continue
            
            key = cells[0]
            val = cells[1]
            
            if not key or not val:
                continue

            label = key.get_text(strip=True)
            value = val.get_text(strip=True)

            if "導演" in label:
                info["director"] = [x.strip() for x in value.split("、")]
            elif "演員" in label:
                info["actors"] = [x.strip() for x in value.split("、")]
            elif "類型" in label:
                info["genres"] = [x.strip() for x in value.split("、")]
            elif "片長" in label:
                info["runtime_text"] = value
                info["runtime_min"] = self._parse_runtime(value)

        return info

    def _parse_runtime(self, text: str) -> int:
        """解析片長文字為分鐘數"""
        # 例：3 時 17 分 → 197
        try:
            h, m = 0, 0
            if "時" in text:
                h = int(text.split("時")[0].strip())
                text = text.split("時")[1]
            if "分" in text:
                m = int(text.replace("分", "").strip())
            return h * 60 + m
        except:
            return None

    # =========================
    # Save
    # =========================
    def _save(self):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(self.movies, f, ensure_ascii=False, indent=2)

        print(f"\n💾 已存檔：{self.output_path.resolve()}")


if __name__ == "__main__":
    VieshowRawMovieCrawler().run()