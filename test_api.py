import requests
import json
import time

def test_api():
    """測試API返回的數據格式及標記"""
    print("===== 測試API返回數據 =====\n")
    
    # API基礎URL
    base_url = "http://localhost:5000"
    
    # 設定關鍵字列表
    keywords = ["台積電", "2330"]
    
    for keyword in keywords:
        print(f"\n使用關鍵字'{keyword}'測試API...\n")
        
        # 記錄開始時間
        start_time = time.time()
        
        # 構建API URL
        api_url = f"{base_url}/api/v2/news?keyword={keyword}&source=moneydj&limit=3"
        print(f"請求URL: {api_url}")
        
        try:
            # 發送API請求
            response = requests.get(api_url)
            
            # 檢查狀態碼
            if response.status_code == 200:
                # 解析返回的JSON數據
                result = response.json()
                
                # 計算請求耗時
                elapsed_time = time.time() - start_time
                
                # 顯示API返回信息
                print(f"API狀態: {result['status']}")
                print(f"API消息: {result['message']}")
                print(f"獲取新聞數量: {result['count']}")
                print(f"API請求耗時: {elapsed_time:.2f}秒\n")
                
                # 檢查新聞數據
                if result['count'] > 0:
                    print(f"新聞示例 (最多顯示3條):")
                    for i, news in enumerate(result['data'][:3], 1):
                        print(f"{i}. {news['title']}")
                        print(f"   日期: {news['published_time']}")
                        print(f"   平台: {news['platform']}")
                        # 檢查並顯示is_sample標記
                        if 'is_sample' in news:
                            sample_status = "示例數據" if news['is_sample'] else "真實數據"
                            print(f"   數據類型: {sample_status}")
                        else:
                            print(f"   數據類型: 未標記")
                        print()
                else:
                    print("沒有找到相關新聞")
            else:
                print(f"API請求失敗，狀態碼: {response.status_code}")
                print(f"錯誤信息: {response.text}")
        
        except Exception as e:
            print(f"測試過程中發生錯誤: {e}")
    
    print("\n===== API測試完成 =====")

if __name__ == "__main__":
    test_api() 