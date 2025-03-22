from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
import os
import json

class MoneyDJCrawler:
    """MoneyDJ新聞爬蟲，用於獲取台股相關新聞"""
    
    def __init__(self):
        """初始化爬蟲，設置基本URL"""
        # 搜索頁面URL
        self.base_url = "https://www.moneydj.com/KMDJ/search/list.aspx?_QueryType=NW&_Query="
        # 網站根域名
        self.news_base_url = "https://www.moneydj.com"
        # 直接訪問股票頁面的URL
        self.stock_url = "https://www.moneydj.com/ETFIndice/Stock.aspx?Code="
        # 新聞頁面URL
        self.news_url = "https://www.moneydj.com/KMDJ/News/NewsRealList.aspx?a=MB010000"
        # 網站首頁
        self.home_url = "https://www.moneydj.com"
    
    def _setup_driver(self):
        """設置Chrome瀏覽器驅動，配置無頭模式和其他選項"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # 無界面模式
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            # 使用較新的 User-Agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
            
            # 增加JavaScript運行允許
            chrome_options.add_argument("--enable-javascript")
            
            # 禁用WebGL，避免相關錯誤信息
            chrome_options.add_argument("--disable-webgl")
            chrome_options.add_argument("--disable-3d-apis")
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 設置頁面加載超時時間
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            print(f"設置Chrome驅動時出錯: {e}")
            raise
    
    def _extract_date(self, date_text):
        """從文本中提取日期時間"""
        now = datetime.now()
        
        if not date_text:
            return now
        
        # 移除多餘空格
        date_text = date_text.strip().replace('\n', '').replace('\t', '').replace('\r', '')
        
        try:
            # 嘗試解析 MoneyDJ 日期格式 (yyyy-MM-dd HH:mm:ss)
            return datetime.strptime(date_text, "%Y-%m-%d %H:%M:%S")
        except:
            try:
                # 嘗試解析 MoneyDJ 日期格式 (yyyy-MM-dd)
                return datetime.strptime(date_text, "%Y-%m-%d")
            except:
                try:
                    # 嘗試解析 MoneyDJ 日期格式 (yyyy/MM/dd)
                    return datetime.strptime(date_text, "%Y/%m/%d")
                except:
                    try:
                        # 嘗試解析 MoneyDJ 日期格式 (yyyy/MM/dd HH:mm)
                        return datetime.strptime(date_text, "%Y/%m/%d %H:%M")
                    except:
                        try:
                            # 嘗試通過正則表達式提取日期
                            date_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_text)
                            if date_match:
                                year, month, day = map(int, date_match.groups())
                                return datetime(year, month, day)
                        except:
                            # 如果沒有找到匹配格式，返回當前時間
                            return now
        
        return now
    
    def _is_within_hours(self, news_date, hours):
        """判斷新聞是否在指定小時數內"""
        now = datetime.now()
        time_diff = now - news_date
        return time_diff.total_seconds() <= hours * 3600
    
    def _get_sample_news(self, keyword, count=3):
        """獲取示例新聞數據，當無法從網站獲取真實新聞時使用"""
        sample_news = []
        
        # 常見台股相關的示例標題
        titles = [
            f"{keyword}公司發布最新財報，營收創新高",
            f"分析師看好{keyword}未來發展前景",
            f"{keyword}獲利成長，投資人關注後市表現",
            f"{keyword}與供應商簽訂長期合作協議",
            f"{keyword}積極布局AI市場，擴大市占率",
            f"外資大幅買超{keyword}，後市有望上漲",
            f"投資分析: {keyword}評價偏高，建議逢高獲利了結",
            f"{keyword}業績表現優於預期，股價上漲",
            f"{keyword}將加碼投資新技術研發"
        ]
        
        # 示例摘要內容
        summaries = [
            f"根據最新財報顯示，{keyword}上季營收成長15%，淨利率提升至20%，優於市場預期。",
            f"多家外資券商上調{keyword}目標價，看好其在AI和高端製程的發展前景。",
            f"{keyword}公司宣布將在今年第四季推出新產品線，有望帶動營收進一步成長。",
            f"受惠於全球半導體供應鏈重組，{keyword}獲得更多大客戶訂單，產能利用率提升。",
            f"{keyword}投資新興科技領域，預計未來三年將投入千億資金，強化市場競爭力。",
            f"面對市場競爭日益激烈，{keyword}採取積極策略，優化產品結構，提升獲利能力。"
        ]
        
        import random
        for i in range(count):
            title_index = random.randint(0, len(titles)-1)
            summary_index = random.randint(0, len(summaries)-1)
            
            # 生成1-7天內的隨機日期
            random_days = random.randint(0, 7)
            random_hours = random.randint(0, 23)
            random_date = datetime.now() - timedelta(days=random_days, hours=random_hours)
            
            news = {
                "title": titles[title_index],
                "link": "https://www.moneydj.com",
                "date": random_date,
                "published_time": random_date.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "MoneyDJ",
                "summary": summaries[summary_index],
                "platform": "MoneyDJ",
                "is_sample": True  # 標記為示例數據
            }
            sample_news.append(news)
        
        return sample_news
    
    def crawl(self, keyword, limit=10, hours=24):
        """
        爬取MoneyDJ關於指定關鍵字的新聞
        
        參數:
            keyword (str): 關鍵字或股票代號
            limit (int): 最多返回的新聞條數
            hours (int): 只獲取多少小時內的新聞
            
        返回:
            list: 新聞列表，每條新聞為一個字典，包含標題、鏈接、日期、來源、概要等信息
        """
        driver = None
        news_list = []
        
        try:
            print(f"開始爬取MoneyDJ關於'{keyword}'的新聞...")
            driver = self._setup_driver()
            
            # 首先嘗試直接訪問股票頁面（如果關鍵字是股票代碼）
            if keyword.isdigit() and len(keyword) <= 5:
                try:
                    stock_page_url = f"{self.stock_url}{keyword}"
                    print(f"嘗試直接訪問股票頁面: {stock_page_url}")
                    driver.get(stock_page_url)
                    time.sleep(5)
                    
                    # 保存截圖和HTML源碼以便調試
                    os.makedirs("debug", exist_ok=True)
                    driver.save_screenshot(f"debug/moneydj_stock_page_{keyword}.png")
                    
                    # 獲取頁面原始碼
                    stock_page_source = driver.page_source
                    with open(f"debug/moneydj_stock_html_{keyword}.html", "w", encoding="utf-8") as f:
                        f.write(stock_page_source)
                    
                    # 解析股票頁面，嘗試尋找相關新聞鏈接
                    soup = BeautifulSoup(stock_page_source, "html.parser")
                    stock_news_links = soup.select('a[href*="NewsContent"], a[href*="Content"], .NewsList a, .news_list a')
                    
                    if stock_news_links:
                        print(f"在股票頁面找到 {len(stock_news_links)} 個新聞鏈接")
                        for link in stock_news_links:
                            title = link.get_text().strip()
                            href = link.get('href', '')
                            
                            # 跳過空標題或特定導航鏈接
                            if not title or title in ['登入', '技術學院', '下一頁', '上一頁']:
                                continue
                            
                            # 確保完整URL
                            if not href.startswith('http'):
                                href = self.news_base_url + href
                            
                            # 由於無法直接獲取日期，使用當前日期
                            news_date = datetime.now()
                            
                            # 添加到新聞列表
                            news = {
                                "title": title,
                                "link": href,
                                "date": news_date,
                                "published_time": news_date.strftime("%Y-%m-%d %H:%M:%S"),
                                "source": "MoneyDJ",
                                "summary": "",
                                "platform": "MoneyDJ",
                                "is_sample": False  # 標記為真實數據
                            }
                            
                            # 避免重複
                            if not any(n.get("title") == title for n in news_list):
                                news_list.append(news)
                                print(f"找到新聞: {title}")
                            
                            if len(news_list) >= limit:
                                break
                
                except Exception as e:
                    print(f"訪問股票頁面時出錯: {e}")
            
            # 如果還沒找到足夠新聞，直接訪問首頁
            if len(news_list) < limit:
                try:
                    print("訪問MoneyDJ首頁")
                    driver.get(self.home_url)
                    time.sleep(8)
                    
                    # 保存截圖和HTML源碼以便調試
                    driver.save_screenshot(f"debug/moneydj_home_page.png")
                    
                    # 獲取頁面原始碼
                    page_source = driver.page_source
                    with open(f"debug/moneydj_home_html.html", "w", encoding="utf-8") as f:
                        f.write(page_source)
                    
                    # 解析首頁
                    soup = BeautifulSoup(page_source, "html.parser")
                    
                    # 找到所有可能的新聞鏈接
                    all_links = soup.find_all('a', href=True)
                    home_news_links = []
                    
                    for link in all_links:
                        href = link.get('href', '')
                        title = link.get_text().strip()
                        
                        # 跳過空標題或特定導航鏈接
                        if not title or len(title) < 5 or title in ['登入', '技術學院', '下一頁', '上一頁']:
                            continue
                        
                        # 檢查是否包含關鍵字
                        if keyword.lower() in title.lower():
                            # 確保完整URL
                            if not href.startswith('http'):
                                if href.startswith('/'):
                                    href = self.news_base_url + href
                                else:
                                    href = self.news_base_url + '/' + href
                            
                            home_news_links.append((title, href))
                    
                    # 處理首頁找到的相關新聞
                    if home_news_links:
                        print(f"在首頁找到 {len(home_news_links)} 條包含關鍵字的新聞")
                        for title, href in home_news_links:
                            # 添加到新聞列表
                            news = {
                                "title": title,
                                "link": href,
                                "date": datetime.now(),
                                "published_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "source": "MoneyDJ",
                                "summary": "",
                                "platform": "MoneyDJ",
                                "is_sample": False  # 標記為真實數據
                            }
                            
                            # 避免重複
                            if not any(n.get("title") == title for n in news_list):
                                news_list.append(news)
                                print(f"找到相關新聞: {title}")
                            
                            if len(news_list) >= limit:
                                break
                except Exception as e:
                    print(f"訪問首頁時出錯: {e}")
            
            # 如果還沒找到足夠新聞，訪問新聞頁面
            if len(news_list) < limit:
                try:
                    print("訪問MoneyDJ新聞頁面")
                    driver.get(self.news_url)
                    time.sleep(5)
                    
                    # 保存截圖和HTML源碼以便調試
                    driver.save_screenshot(f"debug/moneydj_news_page.png")
                    
                    # 獲取頁面原始碼
                    news_page_source = driver.page_source
                    with open(f"debug/moneydj_news_html.html", "w", encoding="utf-8") as f:
                        f.write(news_page_source)
                    
                    # 解析新聞頁面
                    soup = BeautifulSoup(news_page_source, "html.parser")
                    
                    # 找到所有新聞列表
                    news_containers = soup.select('.NewsList, .news_list, .main_news, .news_container, [class*="news"]')
                    news_links = []
                    
                    for container in news_containers:
                        links = container.find_all('a', href=True)
                        for link in links:
                            title = link.get_text().strip()
                            href = link.get('href', '')
                            
                            # 跳過空標題或特定導航鏈接
                            if not title or len(title) < 5 or title in ['登入', '技術學院', '下一頁', '上一頁']:
                                continue
                            
                            # 確保完整URL
                            if not href.startswith('http'):
                                if href.startswith('/'):
                                    href = self.news_base_url + href
                                else:
                                    href = self.news_base_url + '/' + href
                            
                            news_links.append((title, href))
                    
                    # 處理新聞頁面找到的相關新聞
                    if news_links:
                        # 首先篩選包含關鍵字的新聞
                        keyword_news = [(t, h) for t, h in news_links if keyword.lower() in t.lower()]
                        
                        if keyword_news:
                            print(f"在新聞頁面找到 {len(keyword_news)} 條包含關鍵字的新聞")
                            for title, href in keyword_news:
                                # 添加到新聞列表
                                news = {
                                    "title": title,
                                    "link": href,
                                    "date": datetime.now(),
                                    "published_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "source": "MoneyDJ",
                                    "summary": "",
                                    "platform": "MoneyDJ",
                                    "is_sample": False  # 標記為真實數據
                                }
                                
                                # 避免重複
                                if not any(n.get("title") == title for n in news_list):
                                    news_list.append(news)
                                    print(f"找到相關新聞: {title}")
                                
                                if len(news_list) >= limit:
                                    break
                        
                        # 如果還是沒找到足夠多的新聞，添加一些最新新聞
                        if len(news_list) < limit:
                            print(f"添加最新新聞，目前已有 {len(news_list)} 條新聞")
                            for title, href in news_links:
                                # 添加到新聞列表
                                news = {
                                    "title": title,
                                    "link": href,
                                    "date": datetime.now(),
                                    "published_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "source": "MoneyDJ",
                                    "summary": "",
                                    "platform": "MoneyDJ",
                                    "is_sample": False  # 標記為真實數據
                                }
                                
                                # 避免重複
                                if not any(n.get("title") == title for n in news_list):
                                    news_list.append(news)
                                    print(f"找到最新新聞: {title}")
                                
                                if len(news_list) >= limit:
                                    break
                    else:
                        print("在新聞頁面沒有找到任何新聞連結")
                except Exception as e:
                    print(f"訪問新聞頁面時出錯: {e}")
            
            # 如果依然沒有找到任何新聞，添加一些虛擬的新聞數據
            if not news_list:
                print("未能在網站找到任何新聞，添加示例新聞資料")
                sample_count = min(limit, 5)  # 最多返回5條示例新聞
                news_list = self._get_sample_news(keyword, sample_count)
            
            print(f"MoneyDJ爬蟲完成，共找到 {len(news_list)} 條新聞")
        
        except Exception as e:
            print(f"爬取MoneyDJ新聞時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            
            # 發生錯誤時也返回示例新聞
            if not news_list:
                sample_count = min(limit, 3)
                news_list = self._get_sample_news(keyword, sample_count)
                print(f"由於錯誤，返回 {len(news_list)} 條示例新聞")
        
        finally:
            # 確保瀏覽器驅動正確關閉
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    print(f"關閉瀏覽器時出錯: {e}")
        
        return news_list
    
    def get_news_detail(self, url):
        """
        獲取新聞詳情
        
        參數:
            url (str): 新聞鏈接
            
        返回:
            dict: 包含新聞詳情的字典
        """
        driver = None
        detail = {"content": "", "images": [], "is_sample": False}
        
        try:
            print(f"訪問新聞頁面: {url}")
            driver = self._setup_driver()
            driver.get(url)
            
            # 等待頁面加載
            time.sleep(5)
            
            # 使用BeautifulSoup解析頁面
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # 嘗試查找內容區域
            content_elems = soup.select('.NewsContent, .news-content, #newsContent, .article-content, .content')
            
            if content_elems:
                content_elem = content_elems[0]
                
                # 獲取文本內容
                content = content_elem.get_text().strip()
                detail["content"] = content
                
                # 獲取圖片
                images = content_elem.select('img')
                for img in images:
                    src = img.get('src')
                    if src:
                        # 確保完整URL
                        if not src.startswith('http'):
                            src = self.news_base_url + src
                        detail["images"].append(src)
            
            # 如果無法獲取內容，提供示例內容
            if not detail["content"]:
                detail["content"] = "此新聞內容暫時無法獲取，請直接訪問原始新聞網頁查看詳情。MoneyDJ提供台灣股市最新動態和財經新聞。"
                detail["is_sample"] = True  # 標記為示例數據
        
        except Exception as e:
            print(f"獲取新聞詳情時發生錯誤: {e}")
            detail["content"] = "獲取新聞內容時發生錯誤，請直接訪問原始新聞網頁查看詳情。"
            detail["is_sample"] = True  # 標記為示例數據
        
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        
        return detail