from crawlers.yahoo_crawler import YahooFinanceCrawler

def main():
    """測試Yahoo爬蟲的功能"""
    print("===== 測試Yahoo爬蟲 =====")
    
    # 創建爬蟲實例
    crawler = YahooFinanceCrawler(headless=False)
    
    # 測試關鍵字搜索
    keyword = "聯發科"
    print(f"\n使用關鍵字'{keyword}'進行搜索...")
    news = crawler.crawl(keyword, limit=5, hours=24)
    
    print(f"找到 {len(news)} 篇新聞:")
    for i, article in enumerate(news, 1):
        print(f"{i}. {article['title']}")
        print(f"   連結: {article['link']}")
        if article['published_time']:
            print(f"   發布時間: {article['published_time']}")
        if article['source']:
            print(f"   來源: {article['source']}")
        print()
    
    # 測試股票代碼搜索
    stock_code = "2454.TW"
    print(f"\n使用股票代碼'{stock_code}'進行搜索...")
    stock_news = crawler.crawl(stock_code, limit=5, hours=24)
    
    print(f"找到 {len(stock_news)} 篇股票新聞:")
    for i, article in enumerate(stock_news, 1):
        print(f"{i}. {article['title']}")
        print(f"   連結: {article['link']}")
        if article['published_time']:
            print(f"   發布時間: {article['published_time']}")
        if article['source']:
            print(f"   來源: {article['source']}")
        print()

if __name__ == "__main__":
    main() 