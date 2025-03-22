import json
import glob
import os
from pathlib import Path

def fix_json_encoding():
    """修復JSON文件的編碼問題，確保繁體中文正確顯示"""
    # 查找最近生成的JSON文件
    results_dir = Path("results")
    json_files = list(results_dir.glob("*.json"))
    
    if not json_files:
        print("未找到任何JSON文件")
        return
    
    # 按修改時間排序，找出最新的文件
    latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
    print(f"處理文件: {latest_file}")
    
    try:
        # 讀取原始JSON內容
        with open(latest_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                print("成功讀取JSON文件")
            except json.JSONDecodeError:
                # 如果解析失敗，嘗試直接讀取文本內容
                f.seek(0)
                content = f.read()
                print("JSON解析失敗，嘗試修復...")
                
                # 嘗試移除可能損壞的BOM標記或其他異常字符
                if content.startswith('\ufeff'):
                    content = content[1:]
                
                try:
                    data = json.loads(content)
                except:
                    print("無法解析JSON內容")
                    return
        
        # 確認我們能夠顯示原始數據的標題
        print("\n原始數據中的標題:")
        for item in data:
            print(f"- {item.get('title', '無標題')}")
        
        # 修復後的文件名
        fixed_file = latest_file.with_name(f"{latest_file.stem}_fixed.json")
        
        # 重新保存文件
        with open(fixed_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n已修復並保存到: {fixed_file}")
        
        # 顯示修復後的內容
        print("\n修復後的JSON內容:")
        with open(fixed_file, 'r', encoding='utf-8') as f:
            fixed_data = json.load(f)
            print(json.dumps(fixed_data, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"處理過程中發生錯誤: {e}")

if __name__ == "__main__":
    fix_json_encoding() 