from fastapi.testclient import TestClient

from app.main import app, create_task, get_task, reset_tasks

client = TestClient(app)


def setup_function() -> None:
    """各テストに独立した保存状態を用意する。"""

    reset_tasks()


def test_patch_completed_false_updates_response_and_persisted_state() -> None:
    """Falseを明示した部分更新が、応答と保存状態の両方へ反映されることを確認する。"""

    create_task(task_id="task-1", title="完了済みタスク", completed=True)

    response = client.patch("/tasks/task-1", json={"completed": False})

    assert response.status_code == 200
    assert response.json()["completed"] is False

    saved_task = get_task("task-1")
    assert saved_task.completed is False


def test_patch_omitted_completed_keeps_existing_value() -> None:
    """completedを省略した部分更新は既存の真偽値を維持する。"""

    create_task(task_id="task-2", title="完了済みタスク", completed=True)

    response = client.patch("/tasks/task-2", json={})

    assert response.status_code == 200
    assert response.json()["completed"] is True

    saved_task = get_task("task-2")
    assert saved_task.completed is True
