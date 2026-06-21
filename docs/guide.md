# 澳门城市大学校园助手 Skill 详细说明

这是根目录 [README](../README.md) 的详细版，保留完整安装方式、Agent 目录、中国大陆地区限制、使用示例和项目结构说明。

面向澳门城市大学学生、申请人和家长的可复用 Agent Skill。它会按问题读取对应资料，帮助回答：

- 招生、报名、学费、奖学金、注册、体检、D 签注、逗留许可、宿舍和校园服务
- 数据科学学院（FDS）本硕博课程、学分、转专业、导师、论文成果和毕业要求
- 台风、暴雨等恶劣天气下的学校安排

它不会把澳门城市大学（City University of Macau）与香港城市大学混淆。

## 效果示例

**问：拿到学号是不是就完成注册了？**

> 不是。取得学号通常只是流程的一部分，还需按通知完成缴费、网上报到、体检、证件办理、现场或系统注册等步骤。具体日期必须以你所属学年的最新注册通知为准。

**问：数据科学硕士一定要发表论文吗？**

> 现有公开资料要求 MDS 至少取得 1 项学校认可的学术成果，但认可范围可能包括论文、专利或软件著作权，并不等于只能发表期刊论文。投稿前应让导师或学院书面确认成果类型、署名和单位是否符合你入学年份的规定。

**问：GPA 3.7 能保证转入 BCS 吗？**

> 不能保证。3.7 是往年公告中的推荐参考，是否开放申请、笔试面试、名额和最终录取均以当年公告及学院审核为准。

**问：根据我的成绩预测录取概率。**

> 本 Skill 不提供个性化录取概率或“稳录”判断，但可以整理官方申请条件、材料、时间和咨询入口。

## 能力与边界

| 可以做 | 不可以做 |
|---|---|
| 整理公开的申请、注册和校园办事流程 | 保证录取、奖学金、宿位、签注、转专业或毕业结果 |
| 解释 FDS 公开课程和学业要求 | 代替学校认定论文、学分、毕业资格或个案审批 |
| 根据身份和学年提示应查的规则 | 根据不完整成绩、简历或论文预测审批结果 |
| 提供学校及澳门政府官方入口 | 代替移民、法律、财务或医疗专业意见 |
| 提醒高时效信息需要再次核验 | 查询个人成绩、课表、考场或登录私人学生系统 |

资料未覆盖的问题会明确说明无法确认，并指向对应官方部门，不会编造答案。

## 安装前要求

本 Skill 由 Markdown 和 YAML 文件组成，**不要求安装 Python、Java 或其他编程语言**。

| 安装方式 | 要求 |
|---|---|
| 让 Agent 安装 | 一个支持 Agent Skills 的应用，以及可访问 GitHub 的网络 |
| 下载 ZIP 后手动放置 | 不需要 Git、Node.js 或命令行 |
| 使用 `npx skills` 安装 | [Node.js 18 或更高版本](https://nodejs.org/)；安装 Node.js 时会附带 `npm` 和 `npx` |

## 方式一：直接告诉 Agent 安装

这是最简单的方式。把下面整段话发送给支持 Agent Skills 的应用：

```text
请帮我安装这个 Skill：
https://github.com/anmdd1031/cityu-macau-campus-assistant

安装完成后，请告诉我安装位置，并确认 SKILL.md 可以被识别。
```

如果应用询问安装范围：

- 选择“当前项目”，只在当前工作目录使用。
- 选择“全局”或“用户级”，在该应用的所有项目中使用。

安装后重新打开应用或开始一个新会话，然后直接提问即可。

## 中国大陆常见 Agent

下表列出截至 **2026-06-15** 已被通用 [`skills` CLI](https://github.com/vercel-labs/skills) 支持、且在中国大陆通常有本地版本或可配合大陆可用模型使用的常见 Agent。产品、账号、地区和模型政策会变化，这不是“所有 Agent”的永久完整名单。

### 通常优先考虑

| Agent | CLI 名称 | 当前项目中的 Skill 目录 | 用户级目录 | 说明 |
|---|---|---|---|---|
| Qwen Code | `qwen-code` | `.qwen/skills/` | `~/.qwen/skills/` | 通义千问代码 Agent |
| Kimi Code CLI | `kimi-code-cli` | `.agents/skills/` | `~/.agents/skills/` | 可使用 Kimi 服务 |
| Qoder 中国版 | `qoder-cn` | `.qoder/skills/` | `~/.qoder-cn/skills/` | 应选择中国版 |
| Trae 中国版 | `trae-cn` | `.trae/skills/` | `~/.trae-cn/skills/` | 应选择中国版 |
| CodeBuddy | `codebuddy` | `.codebuddy/skills/` | `~/.codebuddy/skills/` | 账号与功能以产品当前说明为准 |
| WorkBuddy | 暂无独立 `workbuddy` CLI 目标 | 按应用内 Skills/技能市场或手动导入 | 以应用当前版本为准 | 腾讯云 CodeBuddy 团队产品；不要写成 `-a workbuddy` |
| 通义灵码 Lingma | `lingma` | `.lingma/skills/` | `~/.lingma/skills/` | 阿里云代码助手 |
| iFlow CLI | `iflow-cli` | `.iflow/skills/` | `~/.iflow/skills/` | 模型可用范围以当前版本为准 |
| CodeArts Agent | `codearts-agent` | `.codeartsdoer/skills/` | `~/.codeartsdoer/skills/` | 华为云开发工具链产品 |

### 取决于你配置的模型

这些客户端本身支持 Skills，但能否在中国大陆正常工作，主要取决于所配置的模型、API 服务和账号地区：

| Agent | CLI 名称 | 当前项目中的 Skill 目录 | 用户级目录 |
|---|---|---|---|
| Cline | `cline` | `.agents/skills/` | `~/.agents/skills/` |
| Roo Code | `roo` | `.roo/skills/` | `~/.roo/skills/` |
| OpenCode | `opencode` | `.agents/skills/` | `~/.config/opencode/skills/` |
| Continue | `continue` | `.continue/skills/` | `~/.continue/skills/` |
| Cursor | `cursor` | `.agents/skills/` | `~/.cursor/skills/` |

## GPT / Codex

### Codex 安装

在 Codex 中直接发送：

```text
请使用 $skill-installer 安装这个 Skill：
https://github.com/anmdd1031/cityu-macau-campus-assistant
```

也可以使用通用 CLI：

```bash
npx skills add https://github.com/anmdd1031/cityu-macau-campus-assistant -g -a codex
```

手动安装时，将完整 Skill 文件夹放到：

- 当前项目：`.agents/skills/cityu-macau-campus-assistant/`
- 用户级：`~/.agents/skills/cityu-macau-campus-assistant/`

Codex CLI、IDE 扩展和 Codex 应用均可识别 Skills。安装后未出现时，重新启动 Codex。详见 [OpenAI Codex Agent Skills 文档](https://developers.openai.com/codex/skills)。

### ChatGPT 自定义 GPT

ChatGPT 自定义 GPT 不直接读取本地 Agent Skills 目录，但可以用“Instructions + Knowledge”方式适配：

1. 在 ChatGPT 的 GPTs 页面选择 **Create**。
2. 将 `SKILL.md` 正文放入 GPT 的 **Instructions**。
3. 将 `references/freshman.md` 和 `references/fds.md` 上传到 **Knowledge**。
4. 在 Preview 中测试示例问题后保存。

创建或编辑自定义 GPT 需要付费订阅；仅聊天的用户也可以在 ChatGPT Project 中上传两份 reference，并把 `SKILL.md` 作为项目指令。详见 [OpenAI 创建 GPT 文档](https://help.openai.com/en/articles/8554397-creating-and-editing-gpts)。

> **中国大陆地区限制：** OpenAI 的[支持国家和地区列表](https://help.openai.com/en/articles/7947663-chatgpt-supported-countries)不包含中国大陆。官方说明指出，从未列出的地区访问或提供访问可能导致账号被阻止或暂停。本项目不提供绕过地区限制的方法。

## Gemini

### Gemini CLI 安装

Gemini CLI 已原生支持 Agent Skills。用户级安装：

```bash
gemini skills install https://github.com/anmdd1031/cityu-macau-campus-assistant --path skills/cityu-macau-campus-assistant --scope user
```

只安装到当前工作区：

```bash
gemini skills install https://github.com/anmdd1031/cityu-macau-campus-assistant --path skills/cityu-macau-campus-assistant --scope workspace
```

手动安装目录：

- 当前项目：`.gemini/skills/cityu-macau-campus-assistant/` 或 `.agents/skills/cityu-macau-campus-assistant/`
- 用户级：`~/.gemini/skills/cityu-macau-campus-assistant/` 或 `~/.agents/skills/cityu-macau-campus-assistant/`

进入 Gemini CLI 后运行 `/skills list` 检查；未显示时运行 `/skills reload`。详见 [Gemini CLI Agent Skills 文档](https://geminicli.com/docs/cli/skills/)。

### Gemini 网页版 Gem

网页版 Gemini 不读取本地 Skill 目录，但可以创建 Gem：

1. 打开 Gemini 的 **Gems > New Gem**。
2. 将 `SKILL.md` 正文放入 Instructions。
3. 在 Knowledge 中上传 `freshman.md` 和 `fds.md`。
4. 预览并保存。

这种方式是对知识和指令的适配，不具备 Gemini CLI 的 Skill 自动发现和按需激活机制。详见 [Google Gems 文档](https://support.google.com/gemini/answer/15146780)。

> **中国大陆地区限制：** Google AI Studio 和 Gemini API 的[可用地区列表](https://ai.google.dev/gemini-api/docs/available-regions)不包含中国大陆。Gemini CLI 通常依赖 Google 账号及 Gemini 服务，因此不作为中国大陆默认方案。

## Claude

### Claude 网页版或桌面版

Claude 已支持直接上传自定义 Skill：

1. 下载本仓库 ZIP 并解压。
2. 找到 `skills/cityu-macau-campus-assistant/`。
3. 将这个 Skill 文件夹单独压缩为 ZIP，不要直接上传整个仓库 ZIP。
4. 在 Claude 打开 **Customize > Skills**。
5. 点击 **+ > Create skill > Upload a skill**，上传刚才的 ZIP 并启用。

详见 [Claude 自定义 Skills 文档](https://support.claude.com/en/articles/12512180-use-skills-in-claude)。

### Claude Code

使用通用 CLI：

```bash
npx skills add https://github.com/anmdd1031/cityu-macau-campus-assistant -g -a claude-code
```

或手动复制到：

- 当前项目：`.claude/skills/cityu-macau-campus-assistant/`
- 用户级：`~/.claude/skills/cityu-macau-campus-assistant/`

Claude Code 可自动按描述调用，也可输入 `/cityu-macau-campus-assistant` 显式调用。详见 [Claude Code Skills 文档](https://code.claude.com/docs/en/skills)。

> **中国大陆地区限制：** Anthropic 的[Claude 支持地区列表](https://support.claude.com/en/articles/8461763-where-can-i-access-claude)不包含中国大陆。Claude 和 Claude Code 均不作为中国大陆默认方案，本项目不提供绕过地区限制的方法。

## 方式二：通用命令安装

已安装 Node.js 18+ 的用户，可在终端执行：

```bash
npx skills add https://github.com/anmdd1031/cityu-macau-campus-assistant
```

默认安装到当前项目。安装为用户级 Skill：

```bash
npx skills add https://github.com/anmdd1031/cityu-macau-campus-assistant -g
```

也可以明确指定 Agent，例如：

```bash
npx skills add https://github.com/anmdd1031/cityu-macau-campus-assistant -g -a qwen-code
npx skills add https://github.com/anmdd1031/cityu-macau-campus-assistant -g -a kimi-code-cli
```

命令显示多个目标时，选择你实际使用的 Agent。CLI 的参数和受支持 Agent 以 [`vercel-labs/skills`](https://github.com/vercel-labs/skills) 当前文档为准。

## 方式三：下载 ZIP 后手动放置

1. 打开本仓库，点击 **Code > Download ZIP**。
2. 解压后找到：

   ```text
   cityu-macau-campus-assistant-main/
   └── skills/
       └── cityu-macau-campus-assistant/
   ```

3. 将完整的 `cityu-macau-campus-assistant` 文件夹复制到 Agent 的项目级或用户级 Skill 目录。目录位置见上方 Agent 表。
4. 检查最终结构。`SKILL.md` 必须直接位于 Skill 文件夹内：

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

上例适用于使用 `.agents/skills/` 的 Agent。Qwen Code 应放到 `.qwen/skills/`，Qoder 中国版应放到 `.qoder/skills/`，其他应用按表格替换目录即可。不要只复制 `SKILL.md`，否则校园和学院参考资料不会随 Skill 一起加载。

## 不支持 Agent Skills 的应用

可以把 `SKILL.md` 作为系统提示词或项目规则，并在提问时同时提供 `references/freshman.md` 和 `references/fds.md`。这种方式通常不会自动路由资料，也不一定能跨会话保存，效果取决于具体应用。

## 使用方法

安装后可直接提问：

```text
澳门城市大学内地本科新生拿到学号后还要完成哪些注册步骤？
```

也可以显式指定 Skill：

```text
使用 $cityu-macau-campus-assistant 查询 MDS 的学分和成果要求。
```

高时效问题请明确身份和学年，例如：

```text
我是 2026/2027 学年内地硕士新生，请核对最新的 D 签注、入境和注册流程。
```

## 更新

命令行安装可执行 `npx skills update cityu-macau-campus-assistant`；手动安装则重新下载 ZIP 并替换原 Skill 文件夹。

## 项目结构

```text
skills/cityu-macau-campus-assistant/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── references/
    ├── freshman.md
    └── fds.md
```

Skill 会根据问题选择相关 reference，不会在每次对话中无差别加载全部资料。
两份 reference 由本项目原 `knowledge-base/freshman.md` 和 `knowledge-base/fds.md` 完整迁入，保留原知识库内容，不使用此前的精简摘要替代。

> 校园与课程资料核验日期：2026-05-22。招生日期、费用、宿舍、签注、注册和学业规则以最新官方通知为准。

## License

[MIT](../LICENSE)
