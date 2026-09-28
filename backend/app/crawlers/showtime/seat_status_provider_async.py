import re
import asyncio
import json
import os
import platform
from pathlib import Path
from playwright.async_api import async_playwright
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
    """秀泰影城座位狀態爬蟲(異步版本 - 加入延遲避免被偵測)"""

    def __init__(self, phone: str = None, password: str = None):
        self.phone = phone
        self.password = password
        self.playwright = None
        self.browser = None
        self.page = None
        self.context = None
        self.login_success = False

    async def start_browser(self):
        """啟動瀏覽器和登入會話"""
        if self.page is not None:
            print("⚠️ 瀏覽器已啟動")
            return True

        chrome_path = get_chrome_path()
        if not chrome_path:
            print("❌ 找不到 Google Chrome")
            return False

        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=False,
                executable_path=chrome_path,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            self.context = await self.browser.new_context(locale="zh-TW")
            self.page = await self.context.new_page()

            print("✅ 瀏覽器已啟動")
            return True
        except Exception as e:
            print(f"❌ 瀏覽器啟動失敗: {e}")
            return False

    async def login(self) -> bool:
        """進行登入(加入人性化延遲)"""
        if self.login_success:
            print("⚠️ 已登入,跳過")
            return True

        if self.page is None:
            if not await self.start_browser():
                return False

        try:
            print("\n🔐 開始登入...")

            # 1. 前往主頁
            print("  1️⃣ 前往主頁...")
            await self.page.goto(
                "https://www.showtimes.com.tw",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            # 🐌 延遲 3-5 秒(模擬真人瀏覽)
            await self.page.wait_for_timeout(3000 + (await self._random_delay(2000)))

            # 2. 點擊「登入秀泰影城」按鈕
            print("  2️⃣ 點擊登入按鈕...")
            login_trigger = self.page.locator(
                "div.sc-iA-DsXs:has-text('登入秀泰影城')"
            ).first

            try:
                is_visible = await login_trigger.is_visible(timeout=3000)
                if not is_visible:
                    print("  ✅ 已經登入")
                    self.login_success = True
                    return True
            except:
                print("  ✅ 已經登入")
                self.login_success = True
                return True

            await login_trigger.click()
            # 🐌 延遲 2-3 秒
            await self.page.wait_for_timeout(2000 + (await self._random_delay(1000)))

            # 3. 等待登入彈窗
            print("  3️⃣ 等待登入彈窗...")
            await self.page.wait_for_selector("#login-modal.show", timeout=8000)
            await self.page.wait_for_timeout(1000)

            # 4. 填入帳密(模擬人類打字速度)
            print(f"  4️⃣ 填入帳密: {self.phone[:4]}****")
            phone_input = self.page.locator("#login-modal input[type='text']").first
            
            # 🐌 逐字輸入手機號碼
            for char in self.phone:
                await phone_input.type(char, delay=100 + (await self._random_delay(50)))
            
            await self.page.wait_for_timeout(800 + (await self._random_delay(400)))

            password_input = self.page.locator(
                "#login-modal input[type='password']"
            ).first
            
            # 🐌 逐字輸入密碼
            for char in self.password:
                await password_input.type(char, delay=80 + (await self._random_delay(40)))
            
            await self.page.wait_for_timeout(1000 + (await self._random_delay(500)))

            # 5. 等待 Cloudflare 驗證
            print("  5️⃣ 等待 Cloudflare 驗證...")
            max_wait = 30
            waited = 0

            while waited < max_wait:
                login_button = self.page.locator(
                    "#login-modal button.btn-primary:has-text('登入')"
                ).first

                try:
                    is_disabled = await login_button.get_attribute("disabled")
                    if is_disabled is None:
                        print("  ✅ 驗證完成")
                        break
                except:
                    pass

                await self.page.wait_for_timeout(500)
                waited += 1

                if waited % 10 == 0:
                    print(f"     等待中... ({waited}秒)")

            if waited >= max_wait:
                print("  ⚠️ Cloudflare 驗證超時,可能需要手動勾選")
                return False

            # 6. 點擊登入
            print("  6️⃣ 點擊登入...")
            login_button = self.page.locator(
                "#login-modal button.btn-primary:has-text('登入')"
            ).first
            
            # 🐌 延遲 0.5-1 秒後點擊
            await self.page.wait_for_timeout(500 + (await self._random_delay(500)))
            await login_button.click()
            
            # 等待頁面跳轉完成
            print("  7️⃣ 等待登入完成(頁面跳轉)...")
            await self.page.wait_for_timeout(5000)

            # 檢查是否登入成功
            current_url = self.page.url
            print(f"  📍 當前 URL: {current_url}")
            
            if (
                "/member" in current_url
                or "/profile" in current_url
                or "/account" in current_url
            ):
                print("  📄 被導向會員頁面,返回主頁...")
                await self.page.goto(
                    "https://www.showtimes.com.tw",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                await self.page.wait_for_timeout(2000)

            # 再次檢查是否有登入按鈕(有表示登入失敗)
            try:
                login_trigger = self.page.locator(
                    "div.sc-iA-DsXs:has-text('登入秀泰影城')"
                ).first
                is_visible = await login_trigger.is_visible(timeout=1500)
                if is_visible:
                    print("  ❌ 登入失敗")
                    return False
            except:
                pass

            print("  ✅ 登入成功!")
            self.login_success = True
            return True

        except Exception as e:
            print(f"  ❌ 登入失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def fetch_multiple_showtimes(self, showtimes: List[Dict]) -> List[Dict]:
        """批次查詢多個場次(共用同一個瀏覽器會話)"""
        results = []
        total = len(showtimes)

        for idx, showtime in enumerate(showtimes, 1):
            print(f"\n[{idx}/{total}] {showtime.get('cinema_name')} - {showtime.get('date')} {showtime.get('time_range')}")

            seat_data = await self.fetch_single_showtime(showtime)

            if seat_data:
                print(f"  ✅ 總: {seat_data['total']}, 可售: {seat_data['available']}, 已售: {seat_data['sold']}, 銷售率: {seat_data['occupancy_rate']}%")
                results.append(seat_data)
            else:
                print(f"  ⚠️ 查詢失敗")
            
            # 🐌 場次間延遲 2-4 秒
            if idx < total:
                await self.page.wait_for_timeout(2000 + (await self._random_delay(2000)))

        return results

    async def fetch_single_showtime(self, showtime: Dict) -> Optional[Dict]:
        """查詢單個場次(加入人性化延遲)"""
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
            await self.page.goto(movie_url, wait_until="domcontentloaded", timeout=30000)
            await self.page.wait_for_selector("button.sc-bypJrT", timeout=10000)
            # 🐌 延遲 3-5 秒(讓頁面完全載入)
            await self.page.wait_for_timeout(3000 + (await self._random_delay(2000)))

            # 2. 點擊影城
            if not await self._click_cinema(cinema_name):
                return None

            # 3. 點擊日期
            if not await self._click_date(date_text):
                return None

            # 4. 點擊座位圖
            if not await self._click_seat_button(screen_info, time_range):
                return None

            # 5. 等待座位頁面
            try:
                print("  ⏳ 等待跳轉到座位頁面...")
                await self.page.wait_for_url("**/ticketing/viewSeats**", timeout=15000)
                print("  ✓ 已跳轉到座位頁面")
            except:
                current_url = self.page.url
                print(f"  ⚠️ URL跳轉超時,當前: {current_url}")
                if "login" in current_url:
                    print("  ❌ 被導向登入頁面")
                    return None

            # 6. 等待座位圖載入(大幅增加等待時間)
            print("  ⏳ 等待座位圖載入...")
            # 🐌 延遲 5-8 秒(給座位圖充足時間載入)
            await self.page.wait_for_timeout(5000 + (await self._random_delay(3000)))

            # 檢查座位容器
            seat_container_count = await self.page.locator("div.sc-aNeao").count()
            print(f"  🔍 找到 {seat_container_count} 個座位容器")

            if seat_container_count == 0:
                print("  ⏳ 座位圖尚未載入,再等待 3 秒...")
                await self.page.wait_for_timeout(3000)
                seat_container_count = await self.page.locator("div.sc-aNeao").count()
                print(f"  🔍 重新檢查: {seat_container_count} 個座位容器")

                if seat_container_count == 0:
                    print("  ⚠️ 找不到座位圖")
                    # 保存截圖用於調試
                    try:
                        await self.page.screenshot(path=f"debug_no_seats_{int(asyncio.get_event_loop().time())}.png")
                        print("  📸 已保存截圖用於調試")
                    except:
                        pass
                    return None

            # 7. 解析座位
            html = await self.page.content()
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
                    "screen_number": screen_number,
                    "screen_type": screen_type,
                    "time_range": time_range,
                }
            )

            return seat_data

        except Exception as e:
            print(f"  ❌ 查詢失敗: {e}")
            return None

    async def _click_cinema(self, cinema_name: str) -> bool:
        """點擊影城按鈕"""
        try:
            cinema_buttons = await self.page.locator("button.sc-bypJrT").all()
            print(f"  🔍 找到 {len(cinema_buttons)} 個影城按鈕")
            
            for button in cinema_buttons:
                try:
                    btn_text = await button.inner_text(timeout=2000)
                    if btn_text == cinema_name:
                        print(f"  🎦 點擊影城: {cinema_name}")
                        # 🐌 延遲 0.5-1.5 秒後點擊
                        await self.page.wait_for_timeout(500 + (await self._random_delay(1000)))
                        await button.click()
                        # 🐌 點擊後延遲 3-5 秒
                        await self.page.wait_for_timeout(3000 + (await self._random_delay(2000)))
                        return True
                except:
                    continue
            
            print(f"  ❌ 找不到影城: {cinema_name}")
            return False
        except Exception as e:
            print(f"  ❌ 點擊影城失敗: {e}")
            return False

    async def _click_date(self, date_text: str) -> bool:
        """點擊日期按鈕"""
        try:
            await self.page.wait_for_selector("div.sc-ijDOKB", timeout=8000)
            # 🐌 延遲 2-3 秒
            await self.page.wait_for_timeout(2000 + (await self._random_delay(1000)))
            
            date_divs = await self.page.locator("div.sc-ijDOKB").all()
            print(f"  🔍 找到 {len(date_divs)} 個日期按鈕")
            
            for date_div in date_divs:
                spans = await date_div.locator("span").all()
                if len(spans) >= 1:
                    try:
                        span_text = await spans[0].inner_text(timeout=2000)
                        if date_text in span_text:
                            print(f"  📅 點擊日期: {date_text}")
                            # 🐌 延遲 0.5-1.5 秒後點擊
                            await self.page.wait_for_timeout(500 + (await self._random_delay(1000)))
                            await date_div.click()
                            # 🐌 點擊後延遲 3-5 秒
                            await self.page.wait_for_timeout(3000 + (await self._random_delay(2000)))
                            return True
                    except:
                        continue
            
            print(f"  ❌ 找不到日期: {date_text}")
            return False
        except Exception as e:
            print(f"  ❌ 點擊日期失敗: {e}")
            return False

    async def _click_seat_button(self, screen_info: str = None, time_range: str = None) -> bool:
        """點擊座位圖按鈕"""
        try:
            await self.page.wait_for_selector("div.grid > div.border-brand-700", timeout=8000)
            # 🐌 延遲 2-3 秒
            await self.page.wait_for_timeout(2000 + (await self._random_delay(1000)))
            
            showtime_cards = await self.page.locator("div.grid > div.border-brand-700").all()
            print(f"  🔍 找到 {len(showtime_cards)} 個場次卡片")
            
            for card in showtime_cards:
                try:
                    match_screen = True
                    if screen_info:
                        screen_elem = card.locator("div.text-sm").first
                        card_screen = await screen_elem.inner_text(timeout=2000)
                        match_screen = (card_screen == screen_info)
                    
                    match_time = True
                    if time_range:
                        time_elem = card.locator("div.text-lg").first
                        card_time = await time_elem.inner_text(timeout=2000)
                        match_time = (card_time == time_range)
                    
                    if match_screen and match_time:
                        seat_button = card.locator("div.flex-1.flex.flex-col").first
                        print(f"  💺 點擊座位圖")
                        # 🐌 延遲 0.8-1.5 秒後點擊
                        await self.page.wait_for_timeout(800 + (await self._random_delay(700)))
                        await seat_button.click()
                        # 🐌 點擊後延遲 3-5 秒(等待頁面跳轉)
                        await self.page.wait_for_timeout(3000 + (await self._random_delay(2000)))
                        return True
                except:
                    continue
            
            print(f"  ❌ 找不到匹配的場次")
            return False
        except Exception as e:
            print(f"  ❌ 點擊座位圖失敗: {e}")
            return False

    def _parse_seats(self, soup: BeautifulSoup) -> Dict:
        """解析座位資訊（修正版 - 使用排號標籤）"""
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
        print(f"  🔍 找到 {len(all_seat_divs)} 個元素")

        # ✅ 步驟1：建立 top -> 排號的映射
        top_to_row = {}
        for div in all_seat_divs:
            seat_classes = div.get("class", [])
            
            # 如果是排號標籤（faAHLJ）
            if "faAHLJ" in seat_classes:
                seat_text = div.get_text(strip=True)
                style = div.get("style", "")
                top_match = re.search(r"top:\s*(\d+)px", style)
                
                if top_match and seat_text.isdigit():
                    top = int(top_match.group(1))
                    row_number = seat_text  # "8", "7", "6"...
                    top_to_row[top] = row_number
        
        print(f"  📍 排號映射: {top_to_row}")

        # ✅ 步驟2：解析所有座位
        for seat_div in all_seat_divs:
            try:
                seat_text = seat_div.get_text(strip=True)

                if not seat_text:
                    continue

                seat_classes = seat_div.get("class", [])

                # 跳過排號標籤
                if "faAHLJ" in seat_classes:
                    continue

                style = seat_div.get("style", "")
                left_match = re.search(r"left:\s*(\d+)px", style)
                top_match = re.search(r"top:\s*(\d+)px", style)

                left = int(left_match.group(1)) if left_match else 0
                top = int(top_match.group(1)) if top_match else 0
                
                # ✅ 使用排號映射獲取真實排號
                row_number = top_to_row.get(top, "?")

                if "hdnKSQ" in seat_classes:
                    status = "sold"
                elif "iFIbTq" in seat_classes:
                    status = "selected"
                elif "bKfFJW" in seat_classes:  # 已選取（不同樣式）
                    status = "selected"
                elif "guIbTP" in seat_classes:
                    status = "available"
                else:
                    status = "unknown"

                seats.append(
                    {
                        "seat_id": f"{row_number}-{seat_text}",  # ✅ 唯一ID："8-15", "8-14"
                        "seat_number": seat_text,
                        "row": row_number,
                        "position": {"left": left, "top": top - 100},
                        "status": status,
                    }
                )

            except Exception as e:
                print(f"  ⚠️  解析座位失敗: {e}")
                continue

        total = len(seats)
        available = sum(1 for s in seats if s["status"] == "available")
        sold = sum(1 for s in seats if s["status"] == "sold")

        print(f"  📊 解析結果: 總 {total}, 可售 {available}, 已售 {sold}")
        
        # ✅ 顯示每排的座位數
        row_counts = {}
        for seat in seats:
            row = seat.get("row", "?")
            row_counts[row] = row_counts.get(row, 0) + 1
        print(f"  📊 每排座位數: {row_counts}")

        return {
            "seats": seats,
            "total": total,
            "available": available,
            "sold": sold,
            "occupancy_rate": round(sold / total * 100, 2) if total > 0 else 0.0,
        }


    async def _random_delay(self, max_ms: int = 1000) -> int:
        """生成隨機延遲時間(毫秒)"""
        import random
        return random.randint(0, max_ms)

    async def close_browser(self):
        """關閉瀏覽器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("\n✅ 瀏覽器已關閉")