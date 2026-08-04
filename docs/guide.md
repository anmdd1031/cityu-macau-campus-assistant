# 澳城大校园资讯智能体详细说明

这是根目录 [README](../README.md) 的详细版。根目录 README 只保留傻瓜式安装；本文件用于说明智能体的能力边界、知识库覆盖情况、各类 Agent 适配方式和维护规则。

## 这个智能体是什么

`cityu-macau-campus-assistant` 是一个面向澳门城市大学公开信息的 Agent 知识与规则包。它不是学校官方系统，也不是一个独立应用；核心文件是：

```text
skills/cityu-macau-campus-assistant/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── references/
```

Agent 被触发后，会先读取 [SKILL.md](../skills/cityu-macau-campus-assistant/SKILL.md)，再按问题读取 `references/` 中对应的知识库。

## 可以回答什么

可以回答：

- 新生申请、注册、缴费、体检、D 签注、逗留许可、宿舍、图书馆、校园服务和恶劣天气安排。
- 数据科学学院、商学院、金融学院、大健康学院、教育学院、法学院、国际旅游与管理学院、人文社会科学学院、创新设计学院、城市与可持续发展研究院、葡语国家研究院及荣誉班的课程、学分、导师、论文、发表、毕业要求和常见办事入口。
- 按官网研究方向、导师资格及官网公开的科研经历、项目和成果筛选数据科学学院教师，并提供可核验的校内工作邮箱与主页索引。
- 氹仔校区校内餐厅、菜单、价格、供应时段和用餐建议。
- 哪些问题需要看最新官方通知，哪些只能由学校或学院审批。

不可以回答或不能承诺：

- 录取概率、奖学金概率、转专业成功率、宿位保证或毕业保证。
- 代替学校确认论文、学分、毕业资格、转专业、签注或逗留许可个案。
- 查询个人成绩、课表、考场、申请状态或登录 TronClass 等私人系统。
- 提供法律、移民、财务、医疗或投资建议。

## 知识库总览

| 知识库 | 文件 | 状态 | 用途 |
|---|---|---|---|
| 新生与校园通用知识库 | [freshman.md](../skills/cityu-macau-campus-assistant/references/freshman.md) | 已完成 | 招生、注册、学费、奖学金、体检、D 签注、逗留许可、宿舍、图书馆、全球交流、暑期项目、创业就业服务、校园服务、恶劣天气 |
| 数据科学学院 FDS | [fds.md](../skills/cityu-macau-campus-assistant/references/fds.md) | 已完成 | BITS、BCS、人工智能学士规划、MDS、MCS、人工智能硕士规划、PhD DS、PhD CS、招生状态、学分、资格考试、论文成果、导师、毕业 |
| FDS 导师基础画像 | [fds_mentors.md](../skills/cityu-macau-campus-assistant/references/mentors/fds_mentors.md) | 已完成 | 58 名 Academic Staff、中文官网职称/职务、导师资格、58 个可核验校内工作邮箱、官网研究方向、科研证据覆盖提示、招募说明和官方主页 |
| FDS 官网完整科研证据 | [fds_official_evidence.md](../skills/cityu-macau-campus-assistant/references/mentors/fds_official_evidence.md) | 已完成 | 58 名教师官网公开的完整科研经历、研究项目和论文成果栏目；按需读取，官网访问失败时可使用本地核验版本 |
| FDS 论文检索索引 | [fds_papers.md](../skills/cityu-macau-campus-assistant/references/mentors/fds_papers.md) | 暂时停用 | 仅为维护者保留，不参与 Agent 路由、回答或导师推荐 |
| FDS 导师匹配规则 | [fds_rules.md](../skills/cityu-macau-campus-assistant/references/mentors/fds_rules.md) | 已完成 | 官网准入、研究方向匹配、官方证据来源和回答边界 |
| 商学院 FOB | [fob.md](../skills/cityu-macau-campus-assistant/references/fob.md) | 已完成 | BBA、MBA、管理分析学硕士（MMA）、DBA、IBC、4+1 项目、导师、论文与毕业要求 |
| 金融学院 FOF | [fof.md](../skills/cityu-macau-campus-assistant/references/fof.md) | 已完成 | BAE、金融精英班、金融学硕士、金融科技硕士、金融学博士、导师、发表与毕业要求 |
| 大健康学院 FH | [fh.md](../skills/cityu-macau-campus-assistant/references/fh.md) | 已完成 | BSW、MSW、MAP、DAP、智慧养老与健康管理、导师、实习与毕业要求 |
| 教育学院 FE/SOE | [fe.md](../skills/cityu-macau-campus-assistant/references/fe.md) | 已完成 | 教育学硕士、教学研究硕士、教育学博士、教育博士（公开状态须确认）、学分、导师、论文与毕业要求 |
| 法学院 FL/SOL | [fl.md](../skills/cityu-macau-campus-assistant/references/fl.md) | 已完成 | 法学硕士、专业方向、学分、导师、论文与毕业要求 |
| 国际旅游与管理学院 FITM | [fitm.md](../skills/cityu-macau-campus-assistant/references/fitm.md) | 已完成 | 国际旅游与酒店管理、国际款待与旅游业管理、国际酒店管理、国际旅游管理、酒店管理、导师、项目报告、论文与毕业要求 |
| 人文社会科学学院 FHSS | [fhss.md](../skills/cityu-macau-campus-assistant/references/fhss.md) | 已完成 | 应用语言学、英语、葡萄牙语、中国文化研究、文化产业管理与文化产业研究课程、学分、论文与毕业要求 |
| FHSS 师资索引 | [fhss_faculty.md](../skills/cityu-macau-campus-assistant/references/faculty/fhss_faculty.md) | 已完成 | 中文官网当前58名全职、9名特聘、5名兼任学术人员，管理团队、课程督导和公开研究方向 |
| 创新设计学院 FIAD | [fiad.md](../skills/cityu-macau-campus-assistant/references/fiad.md) | 已完成 | 设计艺术、设计学、艺术学本硕博课程、学分、学术活动、成果发表、导师与毕业要求 |
| FIAD 师资索引 | [fiad_faculty.md](../skills/cityu-macau-campus-assistant/references/faculty/fiad_faculty.md) | 已完成 | 中文官网当前25名全职教学人员、6名特聘教授、课程负责人和课程督导 |
| 城市与可持续发展研究院 IUSD | [iusd.md](../skills/cityu-macau-campus-assistant/references/iusd.md) | 已完成 | 城市规划与设计硕博课程、学分、资格考试、2025级学术活动与成果规则、导师、表格和毕业要求 |
| 葡语国家研究院 IROPC | [iropc.md](../skills/cityu-macau-campus-assistant/references/iropc.md) | 已完成 | 葡语国家研究硕博、国际关系与政府治理硕士、学分、开题、论文、人员、文件和毕业流程 |
| 荣誉班 Honours Class | [honours_class.md](../skills/cityu-macau-campus-assistant/references/honours_class.md) | 已完成 | 选拔、课程体系、导师指导、科研训练、实习、竞赛与毕业条件 |
| 氹仔校区餐饮指南 | [澳门城市大学氹仔校区_校内餐饮指南.md](../skills/cityu-macau-campus-assistant/references/澳门城市大学氹仔校区_校内餐饮指南.md) | 已完成 | 2026 年 6 月菜单和价格快照、用餐建议；实时状态须以现场或平台为准 |

## 路由规则

| 用户问题 | 应读取 |
|---|---|
| 招生、费用、注册、D 签注、逗留许可、宿舍、全球交流、暑期项目、创业就业服务、校外实习机会、校园服务、台风、暴雨 | `freshman.md` |
| 氹仔校区食堂、餐厅、菜单、价格、咖啡、打包、午餐 | `澳门城市大学氹仔校区_校内餐饮指南.md` |
| FDS 教师名单、导师资格、官方邮箱、联系方式或教师主页 | `references/mentors/fds_mentors.md` |
| FDS 导师推荐、教师研究方向或谁研究某个主题 | `references/mentors/fds_rules.md` + `references/mentors/fds_mentors.md` |
| FDS 完整科研经历、研究项目、官网论文成果或官网访问失败时查询本地资料 | 在上述文件基础上按需读取 `references/mentors/fds_official_evidence.md` |
| FDS 具体论文、论文成果或项目经历 | 只按需读取 `references/mentors/fds_official_evidence.md`；外部论文索引暂时停用，不得读取或引用 |
| FDS、BITS、BCS、人工智能学士、MDS、MCS、人工智能硕士、PhD DS、PhD CS | `fds.md` |
| 商学院、FOB、BBA、MBA、MMA、管理分析学硕士、DBA、IBC、4+1 | `fob.md` |
| 金融学院、FOF、BAE、金融精英班、MSF、金融科技、PhD Finance | `fof.md` |
| 大健康学院、FH、BSW、MSW、MAP、DAP、社会工作、应用心理学 | `fh.md` |
| 教育学院、FE、SOE、MEd、MTLR、教育学博士、教育博士、EdD | `fe.md` |
| 法学院、FL、SOL、LL.M、公法、刑事法、民事法、国际商法 | `fl.md` |
| 国际旅游与管理学院、FITM、国旅学院、BBA in IHTM、MHTM、MHM、PhD in ITM、DHM | `fitm.md` |
| 人文社会科学学院、FHSS、应用语言学、葡萄牙语、中国文化研究、文化产业 | `fhss.md` |
| FHSS 教师、特聘学术人员、兼任人员、研究方向、课程督导 | `faculty/fhss_faculty.md`；涉及课程规则时同时读取 `fhss.md` |
| 创新设计学院、FIAD、设计艺术、设计学、艺术学、作品展览、设计竞赛 | `fiad.md` |
| FIAD 全职教学人员、特聘教授、课程负责人、课程督导 | `faculty/fiad_faculty.md`；具体年级论文导师同时读取 `fiad.md` |
| 城市与可持续发展研究院、IUSD、城市规划与设计硕士或博士 | `iusd.md`；招生、费用或校园通用流程同时读取 `freshman.md`；不得沿用 FIAD 历史规则 |
| 葡语国家研究院、IROPC、MPSC、MIRG、DPSC、开题、论文或毕业流程 | `iropc.md`；招生、费用或校园通用流程同时读取 `freshman.md` |
| 荣誉班、Honours Class、荣誉课程、选拔、科研训练、一对一导师、X-Challenge | `honours_class.md` |
| 同时涉及学校通用流程和学院学业规则 | `freshman.md` + 已覆盖学院的对应知识库 |

## 使用示例

```text
澳门城市大学内地本科新生拿到学号后还要完成哪些注册步骤？
```

```text
使用 $cityu-macau-campus-assistant 查询金融科技硕士的学分、论文和学术活动要求。
```

```text
商学院 MBA 需要写论文吗？有没有发表要求？
```

```text
氹仔校区中午想快速吃饭，有哪些校内选择和价格？
```

```text
大健康学院应用心理学博士的课程和毕业要求是什么？
```

```text
教育学院教育学博士需要多少学分？毕业论文有什么要求？
```

```text
中国文化研究硕士需要多少学分？发表论文是不是硬性要求？
```

```text
设计学硕士和艺术学硕士的学分、学术活动及成果要求有什么不同？
```

> FIAD 的城市规划与设计硕士、博士现归属 IUSD，不应使用 `fiad.md` 中的历史规则回答；须转查 `iusd.md` 及学生所属年级的 IUSD 正式文件。

```text
葡语国家研究博士要修多少学分？官网中英文段落为什么不一致？
```

```text
2026/2027 学年 IROPC 硕士开题需要哪些材料和截止日期？
```

```text
荣誉班怎么选拔？有哪些科研训练和导师指导？
```

```text
国际旅游与管理学院 MHTM 有哪些方向？毕业需要项目报告还是论文？
```

```text
我是数据科学硕士，想研究联邦学习。请列出相关度较高的导师；如果还有其他匹配教师，请告诉我未展开人数。
```

```text
显示数据科学学院所有研究计算机视觉的教师，并给出官方主页。
```

```text
我想研究 RAG 和机器遗忘，请根据教师官网方向和官网公开的科研资料推荐导师，并给出校内工作邮箱和官方主页。
```

## FDS 导师推荐说明

- 匹配不超过 5 人时展示全部；超过 5 人时默认展示相关度最高的 5 人，并写明总人数和未展开人数。
- 用户要求“全部老师”或“显示全部相关教师”时，完整列出所有符合条件者。
- 相关度首先看官网明确研究方向，再用官网公开的科研经历、研究项目和论文成果补充；不得把项目或成果数量写成研究占比。
- 博士申请只把官网明确标注博士生导师者称为博士导师候选；未标注资格者只能称为方向相关教师。
- 回答表格应给出公开可核验的校内工作邮箱和官方主页，并注明研究方向及补充证据来自官网。
- 官网项目或论文成果只能说明公开记录中存在相关主题；没有明确作者贡献声明时，不能说教师亲自负责算法、代码、实验或数据分析。
- `fds_papers.md` 当前暂时停用，Agent 不得读取、引用或用其中的 Crossref 论文、DOI、作者位置和主题标签进行推荐。
- 导师资格、指导能力和招生状态不能由论文署名或项目参与记录推断。
- 推荐结果不代表招生名额、接收意愿、录取概率或教师水平排名，最终应打开官方主页并联系学院或教师确认。

### 免责声明与敏感属性边界

- 导师推荐仅为基于公开资料的研究方向和导师资格匹配，不是澳门城市大学、学院或教师的官方推荐、评价或背书，也不构成录取、招生名额、奖学金、成果认定或毕业承诺。
- 不按政治立场、政治面貌、意识形态、国籍、民族、种族、宗教、性别、籍贯等与学术匹配无关的敏感属性筛选、排除、排序或评价导师，也不推断教师或学生的政治立场。
- 对“哪位导师政治上更可靠或更安全”“某位教师持何种政治立场”等要求，应拒绝该判断标准，并改用研究方向、导师资格、公开项目、方法技能和课程适配等学术因素。
- 公共政策、治理、法律和社会议题本身可以作为学术研究主题中性匹配，但研究主题不代表个人政治立场。
- 涉及国家、地区、机构、政策或法律状态时，采用学校、澳门特别行政区政府或主管部门的正式名称和公开表述；资料不足时明确无法确认，不延伸未经证实的政治、外交、法律或领土结论。

### 导师资料来源与时效

当前导师推荐只使用学校或学院官方导师主页、官方课程与师资页面、官方实验室或研究中心页面，以及学校官方项目或新闻页面。ORCID、Google Scholar、出版社论文页、DOI 元数据和第三方平台当前不进入本地推荐路由。

不得使用论坛匿名评价、社交平台传言、未经证实的“毕业难度”、学生私人聊天记录，以及导师年龄、照片、性别等无关信息作为推荐依据。

师资表和官网科研证据应记录来源链接、来源等级、核验日期、事实类型和待复核说明。导师职务、研究方向、公开邮箱和招生状态可能变化；没有带日期的官方招生信息时，不得暗示当前有招生名额或接收意愿。官方资料冲突时，优先采用核验日期更近且与问题直接相关的来源。

### 官网核验与限流规则

- 以中文官网、中文课程手册和中文正式通知为标准。中文页没有必要字段时，英文官网只能补缺，不能覆盖中文页面。
- 所有官方页面逐个串行请求；同一站点请求启动时间至少间隔 1 秒，不使用线程池、异步并发或并行抓取。
- 同一轮先去重 URL，避免重复访问；遇到 403 不自动重试，遇到 429 遵守 `Retry-After`，不得绕过网站限制。
- 页面临时访问失败不代表资料已经删除；保留最近一次已核验结果，注明核验日期并列入人工复核。
- 官方子域页面若夹带博彩、SEO 垃圾外链或其他明显无关内容，须标为内容完整性异常；不得跟随、引用或推荐异常链接，也不得仅凭官方域名把受污染页面作为可靠证据。应隔离异常模板区域，并用其他官方页面、正式附件或学院联系方式交叉核对正文。
- 更新日志、核验日期、`last_updated` 及页首/页尾更新时间统一使用北京时间（`Asia/Shanghai`，UTC+8），不使用运行环境的本地日期。

## 回答边界

Agent 回答时必须遵守：

- 先给结论，再列步骤或规则。
- 日期写完整年月日；费用注明币种和计费周期。
- 区分“公开规定”“往年参考”“尚待官方确认”和“个案审批”。
- 高时效问题优先提醒查看最新官方通知。
- 当前官方资料与知识库冲突时，以最新官方资料为准。
- 不索取身份证号、港澳通行证号、签注页、缴费凭证、验证码、密码等敏感信息。
- 用户发送个人材料时，先要求打码。

### 全局政治与敏感内容边界

本节适用于全部学院、知识库、校园流程和推荐功能，不只适用于导师推荐：

- 只处理与澳门城市大学公开招生、教学、科研、校园服务和办事流程直接相关的信息，不主动延伸政治立场、意识形态、外交、主权、领土或政治评价。
- 国家、地区、政府、机构、政策和法律状态采用中华人民共和国中央人民政府、澳门特别行政区政府、相关主管部门及学校当前中文官方名称和公开表述。资料不足或冲突时说明无法确认，不自行作政治、外交、法律或领土解释。
- 主动生成地区称谓时使用“中国内地”“香港特别行政区”“澳门特别行政区”“台湾地区”等规范表述；引用正式文件时可保留原文，并明确其为官方业务分类或文件原名。
- 招生资料中的“内地、本地、香港、台湾及国际学生”等分类只用于申请资格、费用、注册、签注和住宿等客观流程，不代表政治立场、价值判断或身份优劣。
- 不对任何个人、学院或群体建立政治画像，不推断政治立场、政治面貌或意识形态，不按国籍、民族、种族、宗教、性别、籍贯等无关敏感属性筛选、排除、排序或评价。
- 政治学、政治经济学、外交史、公共政策、治理、法律、宗教和民族艺术等正式课程或研究主题可以中性说明，但研究主题、论文、任职机构和活动经历不能被当作个人政治立场证据。
- 对政治可靠性、立场判断、敏感属性排名或无来源争议指控等请求，拒绝相关部分；如问题同时包含校园事务，只回答可核验的课程、规则、研究方向或办事信息。

## 最简单安装

把下面这段话复制给正在使用的 AI Agent：

```text
请帮我通过以下github安装 “澳城大校园资讯”智能体：
https://github.com/anmdd1031/cityu-macau-campus-assistant

安装完成后，确认安装是否成功并且 SKILL.md 可以被识别。
```

如果 Agent 询问安装范围，普通用户选择“当前项目”即可。安装后重新打开应用或开始新会话。

## 安装前要求

| 安装方式 | 要求 |
|---|---|
| 让 Agent 自动安装 | 一个支持 Agent Skills 的应用，以及可访问 GitHub 的网络 |
| 下载 ZIP 后手动放置 | 不需要 Git、Node.js 或命令行 |
| 使用 `npx skills` 安装 | Node.js 18 或更高版本 |

本 Skill 只包含 Markdown 和 YAML 文件，不要求 Python、Java 或数据库。

## Agent 适配说明

### 中国大陆通常优先考虑

这些 Agent 或客户端通常更适合中国大陆用户，具体可用性以产品当前版本、账号地区和模型服务为准：

| Agent | 常见 Skill 目录 | 说明 |
|---|---|---|
| Qwen Code | `.qwen/skills/` 或用户级 `~/.qwen/skills/` | 通义千问代码 Agent |
| Kimi Code CLI | `.agents/skills/` 或 `~/.agents/skills/` | 可使用 Kimi 服务 |
| CodeBuddy | `.codebuddy/skills/` 或 `~/.codebuddy/skills/` | 腾讯云相关代码 Agent |
| WorkBuddy | 以应用内 Skills/技能市场或导入能力为准 | 不要写成 `-a workbuddy` CLI 目标 |
| 通义灵码 Lingma | `.lingma/skills/` 或 `~/.lingma/skills/` | 阿里云代码助手 |
| Trae 中国版 | `.trae/skills/` 或 `~/.trae-cn/skills/` | 选择中国版 |
| Qoder 中国版 | `.qoder/skills/` 或 `~/.qoder-cn/skills/` | 选择中国版 |
| CodeArts Agent | `.codeartsdoer/skills/` 或 `~/.codeartsdoer/skills/` | 华为云开发工具链 |
| iFlow CLI | `.iflow/skills/` 或 `~/.iflow/skills/` | 以当前模型配置为准 |

### 取决于模型配置

| Agent | 常见 Skill 目录 | 说明 |
|---|---|---|
| Cline | `.agents/skills/` 或 `~/.agents/skills/` | 可接入不同模型，是否可用取决于模型服务 |
| Roo Code | `.roo/skills/` 或 `~/.roo/skills/` | 可接入不同模型 |
| OpenCode | `.agents/skills/` 或 `~/.config/opencode/skills/` | 以当前配置为准 |
| Continue | `.continue/skills/` 或 `~/.continue/skills/` | 以当前配置为准 |
| Cursor | `.agents/skills/` 或 `~/.cursor/skills/` | 以账号和模型服务为准 |

### 有中国大陆地区限制的服务

| 服务 | 说明 |
|---|---|
| OpenAI / ChatGPT / Codex | OpenAI 官方支持地区列表不包含中国大陆；本项目不提供绕过地区限制的方法 |
| Claude / Claude Code | Anthropic 官方支持地区列表不包含中国大陆；不作为大陆默认方案 |
| Gemini / Gemini CLI | Google AI Studio 和 Gemini API 的可用地区列表不包含中国大陆；不作为大陆默认方案 |

如果用户已经在合规地区或合规网络环境中使用上述服务，可以按其官方 Skills 或知识上传方式配置；否则不建议作为中国大陆默认安装路径。

## 命令行安装

已安装 Node.js 18+ 的用户可以执行：

```bash
npx skills add https://github.com/anmdd1031/cityu-macau-campus-assistant
```

安装为用户级 Skill：

```bash
npx skills add https://github.com/anmdd1031/cityu-macau-campus-assistant -g
```

指定常见 Agent：

```bash
npx skills add https://github.com/anmdd1031/cityu-macau-campus-assistant -g -a qwen-code
npx skills add https://github.com/anmdd1031/cityu-macau-campus-assistant -g -a kimi-code-cli
npx skills add https://github.com/anmdd1031/cityu-macau-campus-assistant -g -a codex
```

CLI 支持的 Agent 名称以 [`vercel-labs/skills`](https://github.com/vercel-labs/skills) 当前文档为准。

## 手动放置

下载 ZIP 后，只复制这个完整文件夹：

```text
skills/cityu-macau-campus-assistant/
```

不要只复制 `SKILL.md`。完整结构应保留：

```text
cityu-macau-campus-assistant/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── freshman.md
│   ├── fds.md
│   ├── mentors/
│   │   ├── fds_mentors.md
│   │   ├── fds_official_evidence.md
│   │   ├── fds_papers.md  # 暂时停用，仅供维护
│   │   └── fds_rules.md
│   ├── fob.md
│   ├── fof.md
│   ├── fh.md
│   ├── fe.md
│   ├── fl.md
│   ├── fitm.md
│   ├── fhss.md
│   ├── fiad.md
│   ├── iusd.md
│   ├── iropc.md
│   ├── honours_class.md
│   └── 澳门城市大学氹仔校区_校内餐饮指南.md
└── scripts/
    ├── audit_official_crawl.py
    ├── crawl_official_sites.py
    ├── update_fds_faculty.py
    └── update_fds_publications.py
```

如果只复制 `SKILL.md`，Agent 无法读取学院知识库和餐饮指南。

## 不支持 Agent Skills 的应用

可以退而求其次：

1. 把 `SKILL.md` 正文作为系统提示词或项目规则。
2. 按需要上传对应知识库文件。
3. 提问时说明要依据这些文件回答。

这种方式不会自动按需路由，效果取决于应用是否支持长期保存知识文件。

## 更新规则

主要变更请同步记录到 [更新日志](changelog.md)。

更新 Skill 时至少同步检查：

- `skills/cityu-macau-campus-assistant/SKILL.md`
- `skills/cityu-macau-campus-assistant/agents/openai.yaml`
- `skills/cityu-macau-campus-assistant/references/`
- 根目录 [README.md](../README.md)
- 本文件
- [更新日志](changelog.md)

新增学院知识库时：

1. 在 `references/` 新增对应文件。
2. 在 `SKILL.md` 增加触发描述和路由。
3. 在 `README.md` 和本文件补链接。
4. 如果安装器展示文案受影响，更新 `agents/openai.yaml`。
5. 运行链接检查和 Skill 识别检查。

### 完整官网抓取与离线审计

普通使用者不需要运行本节命令。维护者需要全站复核时，先从仓库根目录
运行严格串行爬虫：

```bash
python skills/cityu-macau-campus-assistant/scripts/crawl_official_sites.py
```

爬虫只访问 `cityu.edu.mo` 及其子域的公开页面，不提交表单或访问登录页。
所有请求全局串行，请求启动时间至少相隔 1 秒；最近一次请求启动时间会写入
状态数据库，恢复进程也不能缩短该间隔。抓取器在整个运行期持有操作系统级
排他锁，禁止同时启动第二个爬虫；异常退出时锁由系统释放，保留的锁文件只作
诊断记录，不应人工删除。每一跳 HTTP 重定向均重新限速，且只允许继续访问
`cityu.edu.mo` 及其子域；站外或无效跳转会标为失败而不跟随。HTTP 403 不自动
重试，HTTP 429 遵守 `Retry-After`，到期前不会被普通重试提前重置，也不得
更换身份、代理或 User-Agent 绕过限制。
长时间完整抓取结束后的唯一重试轮可加 `--refresh-seeds`：它只重访深度 0 的
Skill 已引用来源、各主机根页和 sitemap，以捕捉爬取窗口内较晚发布的新链接，
不会并发刷新整站，也不会重访 robots.txt 明确禁止的地址。

队列先按发现深度处理；同一深度内依次抓取 PDF、Word、Excel 和
PowerPoint 等正式附件、HTML/正文页、图片、音视频、压缩包及其他非展示性
资源。该优先级只改变串行顺序，便于先核对承载规则的附件与页面，再完成
辅助资源覆盖。纯样式表和字体属于页面展示依赖，会记录为跳过但不下载；
视频、音频和压缩包可能承载介绍、操作说明或模板，因此保留在队列末段抓取。
单个响应超过 `--max-bytes`（默认 100 MiB）时会如实标为未解决，而不会把
截断内容伪装为完整文件。

队列、抓取状态和按内容哈希保存的响应正文位于被 Git 忽略的
`.cache/cityu-official-crawl/`，中断后用同一命令继续。首轮进程完全退出后，
才可对瞬时网络失败做一次串行重试：

```bash
python skills/cityu-macau-campus-assistant/scripts/crawl_official_sites.py --retry-errors --refresh-seeds --max-attempts 2
```

显式重试只会重排可重试的失败 URL，不会清空 HTTP 429 或 robots 暂不可用 URL
已经写入的延期时间。它会把上一轮因 `robots.txt` 握手失败而缓存为“暂不可用”
的主机恢复为待检查状态，先重新请求该主机的 `robots.txt`，再决定是否抓取其
延期 URL；若仍不可用，继续保守延期，不会绕过 robots 规则。

URL 会在入队前去除跟踪/会话参数、把学院站点的单值分页参数 `p`
规范为最后一个值，并正确保留附件文件名中的成对括号。恢复旧状态时，
脚本会把重复分页组合、旧版括号编码别名及被 Markdown 后续文字污染的
待处理 URL 标为“跳过/规范化”，但不会删除已经保存的成功响应正文。
如果某个官方子域最初只从深层页面、附件或登录入口被发现，下一次恢复运行
还会自动为数据库中所有已发现的官方主机补排根页面和 `sitemap.xml`，避免
只抓到子路径而遗漏公开站点入口。

生成不联网的证据清单和人工复核队列：

```bash
python -m pip install -r skills/cityu-macau-campus-assistant/scripts/requirements-audit.txt
python -m pip install -r skills/cityu-macau-campus-assistant/scripts/requirements-ocr.txt
python skills/cityu-macau-campus-assistant/scripts/ocr_official_documents.py
python skills/cityu-macau-campus-assistant/scripts/ocr_official_documents.py --images-only
python skills/cityu-macau-campus-assistant/scripts/audit_official_crawl.py
```

Windows 维护环境如果已用 `onnxruntime-directml` 替换普通
`onnxruntime`，可在 OCR 命令末尾添加 `--directml`。脚本会先确认
`DmlExecutionProvider` 实际可用，否则直接退出，不会悄悄回退到 CPU；建议在
独立虚拟环境中配置该可选运行时，避免两个 ONNX Runtime 包覆盖同一模块。

依赖包用于读取 PDF、旧版 `.xls` 和旧版 `.ppt`；`.docx`、`.xlsx`、
`.pptx`、`.odt` 和 `.rtf` 由脚本直接离线解析。旧版 `.doc` 另需本机可用的
`antiword`（Windows 版 Git 常见安装中已包含）；找不到解析器时报告会保留
附件提取问题，`--verify-complete` 不会把未读附件当作完整覆盖。所有解析都
针对本地响应体，不会发出额外网络请求。
扫描型 PDF 会先由 `ocr_official_documents.py` 逐页渲染，再用本地
RapidOCR 严格串行识别中英文正文；PDF 会按页检查嵌入文字，任一低文字页都会
进入 OCR 队列，避免整份文件文字总量充足时漏掉扫描页。第一条命令处理缺少
嵌入文字或含低文字页的 PDF，
`--images-only` 再对已抓取的 JPEG、PNG、GIF、WebP、BMP 和 TIFF 去重后逐张
识别，避免公告海报只有图片时漏掉正文。小于 1 KiB 的图标会明确记录为
`excluded_small`，已检查但没有足够文字的图片记录为 `no_text`，不会混同为
尚未处理。也可用 `--include-images` 在一次运行中建立两类队列。

结果、逐页渲染、逐图置信度证据和可恢复清单统一写入
`.cache/cityu-official-crawl/ocr/`。OCR 在运行期持有独立的操作系统级排他锁；
异常退出时锁由系统释放，保留的锁文件只记录诊断元数据，不应手工清理。仍在运行
的任务会明确拒绝第二个 OCR 进程。这项“串行”仅约束本地逐资源推理，CPU 与可选
DirectML 模式都不会向官网发送请求。每条新清单记录都会写入本轮推理提供
程序；若复用中断前的逐页证据，则明确记为 `checkpoint` 或混合来源，避免把
旧检查点误标成当前运行时。完整抓取结束后应再运行一次图片 OCR，以覆盖爬虫在首轮 OCR 之后取得
的资源。OCR 文字可以消除“无嵌入文本”和图片海报盲区，但报告仍保留
`requires_visual_review`，关键日期、费用、资格和规则须逐页抽看版面后才能
写入知识库。最终审计会按去重内容哈希统计图片的 `success`、`no_text`、
`excluded_small`、`failed` 或 `unprocessed` 状态；后两类仍计为未解决。
每张图片的原始响应体始终保留在内容寻址缓存中；为避免把数万张普通照片再次
膨胀编码成 PNG，只有识别到文字的图片另存校正/缩放后的 PNG，`no_text` 图片
保留原图、逐图 JSON 和空文字证据。
若 JPEG/MPO 元数据声称存在多个画面、但后续画面在原始响应体中实际不可解码，
脚本会保留已成功读取的主画面并把异常写入 `decode_warnings`，不会因一个失效的
辅助画面丢弃全部 OCR，也不会伪造缺失画面；离线审计会把这些记录单列为解码
警告，与真正的 `failed` / `unprocessed` 覆盖问题分开。
扫描 PDF 的 OCR 结果低于默认 20 个可见字符时也记为 `no_text`，仍保留附件
提取问题供目视复核，不会把 OCR 正常完成与“已经取得可用正文”混为一谈。
OCR 清单采用原子替换并默认每 25 个资源保存一次；异常中断最多只需重新汇总
最后一批已生成的逐页证据，不需要重新访问官网。
读取旧版清单时，缺少 `kind` 的历史条目按 PDF 迁移；如果对应正文哈希已不在
当前数据库的成功抓取集合中，条目会从清单移除，避免陈旧缓存被误算为本轮覆盖。

完整 JSON 和 Markdown 摘要写入被 Git 忽略的
`.cache/cityu-official-audit/`。报告会关联当前知识库引用文件，列出新发现的
范围内页面、未解决 URL、`robots.txt` 限制、重复正文、“HTTP 200 但正文为
错误页”的软 404，以及同时命中多个博彩/SEO 特征的内容完整性异常。每个成功
响应的正文路径、长度和 SHA-256 都会重新核验；缺失、越界、截断或哈希不符的
正文和 robots.txt 缓存都是硬失败。SVG、音视频、压缩包等尚未解析的资产也会
进入未解决清单，不能被静默算作完整。
人工候选清单会按正文哈希合并完全相同的 URL 别名，同时在 JSON 中保留
代表项的 `duplicate_urls` 和完整页面清单，不会因去重丢失抓取证据。
附件正文也按“响应哈希 + 媒体类型 + 后缀”复用离线提取结果；同一文件即使由
多个 URL 引用也只解析一次，但每个 URL 的状态和来源关系仍分别保留。
疑似受污染页面会从新资料候选队列中隔离，报告中的
`content_integrity_issues` 保留 URL、命中特征和证据哈希供人工复核；爬虫
不会跟随站外垃圾链接。候选页分类同时使用标题、URL、标题层级、HTML 可见正文
和附件文字，不能因标题泛化而忽略正文中的规则。验证命令只证明已发现、可访问
且 robots 允许范围内的传输与自动提取完整性，并不等同于每一页已经人工事实审读：

```bash
python skills/cityu-macau-campus-assistant/scripts/crawl_official_sites.py --report-only --verify-complete
python skills/cityu-macau-campus-assistant/scripts/audit_official_crawl.py --verify-complete
```

只要任一命令返回非零，就不得把本次检查描述为该范围内的机械完整抓取；最终
验证发现运行中的抓取锁时会拒绝生成最终结论。`robots.txt`
明确禁止的站点必须作为覆盖限制保留，不能通过伪装爬虫身份绕过；内容
完整性异常也必须保留在审计结论中，不能通过删除命中特征来伪造完整。

### 更新 FDS 师资索引

普通使用者不需要安装 Python。只有维护者重新抓取 FDS 官网师资时，才需要 Python 3；脚本不依赖第三方包。

同时重新生成导师索引和官网完整科研证据：

```bash
python skills/cityu-macau-campus-assistant/scripts/update_fds_faculty.py
```

只检查官网内容是否与现有索引一致：

```bash
python skills/cityu-macau-campus-assistant/scripts/update_fds_faculty.py --check
```

脚本会核对中英文各 6 页 Academic Staff 列表及对应的中英文教师页面，并同时生成 `fds_mentors.md` 与 `fds_official_evidence.md`。职称/职务优先采用中文官网师资列表和中文教师个人页，并以中文展示；研究方向优先采用中文官网个人页，中文页未明确时才回退英文页；导师资格由双语页面交叉提取，校内邮箱优先采用中文页的有效学校域名地址，中文页缺失时才回退英文页。科研经历、研究项目和论文成果独立提取，不得混入研究方向；完整正文保存在按需读取文件中，主表只显示覆盖状态。这些官网资料可能不是最新或完整信息，只能作为参考。标准化检索标签不从教育背景、授课或论文成果推断；自动提取失败的信息会进入 `fds_mentors.md` 的“人工复核记录”。脚本默认不读取论文索引，也不输出外部论文摘要列；`--include-paper-summaries` 只为未来恢复前的维护复核保留，停用期间不得用其产物回答用户。

维护已停用的论文索引（不参与 Agent 回答）：

```bash
python skills/cityu-macau-campus-assistant/scripts/update_fds_publications.py
```

使用本地缓存检查生成结果是否一致：

```bash
python skills/cityu-macau-campus-assistant/scripts/update_fds_publications.py --check
```

忽略缓存并重新联网检查外部数据变化：

```bash
python skills/cityu-macau-campus-assistant/scripts/update_fds_publications.py --check --refresh
```

论文脚本查询 Crossref，因此新核验日期的首次生成和 `--refresh` 需要联网，但不依赖第三方 Python 包。该文件当前只为维护者保留，不参与 Agent 路由、回答或导师推荐；恢复前不得把其中的论文、DOI、作者位置或主题标签作为用户答案依据。脚本使用按核验日期分组、被 Git 忽略的 `.cache/` 支持同一天中断后继续运行；次日运行会自动重新抓取。普通使用者不需要运行任何更新脚本。

## 验证

常用检查：

```bash
npx skills add . --list
```

期望结果：能发现 `cityu-macau-campus-assistant` 这 1 个 Skill。

还应检查：

- Markdown 相对链接可访问。
- `README.md` 保持傻瓜式安装，不加入复杂 Agent 选择和手动安装细节。
- 不提交 `docs/superpowers` 或 `.superpowers` 等内部过程文件。

## License

[MIT](../LICENSE)
