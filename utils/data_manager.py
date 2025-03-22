import os
import json
import csv
import pandas as pd
import webbrowser
import sys
import subprocess
import time
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib

# 確保中文字體顯示正常
# 添加更多字體選項，按優先順序排列
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft JhengHei', 'DFKai-SB', 'PMingLiU', 'Arial Unicode MS', 'Heiti TC', 'LiHei Pro', 'Hiragino Sans GB', 'STHeiti']
matplotlib.rcParams['axes.unicode_minus'] = False  # 解決保存圖像是負號'-'顯示為方塊的問題

# 嘗試導入中文字體支持
try:
    import matplotlib.font_manager as fm
    # 添加用戶安裝的字體
    font_dirs = ['C:/Windows/Fonts', './fonts']
    font_files = fm.findSystemFonts(fontpaths=font_dirs)
    for font_file in font_files:
        try:
            fm.fontManager.addfont(font_file)
        except:
            pass
except:
    pass

class DataManager:
    """數據管理器，負責數據的存儲和加載"""
    
    def __init__(self, data_dir="data"):
        """
        初始化數據管理器
        
        參數:
            data_dir: 數據存儲目錄
        """
        self.data_dir = data_dir
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """確保目錄存在"""
        # 新聞數據目錄
        news_dir = os.path.join(self.data_dir, "news")
        if not os.path.exists(news_dir):
            os.makedirs(news_dir)
        
        # 報告目錄
        report_dir = os.path.join(self.data_dir, "reports")
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        
        # 圖表目錄
        chart_dir = os.path.join(self.data_dir, "charts")
        if not os.path.exists(chart_dir):
            os.makedirs(chart_dir)
    
    def save_news(self, news_list, keyword):
        """
        保存新聞列表為JSON和CSV格式
        
        參數:
            news_list: 新聞列表
            keyword: 關鍵字
            
        返回:
            tuple: (json_path, csv_path)
        """
        if not news_list:
            return None, None
        
        # 文件名包含日期和關鍵字
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"{timestamp}_{keyword}"
        
        # 保存為JSON
        json_path = os.path.join(self.data_dir, "news", f"{filename_base}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            # 轉換datetime對象為字符串
            serializable_news = []
            for news in news_list:
                news_copy = news.copy()
                if isinstance(news_copy.get("date"), datetime):
                    news_copy["date"] = news_copy["date"].strftime("%Y-%m-%d %H:%M:%S")
                serializable_news.append(news_copy)
            
            json.dump(serializable_news, f, ensure_ascii=False, indent=2)
        
        # 保存為CSV
        csv_path = os.path.join(self.data_dir, "news", f"{filename_base}.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            if not news_list:
                return json_path, csv_path
            
            # 獲取所有字段
            fields = set()
            for news in news_list:
                fields.update(news.keys())
            
            writer = csv.DictWriter(f, fieldnames=sorted(fields))
            writer.writeheader()
            
            # 寫入數據（確保datetime被轉換為字符串）
            for news in news_list:
                news_copy = news.copy()
                if isinstance(news_copy.get("date"), datetime):
                    news_copy["date"] = news_copy["date"].strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow(news_copy)
        
        return json_path, csv_path
    
    def save_report(self, keyword, news_list, sentiment_results, trend_prediction):
        """
        保存分析報告
        
        參數:
            keyword: 關鍵字
            news_list: 新聞列表
            sentiment_results: 情感分析結果
            trend_prediction: 趨勢預測結果
            
        返回:
            str: 報告文件路徑
        """
        # 生成報告文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{timestamp}_{keyword}_report.html"
        report_path = os.path.join(self.data_dir, "reports", report_filename)
        
        # 創建情感分布圖表
        chart_path = self._create_sentiment_chart(keyword, sentiment_results)
        
        # 生成HTML報告
        html_content = self._generate_html_report(keyword, news_list, sentiment_results, trend_prediction, chart_path)
        
        # 保存報告
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return report_path
    
    def _create_sentiment_chart(self, keyword, sentiment_results):
        """創建情感分布圖表"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_filename = f"{timestamp}_{keyword}_sentiment.png"
        chart_path = os.path.join(self.data_dir, "charts", chart_filename)
        
        # 獲取情感數據
        news_sentiments = sentiment_results.get("news_sentiments", [])
        if not news_sentiments:
            return None
        
        # 計算積極、消極和中性新聞的數量
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for item in news_sentiments:
            compound = item["sentiment"]["compound"]
            if compound >= 0.05:
                positive_count += 1
            elif compound <= -0.05:
                negative_count += 1
            else:
                neutral_count += 1
        
        # 創建餅圖
        plt.figure(figsize=(10, 8))
        
        # 定義數據和標籤
        labels = ['積極 (紅色)', '中性 (灰色)', '消極 (綠色)']
        sizes = [positive_count, neutral_count, negative_count]
        colors = ['#cc0000', '#666666', '#009900']  # 紅色-積極, 灰色-中性, 綠色-消極
        explode = (0.1, 0, 0)  # 使"積極"部分突出
        
        # 繪製餅圖
        plt.pie(sizes, explode=explode, labels=labels, colors=colors, 
                autopct='%1.1f%%', shadow=True, startangle=90, textprops={'fontsize': 12})
        
        # 確保餅圖是圓形的
        plt.axis('equal')
        
        # 添加標題
        plt.title(f'"{keyword}" 相關新聞的情感分布', fontsize=16, pad=20)
        
        # 添加圖例
        plt.legend(loc='lower left')
        
        # 保存圖表
        plt.savefig(chart_path, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def _generate_html_report(self, keyword, news_list, sentiment_results, trend_prediction, chart_path=None):
        """生成HTML報告"""
        # 報告標題
        title = f"{keyword} 股票趨勢分析報告"
        
        # 生成報告時間
        report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 提取結果
        overall_sentiment = sentiment_results.get("overall_sentiment", "中性")
        confidence = sentiment_results.get("confidence", 0)
        keywords = sentiment_results.get("keywords", [])
        trend = trend_prediction.get("trend", "不確定")
        trend_reason = trend_prediction.get("reason", "")
        
        # 創建HTML內容
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                h1, h2, h3 {{ color: #333; }}
                .container {{ max-width: 1000px; margin: 0 auto; }}
                .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .news-item {{ border-bottom: 1px solid #ddd; padding: 10px 0; }}
                .news-title {{ font-weight: bold; }}
                .news-source {{ color: #666; font-size: 0.9em; }}
                .news-date {{ color: #666; font-size: 0.9em; }}
                .news-summary {{ margin-top: 5px; }}
                .positive {{ color: #cc0000; }}  /* 紅色 - 積極/看漲 */
                .negative {{ color: #009900; }}  /* 綠色 - 消極/看跌 */
                .neutral {{ color: #666666; }}   /* 灰色 - 中性 */
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .chart-container {{ margin: 20px 0; text-align: center; }}
                .bullish {{ color: #cc0000; font-weight: bold; }}  /* 紅色粗體 - 看漲 */
                .bearish {{ color: #009900; font-weight: bold; }}  /* 綠色粗體 - 看跌 */
                .pie-chart-container {{ max-width: 600px; margin: 0 auto; padding: 10px; }}
                .chart-explanation {{ font-size: 0.9em; color: #555; margin-top: 15px; text-align: center; }}
                .chart-explanation span {{ font-weight: bold; padding: 0 3px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{title}</h1>
                <p>報告生成時間: {report_time}</p>
                
                <div class="summary">
                    <h2>分析摘要</h2>
                    <p><strong>分析股票/關鍵詞:</strong> {keyword}</p>
                    <p><strong>新聞數量:</strong> {len(news_list)}</p>
                    <p><strong>整體情感:</strong> <span class="{'positive' if overall_sentiment == '積極' else 'negative' if overall_sentiment == '消極' else 'neutral'}">{overall_sentiment}</span> (信心指數: {confidence:.2f})</p>
                    <p><strong>趨勢預測:</strong> <span class="{'bullish' if trend == '看漲' else 'bearish' if trend == '看跌' else 'neutral'}">{trend}</span></p>
                    <p><strong>預測理由:</strong> {trend_reason}</p>
                    <p><strong>關鍵詞:</strong> {', '.join(keywords[:5]) if keywords else '無'}</p>
                </div>
        """
        
        # 添加情感圖表（如果有）
        if chart_path:
            chart_rel_path = os.path.relpath(chart_path, os.path.dirname(os.path.dirname(chart_path)))
            html += f"""
                <div class="chart-container">
                    <h2>情感分布圖</h2>
                    <div class="pie-chart-container">
                        <img src="../charts/{os.path.basename(chart_path)}" alt="情感分布圖" style="max-width: 100%; display: block; margin: 0 auto;">
                    </div>
                    <p class="chart-explanation">
                        此圓餅圖顯示新聞情感的分布比例：
                        <span class="positive">紅色表示積極情感</span>、
                        <span class="negative">綠色表示消極情感</span>、
                        <span class="neutral">灰色表示中性情感</span>。
                        百分比代表各類情感在所有新聞中的佔比。
                    </p>
                </div>
            """
        
        # 添加新聞列表
        html += """
                <h2>新聞列表</h2>
                <table>
                    <tr>
                        <th>標題</th>
                        <th>來源</th>
                        <th>日期</th>
                        <th>情感</th>
                    </tr>
        """
        
        # 添加情感分析結果到新聞
        news_with_sentiment = []
        for news in news_list:
            news_copy = news.copy()
            for sentiment_item in sentiment_results.get("news_sentiments", []):
                if sentiment_item["title"] == news["title"]:
                    news_copy["sentiment"] = sentiment_item["sentiment"]
                    news_copy["sentiment_label"] = sentiment_item["label"]
                    break
            if "sentiment" not in news_copy:
                news_copy["sentiment"] = {"compound": 0}
                news_copy["sentiment_label"] = "中性"
            news_with_sentiment.append(news_copy)
        
        # 按情感得分排序（從最積極到最消極）
        news_with_sentiment.sort(key=lambda x: x["sentiment"]["compound"], reverse=True)
        
        # 添加到表格
        for news in news_with_sentiment:
            sentiment_label = news.get("sentiment_label", "中性")
            sentiment_class = "positive" if sentiment_label == "積極" else "negative" if sentiment_label == "消極" else "neutral"
            
            html += f"""
                <tr>
                    <td><a href="{news['link']}" target="_blank">{news['title']}</a></td>
                    <td>{news.get('source', '')}</td>
                    <td>{news.get('published_time', '')}</td>
                    <td class="{sentiment_class}">{sentiment_label}</td>
                </tr>
            """
        
        html += """
                </table>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def load_news(self, json_path):
        """從JSON文件加載新聞數據"""
        if not os.path.exists(json_path):
            return []
        
        with open(json_path, "r", encoding="utf-8") as f:
            news_list = json.load(f)
        
        # 轉換日期字符串為datetime對象
        for news in news_list:
            if isinstance(news.get("date"), str):
                try:
                    news["date"] = datetime.strptime(news["date"], "%Y-%m-%d %H:%M:%S")
                except:
                    pass
        
        return news_list
    
    def open_report(self, report_file):
        """
        在預設瀏覽器中打開報告文件
        
        參數:
            report_file: 報告文件路徑
            
        返回:
            bool: 是否成功打開
        """
        if not os.path.exists(report_file):
            print(f"錯誤: 報告文件不存在: {report_file}")
            return False
        
        # 獲取絕對路徑
        abs_path = os.path.abspath(report_file)
        file_url = 'file:///' + abs_path.replace('\\', '/')
        
        # 嘗試順序: 系統命令 -> webbrowser模塊 -> 特定瀏覽器
        try:
            print("嘗試打開報告文件...")
            
            # 方法1: 系統命令 (根據操作系統選擇適當的命令)
            if sys.platform.startswith('win'):
                try:
                    os.system(f'start "" "{abs_path}"')
                    print(f"已使用Windows start命令打開報告")
                    return True
                except Exception as e:
                    print(f"Windows start命令失敗: {e}")
            
            elif sys.platform.startswith('darwin'):  # macOS
                try:
                    subprocess.Popen(['open', abs_path])
                    print(f"已使用macOS open命令打開報告")
                    return True
                except Exception as e:
                    print(f"macOS open命令失敗: {e}")
            
            elif sys.platform.startswith('linux'):  # Linux
                try:
                    subprocess.Popen(['xdg-open', abs_path])
                    print(f"已使用Linux xdg-open命令打開報告")
                    return True
                except Exception as e:
                    print(f"Linux xdg-open命令失敗: {e}")
            
            # 方法2: webbrowser模塊 (如果系統命令失敗)
            try:
                webbrowser.open(file_url)
                print(f"已使用webbrowser模塊打開報告")
                return True
            except Exception as e:
                print(f"webbrowser模塊失敗: {e}")
            
            # 方法3: 指定瀏覽器 (如果前兩種方法都失敗)
            browsers = [
                "chrome", "msedge", "firefox", "iexplore", 
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Mozilla Firefox\firefox.exe"
            ]
            
            for browser in browsers:
                try:
                    webbrowser.get(browser).open(file_url)
                    print(f"已使用{browser}打開報告")
                    return True
                except Exception:
                    continue
            
            # 如果所有方法都失敗
            print(f"無法自動打開報告，請手動打開此文件：\n{abs_path}")
            return False
            
        except Exception as e:
            print(f"打開報告時發生錯誤: {e}")
            print(f"請手動打開報告文件：\n{abs_path}")
            return False 