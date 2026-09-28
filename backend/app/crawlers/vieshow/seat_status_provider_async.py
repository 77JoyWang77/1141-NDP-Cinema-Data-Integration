# app/crawlers/vieshow/seat_status_provider_async.py
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re


class SeatStatusProvider:
    """威秀座位狀態爬蟲（持久化瀏覽器版本）"""
    
    _instance = None
    _browser: Optional[Browser] = None
    _context: Optional[BrowserContext] = None
    _page: Optional[Page] = None
    _playwright = None
    
    def __new__(cls):
        """單例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.base_url = "https://www.vscinemas.com.tw"
    
    async def _ensure_browser(self):
        """確保瀏覽器已啟動"""
        if self._browser is None or not self._browser.is_connected():
            print("  🚀 啟動威秀瀏覽器...")
            
            if self._playwright is None:
                self._playwright = await async_playwright().start()
            
            self._browser = await self._playwright.chromium.launch(
                headless=False,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            self._context = await self._browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )
            
            self._page = await self._context.new_page()
            
            await self._page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            print("  ✓ 威秀瀏覽器已啟動")

    async def fetch(self, seat_query_url: str, referer_url: str = None) -> Dict:
        await self._ensure_browser()
        
        page = self._page
        
        if not referer_url:
            cinema_id_match = re.search(r'CinemaCode=(\d+)', seat_query_url)
            cinema_id = cinema_id_match.group(1) if cinema_id_match else "1"
            referer_url = f"https://www.vscinemas.com.tw/theater/detail.aspx?id={cinema_id}"
        
        await page.set_extra_http_headers({
            "Referer": referer_url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        
        if referer_url:
            try:
                print(f"  📍 訪問來源頁面...")
                await page.goto(referer_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  ⚠️  訪問來源頁面失敗: {e}")
        
        try:
            print(f"  🎬 訪問座位頁面...")
            await page.goto(seat_query_url, wait_until="domcontentloaded", timeout=30000)
            
            print(f"  ⏳ 等待座位表格...")
            await page.wait_for_selector("#GridViewSessionSeats", timeout=10000)
            await page.wait_for_timeout(2000)
            
            print(f"  ✓ 座位頁面載入成功")
            html = await page.content()
            
        except Exception as e:
            print(f"  ❌ 載入座位頁面失敗: {e}")
            return None

        soup = BeautifulSoup(html, 'html.parser')

        return {
            "movie_name": self._get_text(soup, "#LabelMovie_strName"),
            "movie_name_en": self._get_text(soup, "#LabelMovie_strNameEn"),
            "datetime": self._get_text(soup, "#LabelSession_dtmDateTime"),
            "cinema": self._get_text(soup, "#LabelCinema_strName"),
            "screen": self._get_text(soup, "#LabelScreen_strName"),
            "system_time": self._get_text(soup, "#LabelSystem_strTime"),
            "seats": self._parse_seats(soup),
        }

    def _get_text(self, soup: BeautifulSoup, selector: str) -> str:
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else ""

    def _parse_seats(self, soup: BeautifulSoup) -> List[Dict]:
        """解析座位表（支援橫向走道顯示）"""
        seats = []
        
        table = soup.select_one("#GridViewSessionSeats")
        if not table:
            return seats
        
        rows = table.find_all("tr")
        
        # ✅ 第一步：建立排號映射表
        row_mapping = {}  # {row_idx: 排號 或 "AISLE_X"}
        
        for row_idx, tr in enumerate(rows):
            cells = tr.find_all("td")
            
            # 檢查這一排是否有真實座位（有 label 且有 title）
            row_letter = None
            for td in cells:
                div_seat = td.select_one("div.DivSeat")
                if not div_seat:
                    continue
                    
                label = div_seat.select_one("div.label")
                if label:
                    seat_id = label.get("title")
                    if seat_id and len(seat_id) > 0:
                        # ✅ 從真實座位提取排號
                        row_letter = seat_id[0]
                        break
            
            if row_letter:
                # ✅ 這一排有真實座位
                row_mapping[row_idx] = row_letter
            else:
                # ✅ 這一排全是空格（橫向走道）
                # 找到前一排的排號，標記為 "AISLE_after_X"
                prev_row_letter = None
                for prev_idx in range(row_idx - 1, -1, -1):
                    if prev_idx in row_mapping and not row_mapping[prev_idx].startswith("AISLE_"):
                        prev_row_letter = row_mapping[prev_idx]
                        break
                
                if prev_row_letter:
                    row_mapping[row_idx] = f"AISLE_after_{prev_row_letter}"
                else:
                    row_mapping[row_idx] = f"AISLE_{row_idx}"
        
        # ✅ 第二步：解析所有座位
        for row_idx, tr in enumerate(rows):
            cells = tr.find_all("td")
            row_key = row_mapping.get(row_idx)
            
            if not row_key:
                continue
            
            # ✅ 檢查是否是橫向走道
            is_horizontal_aisle = row_key.startswith("AISLE_")
            
            if is_horizontal_aisle:
                # ✅ 橫向走道：創建特殊標記
                seats.append({
                    "seat_id": f"horizontal-aisle-{row_idx}",
                    "row": row_key,  # "AISLE_after_H"
                    "number": 0,
                    "status": "horizontal_aisle",
                    "row_idx": row_idx,
                    "col_idx": 0,
                    "type": "horizontal_aisle",
                    "width": len(cells)
                })
                continue
            
            # ✅ 一般排：解析座位、輪椅位、走道
            for col_idx, td in enumerate(cells):
                div_seat = td.select_one("div.DivSeat")
                if not div_seat:
                    continue
                
                label = div_seat.select_one("div.label")
                img = div_seat.select_one("img")
                
                # 座位（有 label）
                if label:
                    seat_id = label.get("title")
                    if not seat_id:
                        continue
                    
                    status = "available"
                    cls = label.get("class", [])
                    
                    if "label-danger" in cls:
                        status = "sold"
                    elif "label-warning" in cls:
                        status = "few_seats"
                    elif "label-info" in cls:
                        status = "available"
                    
                    seats.append({
                        "seat_id": seat_id,
                        "row": seat_id[0],
                        "number": int(seat_id[1:]) if seat_id[1:].isdigit() else 0,
                        "status": status,
                        "row_idx": row_idx,
                        "col_idx": col_idx,
                        "type": "seat"
                    })
                
                # 輪椅位
                elif img and 'wheelchair' in img.get('src', '').lower():
                    seats.append({
                        "seat_id": f"{row_key}-wheelchair-{col_idx}",
                        "row": row_key,
                        "number": 0,
                        "status": "wheelchair",
                        "row_idx": row_idx,
                        "col_idx": col_idx,
                        "type": "wheelchair"
                    })
                
                # 空位（縱向走道）
                elif img and 'null.png' in img.get('src', '').lower():
                    seats.append({
                        "seat_id": f"{row_key}-empty-{col_idx}",
                        "row": row_key,
                        "number": 0,
                        "status": "empty",
                        "row_idx": row_idx,
                        "col_idx": col_idx,
                        "type": "empty"
                    })
        
        return seats
    
    def get_seat_stats(self, seats: List[Dict]) -> Dict:
        """計算座位統計（只計算真實座位）"""
        real_seats = [s for s in seats if s.get('type') == 'seat']
        total = len(real_seats)
        sold = sum(1 for s in real_seats if s['status'] == 'sold')
        available = total - sold
        
        return {
            "total": total,
            "sold": sold,
            "available": available,
            "occupancy_rate": round(sold / total * 100, 2) if total > 0 else 0
        }
    
    async def close(self):
        """關閉瀏覽器"""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
        
        print("  ✓ 威秀瀏覽器已關閉")