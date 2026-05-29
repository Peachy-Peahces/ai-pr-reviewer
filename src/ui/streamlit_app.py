"""
Streamlit 前端 - AI PR Reviewer

用户界面：输入 PR URL → 显示审查报告
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from src.core.github_client import GitHubClient
from src.core.diff_parser import DiffParser
from src.core.ai_reviewer import AIReviewer


# ========== 页面配置 ==========
st.set_page_config(
    page_title="AI PR Reviewer",
    page_icon="🔍",
    layout="wide"
)

# ========== 初始化 Session State ==========
if 'report' not in st.session_state:
    st.session_state.report = None
if 'reviewed' not in st.session_state:
    st.session_state.reviewed = False


# ========== 标题 ==========
st.title("🔍 AI PR Reviewer")
st.markdown("基于 DeepSeek 的智能代码审查工具")
st.divider()


# ========== 输入区域 ==========
col1, col2, col3 = st.columns([4, 1, 1])

with col1:
    pr_url = st.text_input(
        "GitHub PR URL",
        placeholder="https://github.com/owner/repo/pull/123",
        label_visibility="collapsed"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    review_btn = st.button("🚀 开始审查", type="primary", use_container_width=True)

with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    demo_btn = st.button("🧪 离线测试", use_container_width=True)


# ========== 离线示例数据 ==========
SAMPLE_DIFF = """diff --git a/src/main.py b/src/main.py
index abc1234..def5678 100644
--- a/src/main.py
+++ b/src/main.py
@@ -10,6 +10,12 @@ class Calculator:
     def add(self, a, b):
         return a + b
 
+    def divide(self, a, b):
+        return a / b
+
+    def multiply(self, a, b):
+        result = 0
+        for i in range(b):
+            result = result + a
+        return result
+
     def subtract(self, a, b):
         return a - b
 
diff --git a/src/utils.py b/src/utils.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/src/utils.py
@@ -0,0 +1,10 @@
+import os
+
+def get_env(key):
+    value = os.environ.get(key)
+    if value == None:
+        return ''
+    return value
+
+password = 'admin123'
+api_key = 'sk-abcdef123456'
"""

SAMPLE_PR_INFO = {
    "title": "Add divide and multiply methods",
    "author": "testuser",
    "files_changed": 2
}


# ========== 审查逻辑（共用） ==========
def _generate_mock_report(file_diffs, pr_info):
    """生成 Mock 审查报告（完全离线，不调 API）"""
    from src.core.ai_reviewer import ReviewReport, ReviewIssue
    issues = []
    for fd in file_diffs:
        if fd.additions > 5:
            issues.append(ReviewIssue(
                severity="warning",
                file_path=fd.filename,
                line_number=None,
                rule_id="REVIEW-001",
                title=f"文件 `{fd.filename}` 新增 {fd.additions} 行代码",
                description=f"此文件新增了 {fd.additions} 行代码，建议检查逻辑正确性和边界条件。",
                suggestion="请确认所有新增函数都有对应的测试用例，并检查异常处理是否完善。"
            ))
        if any(kw in fd.diff_content.lower() for kw in ["password", "api_key", "secret", "token"]):
            issues.append(ReviewIssue(
                severity="critical",
                file_path=fd.filename,
                line_number=None,
                rule_id="SECURITY-001",
                title=f"检测到硬编码的敏感信息",
                description=f"在文件 `{fd.filename}` 中检测到硬编码的密码或密钥。",
                suggestion="请使用环境变量或密钥管理服务存储敏感信息，切勿硬编码在代码中。"
            ))
        if "return a / b" in fd.diff_content and "if b == 0" not in fd.diff_content:
            issues.append(ReviewIssue(
                severity="critical",
                file_path=fd.filename,
                line_number=None,
                rule_id="LOGIC-001",
                title=f"`{fd.filename}` 中除法运算未检查除零",
                description="divide 方法直接执行 a/b，未处理 b=0 的情况，会导致 ZeroDivisionError。",
                suggestion="在除法前添加 `if b == 0: raise ValueError(...)` 检查。"
            ))

    return ReviewReport(
        summary=f"审查了 {len(file_diffs)} 个文件的改动（{pr_info.get('title', 'N/A')}），"
                f"发现 {len(issues)} 个潜在问题。代码整体结构清晰，但存在安全和健壮性方面的改进空间。",
        overall_score=6,
        issues=issues,
        strengths=["代码结构清晰，函数职责分明", "使用了类型注解提升代码可读性"],
        suggestions=[
            "建议为所有 public 函数添加单元测试",
            "敏感信息应从环境变量读取，避免硬编码",
            "除法等危险运算应添加边界检查",
        ]
    )


def run_review(diff_text, pr_info):
    """执行审查（联网/离线共用）"""
    parser = DiffParser(diff_text)
    file_diffs = parser.parse()
    
    if not file_diffs:
        st.error("❌ 未解析到任何文件改动")
        return False
    
    reviewer = AIReviewer()
    # 防御：Streamlit 会关闭 sys.stdout，而 requests/urllib3 内部可能写 stdout
    old_stdout = sys.stdout
    try:
        sys.stdout = open(os.devnull, 'w')
        report = reviewer.review(file_diffs, pr_info)
    except Exception as e:
        st.error(f"❌ AI 审查失败: {e}")
        return False
    finally:
        sys.stdout = old_stdout
    st.session_state.report = report
    st.session_state.reviewed = True
    return True


# ========== 按钮事件处理 ==========

if demo_btn:
    # ====== 离线模式 ======
    with st.spinner("⏳ 正在分析代码（离线模式）..."):
        # 解析 diff
        parser = DiffParser(SAMPLE_DIFF)
        file_diffs = parser.parse()
        st.write(f"变更文件: {len(file_diffs)} 个")
        for fd in file_diffs:
            st.write(f"- `{fd.filename}` ({fd.status}, +{fd.additions}/-{fd.deletions})")

        # AI 审查
        st.write("🤖 正在调用 DeepSeek API...")
        try:
            success = run_review(SAMPLE_DIFF, SAMPLE_PR_INFO)
            if success:
                st.success("✅ 审查完成！")
        except (ValueError, Exception) as e:
            st.warning(f"⚠️ API 不可用 ({e})，使用离线 Mock 模式生成报告。")
            mock_report = _generate_mock_report(file_diffs, SAMPLE_PR_INFO)
            st.session_state.report = mock_report
            st.session_state.reviewed = True
            st.success("✅ 离线 Mock 审查完成！")

elif review_btn and pr_url:
    # ====== 联网模式 ======
    pr_url = pr_url.strip()
    if not pr_url.startswith("https://github.com/") or "/pull/" not in pr_url:
        st.error("❌ 请输入正确的 GitHub PR URL（必须包含 /pull/数字）")
    else:
        with st.spinner("⏳ 正在分析代码..."):
            try:
                client = GitHubClient()

                st.write("📡 获取 PR 信息...")
                if client.proxy:
                    st.caption(f"代理: {client.proxy}")
                else:
                    st.caption("⚠️ 未检测到代理，GitHub 可能无法连接")
                pr_info = client.fetch_pr_info(pr_url)
                if not pr_info:
                    st.warning("⚠️ api.github.com SSL 干扰，跳过 PR 元信息，继续获取 diff")
                    parsed = client.parse_pr_url(pr_url)
                    pr_info = {"title": f"PR #{parsed['pr_number']}", "author": "unknown", "files_changed": 0}
                else:
                    st.write(f"**PR**: {pr_info['title']}")
                    st.write(f"**作者**: {pr_info['author']}")
                
                st.write("📄 获取并解析 Diff...")
                diff_text = client.fetch_pr_diff(pr_url)
                if not diff_text:
                    st.error("❌ 无法获取 Diff，请检查网络代理")
                    st.stop()
                st.write(f"Diff 长度: {len(diff_text)} 字符")
                
                st.write("🤖 正在调用 DeepSeek API...")
                if run_review(diff_text, pr_info):
                    st.session_state.pr_url = pr_url
                    st.success("✅ 审查完成！")
                
            except ValueError as e:
                st.error(f"❌ 配置错误: {e}")
            except Exception as e:
                st.error(f"❌ 错误: {e}")


# ========== 展示报告 ==========
if st.session_state.reviewed and st.session_state.report:
    report = st.session_state.report
    
    st.divider()
    
    # 总评分
    score = report.overall_score
    score_color = "green" if score >= 7 else ("orange" if score >= 5 else "red")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"## 总体评分: :{score_color}[{score}/10]")
    
    st.markdown(f"**📝 总体评价:**\n\n{report.summary}")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["⚠️ 问题", "✅ 优点", "💡 建议", "📄 JSON"])
    
    # 问题 Tab
    with tab1:
        if report.issues:
            severity_icons = {
                "critical": "🔴",
                "warning": "🟡",
                "info": "🔵",
                "suggestion": "💡"
            }
            for issue in report.issues:
                icon = severity_icons.get(issue.severity, "❓")
                with st.expander(f"{icon} [{issue.severity.upper()}] {issue.title}"):
                    st.write(f"**文件**: `{issue.file_path}`" + 
                            (f" (行 {issue.line_number})" if issue.line_number else ""))
                    st.write(f"**规则**: {issue.rule_id}")
                    st.write(f"**描述**: {issue.description}")
                    st.write(f"**建议**: {issue.suggestion}")
        else:
            st.success("🎉 没有发现问题！代码质量很好。")
    
    # 优点 Tab
    with tab2:
        if report.strengths:
            for s in report.strengths:
                st.success(f"✅ {s}")
        else:
            st.info("暂无")
    
    # 建议 Tab
    with tab3:
        if report.suggestions:
            for s in report.suggestions:
                st.info(f"💡 {s}")
        else:
            st.info("暂无")
    
    # JSON Tab
    with tab4:
        st.json(report.to_dict())
    
    # 统计
    st.divider()
    st.caption(f"共发现 {len(report.issues)} 个问题 | AI 模型: deepseek-v4-flash | Powered by DeepSeek")

    # ====== 发布到 PR ======
    st.divider()
    st.subheader("📤 发布审查结果")

    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        try:
            with open('config.json', 'r') as f:
                token = json.load(f).get('github_token')
        except Exception:
            pass

    if not token:
        st.info("💡 设置 `GITHUB_TOKEN` 环境变量或 config.json 后即可将审查结果发布到 PR")
        st.caption("Token 需要 `repo` 权限，在 https://github.com/settings/tokens 创建")
    else:
        if st.button("🚀 发布到 GitHub PR", type="primary", use_container_width=True):
            with st.spinner("📤 正在提交 Review 到 GitHub..."):
                client = GitHubClient(token=token)
                commit_id = client.fetch_pr_head_sha(st.session_state.pr_url)
                if not commit_id:
                    st.error("❌ 无法获取 PR commit SHA，请检查网络")
                else:
                    review_url = client.post_review(st.session_state.pr_url, report, commit_id)
                    if review_url:
                        st.success(f"✅ 审查已发布！[查看]({review_url})")
                    else:
                        st.error("❌ 发布失败，请检查 Token 权限和网络（api.github.com 可能需要代理）")
