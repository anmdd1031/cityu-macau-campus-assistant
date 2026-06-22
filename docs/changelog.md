# 更新日志

本文件记录 `cityu-macau-campus-assistant` Skill 的主要更新。只记录影响 Skill 使用、知识库范围、安装方式、路由规则或文档入口的变化；普通文字润色不必逐条记录。

## 2026-06-22

### README 与安装入口

- 将根目录 `README.md` 调整为面向普通用户的傻瓜式安装说明。
- 保留简短安装入口，把 Agent 选择、手动放置、地区限制和维护说明放到 [详细说明](guide.md)。
- 更新 README 开头说明，强调本项目是面向 AI Agent 的澳门城市大学公开信息 Skill。
- 增加开发者信息：蔡剑平教授、金添、李俞萱、金泽同。
- 将最简单安装路径调整为 WorkBuddy 微信小程序使用场景。

### 金融学院知识库

- 新增金融学院知识库：
  - `references/fof.md`
- 覆盖内容包括：
  - 应用经济学学士 BAE
  - 金融精英班
  - 金融学硕士
  - 金融科技硕士
  - 金融学博士
  - 导师、论文发表、学分和毕业要求

### Skill 路由

- 更新 `SKILL.md` 的触发描述，覆盖：
  - 招生、注册、费用、宿舍、签注、校园服务、恶劣天气
  - 校内餐饮
  - 数据科学学院、商学院、金融学院、大健康学院课程与毕业要求
- 增加 reference 路由表：
  - 通用校园问题读取 `freshman.md`
  - 餐饮问题读取餐饮指南
  - FDS 问题读取 `fds.md`
  - FOB 问题读取 `fob.md`
  - FOF 问题读取 `fof.md`
  - FH 问题读取 `fh.md`
- 更新 `agents/openai.yaml`，让安装器展示描述覆盖招生注册、校园服务、餐饮和多学院课程毕业要求。

### 详细说明

- 重写 [docs/guide.md](guide.md)，明确：
  - 已有知识库清单
  - 待补学院知识库清单
  - 中国大陆地区限制说明
  - 通用命令安装和手动放置方式
  - 更新规则与验证方式
- 待补学院或机构包括：
  - 人文社会科学学院
  - 创新设计学院
  - 国际旅游与管理学院
  - 教育学院
  - 法学院
  - 葡语国家研究院
  - 城市与可持续发展研究院

### 验证

- 使用 `npx skills add . --list` 验证本地仓库可识别 1 个 Skill：`cityu-macau-campus-assistant`。
- 检查 Markdown 相对链接可访问。
- 检查 `docs/superpowers` 和 `.superpowers` 未被纳入版本控制。

## 2026-06-21

### 新增知识库

- 新增商学院知识库：
  - `references/fob.md`
- 新增大健康学院知识库：
  - `references/fh.md`
- 新增并更新氹仔校区校内餐饮指南：
  - `references/澳门城市大学氹仔校区_校内餐饮指南.md`

这些资料随后在 2026-06-22 被同步进标准 Skill 目录，并加入 `SKILL.md` 的路由表。

## 2026-06-15

### Skill 标准化与安装文档

- 将项目整理为可复用 Agent Skill，标准结构为：

  ```text
  skills/cityu-macau-campus-assistant/
  ├── SKILL.md
  ├── agents/
  │   └── openai.yaml
  └── references/
  ```

- 删除内部规划材料，避免把过程文件作为 Skill 内容发布。
- 将 `SKILL.md` 精简为路由和边界说明，将详细资料放入 `references/`。
- 恢复并扩展新生与数据科学学院知识库：
  - `references/freshman.md`
  - `references/fds.md`
- 增加面向中国地区用户的安装说明和 Agent 适配说明。
- 验证仓库根目录可作为安装目标。

## 2026-05-25

### 初始知识库与 Skill 雏形

- 创建项目初始文件。
- 创建早期 `skill.md` / `SKILL.md`。
- 创建早期 `README.md`。
- 创建新生知识库 `freshman.md`。
- 创建数据科学学院知识库 `fds.md`。

## 当前知识库范围

| 知识库 | 文件 | 状态 |
|---|---|---|
| 新生与校园通用知识库 | `references/freshman.md` | 已覆盖 |
| 数据科学学院 FDS | `references/fds.md` | 已覆盖 |
| 商学院 FOB | `references/fob.md` | 已覆盖 |
| 金融学院 FOF | `references/fof.md` | 已覆盖 |
| 大健康学院 FH | `references/fh.md` | 已覆盖 |
| 氹仔校区餐饮指南 | `references/澳门城市大学氹仔校区_校内餐饮指南.md` | 已覆盖 |

## 维护规则

每次更新 Skill 时，至少检查：

- `skills/cityu-macau-campus-assistant/SKILL.md`
- `skills/cityu-macau-campus-assistant/agents/openai.yaml`
- `skills/cityu-macau-campus-assistant/references/`
- `README.md`
- `docs/guide.md`
- 本更新日志

新增学院知识库时，应同步记录：

- 新增文件名
- 覆盖学院或课程
- 资料核验日期
- 是否同步更新 `SKILL.md` 路由
- 是否通过 `npx skills add . --list` 验证
