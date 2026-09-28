# filter_valid_showtimes.py

import json
from pathlib import Path
from datetime import datetime, timedelta


def filter_valid_showtimes():
    """過濾出有效的場次並儲存"""
    
    BASE_DIR = Path(__file__).resolve().parents[3]
    input_path = BASE_DIR / "data" / "raw" / "showtime" / "showtime.json"
    output_path = BASE_DIR / "data" / "raw" / "showtime" / "showtime_valid.json"
    
    if not input_path.exists():
        print(f"❌ 找不到 {input_path}")
        return
    
    with open(input_path, "r", encoding="utf-8") as f:
        all_showtimes = json.load(f)
    
    print("=" * 70)
    print("🔍 過濾有效場次")
    print("=" * 70)
    print(f"\n原始資料：{len(all_showtimes)} 個場次")
    
    now = datetime.now()
    print(f"當前時間：{now.strftime('%Y-%m-%d %H:%M')}")
    
    valid_showtimes = []
    
    for showtime in all_showtimes:
        date_str = showtime.get('date', '')
        time_range = showtime.get('time_range', '')
        
        try:
            # 解析日期：12月18日
            month = int(date_str.split('月')[0])
            day = int(date_str.split('月')[1].replace('日', ''))
            
            # 解析時間：14:00 ~ 16:30
            if '~' in time_range:
                start_time = time_range.split('~')[0].strip()
                start_hour = int(start_time.split(':')[0])
                start_minute = int(start_time.split(':')[1])
            else:
                continue
            
            # 構建完整時間
            year = now.year
            # 處理跨年的情況
            if month < now.month:
                year += 1
            
            showtime_dt = datetime(year, month, day, start_hour, start_minute)
            
            # 只保留未來的場次（至少還有30分鐘）
            if showtime_dt > now + timedelta(minutes=30):
                valid_showtimes.append(showtime)
                
        except Exception as e:
            # 解析失敗，跳過
            continue
    
    print(f"過濾後：{len(valid_showtimes)} 個有效場次")
    print(f"移除：{len(all_showtimes) - len(valid_showtimes)} 個過期場次")
    
    # 統計
    date_counts = {}
    for showtime in valid_showtimes:
        date = showtime.get('date', '')
        date_counts[date] = date_counts.get(date, 0) + 1
    
    print("\n📅 各日期的場次數量：")
    for date in sorted(date_counts.keys()):
        print(f"   {date}: {date_counts[date]} 個")
    
    # 儲存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(valid_showtimes, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 已儲存到：{output_path}")
    print("=" * 70)


if __name__ == "__main__":
    filter_valid_showtimes()