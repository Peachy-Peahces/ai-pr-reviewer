"""GitHub API 客户端封装"""
from github import Github, GithubException
from typing import Dict, List, Optional
import re

class GitHubClient:
    """GitHub API 客户端，用于获取 PR 信息和 Diff"""
    
    def __init__(self, token: str = None):
        """初始化 GitHub 客户端
        
        Args:
            token: GitHub Personal Access Token (可选，匿名用户有更严格的 rate limit)
        """
        self.github = Github(token) if token else Github()
        self.token = token
        
    def parse_pr_url(self, pr_url: str) -> Optional[Dict[str, str]]:
        """解析 GitHub PR URL，提取 owner、repo、PR number
        
        Args:
            pr_url: GitHub PR URL，格式如 https://github.com/owner/repo/pull/123
            
        Returns:
            包含 owner, repo, pr_number 的字典，解析失败返回 None
        """
        # 匹配 GitHub PR URL 的正则
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
        """获取 PR 基本信息
        
        Args:
            pr_url: GitHub PR URL
            
        Returns:
            包含 PR 标题、作者、文件列表等信息的字典
        """
        parsed = self.parse_pr_url(pr_url)
        if not parsed:
            return None
            
        try:
            repo = self.github.get_repo(f"{parsed['owner']}/{parsed['repo']}")
            pr = repo.get_pull(parsed['pr_number'])
            
            return {
                'title': pr.title,
                'author': pr.user.login,
                'pr_number': parsed['pr_number'],
                'repo': f"{parsed['owner']}/{parsed['repo']}",
                'state': pr.state,
                'created_at': pr.created_at.isoformat(),
                'updated_at': pr.updated_at.isoformat(),
                'additions': pr.additions,
                'deletions': pr.deletions,
                'changed_files': pr.changed_files,
                'mergeable': pr.mergeable,
                'html_url': pr.html_url
            }
        except GithubException as e:
            print(f"GitHub API 错误: {e}")
            return None
    
    def fetch_pr_diff(self, pr_url: str) -> Optional[str]:
        """获取 PR 的 diff 内容
        
        Args:
            pr_url: GitHub PR URL
            
        Returns:
            PR 的完整 diff 文本，失败返回 None
        """
        parsed = self.parse_pr_url(pr_url)
        if not parsed:
            return None
            
        try:
            repo = self.github.get_repo(f"{parsed['owner']}/{parsed['repo']}")
            pr = repo.get_pull(parsed['pr_number'])
            
            # 获取 diff 文本
            # PyGithub 默认不提供 diff，需要通过 raw 请求获取
            import requests
            
            headers = {}
            if self.token:
                headers['Authorization'] = f'token {self.token}'
            
            diff_url = f"https://github.com/{parsed['owner']}/{parsed['repo']}/pull/{parsed['pr_number']}.diff"
            response = requests.get(diff_url, headers=headers)
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"获取 diff 失败: HTTP {response.status_code}")
                return None
                
        except GithubException as e:
            print(f"GitHub API 错误: {e}")
            return None
        except Exception as e:
            print(f"获取 diff 时发生错误: {e}")
            return None
    
    def fetch_pr_files(self, pr_url: str) -> Optional[List[Dict]]:
        """获取 PR 中变更的文件列表（含文件状态、增删行数）
        
        Args:
            pr_url: GitHub PR URL
            
        Returns:
            文件列表，每个元素包含 filename, status, additions, deletions 等
        """
        parsed = self.parse_pr_url(pr_url)
        if not parsed:
            return None
            
        try:
            repo = self.github.get_repo(f"{parsed['owner']}/{parsed['repo']}")
            pr = repo.get_pull(parsed['pr_number'])
            files = pr.get_files()
            
            result = []
            for file in files:
                result.append({
                    'filename': file.filename,
                    'status': file.status,  # added, modified, removed, renamed
                    'additions': file.additions,
                    'deletions': file.deletions,
                    'changes': file.changes,
                    'patch': file.patch  # 单个文件的 diff patch
                })
            
            return result
        except GithubException as e:
            print(f"GitHub API 错误: {e}")
            return None
"""
使用示例（测试用）：
if __name__ == "__main__":
    client = GitHubClient(token="your_github_token")
    pr_url = "https://github.com/octocat/Hello-World/pull/1"
    diff = client.fetch_pr_diff(pr_url)
    print(diff)
"""
