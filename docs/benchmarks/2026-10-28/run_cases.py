"""Explicit opt-in serial live benchmark. Uses account quota; raw logs should stay local.
HTTP provider override applies only to child processes; no global settings changed.
"""
from pathlib import Path
import subprocess,time,json,shutil
import argparse
p=argparse.ArgumentParser();p.add_argument("--root",required=True);p.add_argument("--out",required=True);p.add_argument("--rounds",type=int,default=2);a=p.parse_args()
out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
common="只读能力测试，不修改文件、不联网、不启动其他 agent。使用当前仓库 skills/cityu-macau-campus-assistant/SKILL.md 及其按需引用资料回答，直接回答，不讨论测试。为避免本机中文工具输出乱码，读取中文文件时用 Python UTF-8 解码并以 json.dumps(..., ensure_ascii=True) 输出。"
cases=[
("map_encoded","澳门城市大学氹仔校区地图中的 B1 是地下一层吗？列出正式名称和来源。"),
("fees_status","按本地资料，2027/2028 内地申请人的人工智能硕士学费是多少？课程标为新课程就说明尚未获批、不能招生吗？请分别回答，标明适用年份和来源，不联网。"),
("eligibility","我是 IUSD 2026 级博士，已修完规定课程学分、通过资格考试和开题，有一篇在读期间接收的原创研究论文，与博士论文相关，导师共同署名且投稿前书面同意，IUSD 为第二署名单位。尚未提供期刊名称、活动记录，也不知道论文是否被其他学生认领。请按本地 2026 级规则逐项检查答辩条件，不替学校审批。"),
("mentors","我是硕士申请人，想做计算机视觉。根据本地 FDS 资料推荐方向相关教师，说明导师资格、匹配依据、公开邮箱和来源；不要把方向匹配说成有招生名额。")]
cases = [(name+"_r"+str(round_number), q) for round_number in range(1,a.rounds+1) for name,q in cases]
for name,q in cases:
 start=time.perf_counter()
 try:
  result=subprocess.run([shutil.which("codex"),"exec","--ephemeral","-c",'model_provider="latency-test"',"-c",'model_providers.latency-test={name="Latency test",wire_api="responses",requires_openai_auth=true,supports_websockets=false}',"--json","-s","read-only",common+q],stdin=subprocess.DEVNULL,capture_output=True,timeout=180,cwd=a.root)
  elapsed=time.perf_counter()-start
  (out/(name+".jsonl")).write_bytes(result.stdout)
  (out/(name+".stderr.txt")).write_bytes(result.stderr)
  events=[json.loads(line) for line in result.stdout.decode("utf-8",errors="replace").splitlines() if line.startswith("{")]
  commands=[e["item"] for e in events if e.get("type")=="item.completed" and e.get("item",{}).get("type")=="command_execution"]
  answers=[e["item"].get("text","") for e in events if e.get("type")=="item.completed" and e.get("item",{}).get("type")=="agent_message"]
  usage=next((e.get("usage") for e in events if e.get("type")=="turn.completed"),None)
  meta={"name":name,"question":q,"seconds":elapsed,"returncode":result.returncode,"command_count":len(commands),"tool_output_chars":sum(len(i.get("aggregated_output","")) for i in commands),"usage":usage,"answers":answers,"errors":[e for e in events if e.get("type") in ("error","turn.failed")],"completed":any(e.get("type")=="turn.completed" for e in events)}
  (out/(name+"-meta.json")).write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
  print(json.dumps({k:v for k,v in meta.items() if k not in ("answers","question")},ensure_ascii=False),flush=True)
  if not meta["completed"]: raise SystemExit(2)
  if any("usage limit" in json.dumps(e).lower() for e in meta["errors"]):
   print("STOP: usage limit; remaining cases not attempted",flush=True)
   break
 except subprocess.TimeoutExpired as e:
  (out/(name+".jsonl")).write_bytes(e.stdout or b"")
  (out/(name+"-meta.json")).write_text(json.dumps({"name":name,"completed":False,"timeout":180}),encoding="utf-8")
  print(json.dumps({"name":name,"timeout":180}),flush=True)
  raise SystemExit(2)
