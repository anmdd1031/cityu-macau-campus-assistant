# 让应用直接使用快速查询

适用于自建 API、后台或能运行本地进程的 Agent 宿主。安装 Skill 本身不会启用此流程。`runtime/host.py` 只依赖 Python 3.9+，每行接收一个 UTF-8 JSON 请求，每行返回一个 JSON 结果，不启动网络服务，也不调用模型。

## 应用如何调用

在应用启动时创建一次进程，后续复用其输入输出管道；每次写入一行请求并 flush，再读取一行结果。单个进程按顺序处理请求，多个调用者共享时由宿主串行调度，避免读错对应响应。关闭时关闭标准输入并等待进程退出。

从仓库根目录启动：

```sh
python skills/cityu-macau-campus-assistant/runtime/host.py
```

以下是四条独立输入，每条占一行：

```jsonl
{"action":"building","code":"B1"}
{"action":"contact","name":"眭相傑"}
{"action":"tuition","course":"人工智能硕士","year":"2027/2028","audience":"mainland"}
{"action":"recommend","query":"计算机视觉","level":"master","limit":5}
```

- `status: answer`：直接展示完整 `answer`，其中已有必要来源或主页、日期及范围；其他字段供宿主保留版本或结构化来源。不要再交给模型改写姓名或“润色”简单答案，否则重新增加模型耗时与抄写风险。
- `status: fallback`：动作、参数或资料范围不适用。保留完整用户问题，转回正常 Skill 工作流，或询问缺失的必要参数；不能把它解释成“学校没有此项资料”。
- `status: error`：输入 JSON 或文件读取出错。交由应用处理，不能将内部错误当成学校事实。坏输入行不会终止后续请求。

Python 宿主的最小可运行示例（从仓库根目录执行）：

```python
import json
from pathlib import Path
import subprocess
import sys

script = Path('skills/cityu-macau-campus-assistant/runtime/host.py').resolve()
worker = subprocess.Popen(
    [sys.executable, str(script)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    text=True, encoding='utf-8',
)
try:
    for request in [
        {'action': 'building', 'code': 'B1'},
        {'action': 'contact', 'name': '眭相傑'},
    ]:
        worker.stdin.write(json.dumps(request, ensure_ascii=False) + '\n')
        worker.stdin.flush()
        line = worker.stdout.readline()
        if not line:
            raise RuntimeError('查询进程已退出')
        result = json.loads(line)
        if result['status'] == 'answer':
            print(result['answer'])  # 应用可把完整文本直接发送给前端
        else:
            print(result)  # 示例诊断；实际应用应接回原有问答/错误处理流程
finally:
    worker.stdin.close()
    worker.wait(timeout=10)
    worker.stdout.close()
```

## 哪些问题可以直接返回

这个入口接收**已经确定类型和参数的结构化请求**，不是自然语言分类器。按钮、表单选择或已验证的应用路由可以提供参数。例如用户同时询问“B1 是什么，还有学费呢”，不能仅提取 B1 并把楼宇答案当作完整答复；无法覆盖全部子问题时交回模型处理。

`tuition` 只支持本地 2027/2028 内地 FDS 对应课程表。`contact` 是原文姓名或 ID 精确匹配。`recommend` 是公开方向的字面初选，结果已注明范围及人数，不代表个性化最优或招生名额；个人经历、研究计划、具体论文贡献等问题继续使用原有证据工作流。

每次请求仍读取当前文件，不缓存旧答案；维护者更新资料后，同一进程的后续请求可见更新。启动首次请求仍有 Python 启动耗时；后续才省去这部分时间。源文件宜完整替换，避免查询撞上维护者写入一半的文件。

## 当前测量范围

本机四类请求各对照 10 次，常驻进程与逐次启动的 JSON 结果完全相同。中位数如下：

| 请求 | 逐次启动 | 常驻进程 |
|---|---:|---:|
| 地图 B1 | 189.849 ms | 0.423 ms |
| 教师邮箱 | 184.882 ms | 0.690 ms |
| 对应届次学费 | 192.444 ms | 6.451 ms |
| 导师字面初选 | 189.071 ms | 2.807 ms |

原始数据和源码版本见 [host-results.json](benchmarks/2026-10-28/host-results.json)，复现脚本为同目录 `bench_host.py`。目录沿用本轮实验起始日期。

这些是“已分类结构化请求 → 完整本地 JSON 响应”的时间，不含自然语言识别、模型、网络及前端渲染。没有下游应用接入证据，不能解释为通用 Agent 已达到毫秒级完整回答。
