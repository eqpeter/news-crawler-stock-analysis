from crawlers.cnyes_crawler import CnyesCrawler
import time
import os

def test_cnyes_crawler():
    """測試鉅亨網爬蟲"""
    print("===== 測試鉅亨網爬蟲 =====")
    
    # 確保debug目錄存在
    os.makedirs("debug", exist_ok=True)
    
    # 初始化爬蟲
    crawler = CnyesCrawler()
    
    # 測試關鍵字
    keyword = "台積電"
    limit = 5
    
    print(f"\n使用關鍵字'{keyword}'進行搜索...")
    start_time = time.time()
    
    # 執行爬蟲
    news_list = crawler.crawl(keyword, limit=limit)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # 顯示結果
    print(f"\n總計找到 {len(news_list)} 條新聞")
    print(f"爬蟲耗時: {elapsed_time:.2f} 秒")
    
    # 顯示新聞詳情
    for i, news in enumerate(news_list, 1):
        print(f"\n{i}. {news['title']}")
        print(f"   鏈接: {news['link']}")
        print(f"   日期: {news.get('published_time') or news.get('date')}")
        if news.get('summary'):
            print(f"   摘要: {news['summary'][:100]}...")

if __name__ == "__main__":
    test_cnyes_crawler() 