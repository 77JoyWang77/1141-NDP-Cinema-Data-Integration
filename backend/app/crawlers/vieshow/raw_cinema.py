import json
import re
import time
from pathlib import Path
from datetime import datetime

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


class VieShowRawCinemaCrawler:
    def __init__(self):
        self.cinema_list_urls = [
            "https://www.vscinemas.com.tw/theater/index.aspx",
            "https://www.vscinemas.com.tw/theater/index2.aspx"
        ]

        BASE_DIR = Path(__file__).resolve().parents[3]  # backend
        self.output_path = BASE_DIR / "data" / "raw" / "vieshow" / "vieshow_cinema.json"

        self.cinemas = []

    # =========================
    # Entry
    # =========================
    def run(self):
        print("=" * 60)
        print("🎬 開始爬取威秀影城（raw_cinema）")
        print("=" * 60)

        self._crawl_cinema_list()
        self._crawl_cinema_detail_pages()
        self._save()

        print("=" * 60)
        print(f"✅ raw_cinema 完成，共 {len(self.cinemas)} 家影城")
        print("=" * 60)

    # =========================
    # Cinema list
    # =========================
    def _crawl_cinema_list(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                locale="zh-TW",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            )
            page = context.new_page()

            for url in self.cinema_list_urls:
                print(f"\n📄 爬取影城列表：{url}")
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_selector("article.article")

                soup = BeautifulSoup(page.content(), "html.parser")
                cinemas = self._parse_cinema_list(soup)
                self.cinemas.extend(cinemas)

            browser.close()

    def _parse_cinema_list(self, soup):
        cinemas = []
        article = soup.select_one("article.article")
        if not article:
            return cinemas

        current_region = None

        for elem in article.find_all(["h1", "ul"]):
            if elem.name == "h1":
                current_region = elem.get_text(strip=True)
                print(f"  📍 區域：{current_region}")

            elif elem.name == "ul" and "theaterInfoList" in elem.get("class", []):
                for li in elem.find_all("li"):
                    cinema = self._parse_cinema_item(li, current_region)
                    if cinema:
                        cinemas.append(cinema)
                        print(f"    ✅ {cinema['name']}")

        return cinemas

    def _parse_cinema_item(self, li, region):
        link = li.select_one("h2 a")
        if not link:
            return None

        href = link.get("href", "")
        match = re.search(r"id=(\d+)", href)
        if not match:
            return None

        cinema_id = match.group(1)
        is_muvie = "index2" in href or "detail2" in href

        name = link.get_text(strip=True)
        english_name = li.select_one("h3")
        english_name = english_name.get_text(strip=True) if english_name else ""

        address = ""
        addr_elem = li.select_one("p.icon-marker")
        if addr_elem:
            address = addr_elem.get_text(strip=True).replace("影城地址：", "")

        phone = ""
        phone_elem = li.select_one("p.icon-phone")
        if phone_elem:
            phone = phone_elem.get_text(strip=True).replace("服務專線：", "")

        return {
            "cinema_id": cinema_id,
            "name": name,
            "english_name": english_name,
            "region": region,
            "address": address,
            "phone": phone,
            "is_muvie": is_muvie,
            "detail_url": f"https://www.vscinemas.com.tw/theater/{href}",
        }

    # =========================
    # Cinema detail
    # =========================
    def _crawl_cinema_detail_pages(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                locale="zh-TW",
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()

            for idx, cinema in enumerate(self.cinemas, start=1):
                print(f"\n🏢 [{idx}/{len(self.cinemas)}] {cinema['name']}")
                page.goto(cinema["detail_url"], wait_until="domcontentloaded", timeout=60000)

                try:
                    page.wait_for_selector("section.bbsArticle", state="attached", timeout=10000)
                    time.sleep(1)
                    soup = BeautifulSoup(page.content(), "html.parser")

                    price_section = soup.select_one("section.bbsArticle")
                    cinema["ticket_price_raw_html"] = (
                        str(price_section) if price_section else None
                    )
                    cinema["crawled_time"] = datetime.now().isoformat()

                except Exception as e:
                    print(f"  ❌ detail 失敗：{e}")
                    cinema["ticket_price_raw_html"] = None

            browser.close()

    # =========================
    # Save
    # =========================
    def _save(self):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(self.cinemas, f, ensure_ascii=False, indent=2)

        print(f"\n💾 已存檔：{self.output_path.resolve()}")


if __name__ == "__main__":
    VieShowRawCinemaCrawler().run()
