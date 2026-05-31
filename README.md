# AI PR Reviewer 🤖

> 七牛云 XEngineer 暑期实训营参赛项目
> ✅ 开发完成

基于大语言模型的 GitHub Pull Request 自动代码审查工具。

输入 GitHub PR URL，自动获取代码变更，通过 **DeepSeek-V4 Flash** 生成结构化 Review 建议（风险等级分类 + 行级定位 + 修改建议），并可一键发布审查结果到 GitHub PR。

## ✨ 功能特性

- 🔍 **智能代码审查**：基于 DeepSeek 多维度分析 PR 代码变更
- ⚡🎯 **多模型切换**：支持 DeepSeek V4 Flash（快速）与 V4 Pro（高精度）一键切换
- 📍 **行级精准定位**：问题精确标注到代码行，附上下文展示（▶ 标记目标行）
- 📝 **自定义审查规则**：`.pr-reviewer.json` 自定义审查维度、忽略模式、自定义规则
- 📦 **大 PR 自动分块**：Diff 超长时按文件边界自动拆分，结果智能合并去重
- 📋 **审查历史**：侧栏展示历史记录，点击恢复任意一次审查结果
- 🌙 **深色/浅色主题**：侧栏一键切换，CSS 实时注入无需刷新
- 📤 **一键发布到 PR**：审查结果以 GitHub Review 形式回写（含行级 inline comments）
- 📄 **导出报告**：支持 Markdown / HTML 格式，可直接打印 PDF
- 🧪 **离线 Mock 模式**：无需 API 即可体验完整审查流程（适合演示）

## 技术栈

- **后端**：Python + FastAPI
- **前端**：Streamlit
- **AI 模型**：DeepSeek V4 Flash（默认）/ V4 Pro（高精度可切换）
- **GitHub API**：requests（原生 REST API，支持代理）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

复制配置模板并填入你的 API Key：

```bash
cp config/config.example.json config.json
# 编辑 config.json，填入 DeepSeek API Key
```

或在环境变量中设置：

```bash
export DEEPSEEK_API_KEY="your-api-key"
export GITHUB_TOKEN="your-github-token"   # 可选，用于发布 Review 到 PR
```

### 3. 启动 Streamlit 前端

```bash
streamlit run src/ui/streamlit_app.py
```

浏览器访问 `http://localhost:8501`

### 4. 使用示例

在界面中输入 GitHub PR URL（如 `https://github.com/microsoft/vscode/pull/7559`），点击「开始审查」即可。

## 项目结构

```
ai-pr-reviewer/
├── README.md
├── requirements.txt
├── .gitignore
├── config/
│   └── config.example.json
├── .pr-reviewer.example.json   # 审查规则配置模板
├── src/
│   ├── api/          # FastAPI 后端（可选）
│   ├── core/         # 核心逻辑
│   │   ├── github_client.py   # GitHub REST API 封装（代理/重试）
│   │   ├── diff_parser.py     # Diff 解析 + 行号标注
│   │   ├── ai_reviewer.py    # AI 审查器（Prompt 工程 + API 调用）
│   │   ├── rule_config.py    # 审查规则配置加载器
│   │   └── export_report.py  # 报告导出（Markdown + HTML）
│   ├── models/       # 数据模型（ReviewReport / ReviewIssue）
│   └── ui/          # Streamlit 前端
├── tests/
└── docs/
```

## 审查规则配置

在项目根目录创建 `.pr-reviewer.json` 可自定义审查行为：

```json
{
  "rules": {
    "security": { "enabled": true, "description": "安全检查" },
    "correctness": { "enabled": true },
    "performance": { "enabled": true },
    "code_quality": { "enabled": true },
    "best_practices": { "enabled": true }
  },
  "custom_rules": [
    { "name": "禁止 print 调试", "description": "...", "severity": "warning" }
  ],
  "ignore_patterns": ["*.md", "*.json", "vendor/*"]
}
```

## 开发进度

- [x] 项目初始化 + GitHub API 对接（代理/重试）
- [x] Diff 解析 + 行号标注
- [x] DeepSeek API 调用 + Prompt 工程
- [x] Streamlit Web 界面 + 离线 Mock 模式
- [x] 行级精准定位（代码上下文 + ▶ 行标记）
- [x] 自定义审查规则（.pr-reviewer.json）
- [x] 大 PR Diff 自动分块处理
- [x] PR 评论回写（行级 inline comments）
- [x] 导出 Markdown / HTML 报告
- [x] 多模型切换（V4 Flash / V4 Pro）
- [x] 审查历史侧栏（恢复/清空）
- [x] 深色/浅色主题切换 + UI 打磨

## 许可证

MIT

---

**作者**：Peachy-Peahces  
**参赛项目**：七牛云 XEngineer 暑期实训营（2026）
