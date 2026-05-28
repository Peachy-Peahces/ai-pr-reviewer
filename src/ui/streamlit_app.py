import streamlit as st
from src.core.github_client import GitHubClient
from src.core.ai_reviewer import AIReviewer
from src.core.diff_parser import DiffParser

st.set_page_config(page_title="AI PR Reviewer", page_icon="🤖")

st.title("🤖 AI PR Reviewer")
st.caption("基于 DeepSeek-V4 Flash 的 GitHub PR 自动审查工具")

# 侧边栏 - 配置
with st.sidebar:
    st.header("⚙️ 配置")
    github_token = st.text_input("GitHub Token", type="password")
    deepseek_api_key = st.text_input("DeepSeek API Key", type="password")
    st.markdown("[获取 GitHub Token](https://github.com/settings/tokens)")
    st.markdown("[获取 DeepSeek API Key](https://platform.deepseek.com/)")

# 主界面
pr_url = st.text_input("📎 输入 GitHub PR URL", placeholder="https://github.com/owner/repo/pull/123")

if st.button("🚀 开始审查", type="primary"):
    if not pr_url:
        st.error("请输入 PR URL")
    elif not github_token or not deepseek_api_key:
        st.error("请在侧边栏填写 GitHub Token 和 DeepSeek API Key")
    else:
        # TODO: 实现审查逻辑
        st.info("⏳ 功能开发中...")
        st.json({
            "pr_title": "示例 PR 标题",
            "files_changed": 3,
            "review_results": []
        })
