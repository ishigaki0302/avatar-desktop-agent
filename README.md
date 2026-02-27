# avatar-desktop-agent

ローカルLLM（Ollama / Qwen3:8b）で会話しつつ、OpenClaw をデスクトップ操作エンジンとして使い、
2D スプライト差し替えで表情・口パク・簡易モーションを表示する **デスクトップコンパニオン** です。

## 技術選定理由

| 決定 | 理由 |
|------|------|
| TypeScript monorepo (pnpm) | 型共有・workspace 管理が容易。Node エコシステムで OpenClaw SDK を流用しやすい |
| Electron (UI) | Mac でネイティブウィンドウ + Canvas 描画。透過/常前面が簡単 |
| fastify (Bridge HTTP) | 軽量、型付きルート、SSE 対応 |
| Ollama REST API | ローカル LLM の事実上の標準。ストリーム対応 |
| OpenClaw Gateway (Route A) | 既存 TS クライアントを流用、署名ハンドシェイク自作なし |

---

## ディレクトリ構成

```
avatar-desktop-agent/
├── apps/
│   ├── ui/              # Electron アバター UI（タイプライタ・口パク・表情）
│   └── bridge/          # ローカル HTTP サーバ + Brain (Ollama) + OpenClaw 連携
├── packages/
│   ├── schema/          # JSON スキーマ・共有型定義
│   └── utils/           # logger / config / text-chunker
├── storage/
│   └── memory/
│       ├── persona.md       # キャラクター固定設定
│       ├── user_profile.md  # ユーザプロファイル（更新）
│       └── episodes/        # YYYY-MM-DD.md 会話要約
├── assets/
│   └── sprites/         # PNG 差分（emotion_open/close, motion frames）
├── .env.example
├── Makefile
├── package.json         # pnpm workspace root
└── pnpm-workspace.yaml
```

---

## 起動手順

### 必要なもの

- Node.js 20+
- pnpm 9+
- [Ollama](https://ollama.com/) インストール済み、`qwen3:8b` モデル pull 済み
- OpenClaw Gateway（Phase 3 以降）

### セットアップ

```bash
# 依存インストール
pnpm install

# 環境変数設定
cp .env.example .env
# .env を編集して OPENCLAW_GATEWAY_URL などを設定

# Ollama モデルを事前取得（未取得の場合）
ollama pull qwen3:8b
```

### 起動

```bash
# 全サービス同時起動（推奨）
pnpm dev
# または
make dev

# 個別起動
pnpm --filter bridge dev   # Bridge サーバ (port 3000)
pnpm --filter ui dev       # Electron UI
```

### テスト

```bash
pnpm test
# または
make test
```

---

## イベント仕様

Bridge と UI は **HTTP SSE**（Server-Sent Events）で通信します。
UI は `GET http://localhost:3000/events` に接続し、以下の JSON イベントを受信します。

### 1. `render` — アバター描画命令 (Brain → UI)

```json
{
  "type": "render",
  "text": "こんにちは！何かお手伝いできますか？",
  "emotion": "happy",
  "motion": "wave"
}
```

| フィールド | 型 | 値 |
|----------|-----|-----|
| `type` | `"render"` | 固定 |
| `text` | `string` | タイプライタ表示するテキスト |
| `emotion` | `"neutral"\|"happy"\|"sad"\|"angry"\|"surprised"\|"confused"` | 表情スプライト切替 |
| `motion` | `"none"\|"bow_small"\|"nod"\|"shake"\|"wave"` | モーション再生 |

**UI 動作:**
- テキストを 35〜60ms/文字 でタイプライタ表示
- タイプ中 100〜140ms 毎に mouth open/close を切替（口パク）
- `、` → 150ms 停止 + 口を閉じる
- `。！？` → 300〜500ms 停止 + 口を閉じる
- `\n` → 400ms 停止 + 口を閉じる
- `emotion` 受信時に表情スプライト切替
- `motion` は 6〜12fps の簡易フレームアニメで再生

### 2. `status` — 状態通知 (Bridge → UI)

```json
{
  "type": "status",
  "state": "running",
  "message": "OpenClaw でタスク実行中..."
}
```

| `state` | 意味 |
|---------|------|
| `running` | 処理中 |
| `idle` | 待機中 |
| `error` | エラー発生 |

### 3. `result` — タスク結果 (Bridge → UI)

```json
{
  "type": "result",
  "summary": "検索完了。上位3件を取得しました。",
  "details": null
}
```

### 4. `task` — デスクトップ操作委譲 (Brain → Bridge / 内部)

```json
{
  "type": "task",
  "goal": "Chrome でニュースを検索する",
  "constraints": {
    "no_credential": true,
    "allow_shell": false,
    "time_budget_sec": 60
  }
}
```

---

## OpenClaw 連携 (Route A)

Bridge が OpenClaw Gateway の既存 TS クライアントを流用して WebSocket 接続します。
実行ログは Bridge で最大 500 字に要約し、生ログを直接 UI/LLM に送りません。

許可操作リスト (`bridge/src/config.ts` で管理):
- ブラウザ起動・URL 開く
- アプリ起動
- クリップボード読み書き
- スクリーンショット取得

禁止（MVP):
- シェル任意実行 (`allow_shell: false`)
- 認証情報アクセス (`no_credential: true`)

---

## メモリ設計

| ファイル | 説明 |
|---------|------|
| `storage/memory/persona.md` | キャラ固定設定（不変） |
| `storage/memory/user_profile.md` | ユーザ情報（ターンごと差分更新） |
| `storage/memory/episodes/YYYY-MM-DD.md` | 会話要約（1セッション1ファイル） |

Brain は各ターン末に必要な差分だけ返す（変更なし → `"NOOP"`）。

---

## 実装フェーズ

| フェーズ | 内容 | 状態 |
|---------|------|------|
| Phase 0 | Repo bootstrap (monorepo, config, schema) | ✅ |
| Phase 1 | UI MVP (Electron + タイプライタ + 口パク) | ✅ |
| Phase 2 | Brain (Ollama/Qwen3:8b 接続 + JSON パーサ) | ✅ |
| Phase 3 | OpenClaw task delegation | 📋 |
| Phase 4 | Hardening (許可リスト, タイムアウト, エラー) | 📋 |

---

## ライセンス

MIT
