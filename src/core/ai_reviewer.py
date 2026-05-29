"""
ai_reviewer.py - AI 代码审查核心模块

核心功能：
1. 构建专业的 code review 提示词（prompt）
2. 调用 DeepSeek API 进行代码审查
3. 解析 AI 返回的结构化 review 结果

使用模型：DeepSeek-V4 Flash（性价比高，适合代码审查场景）
"""

import json
import os
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import requests
from src.core.rule_config import RuleConfig


@dataclass
class ReviewIssue:
    """单个审查问题"""
    severity: str       # critical / warning / info / suggestion
    file_path: str      # 问题所在文件
    line_number: Optional[int]  # 行号（如果有）
    rule_id: str        # 规则 ID（如: SECURITY-001）
    title: str          # 问题标题
    description: str    # 详细描述
    suggestion: str     # 修复建议


@dataclass
class ReviewReport:
    """完整的审查报告"""
    summary: str                # 总体评价
    overall_score: int          # 总分 (1-10)
    issues: List[ReviewIssue]   # 问题列表
    strengths: List[str]        # 做得好的地方
    suggestions: List[str]      # 整体建议
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "summary": self.summary,
            "overall_score": self.overall_score,
            "issues": [asdict(issue) for issue in self.issues],
            "strengths": self.strengths,
            "suggestions": self.suggestions
        }
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class AIReviewer:
    """AI 代码审查器"""
    
    # DeepSeek API 配置（官方接口）
    API_URL = "https://api.deepseek.com/chat/completions"
    
    # 系统提示词：定义 AI 的角色和行为
    SYSTEM_PROMPT = """你是一位资深的代码审查专家（Code Reviewer），拥有 15 年以上的软件开发经验。

## 你的职责
审查 Pull Request 中的代码改动，找出潜在的问题和改进空间。

## 审查维度（按优先级排序）
1. **正确性**：逻辑错误、边界条件、空指针、类型错误
2. **安全性**：SQL注入、XSS、敏感信息泄露、权限校验
3. **性能**：不必要的循环、内存泄漏、N+1查询、算法复杂度
4. **可读性**：命名规范、注释质量、代码长度、嵌套深度
5. **最佳实践**：是否遵循语言/框架的最佳实践和设计模式

## 输出格式要求
必须严格返回 JSON 格式，不要包含任何其他文字：
{
  "summary": "一段话总结整体评价",
  "overall_score": 8,
  "issues": [
    {
      "severity": "critical/warning/info/suggestion",
      "file_path": "文件路径",
      "line_number": null 或 具体行号,
      "rule_id": "如 SECURITY-001, PERF-002 等",
      "title": "简短的问题标题",
      "description": "详细描述为什么这是个问题",
      "suggestion": "具体的修复建议或示例代码"
    }
  ],
  "strengths": ["做得好的地方1", "做得好的地方2"],
  "suggestions": ["整体改进建议1", "整体改进建议2"]
}

## 重要：行号使用
diff 中每行前面的数字（如 " 10: "）是新文件的行号。请在 issue 的 line_number 字段中填写对应的**新文件行号**（整数），不要填 null。这能让审查结果精确到代码行。

## 注意事项
- 如果代码没有明显问题，overall_score 可以给 8-10 分
- 至少给出 1 个 strength（肯定作者的付出）
- severity 说明：critical=必须修复, warning=建议修复, info=提醒注意, suggestion=可选优化
"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 AI 审查器
        
        Args:
            api_key: DeepSeek/SiliconFlow API Key。
                     优先级：参数 > 环境变量 > config.json
        """
        self.api_key = self._load_api_key(api_key)
        
        if not self.api_key:
            raise ValueError(
                "未找到 API Key！请设置以下任一方式：\n"
                "1. 环境变量: $env:DEEPSEEK_API_KEY='your-key'\n"
                "2. config.json: 在项目根目录创建 config.json\n"
                '  {"api_key": "your-key"}'
            )
    
    def _load_api_key(self, api_key: Optional[str]) -> Optional[str]:
        """
        加载 API Key（多级回退）
        
        优先级：参数 > 环境变量 DEEPSEEK_API_KEY > config.json
        """
        if api_key:
            return api_key
        
        # 尝试环境变量
        env_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("SF_API_KEY")
        if env_key:
            return env_key
        
        # 尝试 config.json（向上搜索项目根目录）
        search_dir = os.path.dirname(os.path.abspath(__file__))
        for _ in range(5):  # 最多向上搜索 5 层
            config_path = os.path.join(search_dir, 'config.json')
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                        return config.get("api_key")
                except Exception as e:
                    pass  # config.json not found, will raise below
                break
            parent = os.path.dirname(search_dir)
            if parent == search_dir:
                break
            search_dir = parent
        
        return None
    
    def build_prompt(self, file_diffs: List, pr_info: Dict = None) -> str:
        """
        构建发送给 AI 的完整提示词
        
        Args:
            file_diffs: diff_parser 解析出的 FileDiff 列表
            pr_info: PR 基本信息（标题、作者等）
            
        Returns:
            完整的用户消息（prompt）
        """
        # PR 信息部分
        pr_section = ""
        if pr_info:
            pr_section = f"""## PR 信息
- 标题: {pr_info.get('title', 'N/A')}
- 作者: {pr_info.get('author', 'N/A')}
- 变更文件数: {pr_info.get('files_changed', 'N/A')}

"""
        
        # 代码改动部分
        code_section = "## 代码改动\n\n"
        
        for i, fd in enumerate(file_diffs, 1):
            code_section += f"""### 文件 {i}: `{fd.filename}` ({fd.status}, +{fd.additions}/-{fd.deletions})

```diff
{fd.diff_content}
```

"""
        
        # 组合完整 prompt
        rules_section = RuleConfig().build_rules_prompt()

        full_prompt = f"{pr_section}{rules_section}{code_section}请对以上代码进行全面的 Code Review。"
        
        return full_prompt
    
    def review(self, file_diffs: List, pr_info: Dict = None) -> ReviewReport:
        """
        执行代码审查（主入口）
        
        Args:
            file_diffs: FileDiff 列表（来自 diff_parser）
            pr_info: PR 信息（来自 github_client）
            
        Returns:
            ReviewReport 完整报告
        """
        # 1. 构建 prompt
        prompt = self.build_prompt(file_diffs, pr_info)

        # 2. 调用 API
        raw_response = self._call_api(prompt)

        # 3. 解析响应
        report = self._parse_response(raw_response)
        
        return report
    
    def _call_api(self, prompt: str, model: str = "deepseek-v4-flash") -> str:
        """
        调用 DeepSeek API
        
        Args:
            prompt: 用户提示词
            model: 模型名称
            
        Returns:
            API 原始响应文本
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,           # 低温度 = 更确定性的输出（适合代码审查）
            "max_tokens": 4096            # 最大输出 token 数
        }
        
        # 读取代理（与 github_client.py 一致，优先 env var）
        proxy = os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY') or os.environ.get('http_proxy') or os.environ.get('https_proxy')
        proxies = {'http': proxy, 'https': proxy} if proxy else None

        response = requests.post(
            self.API_URL,
            headers=headers,
            json=payload,
            proxies=proxies,
            timeout=60
        )
        
        # 错误处理
        if response.status_code != 200:
            raise Exception(
                f"API 调用失败 ({response.status_code}): {response.text}"
            )
        
        # 提取 AI 回复内容
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        return content
    
    def _parse_response(self, raw_response: str) -> ReviewReport:
        """
        解析 AI 返回的 JSON 响应
        
        Args:
            raw_response: API 原始返回文本
            
        Returns:
            ReviewReport 对象
        """
        # 清理可能的 markdown 代码块标记
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            # 去掉 ```json 或 ``` 开头和结尾
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            cleaned = "\n".join(lines).strip()
        
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # 如果 AI 没有返回合法 JSON，包装成基本报告
            # AI returned invalid JSON, fallback to raw text
            return ReviewReport(
                summary=raw_response[:500],
                overall_score=5,
                issues=[],
                strengths=[],
                suggestions=[]
            )
        
        # 转换 issues 列表
        issues = []
        for issue_data in data.get("issues", []):
            issues.append(ReviewIssue(**issue_data))
        
        return ReviewReport(
            summary=data.get("summary", ""),
            overall_score=data.get("overall_score", 5),
            issues=issues,
            strengths=data.get("strengths", []),
            suggestions=data.get("suggestions", [])
        )
