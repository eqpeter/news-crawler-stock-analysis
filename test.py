import os
import json
from datetime import datetime

from crawlers.yahoo_crawler import YahooFinanceCrawler

def test_yahoo_crawler():
    """測試Yahoo財經爬蟲功能"""
    print("=" * 50)
    print("測試Yahoo財經爬蟲")
    print("=" * 50)
    
    # 創建結果目錄
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)
    
    # 設置輸出文件路徑
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = os.path.join(output_dir, f"yahoo_news_tsmc_{timestamp}.json")
    output_csv = os.path.join(output_dir, f"yahoo_news_tsmc_{timestamp}.csv")
    
    # 創建爬蟲實例並獲取台積電新聞
    crawler = YahooFinanceCrawler(headless=False)  # 設置為False以便查看瀏覽器操作
    
    # 使用台積電的股票代碼 (2330.TW)
    results = crawler.get_stock_news(
        stock_code="2330.TW",
        output_json=output_json,
        output_csv=output_csv,
        max_articles=10
    )
    
    # 顯示結果
    print(f"\n找到 {len(results)} 篇台積電相關新聞:")
    for i, article in enumerate(results, 1):
        print(f"\n{i}. {article['title']}")
        print(f"   鏈接: {article['link']}")
        if article['published_time']:
            print(f"   發布時間: {article['published_time']}")
        if article['source']:
            print(f"   來源: {article['source']}")
    
    print(f"\n結果已保存到:")
    print(f"- JSON: {output_json}")
    print(f"- CSV: {output_csv}")

if __name__ == "__main__":
    test_yahoo_crawler() 