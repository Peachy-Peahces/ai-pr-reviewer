import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
测试 diff_parser.py 模块

使用之前 github_client 获取的 diff 测试解析功能
"""

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.github_client import GitHubClient
from src.core.diff_parser import DiffParser


def test_with_real_pr():
    """使用真实 PR 测试 diff 解析"""
    
    print("=" * 60)
    print("测试 diff_parser.py")
    print("=" * 60)
    
    # 1. 先获取 PR diff（用之前的 github_client）
    print("\n[步骤 1] 获取 PR diff...")
    
    client = GitHubClient()  # 不需要 token，公开仓库
    
    # 使用 microsoft/vscode PR 7559 测试
    pr_url = "https://github.com/microsoft/vscode/pull/7559"
    diff_text = client.fetch_pr_diff(pr_url)
    
    if not diff_text:
        print("❌ 获取 diff 失败（网络不可达）")
        return
    print(f"✓ 获取成功，diff 长度: {len(diff_text)} 字符")
    
    # 2. 解析 diff
    print("\n[步骤 2] 解析 diff...")
    
    parser = DiffParser(diff_text)
    file_diffs = parser.parse()
    
    print(f"✓ 解析成功，共 {len(file_diffs)} 个文件")
    
    # 3. 显示每个文件的详细信息
    print("\n[步骤 3] 文件详情:")
    print("-" * 60)
    
    for i, file_diff in enumerate(file_diffs, 1):
        print(f"\n文件 {i}: {file_diff.filename}")
        print(f"  状态: {file_diff.status}")
        print(f"  新增: +{file_diff.additions} 行")
        print(f"  删除: -{file_diff.deletions} 行")
        print(f"  diff 长度: {len(file_diff.diff_content)} 字符")
        
        # 显示前 300 字符
        preview = file_diff.diff_content[:300].replace('\n', '\n  ')
        print(f"  预览:\n  {preview}...")
    
    # 4. 获取摘要
    print("\n[步骤 4] 摘要信息:")
    print("-" * 60)
    
    summary = parser.get_summary()
    print(f"变更文件数: {summary['files_changed']}")
    print(f"总新增行: +{summary['total_additions']}")
    print(f"总删除行: -{summary['total_deletions']}")
    
    print("\n" + "=" * 60)
    print("✓ 所有测试通过！")
    print("=" * 60)


def test_with_sample_diff():
    """使用示例 diff 测试（不依赖网络）"""
    
    print("\n" + "=" * 60)
    print("离线测试：使用内置示例 diff")
    print("=" * 60)
    
    # 一个简单的示例 diff
    sample_diff = """diff --git a/src/main.py b/src/main.py
index abc1234..def5678 100644
--- a/src/main.py
+++ b/src/main.py
@@ -10,6 +10,8 @@ def hello():
     print("hello")
 
 def world():
+    # 新增注释
+    print("added line 1")
     print("world")
 
diff --git a/src/utils.py b/src/utils.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/src/utils.py
@@ -0,0 +1,5 @@
+def helper():
+    # 辅助函数
+    return 42
+
+# end of file
"""
    
    parser = DiffParser(sample_diff)
    file_diffs = parser.parse()
    
    print(f"\n解析结果: {len(file_diffs)} 个文件")
    
    for f in file_diffs:
        print(f"\n- {f.filename}")
        print(f"  状态: {f.status}, +{f.additions}/-{f.deletions}")
    
    summary = parser.get_summary()
    print(f"\n摘要: {summary['files_changed']} 文件, +{summary['total_additions']}/-{summary['total_deletions']}")
    
    print("\n✓ 离线测试通过！")


if __name__ == "__main__":
    # 先测试离线版本（不需要网络）
    test_with_sample_diff()
    
    # 再测试真实 PR（需要网络和代理）
    print("\n\n" + "=" * 60)
    print("接下来测试真实 PR（需要网络）...")
    print("=" * 60)
    
    try:
        test_with_real_pr()
    except Exception as e:
        print(f"\n❌ 真实 PR 测试失败: {e}")
        print("可能原因: 网络问题 / 未设置代理")
        print("请先设置代理:")
        print('  $env:HTTP_PROXY="http://127.0.0.1:7897"')
        print('  $env:HTTPS_PROXY="http://127.0.0.1:7897"')
