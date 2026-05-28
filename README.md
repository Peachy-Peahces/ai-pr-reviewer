# AI PR Reviewer 🤖

> 七牛云 XEngineer 暑期实训营参赛项目
> 开发进行中，预计 2026-05-30 完成

基于大语言模型的 GitHub Pull Request 自动代码审查工具。

输入 GitHub PR URL，自动获取代码变更，通过 **DeepSeek-V4 Flash** 生成结构化 Review 建议（风险等级分类 + 修改建议）。

## 技术栈

- **后端**：Python + FastAPI
- **前端**：Streamlit
- **AI 模型**：DeepSeek-V4 Flash（轻量版，低成本高性能）
- **GitHub API**：PyGithub

## 当前进度

- [x] 项目初始化
- [ ] GitHub API 对接
- [ ] Diff 解析与分块
- [ ] DeepSeek API 调用
- [ ] Web 界面开发
- [ ] 测试与优化
- [ ] Demo 录制

## 快速开始

（待核心功能完成后补充）

## 项目结构

```
ai-pr-reviewer/
├── README.md
├── requirements.txt
├── .gitignore
├── config/
│   └── config.example.json
├── src/
│   ├── api/          # FastAPI 后端
│   ├── core/         # 核心逻辑（GitHub客户端、AI审查器、Diff解析）
│   ├── models/       # 数据模型
│   └── ui/           # Streamlit 前端
├── tests/
└── docs/
```

---

**作者**：Peachy-Peaches
**参赛项目**：七牛云 XEngineer 暑期实训营（2026）
