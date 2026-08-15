# FastAPIで`false`の部分更新が保存されないバグを再現して直す

このリポジトリは、FastAPI の部分更新で `{"completed": false}` を送っても、HTTP ステータスが `200 OK` のまま保存済みの真偽値が変わらない不具合を再現・修正する学習用プロジェクトです。

> このプロジェクトは学習・検証用です。本番サービスの構成、認証、トランザクション境界、永続ストアを再現するものではありません。

## 題材

`PATCH /tasks/{task_id}` は `completed` を部分更新します。契約は次のとおりです。

| リクエストの `completed` | 意味 | 更新後の状態 |
| --- | --- | --- |
| キーなし | 変更しない | 既存値を維持する |
| `true` | 完了にする | `True` |
| `false` | 未完了に戻す | `False` |
| `null` | このサンプルでは変更しない | 既存値を維持する |

修正前は `if patch.completed:` という真偽値判定により、`False` が明示された場合も更新処理を通りませんでした。HTTPの成功だけでなく、応答本文と保存済みタスクの両方を確認するテストで不具合を固定します。

## 必要環境

- Python 3.11 以上
- `pip`

## セットアップ

```bash
python -m pip install -e '.[dev]'
```

## テスト実行

```bash
# すべてのテストを実行
python -m pytest

# false更新とキー省略の回帰テストだけを実行
python -m pytest tests/test_task_update.py -q
```

## バグの再現と修正の確認

Git履歴には、失敗する再現テストと修正を分離して残しています。デフォルトブランチは修正済みです。

```bash
# 修正前: false更新のテストが失敗する
git checkout aed2260
python -m pytest tests/test_task_update.py -q

# 修正後: 対象テストと全体テストが成功する
git checkout main
python -m pytest tests/test_task_update.py -q
python -m pytest
```

## 調査記録

観測結果、仮説、原因、修正、回帰確認は [docs/false-update-debugging-record.md](docs/false-update-debugging-record.md) にまとめています。

## 構成

```text
app/main.py                 FastAPIアプリケーションと最小の保存層
tests/test_task_update.py   HTTP応答と保存状態を確認するpytest
docs/                       調査記録
```
