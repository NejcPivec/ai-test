import csv
import io

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal, Optional
from contextlib import asynccontextmanager
import uvicorn
from starlette.responses import StreamingResponse

from ollama_service import ask_ollama
from rag_service import get_context
from router_service import classify_intent
from db_service import init_db, save_message, save_rating, get_conn
from search_formatter import format_tektonika_answer
from admin_tasks import create_task, get_task, get_all_tasks, run_task, TaskStatus
from guard_service import (
    GUARD_BLOCK_MESSAGE,
    GuardUnavailableError,
    UnsafeContentError,
    assert_safe,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("VAC Chat streznik zagnan!")
    yield


app = FastAPI(title="VAČ Chat API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

session_history = {}


class ChatRequest(BaseModel):
    message: str
    userType: Literal["KU", "NU"] = "KU"
    userId: str
    currentPage: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    messageId: int


class RatingRequest(BaseModel):
    messageId: int
    rating: int


# ── Chat endpointi ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    history = session_history.get(request.userId, [])

    try:
        assert_safe(request.message, "input")
    except UnsafeContentError:
        answer = GUARD_BLOCK_MESSAGE
        message_id = save_message(request.userId, request.userType, request.message, answer)
        return ChatResponse(answer=answer, messageId=message_id)
    except GuardUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail="Varnostnega preverjanja trenutno ni mogoče izvesti.",
        ) from exc

    route = classify_intent(
        message=request.message,
        current_page=request.currentPage
    )
    route["current_page"] = request.currentPage

    search_query = request.message
    if request.currentPage and route["intent"] in ("faq", "navigation"):
        search_query = f"{request.message}\n[stran: {request.currentPage}]"

    context = ""
    if route.get("should_use_rag", True):
        context = get_context(
            question=search_query,
            user_type=request.userType,
            current_page=request.currentPage,
            intent=route["intent"],
            corpus=route["corpus"]
        )

    answer = None

    if route["intent"] == "search" and route["corpus"] in ("tektonika", "mixed"):
        answer = format_tektonika_answer(request.message, context)

    if not answer:
        answer = await ask_ollama(
            message=request.message,
            user_type=request.userType,
            route=route,
            context=context,
            history=history
        )

    try:
        assert_safe(answer, "output")
    except UnsafeContentError:
        answer = GUARD_BLOCK_MESSAGE
    except GuardUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail="Varnostnega preverjanja odgovora trenutno ni mogoče izvesti.",
        ) from exc

    history.append({"role": "user", "content": request.message})
    history.append({"role": "assistant", "content": answer})
    session_history[request.userId] = history[-10:]

    message_id = save_message(
        request.userId,
        request.userType,
        request.message,
        answer,
    )

    return ChatResponse(answer=answer, messageId=message_id)


@app.get("/chat/history/{user_id}")
async def chat_history(user_id: str, limit: int = 5, offset: int = 0):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, question, answer, rating, created_at
        FROM chat_history
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """, (user_id, limit + 1, offset))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    has_more = len(rows) > limit
    rows = rows[:limit]

    return {
        "messages": [
            {
                "messageId": r[0],
                "question":  r[1],
                "answer":    r[2],
                "rating":    r[3],
                "time":      r[4].strftime("%d.%m.%Y %H:%M"),
            }
            for r in reversed(rows)
        ],
        "has_more": has_more,
        "next_offset": offset + limit,
    }


@app.post("/chat/rate")
async def rate(request: RatingRequest):
    if request.rating not in (1, -1):
        return {"status": "error", "message": "Rating mora biti 1 ali -1"}

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT rating FROM chat_history WHERE id = %s", (request.messageId,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"status": "error", "message": "Sporočilo ne obstaja"}
    if row[0] != 0:
        return {"status": "already_rated", "message": "Že ocenjeno"}

    save_rating(request.messageId, request.rating)
    return {"status": "ok"}


# ── Admin — statistika in izvoz ────────────────────────────────────────────────

@app.get("/admin/export")
async def export_ratings(
    rating: int = 0,
    dateFrom: Optional[str] = None,
    dateTo: Optional[str] = None
):
    conn = get_conn()
    cur = conn.cursor()

    query = "SELECT question, answer, created_at FROM chat_history WHERE rating = %s"
    params = [rating]
    if dateFrom:
        query += " AND created_at >= %s"
        params.append(dateFrom)
    if dateTo:
        query += " AND created_at <= %s"
        params.append(dateTo + " 23:59:59")
    query += " ORDER BY created_at DESC"

    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Vprašanje", "Odgovor", "Datum"])
    for r in rows:
        writer.writerow([r[0], r[1], r[2].strftime("%d.%m.%Y %H:%M")])

    names = {1: "dobre", -1: "slabe", 0: "neocenjene"}
    filename = f"ocene_{names.get(rating, rating)}.csv"

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/admin/stats/monthly")
async def monthly_stats(rating: int = 1):
    if rating not in (1, -1, 0):
        return {"status": "error", "message": "Rating mora biti 1, -1 ali 0"}

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT TO_CHAR(created_at, 'YYYY-MM') AS month_key,
               TO_CHAR(created_at, 'TMMonth YYYY') AS month_label,
               COUNT(*) AS comments
        FROM chat_history
        WHERE rating = %s
        GROUP BY month_key, month_label
        ORDER BY month_key ASC
    """, (rating,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    MESECI = {
        "January": "Januar", "February": "Februar", "March": "Marec",
        "April": "April", "May": "Maj", "June": "Junij",
        "July": "Julij", "August": "Avgust", "September": "September",
        "October": "Oktober", "November": "November", "December": "December"
    }

    return [
        {
            "month_key": row[0],
            "month": MESECI.get(row[1].split()[0], row[1].split()[0]) + " " + row[1].split()[1],
            "comments": row[2]
        }
        for row in rows
    ]


# ── Admin — task management ────────────────────────────────────────────────────

@app.get("/admin/tasks")
async def list_tasks():
    """Seznam vseh ozadnih nalog in njihovih statusov."""
    return get_all_tasks()


@app.get("/admin/tasks/{task_id}")
async def task_status(task_id: str):
    """Status posamezne naloge."""
    task = get_task(task_id)
    if not task:
        return {"status": "error", "message": "Naloga ne obstaja"}
    return task


# ── Admin — crawl endpointi ────────────────────────────────────────────────────

import sys
import subprocess

def _run_script(script_path: str) -> str:
    """Požene Python skripto kot subprocess in vrne output."""
    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or f"Skripta {script_path} je vrnila napako.")
    return result.stdout.strip() or "Zaključeno."


@app.post("/admin/crawl/gallery")
async def crawl_gallery(background_tasks: BackgroundTasks):
    """Sproži crawlanje virtualnih razstav (crawl/scrape-virtualne-razstave.py)."""
    task_id = create_task("crawl_gallery")
    background_tasks.add_task(run_task, task_id, _run_script, "crawl/scrape-virtualne-razstave.py")
    return {
        "status": "started",
        "task_id": task_id,
        "message": "Crawlanje virtualnih razstav se je začelo.",
        "check_status": f"/admin/tasks/{task_id}"
    }


@app.post("/admin/crawl/tektonika")
async def crawl_tektonika(background_tasks: BackgroundTasks):
    """Sproži crawlanje tektonike (crawl/scrape-tektonika.py)."""
    task_id = create_task("crawl_tektonika")
    background_tasks.add_task(run_task, task_id, _run_script, "crawl/scrape-tektonika.py")
    return {
        "status": "started",
        "task_id": task_id,
        "message": "Crawlanje tektonike se je začelo.",
        "check_status": f"/admin/tasks/{task_id}"
    }


# ── Admin — indexiranje ────────────────────────────────────────────────────────

def _index_docs_task() -> str:
    return _run_script("index/index_docs.py")


def _index_gallery_task() -> str:
    return _run_script("index/index_gallery.py")


def _index_tektonika_task() -> str:
    return _run_script("index/index_tektonika.py")

async def admin_index_docs(background_tasks: BackgroundTasks):
    task_id = create_task("index_docs")
    background_tasks.add_task(run_task, task_id, _index_docs_task)
    return {"status": "started", "task_id": task_id, "check_status": f"/admin/tasks/{task_id}"}


@app.post("/admin/index/gallery")
async def admin_index_gallery(background_tasks: BackgroundTasks):
    task_id = create_task("index_gallery")
    background_tasks.add_task(run_task, task_id, _index_gallery_task)
    return {"status": "started", "task_id": task_id, "check_status": f"/admin/tasks/{task_id}"}


@app.post("/admin/index/tektonika")
async def admin_index_tektonika(background_tasks: BackgroundTasks):
    task_id = create_task("index_tektonika")
    background_tasks.add_task(run_task, task_id, _index_tektonika_task)
    return {"status": "started", "task_id": task_id, "check_status": f"/admin/tasks/{task_id}"}




if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
