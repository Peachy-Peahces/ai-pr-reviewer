import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
测试 ai_reviewer.py 模块

使用之前解析的 diff 数据，调用 DeepSeek API 进行代码审查
"""

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.github_client import GitHubClient
from src.core.diff_parser import DiffParser
from src.core.ai_reviewer import AIReviewer


def test_ai_review():
    """完整流程测试：获取 PR → 解析 diff → AI 审查"""
    
    print("=" * 60)
    print("测试 ai_reviewer.py（完整流程）")
    print("=" * 60)
    
    # 方式一：联网获取真实 PR（需要代理能连 GitHub）
    # 方式二：使用本地示例 diff（离线测试，跳过 GitHub）
    use_local = True  # ← 改成 False 可以测试联网模式
    
    if use_local:
        # ====== 离线模式：使用内置示例 diff ======
        print("\n[步骤 1] 使用内置示例 diff（离线模式）...")
        
        sample_diff = """diff --git a/src/main.py b/src/main.py
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
        
        diff_text = sample_diff
        
        pr_info = {
            "title": "Add divide and multiply methods",
            "author": "testuser",
            "files_changed": 2
        }
        
        print(f"✓ 示例 diff 长度: {len(diff_text)} 字符")
    else:
        # ====== 联网模式：获取真实 PR ======
        print("\n[步骤 1] 获取 PR diff...")
        client = GitHubClient()
        pr_url = "https://github.com/microsoft/vscode/pull/7559"
        
        pr_info_raw = client.fetch_pr_info(pr_url)
        if not pr_info_raw:
            print("❌ 获取 PR 信息失败，请检查网络/代理")
            return
        diff_text = client.fetch_pr_diff(pr_url)
        if not diff_text:
            print("❌ 获取 diff 失败，请检查网络/代理")
            return
        
        pr_info = {
            "title": pr_info_raw['title'],
            "author": pr_info_raw['author'],
            "files_changed": pr_info_raw['changed_files']
        }
        
        print(f"✓ PR: {pr_info['title']} (by {pr_info['author']})")
        print(f"✓ Diff 长度: {len(diff_text)} 字符")
    
    # 2. 解析 diff
    print("\n[步骤 2] 解析 diff...")
    parser = DiffParser(diff_text)
    file_diffs = parser.parse()
    
    print(f"✓ 解析完成: {len(file_diffs)} 个文件")
    for fd in file_diffs:
        print(f"  - {fd.filename} ({fd.status}, +{fd.additions}/-{fd.deletions})")
    
    # 3. AI 审查
    print("\n[步骤 3] 调用 DeepSeek API 进行代码审查...")
    print("（首次调用可能需要 10-30 秒，请耐心等待）")
    
    reviewer = AIReviewer()  # 从 config.json 读取 API Key
    report = reviewer.review(file_diffs, pr_info)
    
    # 4. 显示审查报告
    print("\n" + "=" * 60)
    print("📋 AI Code Review 报告")
    print("=" * 60)
    
    print(f"\n📊 总体评分: {report.overall_score}/10")
    print(f"\n📝 总体评价:\n{report.summary}")
    
    if report.strengths:
        print(f"\n✅ 做得好的地方:")
        for s in report.strengths:
            print(f"  • {s}")
    
    if report.issues:
        print(f"\n⚠️ 发现 {len(report.issues)} 个问题:")
        for i, issue in enumerate(report.issues, 1):
            severity_icon = {
                "critical": "🔴",
                "warning": "🟡",
                "info": "🔵",
                "suggestion": "💡"
            }.get(issue.severity, "❓")
            
            print(f"\n  {severity_icon} [{issue.severity.upper()}] {issue.title}")
            print(f"    文件: {issue.file_path}" + (f" (行 {issue.line_number})" if issue.line_number else ""))
            print(f"    规则: {issue.rule_id}")
            print(f"    描述: {issue.description[:100]}...")
            print(f"    建议: {issue.suggestion[:100]}...")
    
    if report.suggestions:
        print(f"\n💡 整体建议:")
        for s in report.suggestions:
            print(f"  • {s}")
    
    print("\n" + "=" * 60)
    print("✓ AI 审查完成！")
    print("=" * 60)
    
    # 5. 输出 JSON 格式报告
    print(f"\n📄 JSON 格式报告:")
    print(report.to_json()[:500] + "...")


if __name__ == "__main__":
    test_ai_review()
