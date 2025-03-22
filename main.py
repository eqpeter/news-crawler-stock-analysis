import os
import sys
import time
import webbrowser
import subprocess
from datetime import datetime

from crawlers.yahoo_crawler import YahooFinanceCrawler
from crawlers.moneydj_crawler import MoneyDJCrawler
from crawlers.cnyes_crawler import CnyesCrawler
from analysis.sentiment_analyzer import SentimentAnalyzer
from analysis.trend_predictor import TrendPredictor
from utils.data_manager import DataManager

def main():
    """
    新聞爬蟲與股票趨勢分析主程式
    """
    print("===== 新聞爬蟲與股票趨勢分析 =====")
    
    # 獲取用戶輸入
    keyword = input("請輸入關鍵字或股票代號: ")
    if not keyword:
        print("錯誤：未輸入關鍵字或股票代號")
        return
    
    # 創建數據管理器
    data_manager = DataManager()
    
    # 初始化爬蟲
    yahoo_crawler = YahooFinanceCrawler()
    moneydj_crawler = MoneyDJCrawler()
    cnyes_crawler = CnyesCrawler()
    
    all_news = []
    
    # 開始爬取數據
    print(f"\n開始爬取與 '{keyword}' 相關的新聞...")
    
    try:
        # 從Yahoo財經抓取新聞
        print("\n爬取Yahoo財經新聞...")
        yahoo_news = yahoo_crawler.crawl(keyword, limit=10, hours=24)
        all_news.extend(yahoo_news)
        print(f"從Yahoo財經獲取了 {len(yahoo_news)} 條新聞")
        
        # 從鉅亨網抓取新聞
        print("\n爬取鉅亨網新聞...")
        cnyes_news = cnyes_crawler.crawl(keyword, limit=10, hours=24)
        all_news.extend(cnyes_news)
        print(f"從鉅亨網獲取了 {len(cnyes_news)} 條新聞")
        
        # 從MoneyDJ抓取新聞
        print("\n爬取MoneyDJ新聞...")
        moneydj_news = moneydj_crawler.crawl(keyword, limit=10, hours=24)
        all_news.extend(moneydj_news)
        print(f"從MoneyDJ獲取了 {len(moneydj_news)} 條新聞")
        
    except Exception as e:
        print(f"爬取過程中發生錯誤: {str(e)}")
        return
    
    # 保存新聞數據
    data_manager.save_news(all_news, keyword)
    
    # 如果沒有獲取到新聞，則退出
    if not all_news:
        print("未找到相關新聞，請嘗試其他關鍵字")
        return
    
    print(f"\n總共獲取了 {len(all_news)} 條相關新聞")
    
    # 進行情感分析
    print("\n開始進行情感分析...")
    sentiment_analyzer = SentimentAnalyzer()
    sentiment_results = sentiment_analyzer.analyze(all_news)
    
    # 進行趨勢預測
    print("\n開始進行趨勢預測...")
    trend_predictor = TrendPredictor()
    trend_prediction = trend_predictor.predict(all_news, sentiment_results)
    
    # 輸出結果
    print("\n===== 分析結果 =====")
    print(f"情感分析結果: {sentiment_results['overall_sentiment']}")
    print(f"信心指數: {sentiment_results['confidence']:.2f}")
    print(f"關鍵詞: {', '.join(sentiment_results['keywords'][:5])}")
    print(f"趨勢預測: {trend_prediction['trend']}")
    print(f"預測理由: {trend_prediction['reason']}")
    
    # 詢問是否查看分析報告
    view_report = input("\n是否查看分析報告? (y/n): ")
    if view_report.lower() == 'y':
        # 生成分析報告並自動打開
        report_file = data_manager.save_report(keyword, all_news, sentiment_results, trend_prediction)
        print(f"報告已生成: {report_file}")
        
        # 使用專門的方法打開報告
        print("\n正在嘗試打開報告...")
        data_manager.open_report(report_file)
    
    print("\n程式結束")

if __name__ == "__main__":
    main() 