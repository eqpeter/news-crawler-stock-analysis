import json
import os
from datetime import datetime

def test_chinese_encoding():
    """測試繁體中文編碼保存與讀取"""
    print("測試繁體中文編碼")
    print("=" * 50)
    
    # 建立測試資料
    test_data = [
        {
            "title": "台積電第一季財報優於預期",
            "content": "台積電公布第一季財報，優於市場預期，淨利達新台幣2,500億元。",
            "date": "2023-04-15",
            "category": "財經新聞"
        },
        {
            "title": "高端疫苗獲食藥署緊急授權",
            "content": "高端疫苗通過食藥署緊急使用授權，將投入台灣新冠疫苗接種計畫。",
            "date": "2023-04-10",
            "category": "健康醫療"
        },
        {
            "title": "天氣預報：週末全台有雨",
            "content": "中央氣象局預報，本週末全台將有一波鋒面通過，各地有雨。",
            "date": "2023-04-12",
            "category": "氣象報導"
        }
    ]
    
    # 確保目錄存在
    os.makedirs("test_results", exist_ok=True)
    
    # 生成時間戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_file = f"test_results/chinese_encoding_test_{timestamp}.json"
    
    print(f"原始數據:")
    for item in test_data:
        print(f"- {item['title']}")
    
    # 保存測試資料
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n數據已保存到: {test_file}")
    
    # 讀取並顯示
    print("\n讀取保存的數據:")
    with open(test_file, 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    
    for item in loaded_data:
        print(f"- {item['title']}")
    
    # 直接顯示文件內容
    print("\n文件原始內容:")
    with open(test_file, 'r', encoding='utf-8') as f:
        print(f.read())
    
    # 測試不同的編碼格式
    encoding_types = ['utf-8', 'utf-8-sig', 'gb18030', 'big5']
    
    for encoding in encoding_types:
        try:
            read_file = f"test_results/chinese_encoding_{encoding}_{timestamp}.json"
            
            # 使用不同編碼保存
            with open(read_file, 'w', encoding=encoding) as f:
                json.dump(test_data, f, ensure_ascii=False, indent=2)
            
            # 讀取並顯示
            print(f"\n使用 {encoding} 編碼保存後讀取:")
            with open(read_file, 'r', encoding=encoding) as f:
                read_data = json.load(f)
                for item in read_data:
                    print(f"- {item['title']}")
        except Exception as e:
            print(f"{encoding} 編碼測試失敗: {e}")

if __name__ == "__main__":
    test_chinese_encoding() 