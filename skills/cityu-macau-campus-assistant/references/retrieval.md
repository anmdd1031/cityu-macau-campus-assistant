# 按章节读取知识库

这是 Agent 的检索说明，不是学校政策。不需要安装额外依赖；Python 3.9 及以上可选，无 Python 时直接搜索 Markdown 标题并读取完整章节。

命令中的路径相对 Skill 根目录。宿主位于仓库根目录时，前缀为 `skills/cityu-macau-campus-assistant/`。读文件和索引均无网络请求、无文件写入。

## 章节索引

`python runtime/read_sections.py catalog --file freshman.md --query 学费`

实时返回标题、完整上级路径 `path`、唯一章节 `id`、行号、章节结束位置和文件 SHA-256；多个以空格分隔的检索词须同时出现在标题。无匹配时去掉 `--query` 查看该文件目录，再检索正文或同义词，不据此断言没有资料。索引从当前文件生成，无需维护缓存，不会因知识库更新而沿用旧行号。

## 批量读取

`python runtime/read_sections.py read --select "fds.md::3.2" --select "freshman.md::0.2"`

同一调用可重复传入 `--select`，格式为 `文件::完整标题或章节编号`。`*` 表示完整读取小文件。输出保留选中章节的全部子章节、完整表格和备注，同时带上文档页首及各级上级标题的引言、行号和文件哈希；同一文件的重叠片段自动合并。选择不明确时返回所有匹配章节的 ID 和路径，不猜测重复编号。优先复制目录中的 ID，传入 `--select "文件.md::@完整SHA256:标题行号"`。ID 与当前文件版本绑定；文件变动后会返回 `stale_id`，重新获取目录即可，不能直接替换哈希后沿用旧行号。也支持 `文件.md::path:["顶层标题","上级标题","当前标题"]` 的完整路径；路径仍重复时使用 ID。命令行 JSON 引号按宿主 shell 转义，ID 方式更便于直接复制。文件哈希只标识本地版本，不代表官网重新核验。

默认最多返回 24,000 个正文字符，超过时返回结构化 `over_limit` 及可直接读取的子章节 `selector`、包含上级范围的正文字符数和 `fits_budget`，不截断正文。只选择问题需要的子章节；多个叶章节合计超限可分批读取，单个叶章节仍过大时显式增加预算。应改选更小章节；确实需要完整名单或完整证据时显式增加 `--max-chars`。引用来源、年份约束和交叉引用可能位于同级章节，不会自动全部附带：根据目录将必要章节加入同一批读取。不能把片段里没有某项等同于资料库没有。

## 常见批量组合

| 任务 | `read` 后的参数 |
|---|---|
| 氹仔 B1、楼宇图例及官方来源 | `--select "campus_map.md::*"` |
| 2027/2028 内地 FDS 硕博学费及新课程状态边界 | `--select "fds.md::3.2" --select "freshman.md::0.2"` |
| IUSD 2026 级博士辅助检查 | `--select "iusd.md::0." --select "iusd.md::3.8" --select "iusd.md::11."`；不混入 2025 级发表规则 |
| FDS 方向匹配 | `--select "mentors/fds_rules.md::*" --select "mentors/fds_matching_policy.md::*" --select "mentors/fds_mentors.md::*" --max-chars 40000` |

完整官网科研经历仅在问题需要时追加 `mentors/fds_official_evidence.md` 中对应教师章节。教师姓名、邮箱和官方主页按原文复制，姓名不作简繁自动转换或相似字替换。关键词筛选只是召回手段，不能宣称找到了全部语义相关教师。

## 中文输出

读取器明确按 UTF-8 读取和输出。若宿主工具仍损坏中文传输，在子命令前加 `--ascii`，例如 `python runtime/read_sections.py --ascii read --select "campus_map.md::*"`，返回可无损解码的 JSON 转义字符。此方式只用于选中的短片段，不反复转义输出整份大文件。宿主端编码问题不能仅靠 Skill 保证解决。


## 按问题控制证据范围

- 简单事实：优先一次读取对应章节及必要来源，例如校区图例、某届费用。
- 条件对照：按课程、入学年份批量读取相关条件及来源，保留全部限制和例外；证据不足再追加对应章节。
- 教师科研资料：先按姓名定位教师父章节，再从返回的完整路径或 ID 选择其项目/成果；不以重复的“科研项目”等短标题跨教师取第一条。
- 跨学院比较：先列出问题涉及的学院及字段，批量读取各自对应章节，合并去重；超限按完整章节分批，不扩大到整份知识库。

以上为人工编写的检索流程，不是经过训练的 Adaptive-RAG 分类器，不保证自然语言召回完整性。继续用原文作回答证据，不使用自动摘要替代年份、费用或毕业条件。


## 单次证据入口与导师原文表格

`python runtime/query.py bundle map`、`bundle fds-fees-mainland-2027`、`bundle iusd-phd-2026` 分别返回地图、2027/2028 内地 FDS 费用与状态边界、IUSD 2026 博士条件和来源；固定适用范围，不作为通用问题自动分类器。

`python runtime/query.py mentors --query 计算机视觉 --level master` 返回当前 Markdown 解析出的原文结构化记录、规则、口径、人数、版本哈希及可直接复制的表格。计算机视觉/CV 使用公布的视觉、图像及英文同义词，其他查询按字面关键词匹配方向和标签。仅保留明确导师资格（research 不筛硕博资格），按官网原表顺序；这是召回顺序而非质量排名。未命中时扩展词或读原文，不判断不存在相关教师。

对默认推荐先按匹配规则选取候选，以 `python runtime/query.py render --ids 8,9 --sha256 <source_sha256>` 输出选中记录的原文表格。`python runtime/query.py check --ids 8,9 --sha256 <source_sha256> --answer-file <UTF-8草稿>` 要求表格字段与程序生成行完全一致，任何改写、重复或额外表格行均返回退出码 2 和规范表格；通过返回 0。不传 answer-file 时读 UTF-8 标准输入。版本变化时须重新检索。检查不覆盖表格之外的姓名和其他事实，后续宿主输出亦不能由本地脚本强制约束。

这些入口无需第三方库、网络服务或宿主配置变更；宿主支持调用脚本时按上述流程采用。并未自动注册 MCP，也不保证所有 Agent 必然调用。

导师返回字段明确为 `records`（候选详情）、`verbatim_table`（姓名、资格、邮箱、主页四列）、`rules`（匹配规则）。表格保持精简，方向依据按 records 在表外解释；`check` 的输入必须是实际待发送草稿，不能仅将 render 结果再传回充当草稿检查。

## 直接查询与一次生成（2026-10-28）

- `query.py building --code B1`：原始地图表唯一查找，返回名称、地图适用范围、官方链接和原始核验日期。
- `query.py contact --name "眭相傑"`：按原文姓名或 ID 唯一查找邮箱，不接受模糊身份推断。
- `query.py recommend --query 计算机视觉 --level master`：普通方向初选，返回完整 `answer`、匹配规则、人数及版本。按官网方向/标签命中词数排序，同分按官网顺序，默认 5 人；`--limit 0` 返回全部。需明确字面匹配口径；个性化适配仍需模型判断。
- `query.py mentors --query 计算机视觉 --level master --view selection`：个性化分析用，模型只接收候选 ID 与方向等字段，避免重复身份表格。
- `query.py finalize --ids 8,36 --sha256 <版本> --reasons-file reasons.json`：理由文件形如 `{"8":"解释", "36":"解释"}`，必须与 ID 一一对应。表格由程序原文生成并检查；理由不作事实校验。宿主也可直接导入 `finalize(ids, digest, reasons)`。
- `query.py evidence map`：返回原始完整证据文本、行号与文件版本；其他证据包名称与 bundle 相同。

宿主程序直接展示已生成表格时无需重复检查；通用 Agent 的最终答案经过模型生成，即使自认为复制，也须对实际草稿运行 check。recommend/mentors 已返回规则时无需再次读取同一规则文件。关键身份字段不能简繁转换。既有 bundle/mentors/render/check 接口保留。

`query.py tuition --course 人工智能硕士 --year 2027/2028 --audience mainland` 直接查询该届内地 FDS 硕博费用表，返回币种、每学年口径、适用范围、课程列项边界、核验日期和官方来源。参数必须明确；未知课程、其他身份或年份不猜测，转为读取适用原文。

导师普通 Agent 默认仍使用 mentors 返回的原始候选与规则，并校验实际草稿；recommend 仅建议用于宿主直接展示程序结果。实验发现模型可在草稿校验后再次抄错罕见姓名，不能把程序生成成功当成最终答案正确。mentors 返回 check_template 与姓名 Unicode 码位，减少额外帮助查询及罕见字混淆。

### Markdown 姓名无损传递

支持 CommonMark 的客户端可在子命令前加 `--portable-names`，将中文姓名编码成数字字符引用。模型在最终 Markdown 表格和解释中保留引用原样，渲染后显示原始中文；不会替换为别名或改变姓名。普通文本/JSON 数据消费者不加此参数。`check` 按解码后的字段校验，仍拒绝错字、邮箱或主页错配。已用 Markdown-it 验证编码前后表格 HTML 完全相同；运行库仍只依赖 Python 标准库。通用 Agent 的实际草稿校验仍保留，不能把生成器自检当作最终答案保证。
## 应用常驻查询

宿主已确定问题类型和完整参数时，可启动一次 `python runtime/host.py`，用 UTF-8 JSON 行连续请求；每行一个请求并返回一行结果。例如 `{"action":"building","code":"B1"}`。支持 building、contact、tuition、recommend，与 query.py 对应参数相同（recommend 可选 limit）。`status=answer` 时直接展示完整 answer；fallback 转回普通 Skill 问答，error 交宿主处理。该入口不分类自然语言，不能丢掉多问题中的未覆盖部分。进程每次读取当前资料，无答案缓存；共享进程由宿主串行读写。普通一次性 Agent 查询仍用 query.py，无需为了单次问题维持进程。
