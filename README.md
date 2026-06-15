# 澳门城市大学校园助手

一个可直接交给 AI 使用的澳门城市大学校园知识包，覆盖招生、注册、签注、宿舍、费用、校园生活，以及数据科学学院的课程和毕业要求。

> 资料整理日期：2026-05-22。报名时间、费用、宿舍、签注等信息可能变化，请以学校和澳门政府最新公告为准。

## 三步开始使用

中国大陆用户**不需要 Claude，不需要安装 Git、Node.js 或 MCP**。

### 第一步：下载一个文件

点击：

**[下载/打开合并知识库 `cityu-campus-assistant.md`](dist/cityu-campus-assistant.md)**

进入文件页面后，点击右上角下载按钮。也可以在仓库首页选择 `Code -> Download ZIP`，解压后找到：

```text
dist/cityu-campus-assistant.md
```

### 第二步：上传到常用 AI

任选一个可以上传文件的工具：

- Kimi
- DeepSeek
- 豆包
- 智谱清言

新建对话，点击输入框旁边的 `+`、回形针或“上传文件”，上传刚才下载的 Markdown 文件。

### 第三步：发送这句话

```text
请阅读我上传的澳门城市大学校园助手知识库。回答时优先依据文件内容；
涉及报名日期、费用、宿舍、签注和毕业要求时，提醒我以最新官方通知为准；
如果文件中没有答案，请明确说不知道，不要编造。
```

然后可以直接提问：

- 澳门城市大学内地本科怎么报名？
- 新生注册和 D 签注是什么流程？
- 宿舍费和学费是多少？
- 数据科学硕士毕业需要发表论文吗？
- 计算机科学学士有哪些方向？

## 推荐方式

| 使用需求 | 推荐方案 | 难度 |
|---|---|---:|
| 偶尔查询，马上使用 | 上传合并知识库到 Kimi、DeepSeek、豆包或智谱清言 | 最简单 |
| 长期使用或多人共享 | Open WebUI / Dify 知识库 + 国产模型 API | 中等 |
| 不希望文件上传云端 | Ollama + Qwen + Open WebUI | 较高 |
| 已经使用 MCP 客户端 | Filesystem MCP 读取仓库目录 | 较高 |

完整操作见 **[中国地区安装与使用指南](docs/INSTALL_CN.md)**。

## 文件说明

| 文件 | 用途 |
|---|---|
| [`dist/cityu-campus-assistant.md`](dist/cityu-campus-assistant.md) | 已合并，可直接上传给 AI |
| [`SKILL.md`](SKILL.md) | 助手角色、回答规则和知识索引 |
| [`knowledge-base/freshman.md`](knowledge-base/freshman.md) | 招生、注册、签注、宿舍、费用和校园生活 |
| [`knowledge-base/fds.md`](knowledge-base/fds.md) | 数据科学学院课程、毕业、论文和导师信息 |

## 更新合并文件

知识库维护者修改源文件后，可重新生成 `dist/cityu-campus-assistant.md`。

Windows PowerShell：

```powershell
.\scripts\build-knowledge.ps1
```

macOS / Linux：

```bash
sh scripts/build-knowledge.sh
```

普通使用者不需要运行这些命令。

## 关于 Claude

Claude 不是中国大陆用户的默认安装方案。根据 Anthropic 的[官方可用地区列表](https://support.anthropic.com/en/articles/8461763-where-can-i-access-claude-ai)，截至 2026-03-16，中国大陆不在支持地区内。

本项目不要求 Claude，也不会引导用户绕过服务地区限制。身处官方支持地区且已合法使用 Claude Desktop 的用户，可参考详细指南中的 MCP 附录。

## 重要声明

- 本项目是知识文件集合，不是澳门城市大学官方服务，也不是一个独立运行的 MCP Server。
- AI 回答不能替代学校、学院、招生事务处、教务处、财务部或澳门政府的正式答复。
- 不要把身份证、录取通知书、通行证、签注、缴费凭证等敏感文件和本知识库一起上传。
- 不承诺录取、奖学金、宿位、签注审批、论文认定或毕业结果。

## License

[MIT License](LICENSE)
