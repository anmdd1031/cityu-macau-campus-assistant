# 澳门城市大学智能校园助手agent

2026-10-07：依据校方 2026-07-14 新增课程公告，将人工智能学士纳入数据科学学院与全校本科清单，修正旧目录遗漏导致的“仅规划”说法；开设状态与当前报名窗口分别判断。定向更新 `references/fds.md` 与 `references/freshman.md`。

2026-10-06：新增 `references/campus_map.md`，根据官方校园地图图片核对氹仔校区 10 个楼宇标识与大致分布；不推断各学院教室分配，地图修订日期未明。地图中的名称“蔡繼有樓”按原图保留。

2026-10-05 校服补充：维护者反馈平时不需要穿校服，已在校园文化资料中标明来源，并与官方历史活动着装要求分开；特定活动仍以通知为准。

2026-10-05：补充校歌、校服及每周升旗的官方历史证据，区分活动事实和现行参加要求；多问题逐项路由，学院领导保留职务与访问受限说明。资料位于 `skills/cityu-macau-campus-assistant/references/campus_culture.md`，该核验日期不代表所有历史规则仍然有效。

**开 发 者：** 金添、李俞萱、金泽同、汪家怡

**指导老师：** 蔡剑平

**研发单位：** 澳门城市大学 数据科学学院

imcjp 测试：这是我的 README 测试。

大学里的很多问题，并不是没有答案，而是答案分散在不同部门、不同网页、不同公告和不同时间节点里。对新生和在校生来说，真正消耗精力的往往不是理解规则本身，而是在注册、缴费、签注、宿舍、课程、论文和毕业要求之间反复搜索、比对和确认。

“澳城大校园资讯”是一个面向 AI Agent 的澳门城市大学公开信息智能体。它将澳城大新生入学、校园办事、学院课程、学分要求、论文成果、毕业规则和校内餐饮等资料整理为结构化知识库，让 AI Agent 不只是回答“看起来正确”的内容，而是尽量基于公开资料、按照具体场景、带着边界意识回答问题。

这个项目的价值不在于替代学校官方通知，而在于帮助学生更快理解公开规则、定位办事入口、减少重复搜索和信息误读。对于准备报考、刚拿到录取、准备来澳注册，或正在查询学院培养方案和毕业要求的学生来说，它可以作为一个更清晰、更易用的校园信息入口。

它只整理公开资料，不替学校做录取、签注、转专业、论文认定、学分确认或毕业审批。涉及招生时间、费用、宿舍、签注、注册和毕业规则等高时效或个案事项时，最终仍应以澳门城市大学、相关学院及澳门政府部门的最新正式通知为准。

## 最简单安装方法

打开微信小程序WorkBuddy，注册并登录，选择‘云端工作’

把下面这段话复制给WorkBuddy：

```text
请帮我通过以下github安装 “澳城大校园资讯”智能体：
https://github.com/anmdd1031/cityu-macau-campus-assistant

安装完成后，确认安装是否成功并且 SKILL.md 可以被识别。
```

如果 Agent 问你安装到哪里：

- 不知道怎么选，就选“当前项目”。

安装后，可以直接对话或 重新打开 Agent 或开始一个新会话。

如果出现报错，可以选择退出小程序重新安装或对话，或是选择关闭微信重新安装一遍

## 怎么使用

安装后可以直接问：

```text
澳门城市大学内地本科新生拿到学号后还要完成哪些注册步骤？
```

也可以显式指定智能体标识：

```text
使用 $cityu-macau-campus-assistant 查询 MDS 的学分和成果要求。
```

## 这个 Agent 能做什么

可以：

- 整理公开的申请、注册、宿舍、签注和校园办事流程
- 按事项查找[部门联系方式与办公地点](skills/cityu-macau-campus-assistant/references/freshman.md#16-行政部门与地点速查)，注明核验状态
- 查询[学校概况与各机构排名](skills/cityu-macau-campus-assistant/references/freshman.md#23-排名认证与学科优势)，区分世界总榜、区域榜、学科榜和评级
- 了解[校史与校庆](skills/cityu-macau-campus-assistant/references/freshman.md#211-校史与校庆)、横琴科研平台及未来书院；不把成立新闻当作当前招生或上课安排
- 解释 FDS、FOB、FOF、FH、FE、FL、FITM、FHSS、FIAD、IUSD、IROPC 和荣誉班公开课程、学分、论文成果和毕业要求
- 按官网研究方向和导师资格查询 FDS 教师，并给出可解释的候选导师、校内工作邮箱和主页
- 查询氹仔校区校内餐饮、菜单、价格和供应时段
- 直接回答资料已覆盖的学费、报名日期、退款规则和公开课表，注明学年、适用对象与来源；资料不全时先给出可确认部分
- 新课程的登记、刊宪及招生状态按对应正式资料说明，不仅凭“新课程”标签判断尚未获批
- 按适用公开条件辅助检查申请、学分、成果及毕业等要求，列出已满足、尚缺和无法确认的事项，最终认定由学校作出
- 提醒哪些信息需要看最新官方通知

不可以：

- 保证录取、奖学金、宿位、签注、转专业或毕业
- 代替学校做个案审批
- 查询个人成绩、课表、考场或私人账号
- 代替法律、移民、财务或医疗意见
- 对个人、学院或群体作政治立场推断、政治可靠性评价，或按国籍、民族、宗教等无关敏感属性筛选和排序

本智能校园助手仅整合校园公开信息供参考，不替代澳门城市大学官方通知，不具备招生、签注、学分、毕业等审批效力。所有办事、升学、毕业相关事宜，请以学校、学院及澳门相关部门最新正式公告为准，使用者依据助手内容做出的相关决策，责任由本人自行承担。
## 单次证据入口与导师字段校验

支持 Python 的宿主现在可以直接调用 `skills/cityu-macau-campus-assistant/runtime/query.py`：

```sh
python skills/cityu-macau-campus-assistant/runtime/query.py bundle map
python skills/cityu-macau-campus-assistant/runtime/query.py bundle fds-fees-mainland-2027
python skills/cityu-macau-campus-assistant/runtime/query.py bundle iusd-phd-2026
python skills/cityu-macau-campus-assistant/runtime/query.py mentors --query 计算机视觉 --level master
```

证据包名称明确适用年份/类别，不能套用到其他学生。导师入口按公开方向和标签作固定关键词匹配，并按明确导师资格筛选，返回本次口径、人数、原文记录和表格，不代表所有语义相关教师或招生名额。

用返回 ID 和 `source_sha256` 调用 `render --ids ... --sha256 ...` 可生成选中教师的原文表格；用 `check --ids ... --sha256 ... --answer-file ...` 校验 UTF-8 草稿，成功返回 0，不一致返回 2 并附规范表格。此检查仅覆盖表格字段，不校验周围论述或之后的编辑。详见[检索说明](skills/cityu-macau-campus-assistant/references/retrieval.md)。

主 Skill 的快速命令已前置，详细问题路由按需读取。本仓库提供脚本入口，未替宿主注册 MCP 或修改全局配置；实际采用率以模型调用轨迹为准。没有 Python 时仍可直接读 Markdown。

## 可选的本地快速检索

支持 Python 3.9+ 的 Agent 可通过 `skills/cityu-macau-campus-assistant/runtime/read_sections.py` 按标题建立实时索引、一次读取多个完整章节，减少重复加载大文件。无需第三方依赖、联网或缓存写入；没有 Python 时仍直接使用 Markdown。详见[章节检索说明](skills/cityu-macau-campus-assistant/references/retrieval.md)。

```sh
python skills/cityu-macau-campus-assistant/runtime/read_sections.py catalog --file freshman.md --query 学费
python skills/cityu-macau-campus-assistant/runtime/read_sections.py read --select "fds.md::3.2" --select "freshman.md::0.2"
```

中文传输乱码时在 `read` / `catalog` 前加 `--ascii`。目录提供完整标题路径和版本绑定的章节 ID，重复标题可按 ID 唯一读取；文件更新后重新获取目录。超限会返回可选子章节及预计读取量，便于直接缩小范围或分批读取。输出包含本地版本哈希、原文行号和上级适用范围；同级来源章节仍需按问题选取，不能把局部检索当作全库审计。导师匹配与联网维护的详细规则改为按需读取，内容保留。新发布的 `runtime/` 是可选只读工具，与仍仅留在维护者本地的 `scripts/` 不同。下游若固定 Skill 快照或仅加载 Markdown，需单独接入新版本，安装本仓库不会自动更新下游应用。

开发验证：`python -m unittest discover -s tests -v`。

## 更多说明

- [完整说明文档](docs/guide.md)
- [更新日志](docs/changelog.md)
- [智能体规则文件](skills/cityu-macau-campus-assistant/SKILL.md)
- [学校概况、新生与校园知识库](skills/cityu-macau-campus-assistant/references/freshman.md)（校史、办学特色、统计口径、校区和部门入口）
- [数据科学学院知识库](skills/cityu-macau-campus-assistant/references/fds.md)
- [人文社会科学学院知识库](skills/cityu-macau-campus-assistant/references/fhss.md)
- [创新设计学院知识库](skills/cityu-macau-campus-assistant/references/fiad.md)
- [城市与可持续发展研究院知识库](skills/cityu-macau-campus-assistant/references/iusd.md)
- [葡语国家研究院知识库](skills/cityu-macau-campus-assistant/references/iropc.md)
- [数据科学学院导师基础画像（中文官网师资、职称职务、资格、方向、项目及招募说明）](skills/cityu-macau-campus-assistant/references/mentors/fds_mentors.md)
- [数据科学学院导师官网完整科研证据](skills/cityu-macau-campus-assistant/references/mentors/fds_official_evidence.md)
- [FDS 导师匹配规则](skills/cityu-macau-campus-assistant/references/mentors/fds_rules.md)
- [商学院知识库](skills/cityu-macau-campus-assistant/references/fob.md)
- [金融学院知识库](skills/cityu-macau-campus-assistant/references/fof.md)
- [大健康学院知识库](skills/cityu-macau-campus-assistant/references/fh.md)
- [教育学院知识库](skills/cityu-macau-campus-assistant/references/fe.md)
- [法学院知识库](skills/cityu-macau-campus-assistant/references/fl.md)
- [国际旅游与管理学院知识库](skills/cityu-macau-campus-assistant/references/fitm.md)
- [荣誉班知识库](skills/cityu-macau-campus-assistant/references/honours_class.md)
- [氹仔校区餐饮指南](skills/cityu-macau-campus-assistant/references/澳门城市大学氹仔校区_校内餐饮指南.md)

> 2026-10-01 本轮串行刷新知识库引用的官方页面和正式附件：660 个去重引用中 635 个完成请求（599 成功、32 软 404、3 个 404、1 个 TLS/网络失败），另有 25 个受访问保护。按核验结果更新本地当期招生、宿舍、考试、交流、课程表、导师及开题信息；严格全站审计仍未通过（未解决 3,614 项，43,502 个候选 URL、33,733 份候选正文尚未全部人工复核），因此不宣称全站资料已完整更新，详见[更新日志](docs/changelog.md)。商学院部分中文页面出现 SEO/博彩垃圾内容，已从知识候选中隔离；高变动事项以对应官方最新通知为准。

维护者使用的离线 OCR 工具默认在 CPU 上逐个资源运行；Windows 环境也可在安装 `onnxruntime-directml` 后加 `--directml` 使用 GPU 推理。两种模式都只读取本地抓取缓存，保持单进程和可恢复清单，不会增加官网请求并发。PDF 已有可提取正文时只识别审计标出的低文字页，并把嵌入正文与复核页文字合并；整份正文不足或解析失败时才逐页识别全文件。已完成 OCR 且确认无可读文字的 PDF 会保留视觉复核提示，但不再误报为未处理附件。官网爬虫除状态目录锁外，还持有跨仓库副本、跨状态目录共享的单用户操作系统排他锁，并持久化全局请求冷却时间；最终完整性审计也在同一把锁内生成快照。例行更新优先用 `--refresh-url` 精确刷新变更所涉及的官方来源；`--refresh-references` 用于一次复核全部知识库引用。两种模式只跟进直接链接的正式文档，不顺带下载导航页、未引用图片或缩略图；全站发现与覆盖检查单独串行执行。锁占用时必须等待当前任务结束，不得改状态目录、删锁文件或并行启动；异常退出时操作系统会释放锁，保留的锁文件只作诊断记录。OCR 使用独立锁。HTTP 429 和 `robots.txt` 暂不可用均使用有界重试预算与冷却期；预算耗尽的 robots 受阻 URL 会保留为 `robots_unavailable` 并阻止完整性验证，直至冷却期后由维护者显式重试。

以上维护工具仅保存在维护者本地：`scripts/` 及其依赖清单已停止随 GitHub 当前版本发布，并由 `.gitignore` 忽略。正常问答和导师匹配只需规则与知识库，不需要这些程序或 Python；新克隆/下载不会包含脚本。已有副本更新前请单独备份自用脚本，Git 更新可能移除原先被跟踪的文件。旧提交仍保留历史版本，本次不重写 Git 历史。

维护者运行离线审计前，须用同一 Python 安装 `skills/cityu-macau-campus-assistant/scripts/requirements-audit.txt` 中的依赖。审计现在会在缺少依赖时立即退出，保留原报告。2026-10-01 报告中的 2,534 项附件提取问题均由依赖缺失触发，不等于官网附件损坏；修复环境也不代表全站完整性已通过。普通用户使用知识库不需要安装这些维护依赖。

维护更新（2026-10-02）：已修复部分历史来源链接及旧失败状态分类。OCR 维护工具使用独立 Python 3.12 环境，配置见[详细说明](docs/guide.md)；普通用户无需安装该环境。网络恢复结果与未覆盖范围见[更新日志](docs/changelog.md)。

## License

[MIT](LICENSE)
