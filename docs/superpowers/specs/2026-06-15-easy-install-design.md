# 傻瓜化安装改造设计

## 目标

让中国大陆用户无需 Claude、Git、Node.js 或 MCP 配置即可使用本项目。默认流程应缩短为：下载一个文件、上传到常用国内 AI、开始提问。

## 用户路径

### 默认路径：直接上传

仓库提供预合并的 `dist/cityu-campus-assistant.md`。用户从 GitHub 下载该文件，上传到 Kimi、DeepSeek、豆包或智谱清言，并发送一条固定的初始化提示词。

该路径不要求安装软件或申请 API Key，作为 README 首页唯一的推荐路径。

### 进阶路径：知识库平台

需要长期保存、多人共享或更稳定检索的用户，可将两个知识库源文件或预合并文件导入 Open WebUI、Dify 等知识库平台，并接入 DeepSeek、通义千问、GLM 或 Kimi API。

### 隐私路径：本地模型

用户可通过 Ollama 运行 Qwen，并使用 Open WebUI 建立本地知识库。该路径需要较多磁盘、内存和安装步骤，因此只放在详细指南中。

### MCP 路径

仅供已经使用 MCP 客户端的用户。配置采用官方包 `@modelcontextprotocol/server-filesystem`，并说明本仓库自身不是 MCP Server。

Claude Desktop 仅列为 Anthropic 支持地区用户的可选客户端，不作为中国大陆用户的安装建议。

## 仓库结构

- `README.md`：项目介绍、三步快速开始、下载入口、详细指南入口。
- `docs/INSTALL_CN.md`：中国地区完整安装指南、各平台操作、MCP、本地部署和故障排查。
- `dist/cityu-campus-assistant.md`：可直接上传的合并知识文件。
- `scripts/build-knowledge.ps1`：Windows 生成或更新合并文件。
- `scripts/build-knowledge.sh`：macOS/Linux 生成或更新合并文件。
- `config/mcp.filesystem.example.json`：正确的 MCP 配置模板。
- `tests/verify-package.ps1`：验证合并顺序、必要内容、配置 JSON 和文档链接目标。

## 合并规则

输出文件依次包含：

1. 项目名称、生成说明和使用提示；
2. `SKILL.md`；
3. `knowledge-base/freshman.md`；
4. `knowledge-base/fds.md`。

脚本统一使用 UTF-8，确保中文不会乱码。生成文件包含来源边界标记，便于排查和更新。

## 安全与边界

- 不引导中国大陆用户绕过地区限制使用 Claude。
- 不要求用户把整个磁盘暴露给 MCP，只授权本仓库目录。
- 提醒用户不要上传身份证、录取通知书、签注等个人敏感文件。
- 强调招生日期、费用、签注和宿舍信息仍应以官方最新公告为准。

## 验收标准

- 新用户在 README 首屏可以找到不超过三步的使用方法。
- 合并文件可由脚本重复生成，内容顺序稳定且为 UTF-8。
- Windows 与 macOS/Linux 脚本生成结果字节一致。
- MCP 示例是合法 JSON，并使用正确 npm 包名。
- README 和详细指南中的仓库内链接均存在。
- 文档明确说明中国大陆默认不使用 Claude。
