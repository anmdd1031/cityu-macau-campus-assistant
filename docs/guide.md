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
- 数据科学学院、商学院、金融学院、大健康学院、教育学院、法学院、国际旅游与管理学院、荣誉班的课程、学分、导师、论文、发表、毕业要求和常见办事入口。
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
| 新生与校园通用知识库 | [freshman.md](../skills/cityu-macau-campus-assistant/references/freshman.md) | 已完成 | 招生、注册、学费、奖学金、体检、D 签注、逗留许可、宿舍、图书馆、校园服务、恶劣天气 |
| 数据科学学院 FDS | [fds.md](../skills/cityu-macau-campus-assistant/references/fds.md) | 已完成 | BITS、BCS、MDS、MCS、PhD DS、PhD CS、学分、资格考试、论文成果、导师、毕业 |
| FDS 导师基础画像 | [fds_mentors.md](../skills/cityu-macau-campus-assistant/references/mentors/fds_mentors.md) | 已完成 | 58 名 Academic Staff、中文官网职称/职务、导师资格、58 个可核验校内工作邮箱、官网研究方向、科研证据覆盖提示、招募说明和官方主页 |
| FDS 官网完整科研证据 | [fds_official_evidence.md](../skills/cityu-macau-campus-assistant/references/mentors/fds_official_evidence.md) | 已完成 | 58 名教师官网公开的完整科研经历、研究项目和论文成果栏目；按需读取，官网访问失败时可使用本地核验版本 |
| FDS 论文检索索引 | [fds_papers.md](../skills/cityu-macau-campus-assistant/references/mentors/fds_papers.md) | 暂时停用 | 仅为维护者保留，不参与 Agent 路由、回答或导师推荐 |
| FDS 导师匹配规则 | [fds_rules.md](../skills/cityu-macau-campus-assistant/references/mentors/fds_rules.md) | 已完成 | 官网准入、研究方向匹配、官方证据来源和回答边界 |
| 商学院 FOB | [fob.md](../skills/cityu-macau-campus-assistant/references/fob.md) | 已完成 | BBA、MBA、DBA、IBC、4+1 项目、导师、论文与毕业要求 |
| 金融学院 FOF | [fof.md](../skills/cityu-macau-campus-assistant/references/fof.md) | 已完成 | BAE、金融精英班、金融学硕士、金融科技硕士、金融学博士、导师、发表与毕业要求 |
| 大健康学院 FH | [fh.md](../skills/cityu-macau-campus-assistant/references/fh.md) | 已完成 | BSW、MSW、MAP、DAP、智慧养老与健康管理、导师、实习与毕业要求 |
| 教育学院 FE/SOE | [fe.md](../skills/cityu-macau-campus-assistant/references/fe.md) | 已完成 | 教育学硕士、教学研究硕士、教育学博士、学分、导师、论文与毕业要求 |
| 法学院 FL/SOL | [fl.md](../skills/cityu-macau-campus-assistant/references/fl.md) | 已完成 | 法学硕士、专业方向、学分、导师、论文与毕业要求 |
| 国际旅游与管理学院 FITM | [fitm.md](../skills/cityu-macau-campus-assistant/references/fitm.md) | 已完成 | 国际旅游与酒店管理、国际款待与旅游业管理、国际酒店管理、国际旅游管理、酒店管理、导师、项目报告、论文与毕业要求 |
| 荣誉班 Honours Class | [honours_class.md](../skills/cityu-macau-campus-assistant/references/honours_class.md) | 已完成 | 选拔、课程体系、导师指导、科研训练、实习、竞赛与毕业条件 |
| 氹仔校区餐饮指南 | [澳门城市大学氹仔校区_校内餐饮指南.md](../skills/cityu-macau-campus-assistant/references/澳门城市大学氹仔校区_校内餐饮指南.md) | 已完成 | 校内餐厅、菜单、价格、供应时段、用餐建议 |

## 暂不覆盖的知识库

下列学院或机构由项目当前范围主动保留，暂不建立单独知识库。这不是待补资料清单；只有项目负责人决定扩展范围后，才新增对应知识库。

| 学院/机构 | 预留文件名 | 当前状态 |
|---|---|---|
| 人文社会科学学院（FHSS） | `fhss.md` | 主动保留，暂不覆盖 |
| 创新设计学院（FIAD） | `fiad.md` | 主动保留，暂不覆盖 |
| 葡语国家研究院（IROPC） | `iropc.md` | 主动保留，暂不覆盖 |
| 城市与可持续发展研究院（IUSD） | `iusd.md` | 主动保留，暂不覆盖 |

范围规则：

- 不要在 `SKILL.md` 中声称这些学院已有完整知识库。
- 用户问到暂不覆盖的学院或研究院时，可以先读 `freshman.md` 中的通用招生和费用信息。
- 如果现有资料无法确认课程、学分、导师或毕业要求，必须明确说“现有知识库未覆盖”，并引导用户查看学院官网、招生事务处、研究生院或教务处。
- 项目负责人决定新增学院知识库后，再同步更新 `SKILL.md`、`agents/openai.yaml`、`README.md` 和本文件。

## 路由规则

| 用户问题 | 应读取 |
|---|---|
| 招生、费用、注册、D 签注、逗留许可、宿舍、校园服务、台风、暴雨 | `freshman.md` |
| 氹仔校区食堂、餐厅、菜单、价格、咖啡、打包、午餐 | `澳门城市大学氹仔校区_校内餐饮指南.md` |
| FDS 教师名单、导师资格、官方邮箱、联系方式或教师主页 | `references/mentors/fds_mentors.md` |
| FDS 导师推荐、教师研究方向或谁研究某个主题 | `references/mentors/fds_rules.md` + `references/mentors/fds_mentors.md` |
| FDS 完整科研经历、研究项目、官网论文成果或官网访问失败时查询本地资料 | 在上述文件基础上按需读取 `references/mentors/fds_official_evidence.md` |
| FDS 具体论文、论文成果或项目经历 | 只按需读取 `references/mentors/fds_official_evidence.md`；外部论文索引暂时停用，不得读取或引用 |
| FDS、BITS、BCS、MDS、MCS、PhD DS、PhD CS | `fds.md` |
| 商学院、FOB、BBA、MBA、DBA、IBC、4+1 | `fob.md` |
| 金融学院、FOF、BAE、金融精英班、MSF、金融科技、PhD Finance | `fof.md` |
| 大健康学院、FH、BSW、MSW、MAP、DAP、社会工作、应用心理学 | `fh.md` |
| 教育学院、FE、SOE、MEd、MTLR、教育学博士 | `fe.md` |
| 法学院、FL、SOL、LL.M、公法、刑事法、民事法、国际商法 | `fl.md` |
| 国际旅游与管理学院、FITM、国旅学院、BBA in IHTM、MHTM、MHM、PhD in ITM、DHM | `fitm.md` |
| 荣誉班、Honours Class、荣誉课程、选拔、科研训练、一对一导师、X-Challenge | `honours_class.md` |
| 同时涉及学校通用流程和学院学业规则 | `freshman.md` + 已覆盖学院的对应知识库 |
| 问到暂不覆盖的学院或研究院 | 只查 `freshman.md` 中的学校通用信息，再说明单独学院知识库当前未覆盖并给出官方入口 |

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

### 导师资料来源与时效

当前导师推荐只使用学校或学院官方导师主页、官方课程与师资页面、官方实验室或研究中心页面，以及学校官方项目或新闻页面。ORCID、Google Scholar、出版社论文页、DOI 元数据和第三方平台当前不进入本地推荐路由。

不得使用论坛匿名评价、社交平台传言、未经证实的“毕业难度”、学生私人聊天记录，以及导师年龄、照片、性别等无关信息作为推荐依据。

师资表和官网科研证据应记录来源链接、来源等级、核验日期、事实类型和待复核说明。导师职务、研究方向、公开邮箱和招生状态可能变化；没有带日期的官方招生信息时，不得暗示当前有招生名额或接收意愿。官方资料冲突时，优先采用核验日期更近且与问题直接相关的来源。

## 回答边界

Agent 回答时必须遵守：

- 先给结论，再列步骤或规则。
- 日期写完整年月日；费用注明币种和计费周期。
- 区分“公开规定”“往年参考”“尚待官方确认”和“个案审批”。
- 高时效问题优先提醒查看最新官方通知。
- 当前官方资料与知识库冲突时，以最新官方资料为准。
- 不索取身份证号、港澳通行证号、签注页、缴费凭证、验证码、密码等敏感信息。
- 用户发送个人材料时，先要求打码。

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
│   ├── honours_class.md
│   └── 澳门城市大学氹仔校区_校内餐饮指南.md
└── scripts/
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
