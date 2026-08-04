import json
import time
import functools
import os
from datetime import datetime, timezone

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR,"events.jsonl")
os.makedirs(LOG_DIR,exist_ok=True)

def log_event(event_type:str,**fields):
    try:
        record = {
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "event":event_type,
            **fields,
        }
        with open(LOG_FILE,"a") as f:
            f.write(json.dumps(record,default=str) + "\n")

    except Exception:
        pass


def track_latency(event_type:str):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kwargs):
            start  = time.perf_counter()
            try:
                result = func(*args,**kwargs)
                latency_ms = round((time.perf_counter()-start)*100,1)
                log_event(event_type,function=func.__name__,latency_ms = latency_ms,status="success",result_preview=_preview(result))
                return result
            except Exception as e:
                latency_ms = round((time.perf_counter()-start)*1000,1)
                log_event(
                    event_type,
                    function=func.__name__,
                    latency_ms = latency_ms,
                    status = "error",
                    error = str(e),
                )
                raise
        return wrapper

    return decorator


def _preview(result,max_len:int=150) -> str:
    try:
        text = str(result)
        return text[:max_len] + ("..." if len(text) > max_len else "")

    except Exception:
        return "<unprintable>"



def read_recent_events(limit:int=100) -> list[dict]:
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE,"r") as f:
        lines = f.readlines()[-limit:]
    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return list(reversed(events))



def summarize_events(events:list[dict]) ->dict:
    if not events:
        return {"total":0,"error_rate":0,"avg_latency_ms":0,"by_type":{}}

    total = len(events)
    errors = sum(1 for e in events if e.get("status") == "error")
    latencies = [e["latency_ms"] for e in events if "latency_ms" in e]
    avg_latency = round(sum(latencies)/ len(latencies),1) if latencies else 0
    by_type = {}
    for e in events:
        etype = e.get("event","unknown")
        by_type.setdefault(etype,{"count":0,"error":0,"latencies":[]})
        by_type[etype]["count"] +=1
        if e.get("status") == "error":
            by_type[etype]["errors"] +=1

        if "latency_ms" in e:
            by_type[etype]["latencies"].append(e["latency_ms"])

    for etype, stats in by_type.items():
        lats = stats.pop("latencies")
        stats["avg_latency_ms"] = round(sum(lats)/ len(lats),1) if lats else 0



    return {
        "total":total,
        "error_rate": round(errors/ total*100,1),
        "avg_latency_ms" : avg_latency,
        "by_type" : by_type,
    }


