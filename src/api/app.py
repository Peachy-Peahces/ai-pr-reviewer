from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="AI PR Reviewer API")

class PRRequest(BaseModel):
    pr_url: str

class PRResponse(BaseModel):
    pr_title: str
    files_changed: int
    review_results: list

@app.post("/api/review", response_model=PRResponse)
async def review_pr(request: PRRequest):
    """审查 GitHub PR"""
    # TODO: 实现 PR 审查逻辑
    pass

@app.get("/health")
async def health_check():
    return {"status": "ok"}
