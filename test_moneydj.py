import time
import sys
from datetime import datetime
from crawlers.moneydj_crawler import MoneyDJCrawler

def main():
    """測試MoneyDJ爬蟲"""
    print("===== 測試MoneyDJ爬蟲 =====\n")
    
    # 設定搜索關鍵字，嘗試多個關鍵字
    keywords = ["聯發科", "鴻海", "台積電", "2330"]
    
    # 記錄總開始時間
    total_start_time = time.time()
    total_news = 0
    total_sample_news = 0
    
    for keyword in keywords:
        print(f"\n使用關鍵字'{keyword}'進行搜索...\n")
        
        # 記錄開始時間
        start_time = time.time()
        
        # 初始化爬蟲
        crawler = MoneyDJCrawler()
        
        # 執行爬蟲，使用更長的時間範圍
        news_list = crawler.crawl(keyword, limit=3, hours=24*7)  # 搜索一周內的新聞
        
        # 計算爬蟲耗時
        elapsed_time = time.time() - start_time
        
        # 統計示例新聞數量
        sample_count = sum(1 for news in news_list if news.get('is_sample', False))
        
        # 輸出結果
        print(f"\n關鍵字'{keyword}'找到 {len(news_list)} 條新聞，其中 {sample_count} 條為示例數據")
        print(f"爬蟲耗時: {elapsed_time:.2f} 秒\n")
        
        # 顯示找到的新聞
        for i, news in enumerate(news_list, 1):
            print(f"{i}. {news['title']}")
            print(f"   鏈接: {news['link']}")
            print(f"   日期: {news['published_time']}")
            if news.get('summary'):
                print(f"   摘要: {news['summary'][:100]}...")
            # 顯示是否為示例數據
            sample_tag = "[示例數據]" if news.get('is_sample', False) else "[真實數據]"
            print(f"   {sample_tag}")
            print()
        
        total_news += len(news_list)
        total_sample_news += sample_count
    
    # 計算總耗時
    total_elapsed_time = time.time() - total_start_time
    print(f"\n總計找到 {total_news} 條新聞，其中 {total_sample_news} 條為示例數據")
    print(f"總耗時: {total_elapsed_time:.2f} 秒")

if __name__ == "__main__":
    main() 