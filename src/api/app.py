"""
FastAPI 后端 - AI PR Reviewer

提供 REST API 接口，供前端（Streamlit）或外部调用
"""
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from src.core.github_client import GitHubClient
from src.core.diff_parser import DiffParser
from src.core.ai_reviewer import AIReviewer

app = FastAPI(
    title="AI PR Reviewer",
    description="基于 DeepSeek 的智能代码审查工具",
    version="1.0.0"
)


# ========== 请求/响应模型 ==========

class ReviewRequest(BaseModel):
    """审查请求"""
    pr_url: str = Field(..., description="GitHub PR URL", example="https://github.com/microsoft/vscode/pull/7559")
    model: Optional[str] = Field(None, description="AI 模型名称，默认 deepseek-v4-flash")


class ReviewResponse(BaseModel):
    """审查响应"""
    success: bool
    summary: str = ""
    overall_score: int = 0
    issues_count: int = 0
    issues: List[dict] = []
    strengths: List[str] = []
    suggestions: List[str] = []
    raw_report: Optional[dict] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str


# ========== 全局实例（启动时初始化） ==========

github_client = GitHubClient()


# ========== API 路由 ==========

@app.get("/", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(status="ok", version="1.0.0")


@app.post("/api/review", response_model=ReviewResponse)
async def review_pr(request: ReviewRequest):
    """
    审查一个 GitHub PR
    
    流程：获取 PR diff → 解析 → AI 审查 → 返回报告
    """
    try:
        # 1. 获取 PR 信息
        pr_info = github_client.fetch_pr_info(request.pr_url)
        if not pr_info:
            raise HTTPException(status_code=404, detail=f"无法获取 PR 信息: {request.pr_url}")
        
        # 2. 获取 diff
        diff_text = github_client.fetch_pr_diff(request.pr_url)
        if not diff_text:
            raise HTTPException(status_code=404, detail=f"无法获取 PR diff: {request.pr_url}")
        
        # 3. 解析 diff
        parser = DiffParser(diff_text)
        file_diffs = parser.parse()
        
        if not file_diffs:
            raise HTTPException(status_code=422, detail="未解析到任何文件改动")
        
        # 4. AI 审查
        reviewer = AIReviewer()
        report = reviewer.review(file_diffs, pr_info)
        
        # 5. 返回结构化响应
        return ReviewResponse(
            success=True,
            summary=report.summary,
            overall_score=report.overall_score,
            issues_count=len(report.issues),
            issues=[vars(issue) for issue in report.issues],
            strengths=report.strengths,
            suggestions=report.suggestions,
            raw_report=report.to_dict()
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


# ========== 启动方式 ==========
# uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
