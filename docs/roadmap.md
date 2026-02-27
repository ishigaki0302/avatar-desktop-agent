# 残実装 計画書

> 作成日: 2026-02-27
> 対象リポジトリ: https://github.com/ishigaki0302/avatar-desktop-agent

---

## 現在の状態

| フェーズ | 状態 |
|---------|------|
| Phase 0: Repo bootstrap | ✅ 完了 |
| Phase 1: UI MVP | ✅ 完了 |
| Phase 2: Brain (Ollama) | ✅ 完了 |
| **Phase 3: OpenClaw** | 📋 未着手 |
| **Phase 4: Hardening** | 📋 未着手 |
| **スプライト画像組み込み** | ⏸ 別途対応（画像制作中） |

---

## スプライト画像の組み込み手順（画像完成後に実施）

### 期待するファイル構成

```
assets/sprites/
├── neutral_close.png    ← 口閉・表情 neutral（待機・会話中）
├── neutral_open.png     ← 口開・表情 neutral
├── happy_close.png
├── happy_open.png
├── sad_close.png
├── sad_open.png
├── angry_close.png
├── angry_open.png
├── surprised_close.png
├── surprised_open.png
├── confused_close.png
├── confused_open.png
├── motion_bow_small_0.png   ← お辞儀アニメ (4フレーム: 0-3)
├── motion_bow_small_1.png
├── motion_bow_small_2.png
├── motion_bow_small_3.png
├── motion_nod_0.png         ← うなずき (3フレーム: 0-2)
├── motion_nod_1.png
├── motion_nod_2.png
├── motion_shake_0.png       ← 首振り (4フレーム: 0-3)
├── motion_shake_1.png
├── motion_shake_2.png
├── motion_shake_3.png
├── motion_wave_0.png        ← 手振り (6フレーム: 0-5)
├── motion_wave_1.png
├── motion_wave_2.png
├── motion_wave_3.png
├── motion_wave_4.png
└── motion_wave_5.png
```

### 画像スペック

- **サイズ**: 320×320px（Canvas サイズと一致）
- **形式**: PNG（透過可）
- **命名規則**: `{emotion}_{open|close}.png` / `motion_{name}_{N}.png`

### 組み込み時の確認事項

1. `apps/ui/src/renderer/avatar.ts` の `MOTION_FRAMES` 定数がフレーム数と一致しているか確認
   ```typescript
   const MOTION_FRAMES: Record<Motion, number> = {
     none: 0,
     bow_small: 4,  // ← 用意したフレーム数に合わせて変更
     nod: 3,
     shake: 4,
     wave: 6,
   };
   ```
2. `pnpm dev` で Electron を起動し、スプライトが正しくロードされるか確認
3. `esbuild define` の `__SPRITE_BASE__` が正しい絶対パスを指していることを確認
   - `dev.mjs` / `build.mjs` の `path.join(projectRoot, "assets/sprites")` で生成される

---

## Phase 3: OpenClaw task delegation

> 目標: Brain が返した `task` フィールドを OpenClaw Gateway に委譲し、結果を要約して UI に返す

### 前提知識

- OpenClaw Gateway は WebSocket で接続する
- 既存の TS SDK / クライアントがあれば流用する（署名ハンドシェイクを自作しない）
- 実行ログは最大 500 字に要約してから Brain/UI に返す
- `.env` の `OPENCLAW_GATEWAY_URL` と `OPENCLAW_API_KEY` を使う

### 実装ステップ

#### Step 3-1: OpenClaw SDK 調査

```bash
# 公式 SDK を確認し、pnpm で追加
pnpm --filter bridge add @openclaw/sdk  # ← 実際のパッケージ名を確認して変更
```

`apps/bridge/src/openclaw.ts` に以下を実装:

```typescript
// Phase 3 実装箇所（現在は stub）
async function gatewayDelegate(goal: string): Promise<string> {
  // TODO: OpenClaw SDK を使って WS 接続
  // import { OpenClawClient } from "@openclaw/sdk";
  // const client = new OpenClawClient(
  //   config.openclaw.gatewayUrl,
  //   config.openclaw.apiKey
  // );
  // const result = await client.execute({
  //   goal,
  //   constraints: { allow_shell: false, no_credential: true }
  // });
  // return summarizeLog(result.log);
}
```

#### Step 3-2: allowlist の厳格化

`packages/utils/src/config.ts` の `openclaw_allow` を確認・拡張:

```typescript
openclaw_allow: [
  "browser_open",
  "browser_search",
  "app_launch",
  "clipboard_read",
  "clipboard_write",
  "screenshot",
] as string[],
```

`apps/bridge/src/openclaw.ts` の `isAllowed()` 関数を intent 分類ベースに改善:

```typescript
// 現在: キーワードの単純マッチ
// 改善案: 危険パターンの deny-list を明示的に管理
const DENY_PATTERNS = [
  /\brm\s/i, /\bsudo\b/i, /eval\(/, /exec\(/,
  /password/i, /credential/i, /private.key/i,
];
```

#### Step 3-3: `summarizeLog()` の改善

現在の実装（`openclaw.ts` 下部）:
```typescript
export function summarizeLog(rawLog: string): string {
  // 重要行を抽出 → 最大 500 字
}
```

改善点:
- ログが長い場合、Ollama に「以下のログを1〜2文で要約して」と問い合わせる（省コストのため temperature=0.1 で）
- または単純に末尾10行 + error/result 行を抽出する現行実装で十分かも

#### Step 3-4: UI への status/result フロー確認

```
POST /chat (ユーザ入力)
  → Brain.ask() → "task" フィールドあり
  → broadcast({ type:"status", state:"running", message:"タスク実行中..." })
  → delegateTask(goal) → OpenClaw 実行（〜60秒）
  → broadcast({ type:"result", summary:"...", details:null })
  → parseRenderEvent(text, emotion, motion)
  → broadcast({ type:"render", ... })
  → broadcast({ type:"status", state:"idle", message:"Ready" })
```

#### Step 3-5: テスト追加

`apps/bridge/src/openclaw.test.ts`:
- `isAllowed()` のホワイトリスト/ブラックリスト検証
- `summarizeLog()` のトランケーション検証
- `delegateTask()` の stub 動作検証（OPENCLAW_GATEWAY_URL 未設定時）

---

## Phase 4: Hardening

> 目標: ローカル限定・タイムアウト・エラーリカバリを実装し、長時間安定動作させる

### Step 4-1: セキュリティ

#### Bridge ホストバインド確認

`apps/bridge/src/server.ts`:
```typescript
// 現状: config から host を読む
const host = config.bridge.host; // デフォルト "127.0.0.1"
await app.listen({ host, port });
```

- `.env.example` の `BRIDGE_HOST=127.0.0.1` を変更不可にする（コメントで警告）
- `host !== "127.0.0.1" && host !== "localhost"` の場合は起動時に `log.warn` を出す

#### 入力サイズ制限

`apps/bridge/src/server.ts` の POST /chat スキーマ:
```typescript
// 現状
message: { type: "string", minLength: 1, maxLength: 4000 }
// Phase 4: Fastify の bodyLimit も設定
const app = Fastify({ bodyLimit: 8192 });
```

#### SSE クライアント数制限

```typescript
// 現状: 無制限
// Phase 4: 最大 SSE 接続数を制限（例: 1〜3）
const MAX_SSE_CLIENTS = 3;
if (subscribers.size >= MAX_SSE_CLIENTS) {
  reply.status(429).send({ error: "Too many SSE clients" });
  return;
}
```

### Step 4-2: タイムアウト / リトライ

#### Ollama 呼び出しタイムアウト

`apps/bridge/src/brain.ts`:
```typescript
// 現状: AbortSignal.timeout(60_000)
// Phase 4: config 化
signal: AbortSignal.timeout(config.ollama.timeoutMs ?? 60_000),
```

`.env.example` に追加:
```env
OLLAMA_TIMEOUT_MS=60000
```

#### OpenClaw タイムアウト

`apps/bridge/src/openclaw.ts`:
```typescript
// 現状: constraints.time_budget_sec = 60（Brain が生成）
// Phase 4: Bridge 側でも独自タイムアウトを持つ
const result = await Promise.race([
  gatewayDelegate(goal),
  new Promise<string>((_, rej) =>
    setTimeout(() => rej(new Error("OpenClaw timeout")), 70_000)
  ),
]);
```

### Step 4-3: エラーリカバリ

#### Bridge プロセスクラッシュ対策（現状）

`apps/bridge/src/index.ts`:
```typescript
// 現状: uncaughtException → process.exit(1)
// Phase 4: 軽微なエラーは SSE に error を broadcast して続行
```

#### Ollama 未起動時の UI 表示

`apps/bridge/src/brain.ts`:
```typescript
// 現状: try/catch → fallback render
// Phase 4: Ollama が落ちているとき専用のエラーメッセージ
if (err instanceof TypeError && err.message.includes("fetch")) {
  broadcast({ type:"status", state:"error", message:"Ollama に接続できません" });
}
```

#### Electron UI のリロード

`apps/ui/src/renderer/renderer.ts`:
```typescript
// 現状: SSE 切断時 3秒後に再接続
// Phase 4: 指数バックオフ（3s → 6s → 12s → max 30s）
```

### Step 4-4: ログとデバッグ

```typescript
// packages/utils/src/logger.ts に追加予定
// ファイルログ出力（オプション）: LOG_FILE=./storage/bridge.log
```

### Step 4-5: 最大出力量制限

`apps/bridge/src/brain.ts`:
```typescript
// 現状: num_predict: 512
// Phase 4: config 化
num_predict: config.ollama.maxPredictTokens ?? 512,
```

`.env.example` に追加:
```env
OLLAMA_MAX_PREDICT=512
```

### Step 4-6: テスト拡充

```
追加するテスト:
- bridge/server.test.ts: POST /chat, GET /events の HTTP テスト（fetch mock）
- bridge/memory.test.ts: applyMemoryUpdate の書き込み検証（tmp ディレクトリ使用）
- bridge/openclaw.test.ts: isAllowed, summarizeLog
```

---

## 将来の拡張候補（MVP 後）

### A. 音声リップシンク（Non-Goal → 将来）
- Text-to-Speech（例: Voicevox / Style-Bert-VITS2）を bridge に追加
- 音声波形から口パク振幅を生成して UI に渡す
- `RenderEvent` に `audioUrl` フィールドを追加

### B. ストリーミング応答
- Ollama の `stream: true` で逐次トークンを受信
- Bridge が SSE でトークンを逐次 broadcast → UI がリアルタイムにタイプライタ
- `RenderEvent` を `type:"render_start"` / `type:"render_token"` / `type:"render_end"` に分割

### C. メモリ検索強化
- `storage/memory/episodes/` から過去会話を意味検索（簡易 TF-IDF or embeddings）
- Brain のコンテキストに関連エピソードを動的に注入

### D. Live2D / VRM 対応
- `apps/ui` に three.js + pixi-live2d を追加
- 現在の Canvas 2D レイヤーを置き換え

---

## 再開時のチェックリスト

```bash
# 1. リポジトリ確認
cd /Users/ryomaishigaki/prog/avatar-desktop-agent
git log --oneline -5

# 2. 依存確認
pnpm install

# 3. テスト通過確認
pnpm test   # 33/33 pass を確認

# 4. 型チェック
pnpm --filter bridge typecheck
pnpm --filter ui typecheck

# 5. ビルド確認
pnpm --filter ui build

# 6. 動作確認（Ollama が起動している場合）
pnpm dev
```

### スプライト追加後の起動確認

```bash
# sprites を assets/sprites/ に配置後
pnpm --filter ui build  # __SPRITE_BASE__ が絶対パスで埋め込まれる
pnpm dev                # Electron でスプライトが表示されることを確認
```
