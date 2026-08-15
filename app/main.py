from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="False Update Debug Lab")


@dataclass
class Task:
    """学習用タスクを表す最小モデル。"""

    task_id: str
    title: str
    completed: bool


class TaskPatch(BaseModel):
    """タスク更新で受け付けるフィールドを表す入力モデル。"""

    completed: bool | None = None


class TaskResponse(BaseModel):
    """タスク更新の応答モデル。"""

    task_id: str
    title: str
    completed: bool


_TASKS: dict[str, Task] = {}


def reset_tasks() -> None:
    """テストごとに決定的な初期状態を作る。"""

    _TASKS.clear()


def create_task(task_id: str, title: str, completed: bool) -> Task:
    """テスト用タスクを保存する。"""

    task = Task(task_id=task_id, title=title, completed=completed)
    _TASKS[task_id] = task
    return task


def get_task(task_id: str) -> Task:
    """保存済みタスクを取得する。"""

    try:
        return _TASKS[task_id]
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Task not found") from error


@app.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, patch: TaskPatch) -> Task:
    """タスクを部分更新する。"""

    task = get_task(task_id)

    # Noneはキー省略またはnullを表すため既存値を維持し、Falseは明示値として保存する。
    if patch.completed is not None:
        task.completed = patch.completed

    return task
