# 中国地区安装与使用指南

本指南面向中国大陆用户。最简单的方案不需要 Claude、编程基础、API Key、Git、Node.js 或 MCP。

## 先选一种方案

| 方案 | 适合谁 | 是否上传云端 | 预计时间 |
|---|---|---:|---:|
| A. 国内 AI 直接上传 | 个人查询、第一次使用 | 是 | 2 分钟 |
| B. Open WebUI / Dify 知识库 | 长期使用、团队共享 | 取决于部署方式 | 20-60 分钟 |
| C. Ollama + Qwen 本地运行 | 注重隐私、有较好电脑配置 | 否 | 30-90 分钟 |
| D. MCP 客户端 | 已经会使用 AI 编程工具 | 本地读取 | 10-30 分钟 |

不确定时直接选择 **方案 A**。

## 方案 A：国内 AI 直接上传

### 1. 下载知识库

只下载这一个文件：

[`../dist/cityu-campus-assistant.md`](../dist/cityu-campus-assistant.md)

如果单个文件不好下载：

1. 打开项目 GitHub 首页。
2. 点击绿色的 `Code`。
3. 点击 `Download ZIP`。
4. 解压 ZIP。
5. 打开 `dist` 文件夹。
6. 找到 `cityu-campus-assistant.md`。

不要上传整个 ZIP。只上传 `.md` 文件即可。

### 2. 上传到 AI

#### Kimi

1. 打开 [Kimi](https://www.kimi.com/) 并登录。
2. 新建对话。
3. 点击输入框旁的 `+`。
4. 选择“上传文件”，上传 `cityu-campus-assistant.md`。
5. 等待文件解析完成，再发送初始化提示词。

Kimi 官方帮助中心说明网页和移动端均支持文件上传：[Kimi 新手入门指南](https://www.kimi.com/zh-cn/help/new-user-guide/overview)。

#### DeepSeek

1. 打开 [DeepSeek](https://chat.deepseek.com/) 并登录。
2. 新建对话。
3. 点击回形针或文件上传入口。
4. 上传 `cityu-campus-assistant.md`。
5. 文件处理完成后发送初始化提示词。

DeepSeek 官网目前标明支持文件上传和长文本处理。若当前账号或客户端没有上传入口，可使用 Kimi、豆包或智谱清言。

#### 豆包

1. 打开 [豆包](https://www.doubao.com/) 并登录。
2. 新建对话。
3. 点击上传文件入口。
4. 上传 `cityu-campus-assistant.md`。
5. 文件加载完成后发送初始化提示词。

豆包的文件会进入其云端文件服务。敏感个人材料不要与知识库一起上传。

#### 智谱清言

临时查询可在普通对话中上传文件。需要长期保留时：

1. 打开 [智谱清言智能体](https://chatglm.cn/glms)。
2. 创建一个智能体。
3. 在知识库区域上传 `cityu-campus-assistant.md`。
4. 将下方初始化提示词写入智能体指令。
5. 保存后测试。

智谱清言的官方智能体页面提供知识库文件配置入口，部分配置可能要求实名认证。

### 3. 初始化提示词

```text
你是澳门城市大学校园助手。

请优先依据我上传的知识库回答，不要把澳门城市大学与香港城市大学混淆。
涉及报名日期、费用、奖学金、宿舍、注册、D 签注、逗留许可、课程和毕业要求时，
必须提醒我以澳门城市大学、学院或澳门政府的最新正式通知为准。
如果知识库没有答案，请明确说明无法确认，并给出应联系的学校部门或官方入口；
不要猜测，不要承诺录取、奖学金、宿位、签注审批、论文认定或毕业结果。
```

### 4. 验收问题

依次询问：

```text
你服务的是澳门城市大学还是香港城市大学？
```

```text
内地新生拿到学号是否代表已经完成注册？
```

```text
数据科学硕士是否有论文发表要求？回答时说明信息时效。
```

正确表现应包括：

- 明确服务对象是澳门城市大学。
- 说明取得学号不等于完成全部注册。
- 能说明知识库记载的硕士学术成果要求，同时提示按本人入学年份和学院最新规定确认。

### 5. 常见问题

**AI 说文件太大**

分别上传：

- `knowledge-base/freshman.md`
- `knowledge-base/fds.md`

只问招生、注册、签注、宿舍时，上传 `freshman.md` 即可。

**AI 忘记文件内容**

文件通常只对当前会话有效。回到上传文件的原对话，或重新上传。需要长期保存时使用智谱清言智能体、Open WebUI 或 Dify 知识库。

**回答与官网不一致**

以官网为准。知识库采集日期为 2026-05-22，高时效信息可能已经更新。

## 方案 B：Open WebUI 或 Dify 知识库

该方案适合长期使用、固定助手或团队共享。推荐接入中国大陆可正常申请的模型服务：

- DeepSeek
- 阿里云百炼/通义千问
- 智谱 GLM
- Kimi API

这些平台均提供 OpenAI 兼容接口，通常只需配置 `Base URL`、`API Key` 和模型名称：

- [DeepSeek API 文档](https://api-docs.deepseek.com/)
- [阿里云百炼 OpenAI 兼容接口](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope)
- [智谱 OpenAI API 兼容文档](https://docs.bigmodel.cn/cn/guide/develop/openai/introduction)
- [Kimi 从 OpenAI 接口迁移](https://platform.kimi.com/docs/guide/migrating-from-openai-to-kimi)

API 服务通常按量计费。创建 Key 后不要截图公开，也不要提交到 GitHub。

### Open WebUI

Open WebUI 支持 OpenAI 兼容服务、Ollama 和知识库。官方资料：

- [Open WebUI 安装](https://docs.openwebui.com/getting-started/)
- [连接 OpenAI 兼容服务](https://docs.openwebui.com/getting-started/quick-start/connect-a-provider/starting-with-openai-compatible/)
- [Knowledge 知识库](https://docs.openwebui.com/features/workspace/knowledge/)

安装后：

1. 进入管理员设置。
2. 在 `Connections -> OpenAI` 添加国产模型的 Base URL 和 API Key。
3. 进入 `Workspace -> Knowledge`。
4. 创建 `澳门城市大学校园助手` 知识库。
5. 上传 `freshman.md` 和 `fds.md`。
6. 创建模型预设，把知识库和初始化提示词绑定到模型。

分开上传两个源文件通常比上传合并文件更利于检索。

### Dify

Dify 适合通过图形界面建立聊天助手、知识库和工作流。官方资料：

- [Dify 简介](https://docs.dify.ai/zh/use-dify/getting-started/introduction)
- [创建知识库](https://docs.dify.ai/zh/use-dify/knowledge/create-knowledge/introduction)

基本步骤：

1. 在 Dify 的模型供应商设置中配置 DeepSeek、通义千问、GLM 或 Kimi。
2. 点击“知识库 -> 创建知识库”。
3. 上传 `freshman.md` 和 `fds.md`。
4. 检查自动分段效果，不要把每段切得过短。
5. 创建聊天助手并关联知识库。
6. 将初始化提示词放入系统指令。
7. 用验收问题测试召回效果。

## 方案 C：Ollama + Qwen 本地运行

该方案可以让模型和知识文件保留在本机，但安装更复杂，回答质量也取决于硬件和模型大小。

### 硬件建议

以下只是实用参考，不是硬性要求：

| 可用内存 | 建议 |
|---:|---|
| 8 GB | 不推荐完整本地知识库体验，可尝试小模型 |
| 16 GB | 可尝试 4B-8B 量化模型 |
| 32 GB | 可尝试 14B 左右模型 |
| 64 GB 及以上 | 可使用更大模型，效果通常更好 |

模型还会占用数 GB 到数十 GB 磁盘空间。

### 安装 Ollama

从 [Ollama 官方下载页](https://ollama.com/download/windows) 安装。Windows 需要 Windows 10 或更高版本。

安装后打开 PowerShell：

```powershell
ollama run qwen3:8b
```

首次运行会下载模型。模型列表和可用尺寸见 [Ollama Qwen3](https://ollama.com/library/qwen3)。

### 配合 Open WebUI

仅使用 Ollama 命令行不方便管理大型知识库。建议再安装 Open WebUI：

1. 按 [Open WebUI 安装指南](https://docs.openwebui.com/getting-started/)完成安装。
2. 确认 Open WebUI 能看到 Ollama 模型。
3. 创建知识库并上传 `freshman.md` 和 `fds.md`。
4. 把知识库绑定到 Qwen 模型预设。
5. 添加初始化提示词并运行验收问题。

若 Open WebUI 在 Docker 中，而 Ollama 运行在 Windows 主机，连接地址通常不能写 `localhost`，应按官方说明使用 `host.docker.internal`。

## 方案 D：MCP 客户端

### 先理解本项目是什么

本仓库是 `SKILL.md + Markdown 知识库`，**不是独立 MCP Server**。MCP 方案的作用是让支持 MCP 的客户端读取本地仓库文件。

官方 Filesystem MCP Server 包名是：

```text
@modelcontextprotocol/server-filesystem
```

参考：

- [MCP 本地服务器指南](https://modelcontextprotocol.io/docs/develop/connect-local-servers)
- [官方 Filesystem Server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)

### 前置要求

1. 安装 Node.js LTS。
2. 下载并解压本仓库。
3. 确认客户端支持本地 stdio MCP Server。

### 配置模板

复制 [`../config/mcp.filesystem.example.json`](../config/mcp.filesystem.example.json) 的内容到客户端 MCP 配置中，然后修改最后一个路径。

Windows 示例：

```json
{
  "mcpServers": {
    "cityu-campus-assistant": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "D:\\AI\\cityu-macau-campus-assistant"
      ]
    }
  }
}
```

macOS 示例路径：

```text
/Users/your-name/Downloads/cityu-macau-campus-assistant
```

Linux 示例路径：

```text
/home/your-name/cityu-macau-campus-assistant
```

注意：

- Windows JSON 路径中的反斜杠必须写成 `\\`。
- 只授权本仓库目录，不要授权整个用户目录或磁盘。
- 修改配置后完全退出并重启客户端。
- 首次运行 `npx` 需要联网下载 MCP Server 包。

如果 MCP 启动失败：

1. 在终端运行 `node --version` 和 `npx --version`，确认 Node.js 已安装。
2. 将项目移动到不含空格和中文的短路径，例如 `C:\AI\cityu-macau-campus-assistant`。
3. 确认配置中的目录真实存在。
4. 检查 Windows 路径是否使用了双反斜杠。
5. 完全退出客户端后重新打开。

### Claude Desktop

Claude Desktop 只适用于 Anthropic 官方支持地区的用户。Anthropic 于 2026-03-16 更新的[支持地区列表](https://support.anthropic.com/en/articles/8461763-where-can-i-access-claude-ai)不包含中国大陆。

本项目不建议中国大陆用户注册、配置或绕过限制使用 Claude。使用 Cursor、Windsurf、VS Code 插件或其他 MCP 客户端时，也应选用在所在地合法可用的模型服务。

## 不会使用 GitHub 怎么办

### 下载整个项目

1. 打开项目页面。
2. 点击绿色 `Code` 按钮。
3. 点击 `Download ZIP`。
4. 下载完成后右键解压。

不需要安装 Git。

### GitHub 打不开或下载慢

项目维护者可以在 GitHub Releases、学校网盘或可信国内对象存储中同步发布 `cityu-campus-assistant.md`。用户应核对文件来源，避免下载第三方修改版。

本指南不提供来路不明的 GitHub 镜像或代理站点。

## 维护者：重新生成合并文件

源文件更新后，在仓库根目录运行。

Windows：

```powershell
.\scripts\build-knowledge.ps1
```

macOS / Linux：

```bash
sh scripts/build-knowledge.sh
```

验证安装包：

```powershell
.\tests\verify-package.ps1
```

输出文件：

```text
dist/cityu-campus-assistant.md
```

不要直接编辑 `dist` 文件，应修改 `SKILL.md` 或 `knowledge-base` 中的源文件后重新生成。

## 隐私与安全

- 公开知识库本身不含个人申请资料。
- 不要上传身份证、港澳通行证、录取通知书、成绩单、缴费凭证、签注或入境凭条。
- 如需咨询个人情况，先遮盖姓名、证件号码、地址、二维码、条形码和申请编号。
- 云端 AI、API 和知识库平台的数据处理规则不同，上传前阅读对应隐私政策。
- MCP Filesystem Server 具备文件访问能力，只授权必要目录。

## 信息过期时怎么办

优先级如下：

1. 澳门城市大学或学院当年正式公告。
2. 澳门特区政府及治安警察局页面。
3. 本项目知识库。
4. 第三方平台、论坛和社交媒体。

若发现知识库内容过期，请在 GitHub 提交 Issue，并提供官方新页面链接和明确的变更位置。
