import re
import time
import json
import os
import platform
from pathlib import Path
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
from dotenv import load_dotenv


def get_chrome_path():
    """取得系統 Chrome 路徑"""
    system = platform.system()

    if system == "Windows":
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
    elif system == "Darwin":
        paths = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    else:
        paths = ["/usr/bin/google-chrome", "/usr/bin/chromium-browser"]

    for path in paths:
        if Path(path).exists():
            return path
    return None


class ShowtimeSeatStatusProvider:
    """秀泰影城座位狀態爬蟲（一次登入 + 多次查詢版本）"""

    def __init__(self, phone: str = None, password: str = None):
        self.phone = phone
        self.password = password
        self.browser = None
        self.page = None
        self.context = None
        self.login_success = False

    def start_browser(self):
        """啟動瀏覽器和登入會話"""
        if self.page is not None:
            print("⚠️  瀏覽器已啟動")
            return True

        chrome_path = get_chrome_path()
        if not chrome_path:
            print("❌ 找不到 Google Chrome")
            return False

        try:
            p = sync_playwright().__enter__()
            self.browser = p.chromium.launch(
                headless=False,
                executable_path=chrome_path,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            self.context = self.browser.new_context(locale="zh-TW")
            self.page = self.context.new_page()

            print("✅ 瀏覽器已啟動")
            return True
        except Exception as e:
            print(f"❌ 瀏覽器啟動失敗: {e}")
            return False

    def login(self) -> bool:
        """進行登入"""
        if self.login_success:
            print("⚠️  已登入，跳過")
            return True

        if self.page is None:
            if not self.start_browser():
                return False

        try:
            print("\n🔐 開始登入...")

            # 1. 前往主頁
            print("  1️⃣ 前往主頁...")
            self.page.goto(
                "https://www.showtimes.com.tw",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            self.page.wait_for_timeout(2000)

            # 2. 點擊「登入秀泰影城」按鈕
            print("  2️⃣ 點擊登入按鈕...")
            login_trigger = self.page.locator(
                "div.sc-iA-DsXs:has-text('登入秀泰影城')"
            ).first

            if not login_trigger.is_visible(timeout=3000):
                print("  ✅ 已經登入")
                self.login_success = True
                return True

            login_trigger.click()
            self.page.wait_for_timeout(1500)

            # 3. 等待登入彈窗
            print("  3️⃣ 等待登入彈窗...")
            self.page.wait_for_selector("#login-modal.show", timeout=8000)
            self.page.wait_for_timeout(800)

            # 4. 填入帳密
            print(f"  4️⃣ 填入帳密: {self.phone[:4]}****")
            phone_input = self.page.locator("#login-modal input[type='text']").first
            phone_input.fill(self.phone)
            self.page.wait_for_timeout(600)

            password_input = self.page.locator(
                "#login-modal input[type='password']"
            ).first
            password_input.fill(self.password)
            self.page.wait_for_timeout(600)

            # 5. 等待 Cloudflare 驗證
            print("  5️⃣ 等待 Cloudflare 驗證...")
            max_wait = 30
            waited = 0

            while waited < max_wait:
                login_button = self.page.locator(
                    "#login-modal button.btn-primary:has-text('登入')"
                ).first

                try:
                    is_disabled = login_button.get_attribute("disabled")
                    if is_disabled is None:
                        print("  ✅ 驗證完成")
                        break
                except:
                    pass

                self.page.wait_for_timeout(500)
                waited += 1

                if waited % 10 == 0:
                    print(f"     等待中... ({waited}秒)")

            if waited >= max_wait:
                print("  ⚠️  Cloudflare 驗證超時，可能需要手動勾選")
                print("  ⏸️  請手動完成驗證後按 Enter...")
                input()

            # 6. 點擊登入
            print("  6️⃣ 點擊登入...")
            login_button = self.page.locator(
                "#login-modal button.btn-primary:has-text('登入')"
            ).first
            login_button.click()
            
            # 🔥 等待頁面跳轉完成
            print("  7️⃣ 等待登入完成（頁面跳轉）...")
            self.page.wait_for_timeout(5000)

            # 檢查是否登入成功
            current_url = self.page.url
            print(f"  📍 當前 URL: {current_url}")
            
            if (
                "/member" in current_url
                or "/profile" in current_url
                or "/account" in current_url
            ):
                print("  🔄 被導向會員頁面，返回主頁...")
                self.page.goto(
                    "https://www.showtimes.com.tw",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                self.page.wait_for_timeout(2000)

            # 再次檢查是否有登入按鈕（有表示登入失敗）
            try:
                login_trigger = self.page.locator(
                    "div.sc-iA-DsXs:has-text('登入秀泰影城')"
                ).first
                if login_trigger.is_visible(timeout=1500):
                    print("  ❌ 登入失敗")
                    return False
            except:
                pass

            print("  ✅ 登入成功！")
            self.login_success = True
            return True

        except Exception as e:
            print(f"  ❌ 登入失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

    def fetch_multiple_showtimes(self, showtimes: List[Dict]) -> List[Dict]:
        """批次查詢多個場次（共用同一個瀏覽器會話）"""
        results = []
        total = len(showtimes)

        for idx, showtime in enumerate(showtimes, 1):
            print(f"\n[{idx}/{total}] {showtime.get('cinema_name')} - {showtime.get('date')} {showtime.get('time_range')}")

            seat_data = self.fetch_single_showtime(showtime)

            if seat_data:
                print(f"  ✅ 總: {seat_data['total']}, 可售: {seat_data['available']}, 已售: {seat_data['sold']}, 銷售率: {seat_data['occupancy_rate']}%")
                results.append(seat_data)
            else:
                print(f"  ⚠️  查詢失敗")

        return results

    def fetch_single_showtime(self, showtime: Dict) -> Optional[Dict]:
        """查詢單個場次"""
        movie_id = showtime.get("movie_id")
        cinema_name = showtime.get("cinema_name")
        date_text = showtime.get("date")
        screen_number = showtime.get("screen_number")
        screen_type = showtime.get("screen_type")
        time_range = showtime.get("time_range")

        if screen_number and screen_type:
            screen_info = f"{screen_number} | {screen_type}"
        else:
            screen_info = None

        try:
            # 1. 前往電影頁面
            movie_url = f"https://www.showtimes.com.tw/programs/{movie_id}"
            print(f"  🎬 前往電影頁面...")
            self.page.goto(movie_url, wait_until="domcontentloaded", timeout=30000)
            self.page.wait_for_selector("button.sc-bypJrT", timeout=10000)
            self.page.wait_for_timeout(1000)

            # 2. 點擊影城
            if not self._click_cinema(cinema_name):
                return None

            # 3. 點擊日期
            if not self._click_date(date_text):
                return None

            # 4. 點擊座位圖
            if not self._click_seat_button(screen_info, time_range):
                return None

            # 5. 等待座位頁面
            try:
                self.page.wait_for_url("**/ticketing/viewSeats**", timeout=8000)
            except:
                if "login" in self.page.url:
                    print("  ❌ 被導向登入頁面")
                    return None

            # 6. 等待座位圖載入
            self.page.wait_for_timeout(3000)

            seat_container_count = self.page.locator("div.sc-aNeao").count()

            if seat_container_count == 0:
                self.page.wait_for_timeout(2000)
                seat_container_count = self.page.locator("div.sc-aNeao").count()

                if seat_container_count == 0:
                    print("  ⚠️  找不到座位圖")
                    return None

            # 7. 解析座位
            html = self.page.content()
            soup = BeautifulSoup(html, "html.parser")

            seat_data = self._parse_seats(soup)

            if seat_data["total"] == 0:
                return None

            # 添加場次資訊
            seat_data.update(
                {
                    "movie_id": movie_id,
                    "movie_title_cn": showtime.get("movie_title_cn"),
                    "movie_title_en": showtime.get("movie_title_en"),
                    "cinema_name": cinema_name,
                    "date": date_text,
                    "screen_info": screen_info,
                    "time_range": time_range,
                }
            )

            return seat_data

        except Exception as e:
            print(f"  ❌ 查詢失敗: {e}")
            return None

    def _click_cinema(self, cinema_name: str) -> bool:
        """點擊影城按鈕"""
        try:
            cinema_buttons = self.page.locator("button.sc-bypJrT").all()
            print(f"  🔍 找到 {len(cinema_buttons)} 個影城按鈕")
            
            for button in cinema_buttons:
                try:
                    btn_text = button.inner_text(timeout=2000)
                    if btn_text == cinema_name:
                        print(f"  🏢 點擊影城: {cinema_name}")
                        button.click()
                        self.page.wait_for_timeout(1500)
                        return True
                except:
                    continue
            
            print(f"  ❌ 找不到影城: {cinema_name}")
            return False
        except Exception as e:
            print(f"  ❌ 點擊影城失敗: {e}")
            return False

    def _click_date(self, date_text: str) -> bool:
        """點擊日期按鈕"""
        try:
            self.page.wait_for_selector("div.sc-ijDOKB", timeout=8000)
            self.page.wait_for_timeout(1000)
            
            date_divs = self.page.locator("div.sc-ijDOKB").all()
            print(f"  🔍 找到 {len(date_divs)} 個日期按鈕")
            
            for date_div in date_divs:
                spans = date_div.locator("span").all()
                if len(spans) >= 1:
                    try:
                        span_text = spans[0].inner_text(timeout=2000)
                        if date_text in span_text:
                            print(f"  📅 點擊日期: {date_text}")
                            date_div.click()
                            self.page.wait_for_timeout(1500)
                            return True
                    except:
                        continue
            
            print(f"  ❌ 找不到日期: {date_text}")
            return False
        except Exception as e:
            print(f"  ❌ 點擊日期失敗: {e}")
            return False

    def _click_seat_button(self, screen_info: str = None, time_range: str = None) -> bool:
        """點擊座位圖按鈕"""
        try:
            self.page.wait_for_selector("div.grid > div.border-brand-700", timeout=8000)
            self.page.wait_for_timeout(1000)
            
            showtime_cards = self.page.locator("div.grid > div.border-brand-700").all()
            print(f"  🔍 找到 {len(showtime_cards)} 個場次卡片")
            
            for card in showtime_cards:
                try:
                    match_screen = True
                    if screen_info:
                        screen_elem = card.locator("div.text-sm").first
                        if screen_elem:
                            card_screen = screen_elem.inner_text(timeout=2000)
                            match_screen = (card_screen == screen_info)
                    
                    match_time = True
                    if time_range:
                        time_elem = card.locator("div.text-lg").first
                        if time_elem:
                            card_time = time_elem.inner_text(timeout=2000)
                            match_time = (card_time == time_range)
                    
                    if match_screen and match_time:
                        # 🔥 點擊座位按鈕區域
                        seat_button = card.locator("div.flex-1.flex.flex-col").first
                        if seat_button:
                            print(f"  💺 點擊座位圖")
                            seat_button.click()
                            self.page.wait_for_timeout(1500)
                            return True
                except:
                    continue
            
            print(f"  ❌ 找不到匹配的場次")
            return False
        except Exception as e:
            print(f"  ❌ 點擊座位圖失敗: {e}")
            return False

    def _parse_seats(self, soup: BeautifulSoup) -> Dict:
        """解析座位資訊"""
        seats = []

        seat_container = soup.select_one("div.sc-aNeao")

        if not seat_container:
            return {
                "seats": [],
                "total": 0,
                "available": 0,
                "sold": 0,
                "occupancy_rate": 0.0,
            }

        all_seat_divs = seat_container.select("div.sc-fKMpNL")
        print(f"  🔍 找到 {len(all_seat_divs)} 個座位元素")

        for seat_div in all_seat_divs:
            try:
                seat_text = seat_div.get_text(strip=True)

                if not seat_text:
                    continue

                seat_classes = seat_div.get("class", [])

                if "faAHLJ" in seat_classes:
                    continue

                style = seat_div.get("style", "")
                left_match = re.search(r"left:\s*(\d+)px", style)
                top_match = re.search(r"top:\s*(\d+)px", style)

                left = int(left_match.group(1)) if left_match else 0
                top = int(top_match.group(1)) if top_match else 0

                if "hdnKSQ" in seat_classes:
                    status = "sold"
                elif "iFIbTq" in seat_classes:
                    status = "selected"
                elif "guIbTP" in seat_classes:
                    status = "available"
                else:
                    status = "unknown"

                seats.append(
                    {
                        "seat_number": seat_text,
                        "position": {"left": left, "top": top},
                        "status": status,
                    }
                )

            except:
                continue

        total = len(seats)
        available = sum(1 for s in seats if s["status"] == "available")
        sold = sum(1 for s in seats if s["status"] == "sold")

        print(f"  📊 解析結果：總 {total}，可售 {available}，已售 {sold}")

        return {
            "seats": seats,
            "total": total,
            "available": available,
            "sold": sold,
            "occupancy_rate": round(sold / total * 100, 2) if total > 0 else 0.0,
        }

    def close_browser(self):
        """關閉瀏覽器"""
        if self.browser:
            self.browser.close()
            print("\n✅ 瀏覽器已關閉")


# =========================
# 測試腳本
# =========================

if __name__ == "__main__":
    from datetime import datetime, timedelta

    print("=" * 70)
    print("🎬 秀泰影城座位查詢（一次登入 + 多次查詢）")
    print("=" * 70)

    # 1️⃣ 從 .env 讀取帳密
    load_dotenv()
    PHONE = os.getenv("SHOWTIME_PHONE")
    PASSWORD = os.getenv("SHOWTIME_PASSWORD")

    if not PHONE or not PASSWORD:
        print("\n❌ .env 中缺少 SHOWTIME_PHONE 或 SHOWTIME_PASSWORD")
        exit()

    print(f"\n✅ 已讀取帳密: {PHONE[:4]}****")

    # 2️⃣ 載入場次資料
    BASE_DIR = Path(__file__).resolve().parents[3]
    showtime_path = BASE_DIR / "data" / "raw" / "showtime" / "showtime_valid.json"

    if not showtime_path.exists():
        print(f"\n❌ 找不到 {showtime_path}")
        exit()

    with open(showtime_path, "r", encoding="utf-8") as f:
        all_showtimes = json.load(f)

    print(f"✅ 載入 {len(all_showtimes)} 筆場次資料")

    # 3️⃣ 過濾未來場次
    now = datetime.now()
    future_showtimes = []

    for showtime in all_showtimes:
        try:
            date_str = showtime.get("date", "")
            time_range = showtime.get("time_range", "")

            month = int(date_str.split("月")[0])
            day = int(date_str.split("月")[1].replace("日", ""))

            if "~" in time_range:
                start_time = time_range.split("~")[0].strip()
                hour = int(start_time.split(":")[0])
                minute = int(start_time.split(":")[1])
            else:
                continue

            dt = datetime(now.year, month, day, hour, minute)

            if dt > now + timedelta(minutes=30):
                future_showtimes.append(showtime)
        except:
            continue

    print(f"✅ 過濾出 {len(future_showtimes)} 個未來場次")

    if not future_showtimes:
        print("⚠️  沒有可用場次")
        exit()

    # 4️⃣ 排序並顯示
    future_showtimes.sort(key=lambda s: (s.get("date", ""), s.get("time_range", "")))

    print("\n" + "=" * 70)
    print("📋 可用場次（前10個）：")
    print("=" * 70)

    display_count = min(10, len(future_showtimes))

    for i in range(display_count):
        st = future_showtimes[i]
        print(f"\n[{i+1}] {st.get('movie_title_cn')}")
        print(f"    🏢 {st.get('cinema_name')}")
        print(f"    📅 {st.get('date')} {st.get('time_range')}")

    print("\n" + "=" * 70)

    # 5️⃣ 選擇查詢範圍
    choice = input(f"\n輸入要查詢的場次編號（例: 1-5 或 1,3,5）: ").strip()

    selected_showtimes = []

    if "-" in choice:
        # 範圍選擇
        start, end = choice.split("-")
        start = max(1, int(start))
        end = min(display_count, int(end))
        selected_showtimes = future_showtimes[start - 1 : end]
    elif "," in choice:
        # 多選
        indices = [int(x.strip()) - 1 for x in choice.split(",") if x.strip().isdigit()]
        selected_showtimes = [
            future_showtimes[i] for i in indices if 0 <= i < display_count
        ]
    elif choice.isdigit():
        # 單選
        idx = int(choice) - 1
        if 0 <= idx < display_count:
            selected_showtimes = [future_showtimes[idx]]
    else:
        print("❌ 無效選擇")
        exit()

    if not selected_showtimes:
        print("❌ 無有效場次")
        exit()

    print("\n" + "=" * 70)
    print(f"🎯 已選擇 {len(selected_showtimes)} 個場次")
    print("=" * 70)

    # 6️⃣ 建立爬蟲，一次登入
    provider = ShowtimeSeatStatusProvider(phone=PHONE, password=PASSWORD)

    print("\n🚀 啟動瀏覽器並登入...")
    if not provider.login():
        print("\n❌ 登入失敗")
        exit()

    print("\n🔄 開始查詢座位狀態...\n")

    # 7️⃣ 多次查詢
    results = provider.fetch_multiple_showtimes(selected_showtimes)

    print("\n" + "=" * 70)
    print(f"✅ 查詢完成，成功 {len(results)} 個")
    print("=" * 70)

    # 8️⃣ 顯示結果
    for seat_data in results:
        print(f"\n🎬 {seat_data['movie_title_cn']}")
        print(f"🏢 {seat_data['cinema_name']}")
        print(f"📅 {seat_data['date']} {seat_data['time_range']}")
        print(f"💺 總座位：{seat_data['total']}")
        print(f"✅ 可售：{seat_data['available']}")
        print(f"❌ 已售：{seat_data['sold']}")
        print(f"📊 銷售率：{seat_data['occupancy_rate']}%")

    # 9️⃣ 儲存結果
    output_path = BASE_DIR / "data" / "seats" / "showtime_seats.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n💾 結果已儲存: {output_path}")

    # 🔟 關閉瀏覽器
    provider.close_browser()