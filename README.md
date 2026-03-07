# avatar-desktop-agent

ローカル LLM（Ollama / qwen3.5:2b）で会話しつつ、OpenClaw をデスクトップ操作エンジンとして使い、
2D スプライト差し替えで表情・口パク・簡易モーションを表示する **デスクトップコンパニオン** です。

キャラクター「アリス」は音声対話を前提とした短文（1文 15〜40 字）を生成し、
会話ログはセッション単位で JSONL ファイルに自動保存されます。

## 技術選定理由

| 決定 | 理由 |
|------|------|
| TypeScript monorepo (pnpm) | 型共有・workspace 管理が容易。Node エコシステムで OpenClaw SDK を流用しやすい |
| Electron (UI) | Mac でネイティブウィンドウ + Canvas 描画。透過/常前面が簡単 |
| fastify (Bridge HTTP) | 軽量、型付きルート、SSE 対応 |
| Ollama REST API | ローカル LLM の事実上の標準。ストリーム対応 |
| OpenClaw Gateway (Route A) | WebSocket + JSON フレームで接続、署名ハンドシェイク自作なし |

---

## ディレクトリ構成

```
avatar-desktop-agent/
├── apps/
│   ├── ui/              # Electron アバター UI（タイプライタ・口パク・表情）
│   └── bridge/          # ローカル HTTP サーバ + Brain (Ollama) + OpenClaw 連携
│       └── storage/
│           ├── memory/      # ユーザーメモリ（persona.md, user_profile.md）
│           └── sessions/    # セッションログ JSONL（1ファイル/セッション）
├── packages/
│   ├── schema/          # JSON スキーマ・共有型定義
│   └── utils/           # logger / config / text-chunker
├── assets/
│   └── sprites/         # PNG スプライト（emotion_open/close.png）
├── .env.example
├── Makefile
├── package.json         # pnpm workspace root
└── pnpm-workspace.yaml
```

---

## 起動手順

### 必要なもの

- Node.js 22+
- pnpm 9+
- [Ollama](https://ollama.com/) インストール済み・`qwen3.5:2b` pull 済み

### セットアップ

```bash
# 依存インストール
pnpm install

# 環境変数設定
cp .env.example .env

# Ollama モデルを事前取得（未取得の場合）
ollama pull qwen3.5:2b
```

### 起動

```bash
# bridge + UI を同時起動（ローカル Ollama 使用）
pnpm dev
```

### リモート GPU バックエンドで起動する

GPU サーバ上で `/generate` API を立てておき、SSH ポートフォワードでローカルに転送する方法です。

#### 1. SSH ポートフォワードを張る

別ターミナルで以下を実行し、GPU サーバのポートをローカル `10003` に転送します。

```bash
# ssh -L <ローカルポート>:<サーバ内ホスト>:<サーバポート> <SSHホスト>
ssh -L 10003:localhost:10003 your-gpu-server
```

> `your-gpu-server` は `~/.ssh/config` のホスト名や `user@hostname` で指定してください。
> サーバ側の `/generate` API がポート `10003` で起動している想定です。

#### 2. アプリを起動する

```bash
BRAIN_BACKEND=remote-gpu REMOTE_GPU_BASE_URL=http://127.0.0.1:10003 pnpm dev
```

| 環境変数 | 説明 | デフォルト |
|---------|------|-----------|
| `BRAIN_BACKEND` | `ollama`（ローカル）または `remote-gpu` | `ollama` |
| `REMOTE_GPU_BASE_URL` | `/generate` API のベース URL | `http://127.0.0.1:10003` |
| `REMOTE_GPU_MAX_NEW_TOKENS` | 最大生成トークン数 | `512` |
| `REMOTE_GPU_TEMPERATURE` | サンプリング温度 | `0.75` |
| `REMOTE_GPU_TIMEOUT_MS` | タイムアウト（ms） | `120000` |

#### `/generate` API の仕様

GPU サーバ側は以下のリクエスト／レスポンスに対応している必要があります。

**リクエスト（POST `/generate`）**

```json
{
  "prompt": "<システムプロンプト + 会話履歴>",
  "max_new_tokens": 512,
  "temperature": 0.75,
  "do_sample": true
}
```

**レスポンス**

```json
{
  "generated_text": "{\"emotion\":\"happy\",\"motion\":\"wave\",\"text\":\"...\",\"memory_update\":\"NOOP\",\"task\":null}",
  "elapsed_sec": 1.23
}
```

### 送信キー

| 操作 | キー |
|------|------|
| メッセージ送信 | **Shift + Enter** |
| 日本語変換確定 | Enter（送信されません） |

### テスト

```bash
pnpm test
```

---

## キャラクター設定（アリス）

| 項目 | 内容 |
|------|------|
| 名前 | アリス |
| 口調 | 口語体（〜だよ、〜だね、〜かな） |
| 返答長 | 音声読み上げ想定、1文 15〜40 字 |
| 表情 | happy / neutral / surprised / sad / confused |
| モーション | wave / nod / bow_small / shake / none |

---

## セッションログ

会話は `storage/sessions/YYYY-MM-DD_HH-MM-SS_<id>.jsonl` に自動保存されます。
JSONL 形式（1 行 = 1 JSON オブジェクト）なので、pandas・jq などで簡単に分析できます。

### ファイル構造

```jsonl
{"type":"session_start","session_id":"2026-03-01_21-00-00_abc123","started_at":"...","model":"qwen3.5:2b","max_predict_tokens":30,"system_prompt_hash":"97febf0f"}
{"type":"turn","seq":1,"timestamp":"...","user":"おはよう！","assistant":"おはよう！今日も一緒に頑張ろうね！","emotion":"happy","motion":"wave","latency_ms":3200}
{"type":"session_end","session_id":"...","ended_at":"...","turn_count":5}
```

### jq による分析例

```bash
# 全ターンのユーザー発話を時系列で表示
jq -r 'select(.type=="turn") | "\(.timestamp) \(.user)"' storage/sessions/*.jsonl

# 平均レイテンシ（ms）を計算
jq 'select(.type=="turn") | .latency_ms' storage/sessions/*.jsonl | awk '{s+=$1;n++} END{print s/n " ms"}'

# emotion の分布
jq -r 'select(.type=="turn") | .emotion' storage/sessions/*.jsonl | sort | uniq -c | sort -rn
```

---

## イベント仕様（Bridge ↔ UI）

Bridge と UI は **HTTP SSE**（Server-Sent Events）で通信します。
UI は `GET http://localhost:3000/events` に接続し、以下の JSON イベントを受信します。

### ストリーミング応答（render_start / render_token / render_end）

応答は 3 種類のイベントに分割されて逐次配信されます。

```
render_start → render_token × N → render_end
```

#### `render_start` — アバター表情・モーション設定

```json
{ "type": "render_start", "emotion": "happy", "motion": "wave" }
```

emotion/motion が確定した時点で即送信されます。テキスト到着前にアバターが反応します。

#### `render_token` — テキストの逐次配信

```json
{ "type": "render_token", "token": "お" }
```

text フィールドの文字が 1 文字単位で順次送信されます。

#### `render_end` — 応答完了

```json
{ "type": "render_end" }
```

### `status` — 状態通知

```json
{ "type": "status", "state": "running", "message": "考え中..." }
```

| `state` | 意味 |
|---------|------|
| `running` | 処理中 |
| `idle` | 待機中 |
| `error` | エラー発生 |

### `result` — タスク結果

```json
{ "type": "result", "summary": "検索完了。", "details": null }
```

---

## OpenClaw 連携

Bridge が OpenClaw Gateway に WebSocket 接続してデスクトップ操作を委譲します。
`OPENCLAW_GATEWAY_URL` が未設定の場合はスタブ結果を返します。

**deny-list（常時拒否）:**
`rm`, `sudo`, `eval()`, `exec()`, `password`, `credential`, `private.key`

---

## メモリ設計

| ファイル | 説明 |
|---------|------|
| `storage/memory/persona.md` | キャラ固定設定（不変） |
| `storage/memory/user_profile.md` | ユーザー情報（ターンごと差分更新） |

---

## 実装フェーズ

| フェーズ | 内容 | 状態 |
|---------|------|------|
| Phase 1 | UI MVP（Electron + タイプライタ + 口パク） | ✅ |
| Phase 2 | Brain（Ollama 接続 + JSON パーサ） | ✅ |
| Phase 3 | OpenClaw Gateway WebSocket 連携 | ✅ |
| Phase 4 | Hardening（セキュリティ・タイムアウト・エラーリカバリ） | ✅ |
| Phase 5 | qwen3.5:2b + アリスプロンプト設計 | ✅ |
| Phase 6 | セッションログ（JSONL） | ✅ |
| Phase 7 | ストリーミング応答（stream:true + 逐次 SSE） | ✅ |

---

## ライセンス

MIT
