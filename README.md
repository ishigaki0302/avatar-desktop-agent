# avatar-desktop-agent

ローカル LLM（Ollama / Qwen/Qwen3.5-4B）で会話しつつ、OpenClaw をデスクトップ操作エンジンとして使い、
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
- [Ollama](https://ollama.com/) インストール済み・`Qwen/Qwen3.5-4B` pull 済み

### セットアップ

```bash
# 依存インストール
pnpm install

# 環境変数設定
cp .env.example .env

# Ollama モデルを事前取得（未取得の場合）
ollama pull Qwen/Qwen3.5-4B
```

### 起動

```bash
# 個別起動（ターミナル2つ）
pnpm --filter bridge dev   # Bridge サーバ (port 3000)
pnpm --filter ui dev       # Electron UI
```

### 送信キー

| 操作 | キー |
|------|------|
| メッセージ送信 | **Shift + Enter** |
| 日本語変換確定 | Enter（送信されません） |

### テスト

```bash
pnpm --filter bridge test
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
{"type":"session_start","session_id":"2026-03-01_21-00-00_abc123","started_at":"...","model":"Qwen/Qwen3.5-4B","max_predict_tokens":150,"system_prompt_hash":"97febf0f"}
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

### 1. `render` — アバター描画命令

```json
{
  "type": "render",
  "text": "おはよう！今日も一緒に頑張ろうね！",
  "emotion": "happy",
  "motion": "wave"
}
```

### 2. `status` — 状態通知

```json
{ "type": "status", "state": "running", "message": "考え中..." }
```

| `state` | 意味 |
|---------|------|
| `running` | 処理中 |
| `idle` | 待機中 |
| `error` | エラー発生 |

### 3. `result` — タスク結果

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
| Phase 5 | Qwen/Qwen3.5-4B + アリスプロンプト設計 | ✅ |
| Phase 6 | セッションログ（JSONL） | ✅ |

---

## ライセンス

MIT
