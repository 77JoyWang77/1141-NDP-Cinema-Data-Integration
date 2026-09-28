# 電影資訊整合系統（Cinema Info Integration）

整合 **威秀** 與 **秀泰** 兩家影城的電影、場次與即時座位資訊，提供跨影城查詢的網站。

> 國立中央大學「網路與資料庫程式設計」期末個人專案（114-1）

## 專案緣起

原本目標是比較各影城的票價。實作後發現各家的票價規則差異極大、難以標準化，因此先完成跨影城的場次與座位資料整合，作為票價對比的基礎，票價計算列為後續工作。

## 功能

- 跨影城查詢電影、影城與場次（威秀 22 間 + 秀泰 15 間，約 5,300 個場次）
- 同一部電影跨影城合併顯示（以中文片名合併，分級、日期格式統一）
- 即時座位查詢：共用已登入的 session 並非同步化，單次查詢由約 10 秒降到約 1 秒；Redis 快取 60 秒
- 統計頁面：各影城、各電影場次數

## 系統架構

```
Playwright / BeautifulSoup 爬蟲 → JSON（backend/data/raw）
        → db_loader.py 清理、合併、建立索引 → MongoDB
        → FastAPI（backend/main.py） → React + Vite + Tailwind（frontend）
```

| 目錄 | 內容 |
|---|---|
| `backend/app/crawlers/` | 威秀、秀泰的影城 / 電影 / 場次爬蟲與座位查詢 |
| `backend/db_loader.py` | 資料清理、跨影城合併、MongoDB 索引 |
| `backend/main.py` | FastAPI：電影、影城、場次、座位、統計等 API |
| `frontend/` | React 前端 |

## 執行方式

需求：Python 3.11、Node.js 18+、MongoDB，Redis 可選。

```bash
# 後端
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
cp ../.env.example .env        # 填入 MongoDB 連線；座位查詢需填秀泰會員帳密
python db_loader.py            # 匯入 data/raw 中的爬蟲資料
python main.py                 # http://localhost:8000

# 前端
cd frontend
npm install
npm run dev                    # http://localhost:5173
```

## 限制

- 票價對比尚未完成：各影城的票價規則需先建立統一的計價模型。
- 爬蟲依賴網站結構，網站改版後可能需要調整。
