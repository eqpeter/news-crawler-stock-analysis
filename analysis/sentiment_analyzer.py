import jieba
import jieba.analyse
import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd

class SentimentAnalyzer:
    """新聞情感分析器"""
    
    def __init__(self):
        """初始化情感分析器"""
        # 確保下載必要的nltk資源
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon')
        
        # 初始化情感分析器
        self.sia = SentimentIntensityAnalyzer()
        
        # 初始化中文情感詞典（簡化版）
        self.cn_positive_words = set([
            '上漲', '增長', '提高', '發展', '利好', '看好', '突破', '強勁',
            '優質', '穩健', '回升', '獲利', '盈利', '成功', '領先', '創新',
            '機遇', '繁榮', '積極', '樂觀', '良好', '優勢', '擴張', '改善'
        ])
        
        self.cn_negative_words = set([
            '下跌', '降低', '減少', '虧損', '風險', '危機', '擔憂', '問題',
            '下滑', '疲軟', '衰退', '失敗', '困難', '挑戰', '壓力', '負面',
            '違規', '處罰', '調查', '訴訟', '悲觀', '萎縮', '下降', '惡化'
        ])
    
    def _clean_text(self, text):
        """清理文本，去除HTML標籤、URL等"""
        # 去除HTML標籤
        text = re.sub(r'<.*?>', '', text)
        # 去除URL
        text = re.sub(r'http\S+', '', text)
        # 去除多餘空白
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _analyze_chinese_sentiment(self, text):
        """分析中文文本情感"""
        # 分詞
        words = jieba.lcut(text)
        
        # 計算積極和消極詞出現的次數
        positive_count = sum(1 for word in words if word in self.cn_positive_words)
        negative_count = sum(1 for word in words if word in self.cn_negative_words)
        
        # 計算情感得分
        total_words = len(words)
        if total_words == 0:
            return {"pos": 0, "neg": 0, "neu": 1, "compound": 0}
        
        positive_score = positive_count / total_words
        negative_score = negative_count / total_words
        neutral_score = 1 - positive_score - negative_score
        
        # 計算複合得分（-1到1之間）
        compound = (positive_score - negative_score) / (positive_score + negative_score + 0.001)
        
        return {
            "pos": positive_score,
            "neg": negative_score,
            "neu": neutral_score,
            "compound": compound
        }
    
    def _analyze_english_sentiment(self, text):
        """使用VADER分析英文文本情感"""
        return self.sia.polarity_scores(text)
    
    def _extract_keywords(self, news_list, top_n=10):
        """提取新聞中的關鍵詞"""
        # 合併所有新聞文本
        all_text = " ".join([news["title"] + " " + news.get("summary", "") for news in news_list])
        
        # 使用jieba提取關鍵詞
        keywords = jieba.analyse.extract_tags(all_text, topK=top_n, withWeight=True)
        
        return [{"keyword": kw, "weight": weight} for kw, weight in keywords]
    
    def analyze(self, news_list):
        """
        分析新聞列表的情感
        
        參數:
            news_list: 新聞列表，每個新聞是一個字典
            
        返回:
            dict: 情感分析結果，包含整體情感、信心指數、每條新聞的情感以及關鍵詞
        """
        if not news_list:
            return {
                "overall_sentiment": "中性",
                "confidence": 0,
                "news_sentiments": [],
                "keywords": []
            }
        
        # 對每條新聞進行情感分析
        news_sentiments = []
        overall_compound = 0
        
        for news in news_list:
            # 合併標題和概要
            text = news["title"] + " " + news.get("summary", "")
            text = self._clean_text(text)
            
            # 根據文本內容判斷使用中文還是英文情感分析
            if re.search(r'[\u4e00-\u9fff]', text):  # 包含中文字符
                sentiment = self._analyze_chinese_sentiment(text)
            else:
                sentiment = self._analyze_english_sentiment(text)
            
            # 確定情感標籤
            compound = sentiment["compound"]
            if compound >= 0.05:
                label = "積極"
            elif compound <= -0.05:
                label = "消極"
            else:
                label = "中性"
            
            news_sentiment = {
                "title": news["title"],
                "sentiment": sentiment,
                "label": label,
                "date": news.get("published_time") or news.get("date", "未知日期")
            }
            
            news_sentiments.append(news_sentiment)
            overall_compound += sentiment["compound"]
        
        # 計算整體情感得分
        avg_compound = overall_compound / len(news_list)
        
        # 確定整體情感
        if avg_compound >= 0.05:
            overall_sentiment = "積極"
        elif avg_compound <= -0.05:
            overall_sentiment = "消極"
        else:
            overall_sentiment = "中性"
        
        # 計算信心指數（0-1之間）
        confidence = abs(avg_compound)
        
        # 提取關鍵詞
        keywords = self._extract_keywords(news_list)
        
        # 生成結果
        result = {
            "overall_sentiment": overall_sentiment,
            "confidence": confidence,
            "avg_compound": avg_compound,
            "news_sentiments": news_sentiments,
            "keywords": [kw["keyword"] for kw in keywords]
        }
        
        return result 