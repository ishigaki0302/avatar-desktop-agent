# avatar-desktop-agent 実装計画 (Phase 9–19)

> 派生元: [`20260616_local_llm_desktop_agent_requirements.md`](./20260616_local_llm_desktop_agent_requirements.md)（ChatGPT 壁打ち全文ログ / 最終版要件定義 v2）
> 本書は、上記要件定義を **実装に着手できる粒度** に落とし込んだ計画書。各 Phase は GitHub issue とブランチに 1:1 で対応する。
> 作成日: 2026-06-16

---

## 0. このドキュメントの位置づけ

要件定義ログ（壁打ち全文）は「何を作るか・なぜ作るか」を記録したもの。本書は「どう作るか・どの順で作るか」を定義する。

- **Phase 8（gemma4:31b 対応）は `main` で実装済み**（モデル既定値・`.env.example`・README・brain.ts の更新）。
- 本書が扱うのは **Phase 9–19**。各 Phase に GitHub issue を起票し、`feat/phase-NN-*` ブランチを切る。
- 下準備（本書・Python scaffold・CI）は `main` に直接コミットする。

---

## 1. アーキテクチャ決定: ハイブリッド (Python backend + TS UI)

既存は TypeScript モノレポ（Electron UI / Fastify bridge / `brain.ts`）。要件定義が依拠する長期記憶・分析スタック（Letta, LangGraph, LangMem, Chroma, Qdrant, 埋め込み）はすべて Python エコシステム。したがって **新規バックエンドは Python**、**UI は Electron(TS) を維持** するハイブリッド構成とする。

```text
avatar-desktop-agent/
├─ apps/
│  ├─ ui/              # Electron renderer + main (TS, 既存維持)
│  └─ bridge/          # Fastify (TS) — 薄い proxy に縮小 / 段階的に Python へ委譲
├─ services/
│  └─ agent/           # ★新規: Python (FastAPI + uv + ruff + pytest)
│     └─ src/agent/
│        ├─ app.py        # FastAPI エントリ (SSE)
│        ├─ config.py     # 設定 (Ollama / model / storage)
│        ├─ llm/          # Ollama 呼び出し・JSON repair・streaming
│        ├─ memory/       # Profile/Semantic/Episodic/Task/Procedural/Archival
│        ├─ logger/       # Interaction Logging (SQLite)
│        ├─ analytics/    # 満足/不満推定・issue 分類
│        └─ tools/        # filesystem / web / browser / desktop
├─ packages/
│  └─ schema/          # UI が参照する TS 型 (既存)
├─ storage/            # SQLite / vector / logs (Git 管理外)
└─ .github/workflows/  # ruff+pytest (Python) / tsc+test (TS)
```

### 責務分離

| レイヤ | 言語 | 役割 |
|---|---|---|
| UI (Electron) | TS | 入力・応答表示・フィードバックUI・アバター描画 |
| Bridge | TS | UI ↔ agent service の橋渡し（SSE 中継）。将来 Python に委譲可 |
| Agent service | **Python** | LLM 呼び出し・メモリ・ログ・分析・ツール |

UI と Python service は HTTP/SSE で接続する。移行期は Fastify bridge が Python service への proxy を兼ねる。

---

## 2. ログ / 記憶 / Wiki の 3 層分離（要件の中核）

| 層 | 内容 | 保存先 |
|---|---|---|
| Interaction Log | 全やり取りの生ログ（雑談・感想・愚痴含む、原則全保存） | SQLite / JSONL |
| Long-term Memory | 応答に使うため抽出・要約・構造化した記憶 | SQLite + Vector Store + Markdown |
| LLM Wiki (`ai_wiki/`) | 人間が手動で整理する Markdown 知識（自動増殖させない） | Markdown (Git 管理外) |

原則: **全部保存するが、全部は思い出さない**。プロンプトには関連記憶＋直近文脈のみ注入する。

---

## 3. 品質ゲート / CI

参考: `new-maestro-poc/.github`（ruff + pytest）。本リポジトリは Python/TS 二本立て。

| 対象 | lint | test |
|---|---|---|
| Python (`services/agent`) | `ruff check` + `ruff format --check` | `pytest` |
| TypeScript (既存) | `tsc --noEmit`（= `pnpm typecheck`、JS リンタ未導入） | `pnpm test`（tsx --test） |

- `.github/workflows/ci_pr_lint.yml` — `ruff` ジョブ + `typecheck` ジョブ
- `.github/workflows/ci_pr_test.yml` — `python-tests` ジョブ + `ts-tests` ジョブ
- Python 規約は `services/agent/pyproject.toml`（ruff `select=ALL` + 調整済み ignore、`*_test.py` 命名、Python 3.12、uv 管理）に集約。

---

## 4. 規約

- **ブランチ**: `feat/phase-NN-<slug>`（例 `feat/phase-09-interaction-logging`）。
- **コミット**: Conventional Commits（`feat:` / `fix:` / `chore:` / `docs:`）。日本語サマリ可。
- **PR**: 各 Phase ブランチ → `main`。対応 issue を本文で `Closes #N` 参照。CI（ruff/pytest/tsc/test）green を必須。
- 既存の機能 issue（#10〜#28）とは別に新規フェーズ issue を起票し、重複は本文でリンク参照（既存はクローズしない）。

---

## 5. Phase 一覧（issue / ブランチ対応）

凡例: 🎯目的 / 📦主成果物 / ✅受け入れ条件 / 🌿ブランチ / 🔗関連既存issue

### Phase 9 — Interaction Logging v1
- 🎯 全対話を構造化ログとして保存する（雑談・感想も含む）。
- 📦 `services/agent/logger/`、SQLite `sessions` / `turn_logs`、既存 JSONL との互換。
- ✅ すべてのターンがローカル DB に保存される / 雑談も保存される / セッション単位で後から読める。
- 🌿 `feat/phase-09-interaction-logging`
- 🔗 #17（セッションログ分析）の前提基盤

### Phase 10 — Prompt / Tool / Memory Access Logging
- 🎯 エージェントが「何を見て、何を使って」応答したかを追跡する。
- 📦 `prompt_logs` / `tool_call_logs` / `memory_access_logs` / `avatar_event_logs`。
- ✅ 参照した記憶・呼んだツール・プロンプト構築過程を追える。
- 🌿 `feat/phase-10-logging-prompt-tool-memory`

### Phase 11 — Explicit Feedback
- 🎯 ユーザーが明示的に満足/不満を記録できる。
- 📦 UI に 👍/👎/🔁/📝、`explicit_feedback_logs`（rating 1–5 + label + comment）。
- ✅ 各応答に評価を付けられ、ログと紐づく。
- 🌿 `feat/phase-11-explicit-feedback`
- 🔗 #26（フィードバックボタン）を統合・置換候補

### Phase 12 — Long-term Memory v1
- 🎯 Profile / Semantic / Episodic / Task memory を導入する。
- 📦 `services/agent/memory/`、`profile.md`、`memories` / `tasks` テーブル、Vector Store（Chroma）。
- ✅ 過去情報を検索でき、Profile 更新・タスク保持・再起動後の保持ができる。
- 🌿 `feat/phase-12-memory-v1`
- 🔗 #13（エピソードメモリ）を統合・置換候補

### Phase 13 — Memory Retrieval
- 🎯 応答前に関連記憶を検索・注入する。
- 📦 検索クエリ生成 / vector search / relevance・recency・importance スコア / prompt injection。
- ✅ 過去会話や設定を応答に反映でき、無関係な記憶を大量注入しない。
- 🌿 `feat/phase-13-memory-retrieval`

### Phase 14 — Memory Write / Consolidation
- 🎯 ログから有用な記憶を抽出・統合する（hot path + background）。
- 📦 session summary / duplicate merge / superseded 管理 / memory write log。
- ✅ 「覚えて」が保存され、雑談から好みを抽出でき、新旧情報を区別できる。
- 🌿 `feat/phase-14-memory-write`

### Phase 15 — Interaction Analytics v1
- 🎯 満足・不満・失敗パターンを推定する。
- 📦 `inferred_feedback_logs`、issue_type 分類、predicted_satisfaction / evidence / confidence。
- ✅ 各ターンの不満可能性を推定でき、再質問・訂正を検出できる。
- 🌿 `feat/phase-15-analytics-v1`
- 🔗 #17（ログ分析）

### Phase 16 — Dashboard v1
- 🎯 保存ログを後から閲覧・分析できる。
- 📦 セッション一覧 / ターン詳細 / 検索 / フィードバック表示 / issue_type 集計 / latency / memory access。
- ✅ 過去会話を検索でき、不満ログを一覧でき、使われた記憶が見える。
- 🌿 `feat/phase-16-dashboard`

### Phase 17 — Tool Use v1
- 🎯 安全なツール利用を導入する。
- 📦 `filesystem.list/read` / `memory.search/write`、tool schema、tool call validation、deny-list。
- ✅ ファイル一覧取得・README 読解ができ、ツール呼び出しがログに残る。
- 🌿 `feat/phase-17-tool-use`

### Phase 18 — Web / Browser Tool
- 🎯 必要時に Web/ブラウザを利用できる。
- 📦 `web.search` / `browser.open/read`、source 保存、調査ログ。
- ✅ Web 検索結果を要約でき、参照元を保存できる。
- 🌿 `feat/phase-18-web-browser`

### Phase 19 — Avatar / TTS 強化
- 🎯 デスクトップコンパニオンらしい表現を強化する。
- 📦 TTS 導入 / 口パク同期 / 表情精度 / `avatar_event_logs`。
- ✅ テキスト応答に合わせ自然に反応し、必要なら音声読み上げできる。
- 🌿 `feat/phase-19-avatar-tts`
- 🔗 #10（TTS）を統合・置換候補

---

## 6. 実装順と MVP

要件定義の「最重要実装順」に従う。MVP は **Phase 9–16**（ログ基盤 → フィードバック → 記憶 → 分析 → ダッシュボード）で成立する。Phase 17–19（ツール/Web/TTS）は MVP 後。

```text
9 → 10 → 11 → 12 → 13 → 14 → 15 → 16  ［MVP］
17 → 18 → 19                          ［MVP 後］
```

## 7. 安全方針（全 Phase 共通）

- ファイル削除 / sudo / rm / eval / exec / 認証情報アクセスは禁止（deny-list）。
- パスワード・APIキー・トークン等はログから除外/マスク。`保存しないで` 指示を尊重。
- デスクトップ操作・外部送信は原則ユーザー確認付き。Computer Use は MVP 後。
- ローカル LLM の JSON 崩れ前提: schema validation / retry / repair / fallback / error log を必須。
