import time
import json
import csv
import os
import codecs
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re

class YahooFinanceCrawler:
    def __init__(self, headless=True):
        self.headless = headless
        
    def setup_driver(self):
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36')
        # 設置字符編碼
        options.add_argument('--lang=zh-TW')
        options.add_argument('--accept-lang=zh-TW')
        # 強制使用UTF-8編碼
        options.add_argument('--charset=UTF-8')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    
    def _extract_date(self, date_str):
        """從字符串中提取日期時間"""
        now = datetime.now()
        
        if not date_str:
            return now
            
        # 檢查是否為時間戳記 (如果是數字型態)
        if isinstance(date_str, (int, float)):
            try:
                return datetime.fromtimestamp(date_str)
            except:
                pass
                
        if isinstance(date_str, str):
            try:
                # 標準日期格式 "YYYY-MM-DD HH:MM:SS"
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except:
                try:
                    # 或者格式為 "YYYY/MM/DD HH:MM:SS"
                    return datetime.strptime(date_str, "%Y/%m/%d %H:%M:%S")
                except:
                    try:
                        # 或者格式為 "YYYY/MM/DD HH:MM"
                        return datetime.strptime(date_str, "%Y/%m/%d %H:%M")
                    except:
                        try:
                            # 或者格式為 "MM/DD HH:MM" (當前年份)
                            date_with_year = f"{now.year}/{date_str}"
                            return datetime.strptime(date_with_year, "%Y/%m/%d %H:%M")
                        except:
                            # 嘗試解析相對時間，例如"2小時前"、"5分鐘前"
                            if "小時前" in date_str:
                                hours = int(re.search(r"(\d+)小時前", date_str).group(1))
                                return now - timedelta(hours=hours)
                            elif "分鐘前" in date_str:
                                minutes = int(re.search(r"(\d+)分鐘前", date_str).group(1))
                                return now - timedelta(minutes=minutes)
                            elif "天前" in date_str:
                                days = int(re.search(r"(\d+)天前", date_str).group(1))
                                return now - timedelta(days=days)
                            elif "昨天" in date_str:
                                # 如果包含時間，例如 "昨天 HH:MM"
                                time_match = re.search(r"昨天\s*(\d{1,2}:\d{2})", date_str)
                                if time_match:
                                    time_str = time_match.group(1)
                                    hour, minute = map(int, time_str.split(':'))
                                    yesterday = now - timedelta(days=1)
                                    return datetime(yesterday.year, yesterday.month, yesterday.day, hour, minute)
                                else:
                                    return now - timedelta(days=1)
        
        # 如果無法解析，返回當前時間
        return now
    
    def search_news(self, keyword, output_json=None, output_csv=None, max_articles=10):
        results = []
        try:
            driver = self.setup_driver()
            
            # 構建搜索URL - 使用Yahoo財經台灣的特定格式
            search_url = f"https://tw.stock.yahoo.com/quote/{keyword}/news"
            print(f"正在訪問: {search_url}")
            driver.get(search_url)
            
            # 等待頁面加載
            time.sleep(3)
            
            # 滾動頁面以加載更多內容
            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # 獲取頁面源碼
            page_source = driver.page_source
            # 使用正確的編碼解析HTML
            soup = BeautifulSoup(page_source, 'html.parser', from_encoding='utf-8')
            
            # 尋找新聞項目
            print("開始分析頁面尋找新聞...")
            
            # 直接使用Selenium獲取新聞連結
            news_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/news/']")
            print(f"通過Selenium找到 {len(news_links)} 個新聞連結")
            
            # 處理新聞連結
            for link in news_links:
                try:
                    title = link.text.strip()
                    href = link.get_attribute('href')
                    
                    # 忽略空標題或過短的標題
                    if not title or len(title) < 5:
                        continue
                    
                    # 找鄰近元素中的時間和來源
                    parent = link
                    for _ in range(5):  # 增加查找層數到5層
                        parent = parent.find_element(By.XPATH, "./..")
                        if not parent:
                            break
                    
                    pub_time = None
                    source = None
                    
                    if parent:
                        # 查找時間 - 擴大查找範圍
                        try:
                            # 查找包含日期格式的元素
                            time_elem = parent.find_elements(By.XPATH, 
                                ".//span[contains(text(), '/') or contains(text(), ':') or contains(text(), '小時前') or contains(text(), '分鐘前')]")
                            if time_elem and len(time_elem) > 0:
                                pub_time = time_elem[0].text.strip()
                                # 轉換為標準格式
                                formatted_date = self._extract_date(pub_time)
                                pub_time = formatted_date.strftime("%Y-%m-%d %H:%M:%S")
                        except Exception as e:
                            print(f"提取時間時出錯: {e}")
                        
                        # 查找來源 - 擴大查找範圍
                        try:
                            # 嘗試多種可能的來源元素
                            source_elem = parent.find_elements(By.XPATH, 
                                ".//span[contains(@class, 'source') or contains(@class, 'provider') or contains(text(), '新聞') or contains(text(), '報')]")
                            if source_elem and len(source_elem) > 0:
                                source = source_elem[0].text.strip()
                                # 如果來源包含時間，嘗試分離
                                if source and ('/' in source or ':' in source):
                                    parts = re.split(r'[\s\xa0]+', source)
                                    for part in parts:
                                        if '/' in part or ':' in part:
                                            # 這部分可能是時間
                                            if not pub_time:
                                                formatted_date = self._extract_date(part)
                                                pub_time = formatted_date.strftime("%Y-%m-%d %H:%M:%S")
                                        elif len(part) > 1 and not part.isdigit():
                                            # 這部分可能是來源名稱
                                            source = part
                        except Exception as e:
                            print(f"提取來源時出錯: {e}")
                    
                    # 檢查是否從URL中提取來源
                    if (not source or source == "") and href:
                        # 從URL中提取可能的來源
                        domain_match = re.search(r'https?://([^/]+)', href)
                        if domain_match:
                            domain = domain_match.group(1)
                            if 'yahoo' in domain:
                                source = "Yahoo財經"
                            elif any(site in domain for site in ['cnyes', 'anue']):
                                source = "鉅亨網"
                            elif 'money.udn' in domain:
                                source = "經濟日報"
                            elif 'moneydj' in domain:
                                source = "MoneyDJ"
                            elif 'ctee' in domain:
                                source = "工商時報"
                            elif 'cna' in domain:
                                source = "中央社"
                            elif 'chinatimes' in domain:
                                source = "中時"
                            elif 'ltn' in domain:
                                source = "自由時報"
                            elif 'ettoday' in domain:
                                source = "ETtoday"
                    
                    # 設定默認來源
                    if not source or source == "":
                        source = "Yahoo財經"
                    
                    # 設定默認時間
                    if not pub_time or pub_time == "":
                        pub_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 檢查是否是有效的新聞連結
                    if title and href and '/news/' in href and href not in [item['link'] for item in results]:
                        article = {
                            'title': title,
                            'link': href,
                            'published_time': pub_time,
                            'source': source
                        }
                        results.append(article)
                        
                        if len(results) >= max_articles:
                            break
                except Exception as e:
                    print(f"處理新聞連結時出錯: {e}")
                    continue
            
            # 如果還沒有找到足夠的新聞，使用BeautifulSoup尋找
            if len(results) < max_articles:
                print(f"使用BeautifulSoup繼續尋找新聞，當前已找到 {len(results)} 篇")
                
                # 處理找到的新聞容器
                processed_urls = set([item['link'] for item in results])
                
                # 方法1: 查找帶有新聞URL的連結
                news_links = soup.find_all('a', href=lambda href: href and '/news/' in href)
                for link in news_links:
                    title = link.get_text().strip()
                    href = link.get('href')
                    
                    # 確保連結是完整的URL
                    if href and not href.startswith('http'):
                        if href.startswith('/'):
                            href = f"https://tw.stock.yahoo.com{href}"
                        else:
                            href = f"https://tw.stock.yahoo.com/{href}"
                    
                    # 檢查是否是有效的新聞連結
                    if title and href and len(title) > 5 and href not in processed_urls:
                        # 查找父元素中的時間和來源信息
                        parent = link.parent
                        
                        pub_time = None
                        source = None
                        
                        # 尋找時間和來源
                        for _ in range(5):  # 向上查找5層父元素
                            if not parent:
                                break
                                
                            # 尋找時間信息 - 擴大搜索範圍
                            time_elem = parent.find(['time', 'span'], string=re.compile(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}[/-]\d{1,2}|\d{1,2}:\d{2}|\d+小時前|\d+分鐘前'))
                            if time_elem:
                                pub_time = time_elem.get_text().strip()
                                # 轉換為標準格式
                                formatted_date = self._extract_date(pub_time)
                                pub_time = formatted_date.strftime("%Y-%m-%d %H:%M:%S")
                            
                            # 尋找來源信息 - 擴大搜索範圍
                            source_elem = parent.find(['span', 'div'], class_=lambda x: x and ('source' in x.lower() or 'provider' in x.lower() if x else False))
                            if not source_elem:
                                # 嘗試通過文本內容查找
                                source_elem = parent.find(['span', 'div'], string=re.compile(r'新聞$|報$|社$'))
                            if source_elem:
                                source = source_elem.get_text().strip()
                                # 如果來源包含時間，嘗試分離
                                if source and ('/' in source or ':' in source):
                                    parts = re.split(r'[\s\xa0]+', source)
                                    for part in parts:
                                        if '/' in part or ':' in part:
                                            # 這部分可能是時間
                                            if not pub_time:
                                                formatted_date = self._extract_date(part)
                                                pub_time = formatted_date.strftime("%Y-%m-%d %H:%M:%S")
                                        elif len(part) > 1 and not part.isdigit():
                                            # 這部分可能是來源名稱
                                            source = part
                            
                            if pub_time and source:
                                break
                                
                            parent = parent.parent
                        
                        # 從URL中提取可能的來源
                        if not source or source == "":
                            domain_match = re.search(r'https?://([^/]+)', href)
                            if domain_match:
                                domain = domain_match.group(1)
                                if 'yahoo' in domain:
                                    source = "Yahoo財經"
                                elif any(site in domain for site in ['cnyes', 'anue']):
                                    source = "鉅亨網"
                                elif 'money.udn' in domain:
                                    source = "經濟日報"
                                elif 'moneydj' in domain:
                                    source = "MoneyDJ"
                                elif 'ctee' in domain:
                                    source = "工商時報"
                                elif 'cna' in domain:
                                    source = "中央社"
                                elif 'chinatimes' in domain:
                                    source = "中時"
                                elif 'ltn' in domain:
                                    source = "自由時報"
                                elif 'ettoday' in domain:
                                    source = "ETtoday"
                        
                        # 設定默認來源
                        if not source or source == "":
                            source = "Yahoo財經"
                        
                        # 設定默認時間
                        if not pub_time or pub_time == "":
                            pub_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        article = {
                            'title': title,
                            'link': href,
                            'published_time': pub_time,
                            'source': source
                        }
                        results.append(article)
                        processed_urls.add(href)
                        
                        if len(results) >= max_articles:
                            break
            
            # 如果仍然沒有找到足夠的新聞，使用JavaScript直接獲取頁面上的新聞
            if len(results) < max_articles:
                print("尋找更多新聞...")
                
                # 使用JavaScript查找具有特定特徵的新聞元素，嘗試提取時間和來源
                news_elements = driver.execute_script("""
                    // 使用專門針對Yahoo財經的選擇器
                    var newsItems = [];
                    
                    // 查找包含/news/的所有連結
                    var links = document.querySelectorAll('a[href*="/news/"]');
                    for(var i=0; i<links.length; i++) {
                        var link = links[i];
                        var text = link.innerText.trim();
                        var href = link.getAttribute('href');
                        
                        // 確保有標題且不是導航連結
                        if(text && text.length > 5 && !text.includes('看更多') && !text.includes('登入') && href) {
                            // 尋找時間和來源信息
                            var sourceText = null;
                            var timeText = null;
                            var element = link;
                            
                            // 尋找最近的包含時間或來源的元素
                            for(var j=0; j<5; j++) {
                                if(!element || !element.parentElement) break;
                                element = element.parentElement;
                                
                                // 尋找時間元素
                                var timeElements = element.querySelectorAll('span:not([class]), time');
                                for(var k=0; k<timeElements.length; k++) {
                                    var el = timeElements[k];
                                    var elText = el.innerText.trim();
                                    if(elText && (
                                        elText.includes('/') || 
                                        elText.includes(':') ||
                                        elText.includes('小時前') ||
                                        elText.includes('分鐘前')
                                    )) {
                                        timeText = elText;
                                        break;
                                    }
                                }
                                
                                // 尋找來源元素
                                var sourceElements = element.querySelectorAll('span[class*="source"], span[class*="provider"], div[class*="source"]');
                                for(var k=0; k<sourceElements.length; k++) {
                                    var el = sourceElements[k];
                                    var elText = el.innerText.trim();
                                    if(elText && elText.length > 0) {
                                        sourceText = elText;
                                        break;
                                    }
                                }
                                
                                if(timeText && sourceText) break;
                            }
                            
                            newsItems.push({
                                title: text,
                                link: href,
                                source: sourceText,
                                time: timeText
                            });
                        }
                    }
                    
                    return newsItems;
                """)
                
                # 轉換JavaScript獲取的結果
                processed_urls = set([item['link'] for item in results])
                for item in news_elements:
                    if item['link'] not in processed_urls:
                        # 確保URL完整
                        if not item['link'].startswith('http'):
                            item['link'] = f"https://tw.stock.yahoo.com{item['link']}"
                            
                        # 處理時間
                        pub_time = None
                        if 'time' in item and item['time']:
                            # 轉換為標準格式
                            formatted_date = self._extract_date(item['time'])
                            pub_time = formatted_date.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            pub_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                        # 處理來源
                        source = None
                        if 'source' in item and item['source']:
                            source = item['source']
                        else:
                            # 從URL提取
                            domain_match = re.search(r'https?://([^/]+)', item['link'])
                            if domain_match:
                                domain = domain_match.group(1)
                                if 'yahoo' in domain:
                                    source = "Yahoo財經"
                                elif any(site in domain for site in ['cnyes', 'anue']):
                                    source = "鉅亨網"
                                elif 'money.udn' in domain:
                                    source = "經濟日報"
                                elif 'moneydj' in domain:
                                    source = "MoneyDJ"
                                elif 'ctee' in domain:
                                    source = "工商時報"
                                elif 'cna' in domain:
                                    source = "中央社"
                                elif 'chinatimes' in domain:
                                    source = "中時"
                                elif 'ltn' in domain:
                                    source = "自由時報"
                                elif 'ettoday' in domain:
                                    source = "ETtoday"
                            
                            if not source:
                                source = "Yahoo財經"
                        
                        article = {
                            'title': item['title'],
                            'link': item['link'],
                            'published_time': pub_time,
                            'source': source
                        }
                        results.append(article)
                        processed_urls.add(article['link'])
                        
                        if len(results) >= max_articles:
                            break
            
            # 如果仍然找不到新聞，保存調試信息
            if not results:
                print("未找到新聞，保存調試信息...")
                debug_file = 'yahoo_debug.html'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(page_source)
                print(f"頁面源碼已保存至 {debug_file}")
                
                driver.save_screenshot('yahoo_debug.png')
                print("頁面截圖已保存至 yahoo_debug.png")
        
        except Exception as e:
            print(f"爬取過程中發生錯誤: {e}")
        finally:
            if 'driver' in locals():
                driver.quit()
        
        # 保存結果到JSON - 使用UTF-8-SIG確保Windows下正確顯示中文
        if output_json and results:
            os.makedirs(os.path.dirname(output_json), exist_ok=True)
            with codecs.open(output_json, 'w', encoding='utf-8-sig') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"結果已保存至 {output_json}")
            
            # 同時保存一個備份文件，使用不同的編碼方式
            backup_json = output_json.replace('.json', '_utf8.json')
            with open(backup_json, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"UTF-8備份已保存至 {backup_json}")
        
        # 保存結果到CSV - 使用UTF-8-SIG並添加BOM標記
        if output_csv and results:
            os.makedirs(os.path.dirname(output_csv), exist_ok=True)
            # 使用內建的open而不是codecs.open來支持newline參數
            with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['title', 'link', 'published_time', 'source'])
                writer.writeheader()
                writer.writerows(results)
            print(f"結果已保存至 {output_csv}")
        
        return results
    
    def get_stock_news(self, stock_code, output_json=None, output_csv=None, max_articles=10):
        """
        獲取特定股票的新聞
        
        Args:
            stock_code (str): 股票代碼，例如 "2330.TW" 表示台積電
            output_json (str, optional): JSON輸出文件路徑
            output_csv (str, optional): CSV輸出文件路徑
            max_articles (int, optional): 最大文章數量，默認10
            
        Returns:
            list: 新聞文章列表
        """
        return self.search_news(stock_code, output_json, output_csv, max_articles)
        
    def crawl(self, keyword, limit=10, hours=24, output_json=None, output_csv=None):
        """
        爬取新聞的通用接口，與其他爬蟲保持一致
        
        Args:
            keyword (str): 關鍵字或股票代碼
            limit (int, optional): 最大文章數量，默認10
            hours (int, optional): 時間限制，僅返回最近多少小時的新聞，默認24小時
            output_json (str, optional): JSON輸出文件路徑
            output_csv (str, optional): CSV輸出文件路徑
            
        Returns:
            list: 新聞文章列表
        """
        # 檢查是否是股票代碼格式
        if keyword.isdigit() or '.' in keyword:
            # 如果是股票代碼，添加股票代碼後綴（如果沒有）
            if not '.' in keyword:
                # 台灣股票格式為 xxxx.TW
                keyword = f"{keyword}.TW"
            # 使用get_stock_news方法
            return self.get_stock_news(
                stock_code=keyword, 
                output_json=output_json, 
                output_csv=output_csv, 
                max_articles=limit
            )
        else:
            # 如果是關鍵字，使用search_news方法
            return self.search_news(
                keyword=keyword, 
                output_json=output_json, 
                output_csv=output_csv, 
                max_articles=limit
            ) 