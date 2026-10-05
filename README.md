# 澳门城市大学智能校园助手agent

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
- 提醒哪些信息需要看最新官方通知

不可以：

- 保证录取、奖学金、宿位、签注、转专业或毕业
- 代替学校做个案审批
- 查询个人成绩、课表、考场或私人账号
- 代替法律、移民、财务或医疗意见
- 对个人、学院或群体作政治立场推断、政治可靠性评价，或按国籍、民族、宗教等无关敏感属性筛选和排序

本智能校园助手仅整合校园公开信息供参考，不替代澳门城市大学官方通知，不具备招生、签注、学分、毕业等审批效力。所有办事、升学、毕业相关事宜，请以学校、学院及澳门相关部门最新正式公告为准，使用者依据助手内容做出的相关决策，责任由本人自行承担。
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
