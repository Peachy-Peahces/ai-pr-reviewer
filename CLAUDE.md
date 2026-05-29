# AI PR Reviewer

基于 DeepSeek API 的 GitHub Pull Request 自动代码审查工具。

## 架构

```
用户输入 PR URL → GitHubClient 获取 diff → DiffParser 解析 → AIReviewer 调用 DeepSeek → 展示报告
```

- **前端**: Streamlit (`src/ui/streamlit_app.py`)
- **后端 API**: FastAPI (`src/api/app.py`) — 可选，前端可直接调用核心模块
- **核心模块**: `src/core/` (github_client, diff_parser, ai_reviewer)

## 运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Streamlit 前端
streamlit run src/ui/streamlit_app.py

# 或启动 FastAPI 后端
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

## 测试

```bash
# 离线测试（不依赖网络）
python -c "
from src.core.diff_parser import DiffParser
sample = '''diff --git a/src/main.py b/src/main.py
--- a/src/main.py
+++ b/src/main.py
@@ -10,6 +10,8 @@ def hello():
     print('hello')
+    print('new line')
'''
parser = DiffParser(sample)
print(parser.get_summary())
"

# Diff 解析测试（离线 + 在线）
python test_diff_parser.py

# GitHub Client 测试（需要网络和代理）
python test_github_client.py

# AI 审查完整流程测试（需要 DeepSeek API Key）
python test_ai_reviewer.py
```

## 配置

API Key 读取优先级（`src/core/ai_reviewer.py:_load_api_key`）:

1. 构造函数参数
2. 环境变量 `DEEPSEEK_API_KEY` 或 `SF_API_KEY`
3. 项目根目录 `config.json` → `{"api_key": "..."}`

**不要提交 `config.json`！** 已在 `.gitignore` 中排除。

## 代理设置

GitHub 被墙时需要设置代理（所有模块都支持 `HTTP_PROXY`/`HTTPS_PROXY` 环境变量）:

```powershell
$env:HTTP_PROXY = "http://127.0.0.1:7897"
$env:HTTPS_PROXY = "http://127.0.0.1:7897"
```

## 项目结构

```
src/
├── core/
│   ├── github_client.py   # GitHub REST API（requests + 代理支持）
│   ├── diff_parser.py     # Git diff 解析 → FileDiff 结构化数据
│   └── ai_reviewer.py     # DeepSeek API 调用 + ReviewReport 数据模型
├── api/
│   └── app.py             # FastAPI 端点 (/api/review)
├── ui/
│   └── streamlit_app.py   # Streamlit 界面（联网/离线双模式）
└── models/
    └── schemas.py         # Pydantic 模型（预留，核心代码未使用）
```

## 关键数据流

1. `GitHubClient.fetch_pr_diff(url)` → 原始 diff 文本
2. `DiffParser(diff_text).parse()` → `List[FileDiff]`
3. `AIReviewer().review(file_diffs, pr_info)` → `ReviewReport`
4. `ReviewReport` 包含: summary, overall_score, issues (List[ReviewIssue]), strengths, suggestions

## 审查规则配置

通过 `.pr-reviewer.json` 自定义审查行为（参考 `.pr-reviewer.example.json`）:

```json
{
  "rules": { "security": {"enabled": true}, "performance": {"enabled": false} },
  "custom_rules": [
    {"name": "禁止 print()", "description": "...", "severity": "warning"}
  ]
}
```

规则会注入到 AI prompt 中，影响审查结果。

## 注意事项

- **行号定位**: diff 内容已自动标注新文件行号，AI 返回的 `line_number` 可定位到代码行
- **代理架构**: Claude Code 直连 DeepSeek（不走代理），`github_client.py` 内置 Clash 代理
- **离线模式**（Streamlit `demo_btn`）使用内置 `SAMPLE_DIFF` 跳过 GitHub，API 不可用时自动降级到 Mock 报告
- `src/models/schemas.py` 未使用，`unidiff` 也未使用
