# 澳门城市大学校园助手 Skill

这是一个给 AI Agent 使用的澳门城市大学问答 Skill。安装后，你可以直接问它：

- 新生注册、学费、宿舍、D 签注、逗留许可怎么处理
- 数据科学学院 FDS 的课程、学分、论文成果和毕业要求
- 台风、暴雨等恶劣天气下学校怎么安排

它只整理公开资料，不替学校做录取、签注、转专业、论文认定或毕业审批。

## 最简单安装方法

把下面这段话复制给你正在使用的 AI Agent：

```text
请帮我安装这个 Skill：
https://github.com/anmdd1031/cityu-macau-campus-assistant

安装完成后，请告诉我安装位置，并确认 SKILL.md 可以被识别。
```

如果 Agent 问你安装到哪里：

- 只想在当前项目用：选“当前项目”。
- 想以后都能用：选“全局”或“用户级”。

安装后，重新打开 Agent 或开始一个新会话。

## 中国大陆用户怎么选 Agent

优先选择中国大陆可用的 Agent，例如：

- Qwen Code
- Kimi Code CLI
- CodeBuddy
- WorkBuddy
- 通义灵码 Lingma
- Trae 中国版
- Qoder 中国版
- CodeArts Agent
- iFlow CLI

Claude、ChatGPT / Codex、Gemini 在中国大陆有官方地区限制，不建议作为大陆默认方案。

更多 Agent、安装目录和限制说明见：[详细说明](docs/guide.md)。

## 手动安装

如果 Agent 不会自动安装，可以手动放置：

1. 打开本仓库，点击 **Code > Download ZIP**。
2. 解压 ZIP。
3. 找到这个文件夹：

   ```text
   skills/cityu-macau-campus-assistant/
   ```

4. 把整个 `cityu-macau-campus-assistant` 文件夹放进你的 Agent 的 Skills 目录。

常见目录：

| Agent | 放置目录 |
|---|---|
| Codex / Cline / Kimi Code CLI | `.agents/skills/` |
| Qwen Code | `.qwen/skills/` |
| Claude Code | `.claude/skills/` |
| Gemini CLI | `.gemini/skills/` 或 `.agents/skills/` |
| CodeBuddy | `.codebuddy/skills/` |
| Lingma | `.lingma/skills/` |
| Trae 中国版 | `.trae/skills/` |
| Qoder 中国版 | `.qoder/skills/` |

最终结构应该长这样：

```text
你的项目/
└── .agents/
    └── skills/
        └── cityu-macau-campus-assistant/
            ├── SKILL.md
            ├── agents/
            │   └── openai.yaml
            └── references/
                ├── freshman.md
                └── fds.md
```

不要只复制 `SKILL.md`，否则知识库不会一起生效。

## 怎么使用

安装后可以直接问：

```text
澳门城市大学内地本科新生拿到学号后还要完成哪些注册步骤？
```

也可以指定这个 Skill：

```text
使用 $cityu-macau-campus-assistant 查询 MDS 的学分和成果要求。
```

## 这个 Skill 能做什么

可以：

- 整理公开的申请、注册、宿舍、签注和校园办事流程
- 解释 FDS 公开课程、学分、论文成果和毕业要求
- 提醒哪些信息需要看最新官方通知

不可以：

- 保证录取、奖学金、宿位、签注、转专业或毕业
- 代替学校做个案审批
- 查询个人成绩、课表、考场或私人账号
- 代替法律、移民、财务或医疗意见

## 更多说明

- [详细安装与 Agent 说明](docs/guide.md)
- [Skill 主文件](skills/cityu-macau-campus-assistant/SKILL.md)
- [新生与校园知识库](skills/cityu-macau-campus-assistant/references/freshman.md)
- [数据科学学院知识库](skills/cityu-macau-campus-assistant/references/fds.md)

> 知识库资料核验日期：2026-05-22。招生日期、费用、宿舍、签注、注册和学业规则以最新官方通知为准。

## License

[MIT](LICENSE)
