# 澳门城市大学校园助手 Skill

面向澳门城市大学学生与申请人的可复用 Agent Skill，覆盖：

- 招生、学费、注册、D 签注、逗留许可、宿舍与校园服务
- 数据科学学院本硕博课程、学分、论文发表与毕业要求

## 安装

在 Codex 中发送：

```text
请使用 skill-installer 安装：
https://github.com/anmdd1031/cityu-macau-campus-assistant/tree/main/skills/cityu-macau-campus-assistant
```

重启 Codex 后直接提问，或显式调用：

```text
使用 $cityu-macau-campus-assistant 查询内地新生注册和 D 签注流程。
```

其他兼容 Agent Skills 的客户端，可将
[`skills/cityu-macau-campus-assistant`](skills/cityu-macau-campus-assistant)
复制到其 Skills 目录。

## 结构

```text
skills/cityu-macau-campus-assistant/
├── SKILL.md
├── agents/openai.yaml
└── references/
    ├── freshman.md
    └── fds.md
```

Skill 会按问题类型读取对应 reference，不会把全部资料注入每次对话。

## 中国地区

本 Skill 不依赖 Claude，可由 Codex 或其他兼容客户端配合所在地可用模型使用。Claude 不作为中国大陆默认方案。

> 资料核验日期：2026-05-22。报名、费用、宿舍、签注与学业规则以最新官方通知为准。

## License

[MIT](LICENSE)
