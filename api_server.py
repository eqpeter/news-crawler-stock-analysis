from flask import Flask, request, jsonify
import os
import time
from datetime import datetime

from crawlers.yahoo_crawler import YahooFinanceCrawler
from crawlers.moneydj_crawler import MoneyDJCrawler
from crawlers.cnyes_crawler import CnyesCrawler
from utils.data_manager import DataManager

app = Flask(__name__)

# 初始化爬蟲和數據管理器
yahoo_crawler = YahooFinanceCrawler()
moneydj_crawler = MoneyDJCrawler()
cnyes_crawler = CnyesCrawler()
data_manager = DataManager()

@app.route('/')
def index():
    """API首頁"""
    return jsonify({
        "name": "財經新聞爬蟲API",
        "version": "2.0",
        "endpoints": {
            "/api/v2/news": "獲取新聞數據",
            "/api/v2/news_detail": "獲取新聞詳情"
        },
        "documentation": "請參閱README.md了解更多信息"
    })

@app.route('/api/v2/news')
def get_news():
    """
    獲取新聞API
    
    參數:
        keyword: 關鍵字或股票代號
        source: 新聞來源 (yahoo, cnyes, moneydj, all)
        limit: 每個來源最多返回的新聞條數
        hours: 搜索多少小時內的新聞
    """
    # 獲取查詢參數
    keyword = request.args.get('keyword', '')
    source = request.args.get('source', 'all').lower()
    limit = int(request.args.get('limit', 10))
    hours = int(request.args.get('hours', 24))
    
    if not keyword:
        return jsonify({
            "status": "error",
            "message": "缺少關鍵字參數",
            "data": [],
            "count": 0
        }), 400
    
    all_news = []
    start_time = time.time()
    
    try:
        # 根據來源獲取新聞
        if source in ['all', 'yahoo']:
            yahoo_news = yahoo_crawler.crawl(keyword, limit=limit, hours=hours)
            for news in yahoo_news:
                # 確保每條新聞都有is_sample字段，如果原本沒有則設為False
                if 'is_sample' not in news:
                    news['is_sample'] = False
            all_news.extend(yahoo_news)
        
        if source in ['all', 'cnyes']:
            cnyes_news = cnyes_crawler.crawl(keyword, limit=limit, hours=hours)
            for news in cnyes_news:
                # 確保每條新聞都有is_sample字段，如果原本沒有則設為False
                if 'is_sample' not in news:
                    news['is_sample'] = False
            all_news.extend(cnyes_news)
        
        if source in ['all', 'moneydj']:
            moneydj_news = moneydj_crawler.crawl(keyword, limit=limit, hours=hours)
            # MoneyDJ爬蟲已經實現了is_sample標記
            all_news.extend(moneydj_news)
        
        # 保存數據
        data_manager.save_news(all_news, keyword)
        
        elapsed_time = time.time() - start_time
        
        return jsonify({
            "status": "success",
            "message": f"成功獲取{len(all_news)}條新聞",
            "data": all_news,
            "count": len(all_news),
            "elapsed_time": f"{elapsed_time:.2f}秒",
            "keyword": keyword,
            "source": source,
            "limit": limit,
            "hours": hours
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"獲取新聞時發生錯誤: {str(e)}",
            "data": [],
            "count": 0
        }), 500

@app.route('/api/v2/news_detail')
def get_news_detail():
    """
    獲取新聞詳情API
    
    參數:
        url: 新聞URL
        source: 新聞來源 (yahoo, cnyes, moneydj)
    """
    url = request.args.get('url', '')
    source = request.args.get('source', '').lower()
    
    if not url or not source:
        return jsonify({
            "status": "error",
            "message": "缺少必要參數",
            "data": {}
        }), 400
    
    try:
        detail = {}
        
        if source == 'yahoo':
            detail = yahoo_crawler.get_news_detail(url)
        elif source == 'cnyes':
            detail = cnyes_crawler.get_news_detail(url)
        elif source == 'moneydj':
            detail = moneydj_crawler.get_news_detail(url)
        else:
            return jsonify({
                "status": "error",
                "message": f"不支持的新聞來源: {source}",
                "data": {}
            }), 400
        
        # 確保detail含有is_sample字段
        if 'is_sample' not in detail:
            detail['is_sample'] = False
            
        return jsonify({
            "status": "success",
            "message": "成功獲取新聞詳情",
            "data": detail
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"獲取新聞詳情時發生錯誤: {str(e)}",
            "data": {}
        }), 500

if __name__ == '__main__':
    # 在生產環境中不要用Flask自帶的伺服器
    app.run(debug=True, host='0.0.0.0', port=5000) 