"""Pydantic 数据模型定义"""

from pydantic import BaseModel
from typing import List, Optional

class PRInfo(BaseModel):
    """PR 基本信息"""
    title: str
    author: str
    repo: str
    pr_number: int
    files_changed: int

class FileDiff(BaseModel):
    """单个文件的 diff"""
    file_path: str
    status: str  # added, modified, deleted
    diff_text: str
    additions: int
    deletions: int

class ReviewComment(BaseModel):
    """单条 Review 建议"""
    file_path: str
    line_number: Optional[int]
    risk_level: str  # High, Medium, Low
    comment: str
    suggestion: Optional[str]

class ReviewResult(BaseModel):
    """单个文件的 Review 结果"""
    file_path: str
    comments: List[ReviewComment]
    summary: str

class PRReviewResponse(BaseModel):
    """完整 PR Review 结果"""
    pr_info: PRInfo
    results: List[ReviewResult]
    overall_summary: str
