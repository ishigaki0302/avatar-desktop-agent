# 実装ログ

> 最終更新: 2026-02-27
> リポジトリ: https://github.com/ishigaki0302/avatar-desktop-agent

---

## 完了フェーズ一覧

| フェーズ | 内容 | コミット |
|---------|------|---------|
| Phase 0 | Repo bootstrap | `54e8cca` |
| Phase 1 | UI ビルドパイプライン整備 | `76e33d3` |
| Phase 2 | Brain (Ollama/qwen3:8b) 強化 | `c2d682b` |

---

## Phase 0 — Repo Bootstrap

### 作成ファイル（36ファイル）

```
.env.example               # 全設定値の雛形（OLLAMA_BASE_URL, BRIDGE_PORT 等）
.gitignore
Makefile                   # make dev / make test
README.md                  # 起動手順・イベント仕様・構成
package.json               # pnpm workspace root + pnpm.onlyBuiltDependencies
pnpm-workspace.yaml
tsconfig.base.json         # 共通 TypeScript 設定

packages/schema/           # 共有型定義
  src/index.ts             # RenderEvent, StatusEvent, ResultEvent, TaskEvent + バリデータ
  src/index.test.ts        # 7テスト

packages/utils/            # 共通ユーティリティ
  src/logger.ts            # createLogger(prefix) → { debug, info, warn, error }
  src/config.ts            # 全設定値を process.env から読む（型安全）
  src/textChunker.ts       # truncate / chunkBySentence / extractJSON
  src/index.ts             # re-export
  src/textChunker.test.ts  # 6テスト

apps/bridge/
  src/index.ts             # エントリ: dotenv → startServer()
  src/server.ts            # Fastify + SSE (/events) + POST /chat
  src/brain.ts             # Ollama 呼び出し + JSONパーサ + リトライ
  src/memory.ts            # readMemory / writeEpisode
  src/openclaw.ts          # OpenClaw stub (Phase 3 用)

apps/ui/
  src/main.ts              # Electron main process
  src/preload.ts           # contextBridge: sendMessage / getSseUrl
  src/renderer/index.html  # アバター画面 HTML
  src/renderer/renderer.ts # SSE → avatar/typewriter 連携
  src/renderer/typewriter.ts # 口パク同期タイプライタ（Plan A）
  src/renderer/avatar.ts   # Canvas 2D スプライト描画 + fallback

storage/memory/
  persona.md               # キャラ設定（固定）
  user_profile.md          # ユーザプロファイル

assets/sprites/README.md   # スプライト命名規則ドキュメント
```

### データ仕様（確定済み）

```typescript
// Brain → UI
{ type:"render", text:string, emotion:Emotion, motion:Motion }

// Bridge → UI (SSE)
{ type:"status", state:"running"|"idle"|"error", message:string }
{ type:"result", summary:string, details:string|null }

// Brain → Bridge / OpenClaw (内部)
{ type:"task", goal:string, constraints:{ no_credential:true, allow_shell:false, time_budget_sec:60 } }
```

---

## Phase 1 — UI ビルドパイプライン

### 問題と解決

| 問題 | 解決方法 |
|------|---------|
| `tsx src/main.ts` は Electron を起動できない | `apps/ui/scripts/dev.mjs` に esbuild + Electron spawn を実装 |
| Renderer (ブラウザ) が TS のまま | esbuild で `renderer.ts → dist/renderer/renderer.js` (IIFE) にバンドル |
| workspace パッケージを esbuild が解決できない | `alias` で `@avatar-agent/schema/utils → packages/*/src/index.ts` を直指定 |
| `SPRITE_BASE` が相対パスで Electron file:// 不一致 | esbuild `define` で `__SPRITE_BASE__` をビルド時に絶対パス注入 |
| Bridge の dotenv が `apps/bridge/` の CWD を見る | dev スクリプトに `DOTENV_CONFIG_PATH=../../.env` を追加 |
| tsconfig `rootDir` が packages ソースを拒否 | `rootDir` 削除 + `include` に packages ソースを追加 |
| UI tsconfig に DOM 型がない | `lib: ["ES2022","DOM"]` に変更 |
| `Number(8)` typo | `8` に修正 |
| テストファイルが tsc build に混入 | `exclude: ["src/**/*.test.ts"]` + テストは `tsx --test` に変更 |

### ビルド成果物

```
apps/ui/dist/
├── main.js        # Electron main (CJS bundle)
├── preload.js     # Electron preload (CJS bundle)
└── renderer/
    ├── index.html # HTML (コピー)
    └── renderer.js # renderer bundle (IIFE)
```

### 重要な設計決定

- **esbuild alias** でワークスペースパッケージをソースから直接バンドル（tsc ビルドに依存しない）
- **`__SPRITE_BASE__`** define により、スプライト画像パスがビルド時に絶対パスになる
- UI の tsconfig は `"moduleResolution":"bundler"` — esbuild が実際のバンドルを担うため

---

## Phase 2 — Brain (Ollama / qwen3:8b)

### 強化した `textChunker.ts`

```typescript
// 追加した関数
stripLLMNoise(text: string): string
  // → <think>…</think> 除去（qwen3 思考トークン）
  // → ```json … ``` markdown fence 除去
  // → trim

// 改善した extractJSON
extractJSON(text: string): Record<string,unknown> | null
  // → stripLLMNoise() を事前に適用
  // → fast-path: 先頭が '{' なら即 JSON.parse 試行
  // → 文字列内のエスケープを正しく追跡してブラケットマッチ
  // → エスケープ対応により {"text":"彼は\"こんにちは\"と言った"} が正しく解析される
```

### `brain.ts` 変更点

```
1. システムプロンプト改善:
   - スキーマを明記（フィールド名・値候補）
   - few-shot 例を1つ追加
   - motion の選択ガイドを追記

2. 会話履歴管理:
   - MAX_HISTORY_MESSAGES = 20
   - ask() ごとに trimHistory() 呼び出し

3. memory_update の反映:
   - "NOOP" 以外なら applyMemoryUpdate(diff) を非同期実行

4. getHistory() / resetHistory() を export（テスト用）
```

### `memory.ts` 変更点

```
追加: applyMemoryUpdate(diff: string)
  - "NOOP" / 空文字 → 何もしない
  - それ以外 → storage/memory/user_profile.md に
    タイムスタンプ付きで追記
```

### テスト一覧（33/33）

```
packages/schema (7):
  validateUIEvent: valid render
  validateUIEvent: invalid emotion falls through parseRenderEvent
  validateUIEvent: valid status
  validateUIEvent: valid result
  validateUIEvent: unknown type fails
  isValidEmotion: all valid emotions
  isValidMotion: all valid motions

packages/utils (6):
  truncate: short text unchanged
  truncate: long text cut with suffix
  chunkBySentence: splits at sentence boundaries
  extractJSON: finds JSON in surrounding text
  extractJSON: returns null for no JSON
  extractJSON: returns null for malformed JSON

apps/bridge (20):
  stripLLMNoise:
    removes <think> block
    removes multiline <think> block
    removes markdown json fence
    removes plain markdown fence
    leaves clean JSON unchanged
  extractJSON:
    parses clean JSON
    extracts JSON after <think> block
    extracts JSON from markdown fence
    handles nested JSON objects (task field)
    handles JSON with escaped quotes in strings
    returns null for no JSON
    returns null for truncated JSON
  parseRenderEvent:
    valid fields pass through
    invalid emotion falls back to neutral
    invalid motion falls back to none
    undefined fields fall back to defaults
  Full pipeline:
    clean JSON output
    output with think + fence
    missing optional fields → defaults
    empty text → returns null (brain should retry)
```

### 判明した技術的事項

- **pnpm workspace + tsx**: workspace パッケージが ESM（`"type":"module"`）でないと、ESM な bridge から named import できない → `packages/schema` と `packages/utils` に `"type":"module"` を追加した
- **bridge の pretest**: `pnpm -C ../.. --filter @avatar-agent/utils --filter @avatar-agent/schema build` でパッケージを事前ビルドしてから `tsx --test` を実行
- **Node 24 の ESM サイクル制限**: `node --import tsx/esm --test` は Node 24 で動かない → `tsx --test` を使う

---

## 現在の起動確認手順

```bash
cd /Users/ryomaishigaki/prog/avatar-desktop-agent
pnpm install
cp .env.example .env   # 必要に応じて編集
ollama pull qwen3:8b
pnpm dev
# → Bridge が port 3000 で起動 (SSE /events, POST /chat)
# → Electron ウィンドウが開く
# → 入力欄からメッセージ送信 → Ollama 呼び出し → タイプライタ表示
```

```bash
pnpm test   # 33/33 pass
pnpm typecheck  # エラーなし
```
