# `false`の部分更新が保存されない問題のデバッグ記録

## 目的

`PATCH /tasks/{task_id}` に `{"completed": false}` を送ると、未完了へ戻す更新が実行され、応答と保存状態の両方が `False` になることを契約とします。修正前は HTTP ステータスが `200 OK` であっても、既存の `True` が残りました。この記録では、HTTP応答と保存状態を分けて観測し、真偽値を真偽で判定しない最小修正を残します。

## 再現条件

| 項目 | 内容 |
| --- | --- |
| バグを含むコミット | `aed2260` |
| テスト名 | `test_patch_completed_false_updates_response_and_persisted_state` |
| Python実行環境 | Python 3.12.3、FastAPI 0.115.12、Pydantic 2.11.4、pytest 8.3.5 |
| 初期状態 | `completed=True` のタスクを1件作成する |
| 操作 | `PATCH /tasks/task-1` に `{"completed": false}` を送る |
| 期待する最終状態 | 応答と保存済みタスクの `completed` がともに `False` |

## 最初に観測した事実

| 観測対象 | 期待値 | 実際値 | 根拠 |
| --- | --- | --- | --- |
| HTTPステータス | `200 OK` | `200 OK` | 修正前コミットの観測スクリプト |
| 更新応答の `completed` | `False` | `True` | 修正前コミットの観測スクリプト |
| 保存済みの `completed` | `False` | `True` | 修正前コミットの観測スクリプト |

```text
HTTP status: 200
Response completed: True
Persisted completed: True

E       assert True is False
```

この結果から、通信や例外処理の失敗ではなく、更新対象を組み立てる前の条件分岐で `False` が除外されていると考えられます。

## 仮説と切り分け

| 仮説 | 確認方法 | 結果 |
| --- | --- | --- |
| レスポンスモデルの整形だけが古い値を返す | 更新後に `get_task()` で保存済みタスクを読む | 棄却。保存状態も `True` のままだった。 |
| Pydanticが `false` を受け取れていない | HTTP応答と修正前の条件分岐を確認する | 棄却。応答は既存の `True` であり、入力検証エラーも発生していない。 |
| Pythonの真偽値判定で `False` が更新対象から除外される | `if patch.completed:` と明示的な `False` の組合せを確認する | 採用。`False` は偽値のため分岐を通らない。 |

## 原因

修正前のエンドポイントは次のように、`completed` の有無ではなく値そのものを条件にしていました。

```python
if patch.completed:
    task.completed = patch.completed
```

`False` はPythonでは偽値です。そのため、クライアントが `false` を明示しても代入処理が実行されず、保存済みの `True` が残りました。これはPydanticやFastAPIの保存失敗ではなく、アプリケーション側が真偽値の「値」と更新フィールドの「指定有無」を混同したことが原因です。

FastAPIの部分更新ガイドは、入力モデルから実際に指定されたフィールドだけを取り出して既存データへ適用する手順を示しています。[1] Pydantic v2は、モデル生成時に明示指定されたフィールドを `model_fields_set` として公開しています。[2]

## 修正

`False` を明示値として扱うため、真偽値判定を `None` 判定に変更しました。

```python
if patch.completed is not None:
    task.completed = patch.completed
```

このサンプルでは `None` を「キー省略または `null` による変更なし」と定義しています。したがって、`False` と `True` は更新し、`None` は既存値を維持します。

## 再発防止テスト

| テスト | 守る契約 | 最終観測 |
| --- | --- | --- |
| `test_patch_completed_false_updates_response_and_persisted_state` | 明示した `false` を未完了として保存する | 応答と `get_task()` の両方が `False` |
| `test_patch_omitted_completed_keeps_existing_value` | キー省略は既存値を維持する | 応答と `get_task()` の両方が `True` |

修正後は `python -m pytest` で2件のテストが成功しました。

## 再現手順

```bash
# 修正前: false更新のテストが失敗する
git checkout aed2260
python -m pytest tests/test_task_update.py -q

# 修正後: 対象テストと全体テストが成功する
git checkout main
python -m pytest tests/test_task_update.py -q
python -m pytest
```

## 設計上の範囲

このサンプルは、`completed` について `null` とキー省略を同じ「変更しない」として扱います。`null` を「未設定へ戻す」という別の業務操作として扱う場合は、`None` とキー省略を区別できるパッチモデルや、JSON Merge Patchなどの明確な契約を別途設計してください。また、実運用ではインメモリ辞書ではなくDBトランザクションと同時更新の扱いを追加で検証する必要があります。

## References

[1] [FastAPI: Body - Updates](https://fastapi.tiangolo.com/tutorial/body-updates/)

[2] [Pydantic: Models](https://docs.pydantic.dev/latest/concepts/models/)
