# 更新日志

本文件记录 `cityu-macau-campus-assistant` Skill 的主要更新。只记录影响 Skill 使用、知识库范围、安装方式、路由规则或文档入口的变化；普通文字润色不必逐条记录。

## 2026-07-11

### FDS 导师推荐功能

- 新增 `references/fds_faculty.md`，基于数据科学学院官网 6 页 Academic Staff 列表及教师个人页，收录 58 名本校学术人员。
- 为教师记录中英文姓名、职称与职务、官网明确导师资格、多个标准化研究方向、方向依据、官方主页及官网公开的个人主页。
- 明确排除 Academic Advisors、External Instructors 和行政人员，不在知识库复制邮箱、电话或办公室信息。
- 新增零第三方依赖的 `scripts/update_fds_faculty.py`，支持重新抓取和 `--check` 漂移检查，并将无法可靠提取的项目列入人工复核记录。
- 更新 `SKILL.md` 的导师路由、3 至 5 人展示规则、完整名单规则和招生边界；同步更新 README、详细说明与 Agent 展示文案。

## 2026-07-02

### 新增知识库

- 同步新增国际旅游与管理学院知识库：
  - `references/fitm.md`
- 覆盖内容包括：
  - 国际旅游与酒店管理学士
  - 国际款待与旅游业管理硕士
  - 国际酒店管理硕士
  - 国际旅游管理博士
  - 酒店管理博士
  - 导师、项目报告、论文、学分和毕业要求
- 同步更新 `SKILL.md` 路由表、根目录 [README](../README.md) 与 [docs/guide.md](guide.md) 知识库清单。

## 2026-06-23

### 新增知识库

- 同步新增教育学院知识库：
  - `references/fe.md`
- 同步新增法学院知识库：
  - `references/fl.md`
- 同步新增荣誉班知识库：
  - `references/honours_class.md`
- 覆盖内容包括：
  - 教育学院教育学硕士、教学研究硕士、教育学博士、导师、论文和毕业要求
  - 法学院法学硕士、专业方向、导师、论文和毕业要求
  - 荣誉班选拔、课程体系、导师指导、科研训练、实习、竞赛和毕业条件
- 同步更新 `SKILL.md` 路由表、根目录 [README](../README.md) 与 [docs/guide.md](guide.md) 知识库清单。

### 高变动数据回答规则

- 优化 `SKILL.md` 的边界说明，明确“学费、校历、开学时间、注册日程等高变动信息不等于不能回答”。
- 要求 Agent 在 reference 已有数据、表格、日期或官方入口时，先给出知识库中的公开参考值，再标明资料版本、适用对象、币种、学年和最终确认入口。
- 扩展通用知识库路由关键词，加入学费、收费表、校历、行事历、开学、下学期、上课时间和注册日程。
- 针对“各学院学费是多少”“下学期几月开学”等问题，增加明确处理方式，减少 Agent 因边界过严而直接拒答。

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
| 教育学院 FE/SOE | `references/fe.md` | 已覆盖 |
| 法学院 FL/SOL | `references/fl.md` | 已覆盖 |
| 国际旅游与管理学院 FITM | `references/fitm.md` | 已覆盖 |
| 荣誉班 Honours Class | `references/honours_class.md` | 已覆盖 |
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
