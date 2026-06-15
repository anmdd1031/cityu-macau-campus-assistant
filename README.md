# 澳门城市大学校园助手 Skill

可重复安装的澳门城市大学校园问答 Skill，覆盖招生、注册、D 签注、逗留许可、宿舍、费用、校园生活，以及数据科学学院课程、论文和毕业要求。

> 资料核验日期：2026-05-22。报名、费用、宿舍、签注和学业规则等高时效信息仍需以最新官方通知为准。

## 推荐：安装为 Skill

安装一次后，可以在不同对话中反复调用，不需要每次重新上传知识文件。

### Codex 安装

在 Codex 中发送：

```text
请使用 skill-installer 安装这个 Skill：
https://github.com/anmdd1031/cityu-macau-campus-assistant/tree/main/skills/cityu-macau-campus-assistant
```

安装完成后重启 Codex。然后直接提问，或显式调用：

```text
使用 $cityu-macau-campus-assistant 告诉我内地新生注册和 D 签注的流程。
```

```text
使用 $cityu-macau-campus-assistant 查询数据科学硕士的论文发表要求。
```

### 其他兼容 Agent Skills 的客户端

1. 下载本仓库 ZIP 并解压。
2. 找到 [`skills/cityu-macau-campus-assistant`](skills/cityu-macau-campus-assistant)。
3. 将整个文件夹复制到客户端的 Skills 目录。
4. 重启客户端。

必须复制整个文件夹，保留以下结构：

```text
cityu-macau-campus-assistant/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── references/
    ├── freshman.md
    └── fds.md
```

## Skill 如何重复工作

- `SKILL.md` 定义触发条件、资料路由、核验规则和回答格式。
- `references/freshman.md` 按需提供招生、注册、签注、宿舍、费用和校园生活资料。
- `references/fds.md` 按需提供数据科学学院课程、论文、导师和毕业要求。
- Agent 根据每次问题只检索相关章节，不需要把全部知识库塞进每轮对话。
- `agents/openai.yaml` 提供 Skill 列表名称、简介和默认调用提示。

## 不支持 Skills？使用单文件版

Kimi、DeepSeek、豆包、智谱清言等支持文件上传的工具，可以使用：

**[合并知识库 `dist/cityu-campus-assistant.md`](dist/cityu-campus-assistant.md)**

上传后发送：

```text
请优先依据我上传的澳门城市大学校园助手知识库回答。
涉及报名日期、费用、宿舍、签注和毕业要求时，提醒我以最新官方通知为准；
文件中没有答案时请明确说明，不要编造。
```

这种方式只在当前对话或知识库中生效，不等同于安装可重复使用的 Skill。

## 适用问题

- 澳门城市大学内地本科怎么报名？
- 新生注册、体检和 D 签注是什么流程？
- 宿舍费和学费是多少？
- 数据科学硕士毕业需要发表论文吗？
- 计算机科学学士有哪些方向？
- 这个问题应该联系招生事务处、教务处还是学院？

## 项目结构

| 路径 | 用途 |
|---|---|
| [`skills/cityu-macau-campus-assistant`](skills/cityu-macau-campus-assistant) | 可直接安装的标准 Skill |
| [`dist/cityu-campus-assistant.md`](dist/cityu-campus-assistant.md) | 不支持 Skills 客户端使用的合并文件 |
| [`docs/INSTALL_CN.md`](docs/INSTALL_CN.md) | 中国地区完整安装和兼容方案 |
| [`scripts`](scripts) | 维护者生成合并文件的脚本 |
| [`tests/verify-package.ps1`](tests/verify-package.ps1) | Skill 与发布包契约验证 |

## 中国地区说明

本 Skill 不依赖 Claude。中国大陆用户可以使用 Codex、支持 Agent Skills 的客户端、国内模型知识库，或单文件上传方式。

根据 Anthropic 的[官方可用地区列表](https://support.anthropic.com/en/articles/8461763-where-can-i-access-claude-ai)，截至 2026-03-16，中国大陆不在 Claude 支持地区内，因此 Claude 不作为默认方案。

## 维护

更新 `skills/cityu-macau-campus-assistant/references/` 后重新生成单文件版：

```powershell
.\scripts\build-knowledge.ps1
```

验证：

```powershell
.\tests\verify-package.ps1
```

## 重要声明

- 本项目不是澳门城市大学官方服务。
- AI 回答不能替代学校、学院或澳门政府的正式答复。
- 不要提供身份证、通行证、录取通知书条码、缴费凭证、签注页或入境凭条等敏感信息。
- 不承诺录取、奖学金、宿位、签注审批、论文认定、转专业或毕业结果。

## License

[MIT License](LICENSE)
