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
import json
import os
import requests

class CnyesCrawler:
    """鉅亨網新聞爬蟲"""
    
    def __init__(self):
        """初始化爬蟲"""
        self.base_url = "https://news.cnyes.com"
        # 鉅亨網的新搜索路徑
        self.search_url = "https://www.cnyes.com/search/news"
        self.news_url = "https://news.cnyes.com/news/id/"
    
    def _setup_driver(self):
        """設置Chrome瀏覽器驅動"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 無界面模式
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        # 使用較新的 User-Agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    
    def _extract_date(self, date_str):
        """從字符串中提取日期時間"""
        now = datetime.now()
        
        # 檢查是否為時間戳記 (如果是數字型態)
        if isinstance(date_str, (int, float)):
            try:
                return datetime.fromtimestamp(date_str)
            except:
                pass
                
        if isinstance(date_str, str):
            try:
                # API返回的日期格式為 "YYYY-MM-DD HH:MM:SS"
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
        
        # 如果都不是，返回當前時間
        return now
    
    def _is_within_hours(self, news_date, hours):
        """判斷新聞是否在指定小時數內"""
        now = datetime.now()
        time_diff = now - news_date
        return time_diff.total_seconds() <= hours * 3600
    
    def crawl(self, keyword, limit=10, hours=24):
        """
        爬取鉅亨網關於指定關鍵字的新聞
        
        參數:
            keyword (str): 關鍵字或股票代號
            limit (int): 最多返回的新聞條數
            hours (int): 只獲取多少小時內的新聞
            
        返回:
            list: 新聞列表，每條新聞為一個字典，包含標題、鏈接、日期、來源、概要等信息
        """
        driver = self._setup_driver()
        news_list = []
        
        try:
            print(f"開始爬取鉅亨網關於'{keyword}'的新聞...")
            
            # 使用新的網頁搜索頁面
            search_url = f"{self.search_url}?keyword={keyword}"
            print(f"訪問搜索頁面: {search_url}")
            
            # 訪問搜索頁面
            driver.get(search_url)
            
            # 等待頁面加載
            time.sleep(5)
            
            # 截圖頁面以便調試
            os.makedirs("debug", exist_ok=True)
            driver.save_screenshot(f"debug/cnyes_search_page_{keyword}.png")
            
            # 獲取頁面原始碼
            page_source = driver.page_source
            
            # 保存頁面原始碼
            with open(f"debug/cnyes_search_html_{keyword}.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            
            # 使用 BeautifulSoup 解析頁面
            soup = BeautifulSoup(page_source, "html.parser")
            
            # 使用 JavaScript 嘗試尋找搜索結果
            print("嘗試使用 JavaScript 搜索新聞...")
            
            js_result = driver.execute_script("""
            let results = [];
            
            // 嘗試找到新聞區塊
            let newsContainer = document.querySelector('div[data-test="searchResult-news-container"]');
            if (newsContainer) {
                // 找到所有新聞鏈接
                let newsLinks = newsContainer.querySelectorAll('a');
                newsLinks.forEach(a => {
                    // 獲取標題
                    let titleEl = a.querySelector('h3') || a;
                    let title = titleEl.textContent.trim();
                    
                    // 獲取鏈接
                    let link = a.href;
                    
                    // 獲取日期
                    let timeEl = a.querySelector('span[data-test="searchResultNews-item-date"]') || 
                                a.querySelector('time') || 
                                a.querySelector('span.time');
                    let timeText = timeEl ? timeEl.textContent.trim() : '';
                    
                    // 獲取摘要
                    let summaryEl = a.querySelector('p');
                    let summary = summaryEl ? summaryEl.textContent.trim() : '';
                    
                    if (title && link) {
                        results.push({
                            title: title,
                            link: link,
                            timeText: timeText,
                            summary: summary
                        });
                    }
                });
            }
            
            // 如果沒有找到特定容器，嘗試搜索所有可能的新聞鏈接
            if (results.length === 0) {
                document.querySelectorAll('a').forEach(a => {
                    if (a.href && (a.href.includes('/news/id/') || a.href.includes('/news/article/'))) {
                        let titleEl = a.querySelector('h3') || a;
                        let title = titleEl.textContent.trim();
                        let link = a.href;
                        
                        // 找日期元素
                        let timeEl = a.querySelector('time') || 
                                   a.querySelector('.time') || 
                                   a.querySelector('span[data-test="searchResultNews-item-date"]');
                        let timeText = timeEl ? timeEl.textContent.trim() : '';
                        
                        // 找摘要
                        let summaryEl = a.querySelector('p');
                        let summary = summaryEl ? summaryEl.textContent.trim() : '';
                        
                        if (title && link) {
                            results.push({
                                title: title,
                                link: link,
                                timeText: timeText,
                                summary: summary
                            });
                        }
                    }
                });
            }
            
            return results;
            """)
            
            print(f"JavaScript 找到 {len(js_result)} 個搜索結果")
            
            # 保存 JavaScript 結果以便調試
            with open(f"debug/cnyes_js_results_{keyword}.json", "w", encoding="utf-8") as f:
                json.dump(js_result, f, ensure_ascii=False, indent=2)
            
            # 處理 JavaScript 獲取的結果
            for item in js_result:
                title = item.get("title", "")
                link = item.get("link", "")
                time_text = item.get("timeText", "")
                summary = item.get("summary", "")
                
                # 提取日期
                news_date = self._extract_date(time_text) if time_text else datetime.now()
                
                # 檢查是否在指定小時數內
                if not self._is_within_hours(news_date, hours):
                    continue
                
                # 避免重複
                if any(n.get("title") == title for n in news_list):
                    continue
                
                # 如果沒有摘要，嘗試訪問新聞詳情頁獲取摘要
                if not summary and link:
                    try:
                        print(f"訪問詳情頁獲取摘要: {link}")
                        # 訪問新聞詳情頁
                        driver.get(link)
                        time.sleep(2)
                        
                        # 使用 JavaScript 獲取摘要
                        summary = driver.execute_script("""
                        let summaryEl = document.querySelector('.summary') || 
                                     document.querySelector('p.summary') || 
                                     document.querySelector('div[itemprop="articleBody"] > p:first-child');
                        return summaryEl ? summaryEl.textContent.trim() : '';
                        """)
                    except Exception as e:
                        print(f"獲取詳情頁摘要出錯: {e}")
                
                # 添加到新聞列表
                news = {
                    "title": title,
                    "link": link,
                    "date": news_date,
                    "published_time": news_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "鉅亨網",
                    "summary": summary,
                    "platform": "鉅亨網"
                }
                
                news_list.append(news)
                print(f"找到新聞: {title}")
                
                if len(news_list) >= limit:
                    break
            
            # 如果 JavaScript 方法沒有獲得足夠的結果，嘗試使用 BeautifulSoup 解析
            if len(news_list) < limit:
                print(f"JavaScript 只找到 {len(news_list)} 條新聞，嘗試使用 BeautifulSoup...")
                
                # 尋找新聞列表頁面的所有 <a> 標籤
                news_links = soup.find_all("a", href=True)
                
                # 尋找包含新聞鏈接的 <a> 標籤
                for link in news_links:
                    href = link.get("href", "")
                    
                    # 檢查是否是新聞鏈接
                    if "/news/id/" in href or "/news/article/" in href:
                        # 構建完整鏈接
                        full_link = href if href.startswith("http") else f"https://news.cnyes.com{href}"
                        
                        # 獲取標題
                        title_element = link.find("h3") or link
                        title = title_element.get_text().strip()
                        
                        # 跳過沒有標題的鏈接
                        if not title:
                            continue
                        
                        # 獲取時間信息
                        time_element = link.find("span", attrs={"data-test": "searchResultNews-item-date"}) or \
                                     link.find("time") or \
                                     link.find("span", class_=lambda c: c and "time" in c)
                        time_text = time_element.get_text().strip() if time_element else ""
                        
                        # 獲取摘要
                        summary_element = link.find("p")
                        summary = summary_element.get_text().strip() if summary_element else ""
                        
                        # 提取日期
                        news_date = self._extract_date(time_text) if time_text else datetime.now()
                        
                        # 檢查是否在指定小時數內
                        if not self._is_within_hours(news_date, hours):
                            continue
                        
                        # 避免重複
                        if any(n.get("title") == title for n in news_list):
                            continue
                        
                        # 添加到新聞列表
                        news = {
                            "title": title,
                            "link": full_link,
                            "date": news_date,
                            "published_time": news_date.strftime("%Y-%m-%d %H:%M:%S"),
                            "source": "鉅亨網",
                            "summary": summary,
                            "platform": "鉅亨網"
                        }
                        
                        news_list.append(news)
                        print(f"從網頁找到新聞: {title}")
                        
                        if len(news_list) >= limit:
                            break
            
            print(f"鉅亨網爬蟲完成，共找到 {len(news_list)} 條新聞")
        
        except Exception as e:
            print(f"爬取鉅亨網新聞時發生錯誤: {e}")
        
        finally:
            driver.quit()
        
        return news_list 