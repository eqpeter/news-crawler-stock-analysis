import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime, timedelta

def test_yahoo_stock_news():
    """測試Yahoo財經個股新聞功能"""
    print("測試Yahoo財經個股新聞功能...")
    
    # 設置Chrome瀏覽器
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 無界面模式
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")  # 增加視窗大小
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # 台積電股票代碼
        stock_code = "2330.TW"
        
        # 直接訪問個股新聞頁面
        news_url = f"https://tw.stock.yahoo.com/quote/{stock_code}/news"
        print(f"訪問個股新聞頁面: {news_url}")
        driver.get(news_url)
        
        # 等待頁面加載
        time.sleep(5)
        print("頁面標題: " + driver.title)
        
        # 滾動頁面以加載更多內容
        print("滾動頁面以加載更多內容...")
        for i in range(3):
            driver.execute_script("window.scrollBy(0, 500)")
            time.sleep(1)
        
        # 使用JavaScript分析頁面
        print("\n使用JavaScript分析頁面...")
        has_news_js = driver.execute_script("""
            // 嘗試查找包含'新聞'的元素
            var elements = document.querySelectorAll('*');
            var newsElements = [];
            for(var i=0; i<elements.length; i++) {
                if(elements[i].innerText && elements[i].innerText.includes('新聞')) {
                    newsElements.push({
                        tag: elements[i].tagName,
                        text: elements[i].innerText.substring(0, 50),
                        childCount: elements[i].children.length
                    });
                }
            }
            return newsElements.slice(0, 10); // 返回前10個
        """)
        
        print(f"找到 {len(has_news_js)} 個包含'新聞'的元素")
        for i, elem in enumerate(has_news_js):
            print(f"  {i+1}. {elem['tag']}: {elem['text']}... (子元素: {elem['childCount']})")
        
        # 使用BeautifulSoup解析頁面
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # 尋找所有連結
        print("\n分析頁面中的連結...")
        links = soup.find_all('a')
        print(f"頁面中共有 {len(links)} 個連結")
        
        # 找出可能包含新聞的連結
        news_links = []
        for link in links:
            # 檢查連結文本或href是否包含新聞相關關鍵詞
            link_text = link.text.strip()
            link_href = link.get('href', '')
            if (link_text and len(link_text) > 10 and not link_text.startswith('http') and 
                not any(keyword in link_text.lower() for keyword in ['登入', '註冊', '首頁', '股市', '選單', '會員'])):
                # 可能是新聞標題
                news_links.append({
                    'text': link_text[:50] + ('...' if len(link_text) > 50 else ''),
                    'href': link_href
                })
        
        # 打印可能的新聞連結
        print(f"\n找到 {len(news_links)} 個可能的新聞連結")
        for i, link in enumerate(news_links[:10]):  # 只顯示前10個
            print(f"  {i+1}. {link['text']} -> {link['href'][:50]}...")
        
        # 尋找包含時間的元素
        print("\n尋找包含時間的元素...")
        time_patterns = [
            r'\d{1,2}小時前', 
            r'\d{1,2}分鐘前',
            r'\d{4}/\d{1,2}/\d{1,2}',
            r'\d{2}:\d{2}'
        ]
        
        for pattern in time_patterns:
            time_elements = soup.find_all(string=re.compile(pattern))
            print(f"包含'{pattern}'的元素數量: {len(time_elements)}")
            for i, elem in enumerate(time_elements[:3]):  # 只顯示前3個
                parent = elem.parent
                parent_name = parent.name if parent else "無"
                print(f"  {i+1}. '{elem.strip()}' (父元素: {parent_name})")
                # 檢查附近的元素是否包含可能的新聞標題
                if parent:
                    siblings = list(parent.next_siblings) + list(parent.previous_siblings)
                    for sibling in siblings[:2]:
                        if hasattr(sibling, 'text') and sibling.text and len(sibling.text.strip()) > 10:
                            print(f"     相鄰元素: {sibling.name}: {sibling.text.strip()[:50]}...")
        
        # 手動點擊"更多"按鈕以加載更多新聞
        try:
            print("\n嘗試點擊'更多'按鈕...")
            more_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), '更多')]")
            if more_buttons:
                print(f"找到 {len(more_buttons)} 個'更多'按鈕")
                for i, button in enumerate(more_buttons):
                    print(f"  嘗試點擊第 {i+1} 個按鈕")
                    try:
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(2)
                        print("  點擊成功")
                    except Exception as e:
                        print(f"  點擊失敗: {str(e)}")
            else:
                print("未找到'更多'按鈕")
        except Exception as e:
            print(f"查找'更多'按鈕時發生錯誤: {str(e)}")
        
        # 再次解析頁面以查找可能新增的內容
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # 嘗試分析最可能的新聞列表結構
        print("\n嘗試識別新聞列表結構...")
        # 檢查不同的列表元素
        list_containers = ['ul', 'ol', 'div[role="list"]']
        for container in list_containers:
            lists = soup.select(container)
            for i, lst in enumerate(lists):
                items = lst.find_all(['li', 'div[role="listitem"]', 'article']) if container == 'div[role="list"]' else lst.find_all(['li', 'article'])
                if len(items) >= 3:  # 至少有3個項目才可能是新聞列表
                    print(f"潛在的新聞列表 {i+1}: {lst.name} 包含 {len(items)} 個項目")
                    # 檢查第一個項目
                    sample_item = items[0]
                    links_in_item = sample_item.find_all('a')
                    times_in_item = sample_item.find_all(string=lambda text: any(re.search(pattern, str(text)) for pattern in time_patterns))
                    if links_in_item and times_in_item:
                        print(f"  可能性很高! 包含鏈接和時間信息")
                        print(f"  示例標題: {sample_item.text.strip()[:50]}...")
                        # 提取並顯示前3條新聞
                        print("\n提取的新聞:")
                        for j, item in enumerate(items[:3]):
                            title_elem = item.find('a')
                            time_elem = item.find(string=lambda text: any(re.search(pattern, str(text)) for pattern in time_patterns))
                            if title_elem and time_elem:
                                print(f"  {j+1}. 標題: {title_elem.text.strip()[:50]}...")
                                print(f"     時間: {time_elem.strip()}")
                                print(f"     鏈接: {title_elem.get('href', '無連結')[:50]}...")
    
    except Exception as e:
        print(f"測試過程中發生錯誤: {str(e)}")
    
    finally:
        # 保存頁面源碼以供分析
        with open("yahoo_stock_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("\n已保存頁面源碼到 yahoo_stock_page.html 文件")
        
        # 截圖以供分析
        driver.save_screenshot("yahoo_stock_page.png")
        print("已保存頁面截圖到 yahoo_stock_page.png 文件")
        
        # 關閉瀏覽器
        driver.quit()

if __name__ == "__main__":
    test_yahoo_stock_news() 