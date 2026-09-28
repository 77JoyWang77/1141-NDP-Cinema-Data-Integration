# seat_status_provider.py
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from typing import Dict, List
import re


class SeatStatusProvider:
    def __init__(self):
        self.base_url = "https://www.vscinemas.com.tw"

    def fetch(self, seat_query_url: str, referer_url: str = None) -> Dict:
        """
        取得單一場次的座位狀態
        
        Args:
            seat_query_url: 座位查詢 URL
            referer_url: 來源頁面 URL（影城場次頁面）
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False
            )
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            )
            
            page = context.new_page()
            
            # 🔥 關鍵：添加反爬蟲腳本
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            # 🔥 方法 1: 如果有 referer，先訪問來源頁面
            if referer_url:
                try:
                    print(f"  先訪問來源頁面: {referer_url}")
                    page.goto(referer_url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(2000)  # 等待 2 秒
                except Exception as e:
                    print(f"  ⚠️  訪問來源頁面失敗: {e}")
            
            # 🔥 方法 2: 設定 Referer header
            if not referer_url:
                # 從 seat_query_url 推測 cinema_id
                cinema_id_match = re.search(r'CinemaCode=(\d+)', seat_query_url)
                cinema_id = cinema_id_match.group(1) if cinema_id_match else "1"
                referer_url = f"https://www.vscinemas.com.tw/theater/detail.aspx?id={cinema_id}"
            
            # 設定額外的 headers
            page.set_extra_http_headers({
                "Referer": referer_url,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            })
            
            # 訪問座位頁面
            try:
                print(f"  正在訪問座位頁面...")
                page.goto(seat_query_url, wait_until="domcontentloaded", timeout=30000)
                
                # 等待座位表格載入
                page.wait_for_selector("#GridViewSessionSeats", timeout=10000)
                page.wait_for_timeout(2000)  # 額外等待確保資料載入完成
                
                html = page.content()
                browser.close()
                
            except Exception as e:
                print(f"  ❌ 載入座位頁面失敗: {e}")
                browser.close()
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

    # -----------------------
    # Internal helpers
    # -----------------------

    def _get_text(self, soup: BeautifulSoup, selector: str) -> str:
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else ""

    def _parse_seats(self, soup: BeautifulSoup) -> List[Dict]:
        """
        解析座位表（GridViewSessionSeats）
        """
        seats = []
        seat_divs = soup.select("#GridViewSessionSeats div.DivSeat")

        for div in seat_divs:
            label = div.select_one("div.label")
            img = div.select_one("img")

            # 空白 / 走道 / 輪椅位
            if not label:
                # 檢查是否為輪椅位
                if img and 'wheelchair' in img.get('src', ''):
                    wheelchair_title = img.get('alt', '') or img.get('title', '')
                    # 可以記錄輪椅位的位置，但不加入座位列表
                    continue
                # 普通空白格
                continue

            seat_id = label.get("title")
            if not seat_id:
                continue

            # 判斷座位狀態
            status = "available"
            cls = label.get("class", [])

            if "label-danger" in cls:
                status = "sold"
            elif "label-warning" in cls:
                status = "few_seats"  # 如果有黃色警告
            elif "label-info" in cls:
                status = "available"

            seats.append({
                "seat_id": seat_id,
                "row": seat_id[0],
                "number": int(seat_id[1:]) if seat_id[1:].isdigit() else 0,
                "status": status
            })

        return seats
    
    def get_seat_stats(self, seats: List[Dict]) -> Dict:
        """計算座位統計"""
        total = len(seats)
        sold = sum(1 for s in seats if s['status'] == 'sold')
        available = total - sold
        
        return {
            "total": total,
            "sold": sold,
            "available": available,
            "occupancy_rate": round(sold / total * 100, 2) if total > 0 else 0
        }


# -----------------------
# Debug / standalone run
# -----------------------

if __name__ == "__main__":
    # 測試 URL
    seat_url = "https://sales.vscinemas.com.tw/VoucherTicketing/SessionSeats.aspx?CinemaCode=1&txtSessionId=1833978"
    
    # 來源頁面（影城場次頁面）
    referer = "https://www.vscinemas.com.tw/theater/detail.aspx?id=1"
    
    provider = SeatStatusProvider()
    
    print("=" * 60)
    print("測試：抓取座位狀態")
    print("=" * 60)
    
    data = provider.fetch(seat_url, referer_url=referer)
    
    if data:
        print(f"\n🎬 電影：{data['movie_name']} / {data['movie_name_en']}")
        print(f"🏢 影城：{data['cinema']}")
        print(f"🎥 廳別：{data['screen']}")
        print(f"🕒 場次：{data['datetime']}")
        print(f"⏰ 系統時間：{data['system_time']}")
        
        # 統計座位
        stats = provider.get_seat_stats(data['seats'])
        print(f"\n💺 總座位數：{stats['total']}")
        print(f"✅ 可售座位：{stats['available']}")
        print(f"❌ 已售座位：{stats['sold']}")
        print(f"📊 銷售率：{stats['occupancy_rate']}%")
        
        # 顯示已售座位
        sold_seats = [s for s in data['seats'] if s['status'] == 'sold']
        if sold_seats:
            print(f"\n已售座位：")
            for seat in sold_seats[:10]:  # 只顯示前 10 個
                print(f"  {seat['seat_id']}", end=" ")
            if len(sold_seats) > 10:
                print(f"... 等 {len(sold_seats)} 個座位")
            else:
                print()
    else:
        print("❌ 抓取失敗")