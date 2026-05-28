"""DeepSeek API 调用封装"""

class AIReviewer:
    def __init__(self, api_key: str, base_url: str, model: str):
        """初始化 AI 审查器"""
        pass
    
    def review_diff(self, diff_text: str, file_path: str):
        """审查单个 diff 块"""
        pass
    
    def parse_response(self, response: str):
        """解析 AI 返回的结果（风险等级 + 建议）"""
        pass
