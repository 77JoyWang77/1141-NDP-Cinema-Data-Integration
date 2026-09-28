import json
import time
from pathlib import Path
from datetime import datetime

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


class ShowtimeRawCinemaCrawler:
    def __init__(self):
        self.cinema_list_url = f"https://www.showtimes.com.tw/info/cinema"

        BASE_DIR = Path(__file__).resolve().parents[3]  # backend
        self.output_path = BASE_DIR / "data" / "raw" / "showtime" / "showtime_cinema.json"

        self.cinemas = []

    # =========================
    # Entry
    # =========================
    def run(self):
        print("=" * 60)
        print("🎬 開始爬取秀泰影城（raw_cinema）")
        print("=" * 60)

        self._crawl_cinema_list()
        self._crawl_cinema_detail_pages()
        self._save()

        print("=" * 60)
        print(f"✅ raw_cinema 完成，共 {len(self.cinemas)} 家影城")
        print("=" * 60)

    # =========================
    # Cinema list (SPA, click-based)
    # =========================
    def _crawl_cinema_list(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                locale="zh-TW",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            )
            page = context.new_page()

            print(f"\n📄 爬取影城列表：{self.cinema_list_url}")
            page.goto(self.cinema_list_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("div.col-6.col-md-4", timeout=60000)

            cards_count = page.locator("div.col-6.col-md-4").count()

            for i in range(cards_count):
                cards = page.locator("div.col-6.col-md-4")
                card = cards.nth(i)

                soup = BeautifulSoup(card.inner_html(), "html.parser")

                name = soup.select_one(".sc-uVWWZ")
                infos = soup.select(".sc-hCPjZK")
                img = soup.select_one("img")

                if not name or len(infos) < 2:
                    continue

                cinema = {
                    "name": name.get_text(strip=True),
                    "address": infos[0].get_text(strip=True),
                    "phone": infos[1].get_text(strip=True),
                    "image": img["src"] if img else None,
                }

                # SPA：必須點擊才能拿到 URL
                card.click()
                page.wait_for_url("**/info/cinema/**", timeout=60000)
                cinema["detail_url"] = page.url

                print(f"  ✅ {cinema['name']}")

                self.cinemas.append(cinema)

                page.go_back()
                page.wait_for_selector("div.col-6.col-md-4", timeout=60000)

            browser.close()

    # =========================
    # Cinema detail (ticket price)
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
                    page.wait_for_selector("div.container-fluid", timeout=10000)
                    time.sleep(1)

                    html = page.content()
                    soup = BeautifulSoup(html, "html.parser")

                    cinema["ticket_prices"] = self._parse_showtime_ticket_table(soup)

                    cinema["ticket_extra_rules"] = self._parse_ticket_extra_rules(soup)
                    cinema["crawled_time"] = datetime.now().isoformat()

                except Exception as e:
                    print(f"  ❌ detail 失敗：{e}")
                    cinema["ticket_extra_rules"] = None
                    cinema["ticket_prices"] = None

            browser.close()

    # =========================
    # Parser (raw stage)
    # =========================
    def _parse_ticket_extra_rules(self, soup):
        """
        解析票價表最後一行的「加價規則文字」
        不嘗試結構化，只保留原始文字
        """
        rule_div = soup.select_one("div.row div.col.mt-3")
        if not rule_div:
            return None

        text = rule_div.get_text(strip=True)
        return text if text else None

    
    def _parse_showtime_ticket_table(self, soup):
        prices = []

        rows = soup.select("div.container-fluid div.row")
        if not rows:
            return prices

        # 跳過 header row
        for row in rows[1:]:
            cols = row.select("div.col")
            if len(cols) < 4:
                continue

            version = row.select_one("div.col-3")
            if not version:
                continue

            def to_int(x):
                try:
                    return int(x.strip())
                except:
                    return None

            prices.append({
                "version": version.get_text(strip=True),
                "prices": {
                    "full": to_int(cols[0].get_text()),
                    "discount": to_int(cols[1].get_text()),
                    "morning": to_int(cols[2].get_text()),
                    "charity": to_int(cols[3].get_text()),
                }
            })

        return prices

    # =========================
    # Save
    # =========================
    def _save(self):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(self.cinemas, f, ensure_ascii=False, indent=2)

        print(f"\n💾 已存檔：{self.output_path.resolve()}")


if __name__ == "__main__":
    ShowtimeRawCinemaCrawler().run()
