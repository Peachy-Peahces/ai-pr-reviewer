"""测试 GitHub Client - 获取真实 PR 的 diff"""
from src.core.github_client import GitHubClient

# 使用真实存在的公开 PR
TEST_PR_URL = "https://github.com/microsoft/vscode/pull/7559"

def test_github_client():
    print("测试 GitHub Client...")
    
    # 不传 token（匿名访问，有 rate limit）
    client = GitHubClient()
    
    # 1. 测试 URL 解析
    print("\n1. 测试 URL 解析...")
    parsed = client.parse_pr_url(TEST_PR_URL)
    if parsed:
        print(f"解析成功: {parsed}")
    else:
        print("解析失败")
        return
    
    # 2. 测试获取 PR 信息
    print("\n2. 测试获取 PR 信息...")
    pr_info = client.fetch_pr_info(TEST_PR_URL)
    if pr_info:
        print(f"PR 标题: {pr_info['title']}")
        print(f"  作者: {pr_info['author']}")
        print(f"  变更文件数: {pr_info['changed_files']}")
    else:
        print("获取 PR 信息失败")
        return
    
    # 3. 测试获取 PR diff
    print("\n3. 测试获取 PR diff...")
    diff = client.fetch_pr_diff(TEST_PR_URL)
    if diff:
        print(f"Diff 获取成功，长度: {len(diff)} 字符")
        print(f"  前 200 字符:\n{diff[:200]}...")
    else:
        print("获取 diff 失败")
        return
    
    # 4. 测试获取文件列表
    print("\n4. 测试获取文件列表...")
    files = client.fetch_pr_files(TEST_PR_URL)
    if files:
        print(f"获取到 {len(files)} 个文件:")
        for f in files[:3]:  # 只显示前3个
            print(f"   - {f['filename']} ({f['status']}, +{f['additions']} -{f['deletions']})")
    else:
        print("获取文件列表失败")
        return
    
    print("\n所有测试通过！")

if __name__ == "__main__":
    test_github_client()
