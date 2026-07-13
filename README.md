# 澳门城市大学校园助手 Skill

**开 发 者：** 金添、李俞萱、金泽同

**指导老师：** 蔡剑平

**研发单位：** 澳门城市大学 数据科学学院


大学里的很多问题，并不是没有答案，而是答案分散在不同部门、不同网页、不同公告和不同时间节点里。对新生和在校生来说，真正消耗精力的往往不是理解规则本身，而是在注册、缴费、签注、宿舍、课程、论文和毕业要求之间反复搜索、比对和确认。

`cityu-macau-campus-assistant` 是一个面向 AI Agent 的澳门城市大学公开信息 Skill。它将澳城大新生入学、校园办事、学院课程、学分要求、论文成果、毕业规则和校内餐饮等资料整理为结构化知识库，让 AI Agent 不只是回答“看起来正确”的内容，而是尽量基于公开资料、按照具体场景、带着边界意识回答问题。

这个项目的价值不在于替代学校官方通知，而在于帮助学生更快理解公开规则、定位办事入口、减少重复搜索和信息误读。对于准备报考、刚拿到录取、准备来澳注册，或正在查询学院培养方案和毕业要求的学生来说，它可以作为一个更清晰、更易用的校园信息入口。

它只整理公开资料，不替学校做录取、签注、转专业、论文认定、学分确认或毕业审批。涉及招生时间、费用、宿舍、签注、注册和毕业规则等高时效或个案事项时，最终仍应以澳门城市大学、相关学院及澳门政府部门的最新正式通知为准。

## 最简单安装方法

打开微信小程序WorkBuddy，注册并登录，选择‘云端工作’

把下面这段话复制给WorkBuddy：

```text
请帮我安装这个 Skill：
https://github.com/anmdd1031/cityu-macau-campus-assistant

安装完成后，请告诉我安装位置，并确认 SKILL.md 可以被识别。
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

也可以指定这个 Skill：

```text
使用 $cityu-macau-campus-assistant 查询 MDS 的学分和成果要求。
```

## 这个 Skill 能做什么

可以：

- 整理公开的申请、注册、宿舍、签注和校园办事流程
- 解释 FDS、FOB、FOF、FH、FE、FL、FITM 和荣誉班公开课程、学分、论文成果和毕业要求
- 按来源等级、论文主题和贡献证据查询 FDS 教师近期方向，并给出可解释的候选导师、校内工作邮箱和主页
- 查询氹仔校区校内餐饮、菜单、价格和供应时段
- 提醒哪些信息需要看最新官方通知

不可以：

- 保证录取、奖学金、宿位、签注、转专业或毕业
- 代替学校做个案审批
- 查询个人成绩、课表、考场或私人账号
- 代替法律、移民、财务或医疗意见

## 更多说明

- [完整说明文档](docs/guide.md)
- [更新日志](docs/changelog.md)
- [Skill 主文件](skills/cityu-macau-campus-assistant/SKILL.md)
- [新生与校园知识库](skills/cityu-macau-campus-assistant/references/freshman.md)
- [数据科学学院知识库](skills/cityu-macau-campus-assistant/references/fds.md)
- [数据科学学院导师基础画像（官网师资、资格、方向、项目及招募说明）](skills/cityu-macau-campus-assistant/references/mentors/fds_mentors.md)
- [数据科学学院教师论文检索索引](skills/cityu-macau-campus-assistant/references/mentors/fds_papers.md)
- [FDS 导师匹配与贡献证据规则](skills/cityu-macau-campus-assistant/references/mentors/fds_rules.md)
- [商学院知识库](skills/cityu-macau-campus-assistant/references/fob.md)
- [金融学院知识库](skills/cityu-macau-campus-assistant/references/fof.md)
- [大健康学院知识库](skills/cityu-macau-campus-assistant/references/fh.md)
- [教育学院知识库](skills/cityu-macau-campus-assistant/references/fe.md)
- [法学院知识库](skills/cityu-macau-campus-assistant/references/fl.md)
- [国际旅游与管理学院知识库](skills/cityu-macau-campus-assistant/references/fitm.md)
- [荣誉班知识库](skills/cityu-macau-campus-assistant/references/honours_class.md)
- [氹仔校区餐饮指南](skills/cityu-macau-campus-assistant/references/澳门城市大学氹仔校区_校内餐饮指南.md)

> 知识库资料核验日期：新生与 FDS 课程资料为 2026-05-22；FDS 师资、邮箱与近期论文为 2026-07-12；商学院、大健康学院资料为 2026-06-21；金融学院、教育学院、法学院、荣誉班资料为 2026-06-22；国际旅游与管理学院资料为 2026-06-29。招生日期、费用、宿舍、签注、注册、师资和学业规则以最新官方通知为准。

## License

[MIT](LICENSE)
