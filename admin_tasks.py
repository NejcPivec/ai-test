"""
admin_tasks.py
Upravljanje admin ozadnih nalog (crawl, indexiranje).

Vsaka naloga dobi unikaten task_id.
Status se hrani v spominu — ob restartu strežnika se izgubi.
"""

import uuid
import traceback
from datetime import datetime
from enum import Enum
from typing import Callable


class TaskStatus(str, Enum):
    PENDING  = "pending"
    RUNNING  = "running"
    DONE     = "done"
    ERROR    = "error"


# Shramba statusov nalog
_tasks: dict[str, dict] = {}


def create_task(name: str) -> str:
    """Ustvari novo nalogo in vrne task_id."""
    task_id = str(uuid.uuid4())[:8]
    _tasks[task_id] = {
        "id":         task_id,
        "name":       name,
        "status":     TaskStatus.PENDING,
        "started_at": None,
        "finished_at": None,
        "message":    "Čakam na zagon...",
        "error":      None,
    }
    return task_id


def get_task(task_id: str) -> dict | None:
    return _tasks.get(task_id)


def get_all_tasks() -> list[dict]:
    return sorted(_tasks.values(), key=lambda t: t.get("started_at") or "", reverse=True)


def run_task(task_id: str, fn: Callable, *args, **kwargs):
    """
    Izvede funkcijo kot ozadno nalogo.
    Pokliči iz FastAPI BackgroundTasks:
        background_tasks.add_task(run_task, task_id, moja_funkcija, arg1, arg2)
    """
    task = _tasks.get(task_id)
    if not task:
        return

    task["status"] = TaskStatus.RUNNING
    task["started_at"] = datetime.now().isoformat()
    task["message"] = "Teče..."

    try:
        result = fn(*args, **kwargs)
        task["status"] = TaskStatus.DONE
        task["message"] = result if isinstance(result, str) else "Uspešno zaključeno."
    except Exception as e:
        task["status"] = TaskStatus.ERROR
        task["error"] = traceback.format_exc()
        task["message"] = f"Napaka: {str(e)}"
    finally:
        task["finished_at"] = datetime.now().isoformat()