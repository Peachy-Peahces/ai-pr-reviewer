"""GitHub API 客户端封装

使用 requests 库直接调用 GitHub REST API（而非 PyGithub）
原因：requests 天然支持 HTTP_PROXY 环境变量，PyGithub 不支持
"""
import re
import os
import json
import logging
import time
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GitHubClient:
    """GitHub API 客户端，用于获取 PR 信息和 Diff"""
    
    # GitHub REST API Base URL
    API_BASE = "https://api.github.com"
    
    def __init__(self, token: str = None):
        """初始化 GitHub 客户端
        
        Args:
            token: GitHub Personal Access Token (可选，匿名用户有更严格的 rate limit)
        """
        self.token = token or os.environ.get('GITHUB_TOKEN')
        if not self.token:
            self.token = self._load_token_from_config()
        # 读取代理（优先级：env var > 系统代理 > Clash 默认端口）
        self.proxy = (
            os.environ.get('HTTP_PROXY') or
            os.environ.get('HTTPS_PROXY') or
            os.environ.get('http_proxy') or
            os.environ.get('https_proxy')
        )
        if not self.proxy:
            try:
                import urllib.request
                sys_proxy = urllib.request.getproxies().get('http', '')
                if sys_proxy.startswith(('http://', 'https://')):
                    self.proxy = sys_proxy
            except Exception:
                pass
        if not self.proxy:
            self.proxy = 'http://127.0.0.1:7897'  # Clash 默认端口
        self.proxies = {'http': self.proxy, 'https': self.proxy}
        
    def _load_token_from_config(self) -> Optional[str]:
        """从 config.json 加载 GitHub token"""
        search_dir = os.path.dirname(os.path.abspath(__file__))
        for _ in range(5):
            config_path = os.path.join(search_dir, 'config.json')
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        return json.load(f).get('github_token')
                except Exception:
                    pass
                break
            parent = os.path.dirname(search_dir)
            if parent == search_dir:
                break
            search_dir = parent
        return None

    def _get_headers(self) -> Dict[str, str]:
        """构建请求头"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-PR-Reviewer/1.0"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers
    
    def _api_get(self, url: str, retries: int = 5) -> Optional[dict]:
        """通用 GET 请求（自动带代理和认证，自动重试）"""
        for attempt in range(retries):
            try:
                resp = requests.get(url, headers=self._get_headers(), proxies=self.proxies, timeout=60)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 403 and attempt < retries - 1:
                    logger.warning("API 限流 (403)，等待后重试...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.warning("API 请求失败: %s → HTTP %s", url, resp.status_code)
                    return None
            except Exception as e:
                logger.warning("网络请求错误 (attempt %s/%s): %s", attempt + 1, retries, e)
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        return None
    
    def _raw_get(self, url: str, retries: int = 5) -> Optional[str]:
        """通用 GET 请求，返回原始文本（用于 .diff 等非 JSON 接口，自动重试）"""
        for attempt in range(retries):
            try:
                resp = requests.get(url, headers=self._get_headers(), proxies=self.proxies, timeout=60)
                if resp.status_code == 200:
                    return resp.text
                elif resp.status_code == 403 and attempt < retries - 1:
                    logger.warning("限流 (403)，等待后重试...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.warning("请求失败: %s → HTTP %s", url, resp.status_code)
                    return None
            except Exception as e:
                logger.warning("网络请求错误 (attempt %s/%s): %s", attempt + 1, retries, e)
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        return None
    
    def parse_pr_url(self, pr_url: str) -> Optional[Dict[str, str]]:
        """解析 GitHub PR URL，提取 owner、repo、PR number
        
        Args:
            pr_url: GitHub PR URL，格式如 https://github.com/owner/repo/pull/123
            
        Returns:
            包含 owner, repo, pr_number 的字典，解析失败返回 None
        """
        pattern = r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)'
        match = re.match(pattern, pr_url)
        
        if not match:
            return None
            
        return {
            'owner': match.group(1),
            'repo': match.group(2),
            'pr_number': int(match.group(3))
        }
    
    def fetch_pr_info(self, pr_url: str) -> Optional[Dict]:
        """获取 PR 基本信息（使用 REST API）
        
        Returns:
            包含 PR 标题、作者等信息的字典
        """
        parsed = self.parse_pr_url(pr_url)
        if not parsed:
            return None
            
        api_url = f"{self.API_BASE}/repos/{parsed['owner']}/{parsed['repo']}/pulls/{parsed['pr_number']}"
        data = self._api_get(api_url)
        
        if not data:
            return None
            
        return {
            'title': data.get('title', ''),
            'author': data.get('user', {}).get('login', ''),
            'pr_number': parsed['pr_number'],
            'repo': f"{parsed['owner']}/{parsed['repo']}",
            'state': data.get('state', ''),
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', ''),
            'additions': data.get('additions', 0),
            'deletions': data.get('deletions', 0),
            'changed_files': data.get('changed_files', 0),
            'mergeable': data.get('mergeable'),
            'html_url': data.get('html_url', '')
        }
    
    def fetch_pr_diff(self, pr_url: str) -> Optional[str]:
        """获取 PR 的完整 diff 文本
        
        Returns:
            diff 文本字符串
        """
        parsed = self.parse_pr_url(pr_url)
        if not parsed:
            return None
            
        diff_url = f"https://github.com/{parsed['owner']}/{parsed['repo']}/pull/{parsed['pr_number']}.diff"
        return self._raw_get(diff_url)
    
    def fetch_pr_files(self, pr_url: str) -> Optional[List[Dict]]:
        """获取 PR 中变更的文件列表
        
        Returns:
            文件列表，每个元素包含 filename, status, additions, deletions 等
        """
        parsed = self.parse_pr_url(pr_url)
        if not parsed:
            return None
            
        api_url = f"{self.API_BASE}/repos/{parsed['owner']}/{parsed['repo']}/pulls/{parsed['pr_number']}/files"
        data = self._api_get(api_url)
        
        if not data or not isinstance(data, list):
            return None
            
        result = []
        for f in data:
            result.append({
                'filename': f.get('filename', ''),
                'status': f.get('status', ''),
                'additions': f.get('additions', 0),
                'deletions': f.get('deletions', 0),
                'changes': f.get('changes', 0),
                'patch': f.get('patch', '')  # 单个文件的 diff patch
            })
        
        return result


    def fetch_pr_head_sha(self, pr_url: str) -> Optional[str]:
        """获取 PR 的 HEAD commit SHA（发 review 必需）"""
        parsed = self.parse_pr_url(pr_url)
        if not parsed:
            return None
        api_url = f"{self.API_BASE}/repos/{parsed['owner']}/{parsed['repo']}/pulls/{parsed['pr_number']}"
        data = self._api_get(api_url)
        if not data:
            return None
        return data.get('head', {}).get('sha')

    def post_review(self, pr_url: str, report, commit_id: str) -> Optional[str]:
        """将审查报告以 PR Review 形式提交到 GitHub

        返回 review HTML URL 或 None
        """
        parsed = self.parse_pr_url(pr_url)
        if not parsed:
            logger.warning("无法解析 PR URL")
            return None
        if not self.token:
            logger.warning("未设置 GitHub Token，无法提交 Review")
            return None

        # 构建评论列表：只提交有具体文件路径和行号的 issue
        comments = []
        for issue in report.issues:
            if not issue.file_path:
                continue
            body_parts = [f"**{issue.title}** ({issue.severity})"]
            if issue.description:
                body_parts.append(issue.description)
            if issue.suggestion:
                body_parts.append(f"💡 建议: {issue.suggestion}")
            comments.append({
                "path": issue.file_path,
                "line": issue.line_number or 1,
                "body": "\n\n".join(body_parts)
            })

        # 构建 review body
        body_lines = [
            f"## 🤖 AI Code Review",
            f"",
            f"**评分**: {report.overall_score}/10",
            f"",
            report.summary,
        ]
        if report.strengths:
            body_lines.append("\n### ✅ 优点")
            for s in report.strengths:
                body_lines.append(f"- {s}")
        if report.suggestions:
            body_lines.append("\n### 💡 建议")
            for s in report.suggestions:
                body_lines.append(f"- {s}")

        payload = {
            "commit_id": commit_id,
            "body": "\n".join(body_lines),
            "event": "COMMENT",
            "comments": comments
        }

        api_url = f"{self.API_BASE}/repos/{parsed['owner']}/{parsed['repo']}/pulls/{parsed['pr_number']}/reviews"
        for attempt in range(3):
            try:
                resp = requests.post(api_url, headers=self._get_headers(),
                                     json=payload, proxies=self.proxies, timeout=60)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    return data.get('html_url', '')
                elif resp.status_code == 422 and attempt < 2:
                    # 422 可能是 commit_id 过期或行号不对，降级为纯文字评论
                    if attempt == 1:
                        payload.pop("comments", None)
                        payload["body"] += "\n\n(行级评论提交失败，仅提交了摘要)"
                    time.sleep(2)
                    continue
                else:
                    logger.warning("Review 提交失败: HTTP %s %s", resp.status_code, resp.text[:200])
                    return None
            except Exception as e:
                logger.warning("Review 提交网络错误 (attempt %s/3): %s", attempt + 1, e)
                if attempt < 2:
                    time.sleep(2 ** attempt)
        return None


"""
使用示例：
if __name__ == "__main__":
    client = GitHubClient()
    pr_url = "https://github.com/microsoft/vscode/pull/7559"
    
    info = client.fetch_pr_info(pr_url)
    print(f"PR: {info['title']}")
    
    diff = client.fetch_pr_diff(pr_url)
    print(f"Diff 长度: {len(diff)}")
"""
