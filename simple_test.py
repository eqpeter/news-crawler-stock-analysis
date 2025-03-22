import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def test_browser_connection():
    """測試Chrome瀏覽器連接"""
    print("測試Chrome瀏覽器連接...")
    
    try:
        # 設置Chrome瀏覽器
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 無界面模式
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # 使用webdriver_manager自動下載並管理ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 訪問Yahoo財經網站
        driver.get("https://tw.stock.yahoo.com/")
        
        # 等待頁面加載
        time.sleep(3)
        
        # 獲取頁面標題
        title = driver.title
        print(f"成功連接到網站。頁面標題: {title}")
        
        # 關閉瀏覽器
        driver.quit()
        
        return True
    
    except Exception as e:
        print(f"連接測試失敗: {str(e)}")
        return False

if __name__ == "__main__":
    test_browser_connection() 