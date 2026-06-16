# avatar-agent (Python backend)

avatar-desktop-agent の Python バックエンド。LLM オーケストレーション・長期記憶・対話ログ・分析・ツールを担当する。Electron UI とは HTTP/SSE で接続する。

## 開発

```bash
cd services/agent
uv sync --group dev          # 依存インストール
uv run uvicorn agent.app:app --reload   # 開発サーバ (http://127.0.0.1:8000)
uv run ruff check .          # lint
uv run ruff format .         # format
uv run pytest -v             # test
```

詳細な構成・フェーズ計画は [`../../docs/20260616_implementation_plan.md`](../../docs/20260616_implementation_plan.md) を参照。

## 構成

```text
src/agent/
├─ app.py        # FastAPI エントリ
├─ config.py     # 設定 (環境変数)
├─ llm/          # Ollama 呼び出し・JSON repair・streaming   (Phase 9+)
├─ memory/       # 長期記憶 (Profile/Semantic/Episodic/Task) (Phase 12+)
├─ logger/       # Interaction Logging (SQLite)               (Phase 9+)
├─ analytics/    # 満足/不満推定・issue 分類                   (Phase 15+)
└─ tools/        # filesystem / web / browser / desktop        (Phase 17+)
```
