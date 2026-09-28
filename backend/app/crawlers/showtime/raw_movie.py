import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


class ShowtimeRawMovieCrawler:
    def __init__(self):
        BASE_DIR = Path(__file__).resolve().parents[3]  # backend
        self.output_path = BASE_DIR / "data" / "raw" / "showtime" / "showtime_movie.json"
        self.movies = []

    # =========================
    # Entry
    # =========================
    def run(self):
        print("=" * 60)
        print("🎬 開始爬取秀泰電影（raw_movie）")
        print("=" * 60)

        self._crawl_all_pages()
        self._save()

        print("=" * 60)
        print(f"✅ raw_movie 完成，共 {len(self.movies)} 部電影")
        print("=" * 60)

    # =========================
    # Movie list (SPA, click-based)
    # =========================
    def _crawl_all_pages(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                locale="zh-TW",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            )
            page = context.new_page()

            url = "https://www.showtimes.com.tw/programs"
            
            print(f"\n📄 爬取電影列表：{url}")
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 等待頁面載入
            page.wait_for_selector("div.sc-dcJsrY.jhxKAx", timeout=60000)
            time.sleep(2)
            
            # 🔥 找到所有標題區塊
            title_divs = page.locator("div.sc-dcJsrY.jhxKAx").all()
            
            now_showing_index = None
            
            for idx, title_div in enumerate(title_divs):
                try:
                    text = title_div.inner_text(timeout=3000)
                    print(f"找到區塊 {idx+1}：{text}")
                    
                    if "現正熱映" in text:
                        now_showing_index = idx
                        break
                except:
                    continue
            
            if now_showing_index is None:
                print("❌ 找不到「現正熱映」區塊")
                browser.close()
                return
            
            print(f"✅ 找到「現正熱映」區塊（索引 {now_showing_index}）")
            
            # 🔥 找到「現正熱映」對應的電影容器區塊
            all_movie_sections = page.locator("div.sc-aXZVg.ilOWSk").all()
            
            if now_showing_index >= len(all_movie_sections):
                print("❌ 找不到對應的電影區塊")
                browser.close()
                return
            
            now_showing_section = all_movie_sections[now_showing_index]
            
            # 🔥 計算該區塊內的電影卡片
            cards = now_showing_section.locator("div.sc-kOPcWz")
            cards_count = cards.count()
            print(f"找到 {cards_count} 部現正熱映電影")
            
            # 🔥 逐一點擊取得 detail_url 並爬取詳細資訊
            for i in range(cards_count):
                try:
                    # 🔥 重新定位區塊
                    all_movie_sections = page.locator("div.sc-aXZVg.ilOWSk").all()
                    now_showing_section = all_movie_sections[now_showing_index]
                    
                    # 取得卡片
                    cards = now_showing_section.locator("div.sc-kOPcWz")
                    card = cards.nth(i)
                    
                    # 解析卡片內容（基本資訊）
                    card_html = card.inner_html()
                    soup = BeautifulSoup(card_html, "html.parser")
                    
                    movie = self._parse_movie_item(soup)
                    if not movie:
                        print(f"  ⚠️  [{i+1}/{cards_count}] 解析失敗，跳過")
                        continue
                    
                    # 🔥 點擊卡片進入詳細頁面
                    clickable = card.locator("a").first
                    clickable.click()
                    
                    # 等待頁面跳轉
                    page.wait_for_url("**/programs/**", timeout=10000)
                    movie["detail_url"] = page.url
                    movie["movie_id"] = page.url.rstrip("/").split("/")[-1]
                    
                    print(f"  ✅ [{i+1}/{cards_count}] {movie['title_cn']}")
                    
                    # 🔥 等待詳細頁面載入並爬取額外資訊
                    time.sleep(3)
                    detail_html = page.content()
                    detail_soup = BeautifulSoup(detail_html, "html.parser")
                    
                    # 解析詳細資訊
                    movie_info = self._parse_movie_info(detail_soup)
                    synopsis = self._parse_synopsis(detail_soup)
                    
                    # 合併資訊
                    movie.update(movie_info)
                    movie["synopsis"] = synopsis
                    
                    self.movies.append(movie)
                    
                    # 🔥 返回列表頁
                    page.go_back()
                    page.wait_for_selector("div.sc-dcJsrY.jhxKAx", timeout=10000)
                    time.sleep(1.5)
                    
                except Exception as e:
                    print(f"  ❌ 處理第 {i+1} 部電影失敗: {e}")
                    try:
                        page.go_back()
                        page.wait_for_selector("div.sc-dcJsrY.jhxKAx", timeout=10000)
                        time.sleep(1)
                    except:
                        pass
                    continue

            browser.close()

    # =========================
    # Parse movie card (列表頁基本資訊)
    # =========================
    def _parse_movie_item(self, soup: BeautifulSoup) -> Dict:
        """解析電影卡片的基本資訊"""
        try:
            # 中文標題
            title_cn_elem = soup.select_one("div.sc-cWSHoV")
            if not title_cn_elem:
                return None
            title_cn = title_cn_elem.get_text(strip=True)
            
            # 英文標題
            title_en_elem = soup.select_one("div.sc-eBMEME")
            title_en = title_en_elem.get_text(strip=True) if title_en_elem else ""
            
            # 上映日期
            date_elem = soup.select_one("div.sc-dCFHLb")
            release_date = date_elem.get_text(strip=True) if date_elem else ""
            release_date = release_date.replace("上映日期：", "").replace("活動日期：", "")
            
            # 分級
            rating = None
            rating_div = soup.select_one("div.sc-dtInlm")
            if rating_div:
                classes = rating_div.get("class", [])
                rating_map = {
                    "bEwoGm": "普遍級",
                    "cdbeQZ": "保護級", 
                    "iyepch": "輔12級",
                    "VAQui":  "輔15級",
                    "fJqkNT": "限制級",
                    "jtKTxD": "未分級",
                }
                for cls in classes:
                    if cls in rating_map:
                        rating = rating_map[cls]
                        break
            
            # 放映版本標記
            theater_marks = []
            for mark_div in soup.select("div[style*='rotate']"):
                text = mark_div.get_text(strip=True)
                if text and text not in ["元旦應援場", "約會場", "特別場", "韓式炸雞場", "微醺加碼場", "好評再加場", "相愛永恆場", "應援場"]:
                    theater_marks.append(text)
            
            return {
                "movie_id": None,  # 稍後補上
                "title_cn": title_cn,
                "title_en": title_en,
                "release_date": release_date,
                "rating": rating,
                "theater_marks": theater_marks,
                "detail_url": None,  # 稍後補上
                "status": "now_showing",
                "crawled_time": datetime.now().isoformat(),
            }
            
        except Exception as e:
            print(f"    ❌ 解析失敗: {e}")
            return None

    # =========================
    # Parse movie info (詳細頁額外資訊)
    # =========================
    def _parse_movie_info(self, soup: BeautifulSoup) -> Dict:
        """解析電影詳細資訊（級別、片長、類型、演員、導演等）"""
        info = {}
        
        # 找到所有資訊行
        info_rows = soup.select("div.sc-jlGgGc.biPqRy")
        
        for row in info_rows:
            label_elem = row.select_one("div.sc-gplwa-d.hDoOny")
            value_elem = row.select_one("div.sc-cTTdyq.iOPimt")
            
            if not label_elem or not value_elem:
                continue
            
            label = label_elem.get_text(strip=True)
            
            # 級別（從 class 判斷，可能與列表頁重複但更準確）
            if label == "級別":
                rating_div = value_elem.select_one("div.sc-dtInlm")
                if rating_div:
                    classes = rating_div.get("class", [])
                    rating_map = {
                        "bEwoGm": "普遍級",
                        "hKYttV": "保護級",
                        "cdbeQZ": "保護級",
                        "iyepch": "輔12級",
                        "VAQui": "輔15級",
                        "fJqkNT": "限制級",
                        "jtKTxD": "未分級",
                    }
                    for cls in classes:
                        if cls in rating_map:
                            info["rating_detail"] = rating_map[cls]
                            break
            
            # 片長
            elif label == "片長":
                duration_text = value_elem.get_text(strip=True)
                duration_match = duration_text.replace("分", "").strip()
                try:
                    info["runtime_min"] = int(duration_match)
                    info["runtime_text"] = duration_text
                except:
                    info["runtime_text"] = duration_text
            
            # 上映日（詳細頁可能有完整日期）
            elif label == "上映日":
                release_date_detail = value_elem.get_text(strip=True)
                if release_date_detail:
                    info["release_date_detail"] = release_date_detail
            
            # 上映影城
            elif label == "上映影城":
                cinemas_text = value_elem.get_text(strip=True)
                info["available_cinemas"] = [c.strip() for c in cinemas_text.split("，")]
            
            # 類型
            elif label == "類型":
                genres_text = value_elem.get_text(strip=True)
                info["genres"] = [g.strip() for g in genres_text.split("，")]
            
            # 演員
            elif label == "演員":
                actors_text = value_elem.get_text(strip=True)
                info["actors"] = [a.strip() for a in actors_text.split("，")]
            
            # 導演
            elif label == "導演":
                info["director"] = value_elem.get_text(strip=True)
        
        return info

    # =========================
    # Parse synopsis
    # =========================
    def _parse_synopsis(self, soup: BeautifulSoup) -> str:
        """解析簡介"""
        synopsis_rows = soup.select("div.sc-jlGgGc.biPqRy")
        
        for row in synopsis_rows:
            label = row.select_one("div.sc-gplwa-d.hDoOny")
            if label and "簡介" in label.get_text():
                content_div = row.select_one("div.sc-rPWID.iPjMGL")
                if content_div:
                    return content_div.get_text(strip=True)
        
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
    ShowtimeRawMovieCrawler().run()