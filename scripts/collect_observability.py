from __future__ import annotations
import json,os,subprocess
from pathlib import Path
from observability.report import build_summary,parse_json_lines,write_json
from observability.schema import Event
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"observability"/"latest"; RAW=ROOT/"observability"/"raw"; REPO=os.environ.get("GITHUB_REPOSITORY","siasoltoon/forex-signal-bot")
def run(cmd,env=None):
    p=subprocess.run(cmd,text=True,capture_output=True,env=env); return p.returncode,p.stdout,p.stderr
def collect_railway():
    token=os.environ.get("RAILWAY_API_TOKEN"); project=os.environ.get("RAILWAY_PROJECT_ID"); environment=os.environ.get("RAILWAY_ENVIRONMENT_ID"); service=os.environ.get("RAILWAY_SERVICE_ID")
    if not token or not project or not environment:
        write_json(OUT/"railway-status.json",{"status":"not_configured","required":["RAILWAY_API_TOKEN","RAILWAY_PROJECT_ID","RAILWAY_ENVIRONMENT_ID"]}); return []
    env=os.environ.copy(); env["RAILWAY_API_TOKEN"]=token
    cmd=["npx","-y","@railway/cli","logs","--json","--lines",os.environ.get("RAILWAY_LOG_LINES") or "500","--project",project,"--environment",environment]
    if service: cmd += ["--service",service]
    code,out,err=run(cmd,env)
    if code:
        write_json(OUT/"railway-status.json",{"status":"error","error":err[-4000:]}); return []
    events=parse_json_lines(out,"railway","forex-signal-bot"); d=RAW/"railway"; d.mkdir(parents=True,exist_ok=True); (d/"runtime.jsonl").write_text("\\n".join(e.to_json() for e in events)+("\\n" if events else ""),encoding="utf-8")
    write_json(OUT/"railway-status.json",{"status":"ok","event_count":len(events),"project_id":project,"environment_id":environment,"service_id":service}); return events
def collect_github():
    token=os.environ.get("GITHUB_TOKEN")
    if not token: return []
    import urllib.request
    req=urllib.request.Request(f"https://api.github.com/repos/{REPO}/actions/runs?per_page=30",headers={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"})
    with urllib.request.urlopen(req,timeout=30) as r: runs=json.load(r).get("workflow_runs",[])
    events=[]
    for x in runs:
        conclusion=x.get("conclusion"); level="INFO" if conclusion=="success" else ("ERROR" if conclusion in {"failure","timed_out","startup_failure"} else "WARN")
        events.append(Event(timestamp=x.get("updated_at") or x.get("created_at"),source="github",service="actions",level=level,event="workflow_run",message=f'{x.get("name")} => {x.get("status")}/{conclusion}',metadata={"run_id":x.get("id"),"workflow":x.get("name"),"head_sha":x.get("head_sha"),"html_url":x.get("html_url") }))
    write_json(OUT/"github-actions.json",{"status":"ok","run_count":len(events),"runs":[e.to_dict() for e in events]}); return events
def main():
    OUT.mkdir(parents=True,exist_ok=True); railway=collect_railway(); github=collect_github(); events=railway+github; summary=build_summary(events,commit_sha=os.environ.get("GITHUB_SHA")); write_json(OUT/"system-status.json",summary); write_json(OUT/"incident-status.json",{"status":"incident" if summary["errors"] else "healthy","error_count":len(summary["errors"]),"latest_errors":summary["errors"][-20:]}); print(json.dumps({"events":len(events),"railway":len(railway),"github_actions":len(github),"errors":len(summary["errors"])})); return 0
if __name__=="__main__": raise SystemExit(main())
