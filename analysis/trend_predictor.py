import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re

class TrendPredictor:
    """趨勢預測器"""
    
    def __init__(self):
        """初始化趨勢預測器"""
        # 積極情感詞和消極情感詞的權重
        self.positive_weight = 1.5
        self.negative_weight = 1.0
        
        # 時間權重參數（越近的新聞權重越高）
        self.time_decay_factor = 0.9
    
    def _calculate_time_weight(self, news_date, now=None):
        """計算時間權重，越近的新聞權重越高"""
        if now is None:
            now = datetime.now()
        
        # 將字符串日期轉換為datetime對象
        if isinstance(news_date, str):
            try:
                news_date = datetime.strptime(news_date, "%Y-%m-%d %H:%M:%S")
            except:
                news_date = now
        
        # 計算距離現在的小時數
        hours_diff = max(0, (now - news_date).total_seconds() / 3600)
        
        # 應用時間衰減因子
        weight = self.time_decay_factor ** hours_diff
        
        return weight
    
    def _apply_weights(self, news_sentiments):
        """應用時間權重和情感權重"""
        now = datetime.now()
        weighted_sentiments = []
        
        for item in news_sentiments:
            # 獲取情感得分
            sentiment = item["sentiment"]
            compound = sentiment["compound"]
            
            # 計算時間權重
            time_weight = self._calculate_time_weight(item["date"], now)
            
            # 應用情感權重
            if compound > 0:
                weighted_sentiment = compound * self.positive_weight * time_weight
            else:
                weighted_sentiment = compound * self.negative_weight * time_weight
            
            weighted_sentiments.append(weighted_sentiment)
        
        return weighted_sentiments
    
    def _analyze_momentum(self, news_sentiments):
        """分析情感動量（趨勢）"""
        # 按時間排序
        sorted_sentiments = sorted(news_sentiments, key=lambda x: x["date"])
        
        # 如果新聞數量太少，無法分析動量
        if len(sorted_sentiments) < 3:
            return 0
        
        # 將新聞分為前半部分和後半部分
        mid_point = len(sorted_sentiments) // 2
        early_sentiments = sorted_sentiments[:mid_point]
        recent_sentiments = sorted_sentiments[mid_point:]
        
        # 計算前半部分和後半部分的平均情感得分
        early_avg = sum(item["sentiment"]["compound"] for item in early_sentiments) / len(early_sentiments)
        recent_avg = sum(item["sentiment"]["compound"] for item in recent_sentiments) / len(recent_sentiments)
        
        # 計算動量（情感變化）
        momentum = recent_avg - early_avg
        
        return momentum
    
    def predict(self, news_list, sentiment_results=None):
        """
        基於新聞和情感分析結果預測趨勢
        
        參數:
            news_list: 新聞列表
            sentiment_results: 情感分析結果，如果為None則內部計算
            
        返回:
            dict: 趨勢預測結果
        """
        # 如果沒有提供情感分析結果
        if sentiment_results is None:
            from .sentiment_analyzer import SentimentAnalyzer
            sentiment_analyzer = SentimentAnalyzer()
            sentiment_results = sentiment_analyzer.analyze(news_list)
        
        # 獲取情感分析結果
        news_sentiments = sentiment_results.get("news_sentiments", [])
        overall_sentiment = sentiment_results.get("overall_sentiment", "中性")
        keywords = sentiment_results.get("keywords", [])
        
        # 如果沒有足夠的新聞，無法預測
        if len(news_sentiments) < 2:
            return {
                "trend": "不確定",
                "confidence": 0,
                "reason": "新聞數量不足，無法預測趨勢"
            }
        
        # 應用權重
        weighted_sentiments = self._apply_weights(news_sentiments)
        
        # 計算加權平均情感得分
        weighted_avg = sum(weighted_sentiments) / len(weighted_sentiments)
        
        # 分析情感動量（趨勢）
        momentum = self._analyze_momentum(news_sentiments)
        
        # 結合情感得分和動量預測趨勢
        trend_score = weighted_avg + momentum * 0.5
        
        # 根據趨勢得分確定趨勢
        if trend_score > 0.1:
            trend = "看漲"
            reason = f"基於{len(news_list)}條新聞分析，整體情感為{overall_sentiment}，且情感持續向好"
        elif trend_score < -0.1:
            trend = "看跌"
            reason = f"基於{len(news_list)}條新聞分析，整體情感為{overall_sentiment}，且情感持續惡化"
        else:
            trend = "震盪"
            reason = f"基於{len(news_list)}條新聞分析，整體情感為{overall_sentiment}，但趨勢不明顯"
        
        # 添加關鍵詞信息
        if keywords:
            reason += f"，關鍵詞包括: {', '.join(keywords[:3])}"
        
        # 計算信心指數（0-1之間）
        confidence = min(1.0, abs(trend_score) * 2)
        
        return {
            "trend": trend,
            "confidence": confidence,
            "trend_score": trend_score,
            "momentum": momentum,
            "reason": reason,
            "keywords": keywords[:5] if keywords else []
        } 