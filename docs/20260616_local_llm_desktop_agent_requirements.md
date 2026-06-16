# ローカルLLMデスクトップエージェント要件定義 — ChatGPT 壁打ち全文ログ

> 出典: ChatGPT 共有会話「ローカルLLMエージェント要件」
> <https://chatgpt.com/share/6a308848-bf74-83e8-ac5f-b008a5c2725b>
> 会話日: 2026-06-16 ／ 対象リポジトリ: `avatar-desktop-agent`
> 要約せず、発言を時系列で整理した全文記録。Canvas マーカー（`:::writing`）と ChatGPT 内部の引用トークンのみ除去。末尾に会話中に参照された全出典 URL を掲載。

---

## 発言 1 — 👤 石垣（ユーザー）

ローカルでgemma 31bをollamaで使える環境を持っていて、デスクトップエージェントやaituberを作りたいんだけど、要件定義できますか？
関連研究も調べて欲しいです。
クエリさえ作ってくれればディープリサーチの結果を渡します

---

## 発言 2 — 🤖 ChatGPT

かなり面白いテーマですね。

あなたの場合、

- ローカルにGemma 3 31B（Ollama）
- NLP/LLM研究経験あり
- MCPやエージェントにも興味あり
- 研究にも繋がる可能性あり

なので、単なる「作ってみた」ではなく、

**「ローカルLLMを用いた人格一貫型デスクトップエージェント」**
あるいは
**「AITuberとしても振る舞えるマルチモーダルエージェント」**

まで狙えそうです。

---

# まず要件を分解する

実は

> デスクトップエージェント

と

> AITuber

は80%同じです。

共通部分は

```text
ASR
 ↓
LLM
 ↓
Tool Use
 ↓
TTS
 ↓
Avatar
```

だけです。

---

# 案1: デスクトップエージェント

目標

```text
「Ryoma、Slack見て」
「この論文を読んで」
「明日の予定教えて」
```

で実行できる。

---

## 必須機能

### ① 会話

```text
User
 ↓
Whisper
 ↓
Gemma31B
 ↓
TTS
```

低遅延会話

---

### ② MCP

Gemmaが

```text
gmail
calendar
filesystem
browser
slack
```

を呼ぶ

---

### ③ Computer Use

画面を見て

```text
クリック
タイピング
スクロール
```

する

最近は

- OpenHands
- Browser Use
- Agent S2

あたりが強いです。

---

### ④ 長期記憶

```text
Vector DB
+
Profile
+
Task History
```

---

### ⑤ 自律行動

例

```text
毎朝

研究関係の論文検索
↓
要約
↓
Slack送信
```

---

# 案2: AITuber

目標

Neuro-samaみたいなやつ。

---

## 必須機能

### ① 音声会話

```text
ASR
↓
LLM
↓
TTS
```

---

### ② Avatar

候補

- Live2D
- VTube Studio
- Unity

---

### ③ 感情

出力

```json
{
  "emotion":"happy",
  "energy":0.8
}
```

↓

表情制御

---

### ④ Twitch/YouTube Chat

```text
チャット取得
↓
要約
↓
応答
```

---

### ⑤ キャラクター人格

ここが一番重要

あなたのBig Five研究と直結する。

```text
人格ベクトル
+
長期記憶
+
口調
```

で固定人格を作れる。

---

# 実は面白い統合案

私はこれを推します。

---

## Companion Agent

AITuberでもあり

デスクトップエージェントでもある

```text
        Gemma31B
             |
    ----------------
    |              |
Desktop       Avatar
 Agent         Agent
```

---

例えば

```text
「ACLの締切調べて」
```

↓

ブラウザ検索

↓

結果を取得

↓

画面横のキャラが

```text
ACL SRWは7/18締切ですよ！
```

と話す

---

これは既存の
[Open-LLM-VTuber公式プロジェクト](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber)
に近い方向です。完全ローカル動作やLive2D連携を志向しています。

---

# 研究として面白い部分

あなたなら研究にできる。

---

## テーマA

人格一貫性

```text
Long-term Memory
vs
System Prompt
```

どちらが効く？

---

## テーマB

人格方向ベクトル

あなたのBig Five研究の延長。

```text
LLM
+
Personality Vector
+
Agent
```

で行動が変わるか。

---

## テーマC

法務相談エージェント

最近やってる

```text
法務判断
+
過去事例
+
Agent
```

と統合

---

## テーマD

Continuous Agent Memory

これはかなり研究向き。

```text
記憶追加
↓
人格変化
↓
行動変化
```

を評価する。

---

# ディープリサーチ用プロンプト

そのまま投げられるレベルで書きます。

---

**調査目的**

ローカルLLM（Gemma 3 31B + Ollama）を用いて、

1. デスクトップエージェント
2. AI VTuber
3. 両者を統合したCompanion Agent

を構築するための最新技術を調査したい。

以下の観点で包括的に調査してください。

---

### 1. システムアーキテクチャ

- ASR
- LLM
- Tool Use
- MCP
- RAG
- Long-term Memory
- TTS
- Avatar
- Computer Use

を含む標準構成

---

### 2. OSS調査

以下を中心に比較

- Open-LLM-VTuber
- OpenHands
- Browser Use
- Agent S2
- Open Interpreter
- CrewAI
- AutoGen
- LangGraph
- smolagents

それぞれ

- 特徴
- 活発度
- ローカルLLM対応
- Gemma対応
- Ollama対応
- 拡張性

を整理する。

---

### 3. AI VTuber研究

調査対象

- Neuro-sama系
- VTuberエージェント
- Conversational Avatar
- Embodied Agent
- Virtual Companion

について

- システム構成
- 表情制御
- 感情モデル
- 長期記憶
- リアルタイム性

を整理する。

---

### 4. デスクトップエージェント研究

調査対象

- Computer Use Agent
- GUI Agent
- Desktop Agent

について

- 画面理解
- GUI操作
- Vision-Language Model
- 安全性
- タスク成功率

を整理する。

---

### 5. 長期記憶

- MemGPT
- Letta
- Generative Agents
- MemoryBank
- LongMem

などの手法を比較する。

---

### 6. ローカル実行

Gemma 3 31B + Ollama を前提に

- 推論速度
- VRAM要件
- 量子化
- 音声処理
- マルチプロセス構成

を整理する。

---

### 7. 未解決課題

以下を重点的に調査

- 人格の一貫性
- 長期記憶の劣化
- Tool Use失敗
- Hallucination
- Avatarとの整合性
- マルチエージェント化

---

### 8. 研究テーマ候補

トップ会議

- ACL
- EMNLP
- NAACL
- ICLR
- NeurIPS

を狙えるレベルで

「Companion Agent」
「AI VTuber」
「Desktop Agent」

に関する未解決研究課題を10件以上提案する。特に人格制御・長期記憶・エージェント行動評価を重視する。

---

個人的には、あなたのバックグラウンドなら

**「Big Five人格方向 × 長期記憶 × Desktop Agent」**

が一番論文化しやすい気がします。

既に人格方向ベクトルを持っているので、

```text
人格
↓
ツール選択
↓
行動
↓
長期記憶
```

まで評価すると、単なるAITuber制作ではなく研究テーマになります。

---

## 発言 3 — 👤 石垣（ユーザー）

入力は文字でいいです

---

## 発言 4 — 🤖 ChatGPT

了解です。入力が文字なら、かなり簡単になります。

構成はこうで十分です。

```text
User text
  ↓
Gemma 31B / Ollama
  ↓
Tool use / MCP
  ↓
Text response
  ↓
TTS
  ↓
Avatar / Desktop UI
```

つまり **ASRは不要** です。

ディープリサーチのプロンプトも、以下のように修正するとよいです。

```text
ローカルLLM（Gemma 3 31B + Ollama）を用いて、テキスト入力ベースのデスクトップエージェント／AI VTuber／Companion Agentを構築するための関連研究・OSS・実装アーキテクチャを調査してください。

前提：
- ユーザー入力は音声ではなくテキスト
- 音声認識（ASR）は不要
- 出力はテキストに加えて、必要ならTTSとアバター表情制御を行う
- LLMはOllama上のGemma 3 31Bを想定
- ローカル実行を重視する
- 可能ならMCPやTool Useを使ってデスクトップ操作・ファイル操作・ブラウザ操作を行う

調査観点：
1. テキスト入力型デスクトップエージェントの標準構成
2. AI VTuber／Conversational Avatarの構成
3. Ollama対応のOSS比較
   - Open-LLM-VTuber
   - Open Interpreter
   - OpenHands
   - Browser Use
   - LangGraph
   - AutoGen
   - CrewAI
   - Letta / MemGPT
4. Tool Use / MCP / Computer Useの実装方法
5. 長期記憶・人格一貫性・キャラクター設定の関連研究
6. Gemma 3 31Bをローカルで使う場合の制約
7. 最小実装MVP案
8. 研究テーマ化できる未解決課題

特に、音声入力ではなくテキスト入力であることを前提に、ASRを除いた構成で整理してください。
```

要件定義も **MVPは「テキストチャット + TTS + Live2D + ツール実行」** でよさそうです。

---

## 発言 5 — 👤 石垣（ユーザー）

「Big Five人格方向
この話は一旦置いておいていいです

---

## 発言 6 — 🤖 ChatGPT

そうですね。現時点では完全に切り離して考えていいと思います。

むしろ最初にやるべきは

```text
人格
↓
行動
```

ではなく

```text
行動できる
↓
安定して動く
↓
長期記憶がある
↓
人格を載せる
```

です。

---

もし私が今のあなたの状況で作るなら、

## Phase 1

まずは

**「デスクトップマスコット」**

を作ります。

イメージは

```text
右下にキャラがいる

ユーザー
「ACLの締切調べて」

↓
ブラウザ検索

↓
結果取得

↓
キャラが喋る
```

だけ。

人格は不要。

---

## MVP要件

### 必須

- Gemma 31B (Ollama)
- テキスト入力
- テキスト出力
- TTS
- Live2D

---

### ツール

最初は2つだけ

```text
Web Search
Filesystem
```

---

### 長期記憶

なし

---

### 自律行動

なし

---

これだけで十分面白いです。

---

# Phase 2

次に

```text
Memory
```

を追加

例えば

```text
研究テーマ
締切
好きなこと
```

を覚える。

ここで

- Letta
- MemGPT
- GraphRAG

あたりを調べる。

---

# Phase 3

ようやくAgent化

```text
論文を探す
↓
読む
↓
要約する
```

みたいな行動をする。

---

# ディープリサーチで本当に調べるべきこと

正直、

```text
AITuber
```

より

```text
Desktop Companion
Desktop Agent
```

の方が重要です。

なぜならAITuber部分は

```text
Live2D
+
TTS
```

を付けるだけだから。

難しいのは

```text
どう考えるか
どう記憶するか
どう行動するか
```

です。

---

なので調査クエリも、

```text
Desktop Companion Agent
Desktop Assistant
Personal AI Assistant
Computer Use Agent
Memory-Augmented Agent
```

を中心にした方がいいです。

---

個人的には、

Neuro-sama方向よりも

「PC上にいる研究アシスタント」

の方があなたに合っています。

例えば

```text
「この論文読んどいて」

↓
PDF解析

↓
要約

↓
関連研究検索

↓
口頭で説明
```

までできると、博士課程との相性がかなり良いです。

その上で見た目だけLive2D化すると、自然にAITuber要素も入ります。

---

## 発言 7 — 👤 石垣（ユーザー）

長期記憶は欲しい

---

## 発言 8 — 🤖 ChatGPT

了解です。では **長期記憶あり** を前提にすると、MVPはこうです。

```text
User text
  ↓
Conversation Manager
  ↓
Memory Retrieval
  ↓
Gemma 31B / Ollama
  ↓
Tool Use
  ↓
Memory Write
  ↓
Text / TTS / Avatar
```

要件としては、長期記憶を3層に分けるのがよさそうです。

```text
1. Profile Memory
   ユーザーの基本情報・好み・研究テーマ

2. Episodic Memory
   過去の会話・依頼・作業履歴

3. Task Memory
   進行中タスク・締切・ToDo・未完了作業
```

最初の実装では、全部を複雑にせず、

```text
SQLite
+
Vector DB
+
Memory Summarizer
```

で十分です。

具体的には、

```text
会話終了ごとに要約
↓
重要そうな情報だけ保存
↓
次回会話時に類似検索
↓
プロンプトへ注入
```

です。

ディープリサーチ用プロンプトはこの方向で修正するとよいです。

```text
ローカルLLM（Gemma 3 31B + Ollama）を用いて、テキスト入力型のデスクトップコンパニオンエージェント／AI VTuberを構築するための関連研究・OSS・実装アーキテクチャを調査してください。

前提：
- ユーザー入力はテキスト
- ASRは不要
- 出力はテキスト、必要に応じてTTSとLive2D等のアバター制御
- LLMはOllama上のGemma 3 31B
- ローカル実行を重視
- 長期記憶を必須機能とする
- Big Fiveなど人格方向ベクトルの話は今回は対象外

特に以下を重点的に調査してください。

1. テキスト入力型デスクトップエージェントの標準アーキテクチャ
2. 長期記憶を持つLLMエージェントの関連研究
   - MemGPT / Letta
   - Generative Agents
   - MemoryBank
   - LongMem
   - Reflexion
   - Voyager
   - Agent memory architectures
3. 長期記憶の設計方式
   - Profile memory
   - Episodic memory
   - Semantic memory
   - Task memory
   - Vector DB memory
   - Knowledge graph memory
   - Summarization-based memory
4. 記憶の書き込み方
   - 何を記憶するか
   - いつ記憶するか
   - ユーザー許可を必要にするか
   - 忘却・更新・矛盾解決をどう扱うか
5. 記憶の読み出し方
   - 類似検索
   - 時間順検索
   - 重要度スコア
   - recency / relevance / importance
   - RAGとの違い
6. OSS比較
   - Letta / MemGPT
   - LangGraph
   - AutoGen
   - CrewAI
   - Open Interpreter
   - Open-LLM-VTuber
   - OpenHands
   - Browser Use
7. ローカルLLM + Ollamaでの実装可能性
   - Gemma 3 31Bでのtool use
   - JSON出力安定性
   - 推論速度
   - 量子化
   - ローカルVector DB
8. MVP設計
   - 最小構成
   - 推奨技術スタック
   - 実装順序
   - 失敗しやすい点
9. 研究テーマ化できる未解決課題
   - 長期記憶の評価
   - 記憶の一貫性
   - 記憶の更新・忘却
   - ユーザー依存パーソナライズ
   - Desktop Agentにおける記憶利用の有効性評価
```

この方針なら、研究にも開発にも使いやすいです。

---

## 発言 9 — 👤 石垣（ユーザー）

そういえば昔レポジトリ作って似たようなことやってたみたい
これをそのまま上書きする形で実装したい

git@github.com:ishigaki0302/avatar-desktop-agent.git

---

## 発言 10 — 🤖 ChatGPT

既存リポジトリを上書き前提にすると、要件定義は「新規開発」よりも「移行・再構成」の形にした方がよいです。まず公開情報として見える範囲を確認しつつ、ローカルで確認してほしいコマンドも含めて整理します。

---

## 発言 11 — 🤖 ChatGPT

リポジトリ自体は検索では見つからなかったので、privateか未indexっぽいです。

上書き前提なら、まずローカルでこれを実行して構成を見たいです。

```bash
git clone git@github.com:ishigaki0302/avatar-desktop-agent.git
cd avatar-desktop-agent
find . -maxdepth 3 -type f | sed 's#^\./##' | sort
```

その出力を渡してもらえれば、既存構成を活かした上書き設計にできます。

現時点の上書き方針はこれです。

```text
avatar-desktop-agent/
├── apps/
│   ├── desktop/        # Electron / Tauri UI
│   └── agent/          # Python or Node agent server
├── packages/
│   ├── memory/         # 長期記憶
│   ├── llm/            # Ollama / Gemma 31B
│   ├── tools/          # web, filesystem, browser, desktop操作
│   ├── tts/            # VOICEVOX等
│   └── avatar/         # Live2D / VTube Studio連携
├── data/
│   ├── memory.db
│   └── vector_store/
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   └── research_prompt.md
└── README.md
```

MVP要件はこうです。

```text
テキスト入力
↓
長期記憶検索
↓
Gemma 3 31B / Ollama
↓
必要ならツール実行
↓
応答生成
↓
記憶更新
↓
テキスト表示 + TTS + アバター制御
```

優先実装順は、

```text
1. Ollama接続
2. チャットUI
3. memory.db + vector store
4. memory read/write
5. TTS
6. Live2D / VTube Studio
7. filesystem tool
8. web/browser tool
```

です。

ディープリサーチには、既存リポジトリ上書き前提としてこの一文を足すとよいです。

```text
既存の GitHub リポジトリ avatar-desktop-agent を上書き・再構成する前提で、破壊的変更を許容しつつ、長期保守しやすいディレクトリ構成、MVP実装順序、移行方針も提案してください。
```

---

## 発言 12 — 👤 石垣（ユーザー）

https://github.com/ishigaki0302/avatar-desktop-agent.git
パブリックになってるはず

---

## 発言 13 — 🤖 ChatGPT

URLありがとうございます。公開URLで確認して、既存の構成に合わせた「上書き実装」の要件定義とディープリサーチ用クエリに寄せます。

---

## 発言 14 — 🤖 ChatGPT

見えました。かなり土台あります。

現状はすでに、

- TypeScript monorepo + pnpm
- Electron UI
- Fastify bridge
- Ollama REST
- OpenClaw連携
- SSEストリーミング
- 表情・モーション制御
- セッションログ JSONL
- 簡易メモリ `persona.md` / `user_profile.md`

まで実装済みです。README上では Phase 1〜7 が完了扱いです。 

なので「上書き」というより、次は **Gemma 31B + 長期記憶 + 実用ツール化** に拡張するのがよさそうです。

## 次の要件定義

```text
Phase 8  Gemma 31B 対応
- qwen3.5:2b 前提を gemma3:31b に変更
- モデル名を .env 管理
- 長文応答・JSON崩れ対策
```

```text
Phase 9  長期記憶 v2
- user_profile.md だけでなく SQLite / Vector DB を追加
- episodic memory: 過去会話
- semantic memory: ユーザー情報・好み・研究テーマ
- task memory: 未完了タスク・締切
```

```text
Phase 10  Memory Retrieval
- 毎ターン前に関連記憶を検索
- system prompt に注入
- recency / relevance / importance でランキング
```

```text
Phase 11  Memory Write
- 会話後に記憶候補を抽出
- 保存 / 更新 / 削除 / NOOP をJSONで返す
- 矛盾時は上書きではなく履歴付き更新
```

```text
Phase 12  Tool Use
- filesystem
- web search
- browser操作
- OpenClaw経由の安全なdesktop操作
```

OpenClawはすでにWebSocket連携とdeny-listがあるので、そこは活かせます。

## ディープリサーチ用プロンプトに追加する一文

```text
既存リポジトリ avatar-desktop-agent は、TypeScript monorepo、Electron UI、Fastify bridge、Ollama REST、OpenClaw連携、SSEストリーミング、JSONLセッションログ、persona.md/user_profile.md による簡易メモリを持つ。これを破壊的に作り直すのではなく、Gemma 3 31B、長期記憶v2、Memory Retrieval/Write、実用Tool Useへ拡張する前提で調査してください。
```

結論として、今のrepoは捨てなくてよくて、**Phase 8以降を足す形** が一番よさそうです。

---

## 発言 15 — 👤 石垣（ユーザー）

それを踏まえた要件定義をお願いします

---

## 発言 16 — 🤖 ChatGPT

既存実装を前提に、今回は「作り直し」ではなく「Phase 8以降の正式な要件定義」としてまとめます。公開リポジトリのREADMEと構成で確認できる範囲に寄せます。

---

## 発言 17 — 🤖 ChatGPT

確認した前提：既存repoは Electron UI、Fastify bridge、Ollama REST、OpenClaw、SSE、JSONLログ、`persona.md` / `user_profile.md` の簡易メモリまで実装済みです。

以下をそのまま要件定義として使えます。

# avatar-desktop-agent 要件定義

## 1. 目的

ローカルLLMである Gemma 3 31B を Ollama 経由で利用し、テキスト入力ベースのデスクトップコンパニオンエージェントを構築する。

本システムは、既存の `avatar-desktop-agent` を土台とし、既存の Electron UI、Fastify bridge、Ollama 接続、OpenClaw 連携、SSE ストリーミング、アバター表示機能を活かしながら、長期記憶と実用的なツール利用を追加する。

## 2. 想定ユースケース

### 2.1 日常会話

ユーザーがテキストで話しかけると、アバターが表情・モーション付きで応答する。

例：

```text
今日やること整理して
```

### 2.2 研究アシスタント

論文、実験、締切、アイデア、過去の会話を記憶し、必要に応じて思い出して応答する。

例：

```text
前に話してた法務審査AIの研究テーマ、もう一回整理して
```

### 2.3 デスクトップ補助

OpenClaw やツール機能を通じて、ファイル確認、ブラウザ操作、簡単なデスクトップ操作を支援する。

例：

```text
このフォルダのREADMEを読んで要約して
```

### 2.4 AITuber 的表現

入力はテキストのまま、出力をアバター・TTS・表情制御に接続することで、AITuber風の反応を行う。

## 3. 対象外

初期段階では以下は対象外とする。

- 音声入力
- ASR
- Big Five 人格方向ベクトル
- 完全自律型の常時監視エージェント
- 危険なOS操作
- SNSや配信サイトへの自動投稿

## 4. システム構成

```text
User Text
  ↓
Electron UI
  ↓
Fastify Bridge
  ↓
Memory Retrieval
  ↓
Gemma 3 31B / Ollama
  ↓
Tool Router
  ↓
Memory Write
  ↓
SSE Streaming
  ↓
Avatar UI / Text / TTS
```

## 5. 機能要件

## 5.1 LLM接続

### 必須要件

- Ollama 経由で Gemma 3 31B を利用できる
- モデル名は `.env` で変更可能にする
- 既存の `qwen3.5:2b` 依存をなくす
- JSON出力の失敗時にリトライまたはフォールバックする
- ストリーミング応答を維持する

### 環境変数案

```env
BRAIN_BACKEND=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:31b
OLLAMA_TEMPERATURE=0.7
OLLAMA_MAX_TOKENS=512
```

## 5.2 チャットUI

### 必須要件

- テキスト入力できる
- Shift + Enter で送信できる
- 応答を逐次表示できる
- 表情・モーションを応答に合わせて変更できる
- エラー時に UI 側で分かるように表示する

### 継続利用する既存要素

- Electron UI
- Canvas / スプライト描画
- タイプライタ表示
- 口パク
- 表情
- モーション

## 5.3 長期記憶

長期記憶は本システムの中心機能とする。

### 記憶タイプ

```text
Profile Memory
  ユーザーの基本情報、好み、研究テーマ、作業スタイル

Episodic Memory
  過去の会話、相談、意思決定、作業履歴

Task Memory
  未完了タスク、締切、やること、進行中プロジェクト

Semantic Memory
  会話から抽出された一般化された知識
```

### 保存方式

MVPでは以下を採用する。

```text
SQLite
  構造化メモリ、タスク、会話要約

Vector Store
  類似検索用の埋め込み

Markdown
  persona.md などの人間が直接編集する固定設定
```

### メモリスキーマ案

```sql
memories (
  id TEXT PRIMARY KEY,
  type TEXT,
  content TEXT,
  source TEXT,
  importance INTEGER,
  created_at TEXT,
  updated_at TEXT,
  last_accessed_at TEXT,
  embedding_id TEXT,
  metadata JSON
)
```

```sql
tasks (
  id TEXT PRIMARY KEY,
  title TEXT,
  status TEXT,
  due_date TEXT,
  content TEXT,
  created_at TEXT,
  updated_at TEXT
)
```

## 5.4 Memory Retrieval

各ターンの応答前に、関連する記憶を検索してプロンプトへ注入する。

### 検索条件

- 類似度
- 新しさ
- 重要度
- タスク状態
- ユーザーが明示的に言及したキーワード

### ランキング式の例

```text
score = relevance + recency + importance
```

### プロンプト注入

```text
Relevant memories:
- ...
- ...

Current tasks:
- ...
```

のように、LLM入力に追加する。

## 5.5 Memory Write

各ターン後に、会話内容から保存すべき記憶を抽出する。

### 書き込み分類

```json
{
  "operation": "CREATE | UPDATE | DELETE | NOOP",
  "memory_type": "profile | episodic | task | semantic",
  "content": "...",
  "reason": "..."
}
```

### 保存対象

- ユーザーが明示的に「覚えて」と言ったこと
- 今後も役立つ好み・制約・研究テーマ
- 未完了のタスク
- 重要な意思決定
- 継続中のプロジェクト情報

### 保存しないもの

- 一時的な雑談
- その場限りの感情
- 不確かな推測
- 秘密情報
- パスワードや認証情報

## 5.6 Tool Use

MVPでは安全なツールから実装する。

### Phase 1 Tools

```text
filesystem.read
filesystem.list
memory.search
memory.write
```

### Phase 2 Tools

```text
web.search
browser.open
browser.read
```

### Phase 3 Tools

```text
desktop.click
desktop.type
desktop.scroll
desktop.screenshot
```

### 安全要件

- 危険操作は deny-list で禁止
- ファイル削除は禁止
- `sudo`, `rm`, `eval`, `exec`, credential 系操作は禁止
- デスクトップ操作は原則ユーザー確認を挟む
- パスワード欄への入力は禁止

## 5.7 TTS

初期段階では任意機能とする。

### 要件

- 応答テキストをTTSに渡せる
- TTSの有効・無効を設定できる
- 長文は文単位で分割して読み上げる
- 読み上げ中に口パクと同期する

### 候補

- VOICEVOX
- AivisSpeech
- Style-Bert-VITS2
- Web Speech API

## 5.8 アバター制御

既存の emotion / motion 形式を維持する。

### emotion

```text
happy
neutral
surprised
sad
confused
```

### motion

```text
wave
nod
bow_small
shake
none
```

LLM出力形式は以下を基本とする。

```json
{
  "emotion": "happy",
  "motion": "nod",
  "text": "いいね、それならまず要件を整理しよう。",
  "memory_update": "NOOP",
  "task": null
}
```

## 6. 非機能要件

## 6.1 ローカル実行

- LLMはローカルOllamaを基本とする
- メモリDBもローカル保存
- 外部API依存を最小化する
- ネットワーク通信が必要な機能は明示的に分離する

## 6.2 レイテンシ

目標値：

```text
短文応答開始: 5秒以内
通常応答完了: 30秒以内
長文・ツール利用: 60秒以内
```

Gemma 31B は重いため、応答開始の速さを重視し、ストリーミングを必須とする。

## 6.3 保守性

- TypeScript monorepo を維持する
- package単位で責務を分ける
- schemaを共有する
- memory / tools / llm / avatar を疎結合にする

## 6.4 ログ

既存の JSONL セッションログを維持する。

追加で以下を記録する。

- 使用モデル
- retrievalされた記憶
- 書き込まれた記憶
- tool call
- latency
- error

## 7. 推奨ディレクトリ構成

```text
avatar-desktop-agent/
├── apps/
│   ├── ui/
│   └── bridge/
├── packages/
│   ├── schema/
│   ├── utils/
│   ├── llm/
│   ├── memory/
│   ├── tools/
│   ├── avatar/
│   └── tts/
├── storage/
│   ├── memory/
│   │   ├── persona.md
│   │   ├── user_profile.md
│   │   ├── memory.sqlite
│   │   └── vector/
│   └── sessions/
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── memory-design.md
│   └── research.md
└── README.md
```

## 8. 実装フェーズ

## Phase 8: Gemma 31B 対応

### 目的

既存の qwen3.5:2b 前提をなくし、Gemma 3 31B を正式対応する。

### 作業

- `.env` にモデル名を移す
- READMEのモデル説明を更新
- JSON出力パーサを強化
- 長文出力対応
- タイムアウト値を調整

### 完了条件

- `OLLAMA_MODEL=gemma3:31b` で起動できる
- 既存UIで応答が表示される
- emotion / motion / text が正常に処理される

## Phase 9: Memory v2

### 目的

`user_profile.md` 中心の簡易メモリから、SQLite + Vector Store に移行する。

### 作業

- memory package 作成
- SQLite schema 作成
- memory create / update / search 実装
- 既存 `user_profile.md` を初期データとして取り込む

### 完了条件

- 会話内容からメモリを書き込める
- 過去メモリを検索できる
- メモリが再起動後も保持される

## Phase 10: Memory Retrieval

### 目的

応答前に関連記憶を自動取得する。

### 作業

- ユーザー入力を検索クエリ化
- vector search
- recency / importance ranking
- prompt injection

### 完了条件

- 過去に話した内容を自然に参照できる
- 関係ない記憶が大量に入らない
- retrieval結果がログに残る

## Phase 11: Memory Write

### 目的

会話後に保存すべき記憶を自動抽出する。

### 作業

- memory write prompt 作成
- CREATE / UPDATE / DELETE / NOOP 対応
- ユーザー明示保存に対応
- 矛盾検出

### 完了条件

- 「覚えて」と言った内容が保存される
- 不要な雑談は保存されない
- 既存記憶の更新ができる

## Phase 12: Tool Use v1

### 目的

安全なファイル操作とメモリ操作をツール化する。

### 作業

- tool schema 作成
- filesystem read/list
- memory search/write
- tool callログ保存

### 完了条件

- 指定フォルダのファイル一覧を取得できる
- README等を読んで要約できる
- ツール利用結果を応答に反映できる

## Phase 13: Web / Browser Tool

### 目的

研究補助のためにWeb検索・ブラウザ閲覧を可能にする。

### 作業

- web search
- browser open/read
- 検索結果要約
- 引用元管理

### 完了条件

- Web検索して結果を要約できる
- 参照元URLを保持できる
- 調査結果を会話に反映できる

## Phase 14: TTS

### 目的

AITuber / デスクトップマスコットらしい出力体験を作る。

### 作業

- TTS backend 選定
- 文単位分割
- 口パク同期
- ON/OFF設定

### 完了条件

- 応答を音声読み上げできる
- 読み上げ中にアバターが口パクする
- テキストのみモードでも動く

## 9. MVP定義

最初の完成形は以下とする。

```text
Gemma 3 31B / Ollama
+ テキスト入力
+ アバター応答
+ 長期記憶
+ セッションログ
+ filesystem read/list
```

MVPではWeb検索、TTS、完全なデスクトップ操作は必須ではない。

## 10. 成功基準

### 定性的基準

- 過去に話した研究テーマを覚えている
- ユーザーの好みや作業方針を踏まえて応答できる
- アバターとして自然に反応する
- ローカル環境で完結して動く

### 定量的基準

- 再起動後も記憶が保持される
- 関連記憶の retrieval 成功率を評価できる
- tool call 成功率をログから集計できる
- 平均レイテンシを計測できる

## 11. 今後の研究化ポイント

- 長期記憶がデスクトップエージェントの有用性をどれだけ上げるか
- どの記憶を保存すべきか
- 記憶の更新・忘却をどう扱うべきか
- ユーザー固有コンテキストがツール利用に与える影響
- アバター表現がエージェントへの信頼感に与える影響

この要件定義なら、既存repoを捨てずに **Phase 8以降の拡張仕様** としてそのまま `docs/requirements.md` に置けます。

---

## 発言 18 — 👤 石垣（ユーザー）

少し本筋とは外れるんですが、僕とaiがどういう対話をしているかを全部記録しておきたいです

エージェントを使っていて、何を不満に思っていたのか、をログとして保存し解析したい

---

## 発言 19 — 🤖 ChatGPT

それ、本筋から外れているように見えて、実はかなり重要な要件だと思います。

むしろ

> 長期記憶を作る

より先に

> 人間とエージェントのインタラクションを観測可能にする

をやった方がいいかもしれません。

---

# なぜ重要か

普通のエージェントは

```text
User
↓
Agent
↓
Response
```

しか残していません。

でも本当に知りたいのは

```text
なぜユーザーは満足したのか

なぜユーザーは不満だったのか

どこで期待とズレたのか
```

です。

---

例えば

```text
ユーザー
「論文読んどいて」

Agent
「要約しました」
```

だけ保存しても、

実は

```text
不満:
- 要約が浅い
- 数式を読んでない
- 関連研究がない
```

が分かりません。

---

# 私ならMemoryとは別に

新しく

```text
Interaction Analytics
```

を作ります。

---

## Session Log

既存JSONLの拡張

```json
{
  "timestamp":"...",
  "user":"論文読んどいて",
  "assistant":"...",
  "latency":12.4,
  "tool_calls":["pdf.read"],
  "memory_used":[...]
}
```

---

## Feedback Log

これを別に持つ

```json
{
  "session_id":"...",
  "turn_id":"...",
  "satisfaction":2,
  "reason":"要約が浅い"
}
```

---

# もっと面白い

ユーザーが明示的に評価しなくても、

エージェントに自己分析させる。

---

例

毎ターン後

```text
ユーザーは満足したか？
```

を推定

```json
{
  "predicted_satisfaction":0.4,
  "possible_issue":"回答が一般論"
}
```

保存

---

すると

```text
会話ログ
+
推定不満ログ
```

が溜まる。

---

# 研究的にはこっちが面白い

正直、

```text
長期記憶
```

単体より

```text
長期記憶
+
ユーザー不満分析
```

の方が研究として面白いです。

---

例えば半年後

```text
1000ターン
```

くらい貯まると

解析できる。

---

## 解析1

どのツールが不満を生むか

```text
filesystem
  満足度 4.2

web search
  満足度 3.8

pdf reading
  満足度 2.1
```

---

## 解析2

どの研究タスクで失敗するか

```text
論文要約
  高評価

関連研究探索
  低評価
```

---

## 解析3

長期記憶は本当に役立っているか

```text
memory使用時
平均満足度 4.3

memory未使用時
平均満足度 3.1
```

---

# 要件に追加したい機能

私はむしろ

```text
Phase 9.5

Interaction Analytics
```

を入れます。

---

保存対象

```text
全会話

全ツール呼び出し

全メモリ参照

レイテンシ

ユーザー修正

ユーザーの再質問

ユーザーの否定表現
```

---

さらに

```text
会話終了時

「今日の不満点あった？」
```

ボタンを置く。

---

すると

将来的に

```text
Human-Agent Interaction Dataset
```

になります。

これ、実は今後かなり価値が出る可能性があります。

あなたの場合、

「自分専用のコンパニオンエージェントを育てる」

だけでなく、

**「エージェントとの長期インタラクションを観測する実験基盤」**

として設計した方が、研究的なリターンも大きいと思います。

---

## 発言 20 — 👤 石垣（ユーザー）

そうそう
要件定義を再構築して

---

## 発言 21 — 🤖 ChatGPT

はい。中心を **「長期記憶つきデスクトップエージェント」から「対話ログ分析基盤つきエージェント」** に再構築するとよさそうです。

# avatar-desktop-agent 要件定義 v2

## 1. 目的

本システムは、ローカルLLMである Gemma 3 31B を Ollama 経由で利用し、テキスト入力型のデスクトップコンパニオンエージェントを構築する。

単に応答するエージェントではなく、ユーザーとAIの対話、ツール利用、記憶利用、満足・不満の発生を継続的に記録し、後から分析できる実験基盤として設計する。

## 2. 中心コンセプト

```text
会話できる
↓
記憶できる
↓
行動できる
↓
ログを残せる
↓
不満を分析できる
↓
改善できる
```

本システムでは、長期記憶と同じくらい、あるいはそれ以上に、Interaction Analytics を重要機能として扱う。

## 3. 想定ユースケース

### 3.1 デスクトップコンパニオン

ユーザーがテキストで話しかけると、アバターが応答する。

```text
今日やること整理して
```

### 3.2 研究アシスタント

論文、研究アイデア、締切、過去の相談内容を記憶し、必要に応じて参照する。

```text
前に話してた法務審査AIの研究テーマを整理して
```

### 3.3 作業補助エージェント

ファイル確認、README読解、軽いブラウザ調査、メモリ検索などを行う。

```text
このフォルダのREADMEを読んで要約して
```

### 3.4 対話ログ分析

エージェント利用中に、どのような不満・期待外れ・再質問・修正要求が発生したかを記録する。

```text
この回答、浅い
```

```text
違う、そうじゃなくて
```

```text
もっと具体的に
```

これらを単なる会話として捨てず、改善分析用のデータとして保存する。

## 4. 対象外

初期段階では以下は対象外とする。

- 音声入力
- ASR
- Big Five 人格方向ベクトル
- 完全自律型エージェント
- 危険なOS操作
- SNSや配信サイトへの自動投稿
- ユーザー許可なしの外部送信

## 5. 全体アーキテクチャ

```text
User Text
  ↓
Electron UI
  ↓
Fastify Bridge
  ↓
Interaction Logger
  ↓
Memory Retrieval
  ↓
Gemma 3 31B / Ollama
  ↓
Tool Router
  ↓
Response Generator
  ↓
Memory Writer
  ↓
Interaction Analyzer
  ↓
SSE Streaming
  ↓
Avatar / Text / TTS
```

## 6. 主要モジュール

```text
LLM Module
  Ollama / Gemma 3 31B

Memory Module
  長期記憶の保存・検索・更新

Tool Module
  filesystem, browser, web, memory tools

Avatar Module
  表情・モーション・TTS

Interaction Logging Module
  全対話・ツール利用・記憶利用を記録

Interaction Analytics Module
  不満・満足・失敗パターンを抽出

Dashboard Module
  ログ・満足度・失敗傾向を可視化
```

## 7. 機能要件

## 7.1 LLM接続

- Ollama 経由で Gemma 3 31B を使える
- モデル名は `.env` で変更可能にする
- ストリーミング応答を維持する
- JSON出力が壊れた場合のリトライ処理を持つ
- 小型モデルへの切り替えも可能にする

```env
BRAIN_BACKEND=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:31b
OLLAMA_TEMPERATURE=0.7
OLLAMA_MAX_TOKENS=1024
```

## 7.2 チャットUI

- テキスト入力できる
- 応答を逐次表示できる
- 会話履歴を表示できる
- 各応答にフィードバックボタンを付ける
- 表情・モーションを応答に合わせて変更できる

フィードバックUI例：

```text
👍 良い
👎 微妙
📝 理由を書く
🔁 やり直し
```

## 7.3 長期記憶

記憶は以下の4種類に分ける。

```text
Profile Memory
  ユーザーの基本情報、好み、研究テーマ

Episodic Memory
  過去の会話、相談、意思決定

Task Memory
  未完了タスク、締切、ToDo

Semantic Memory
  会話から抽出された一般化知識
```

保存方式：

```text
SQLite
  構造化メモリ

Vector Store
  類似検索

Markdown
  persona.md / user_profile.md などの固定設定
```

## 7.4 Memory Retrieval

各ターン前に、関連記憶を検索する。

検索スコア：

```text
score = relevance + recency + importance
```

検索結果はプロンプトに注入する。

```text
Relevant memories:
- ...

Current tasks:
- ...
```

また、どの記憶を参照したかを必ずログに残す。

## 7.5 Memory Write

各ターン後に、保存すべき記憶を抽出する。

```json
{
  "operation": "CREATE | UPDATE | DELETE | NOOP",
  "memory_type": "profile | episodic | task | semantic",
  "content": "...",
  "reason": "..."
}
```

保存対象：

- ユーザーが明示的に覚えてと言ったこと
- 今後も役立つ好み・制約
- 研究テーマ
- 未完了タスク
- 重要な意思決定
- エージェントへの継続的な不満

保存しないもの：

- 一時的な雑談
- パスワード
- 認証情報
- 不確かな推測
- 機微情報

## 7.6 Interaction Logging

全ターンを構造化ログとして保存する。

### turn_logs

```sql
turn_logs (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  turn_index INTEGER,
  timestamp TEXT,
  user_input TEXT,
  assistant_output TEXT,
  model TEXT,
  latency_ms INTEGER,
  emotion TEXT,
  motion TEXT,
  created_at TEXT
)
```

### tool_call_logs

```sql
tool_call_logs (
  id TEXT PRIMARY KEY,
  turn_id TEXT,
  tool_name TEXT,
  input_json TEXT,
  output_json TEXT,
  status TEXT,
  latency_ms INTEGER,
  error TEXT,
  created_at TEXT
)
```

### memory_access_logs

```sql
memory_access_logs (
  id TEXT PRIMARY KEY,
  turn_id TEXT,
  memory_id TEXT,
  access_type TEXT,
  relevance_score REAL,
  reason TEXT,
  created_at TEXT
)
```

## 7.7 Interaction Analytics

ユーザーが何に不満を持ったのかを分析する。

### 保存する分析対象

- 明示的な低評価
- 再質問
- 訂正
- 否定表現
- 「違う」
- 「浅い」
- 「もっと具体的に」
- 「それは不要」
- 「前にも言った」
- ツール失敗
- 応答遅延
- 記憶の取り違え
- 幻覚
- 過剰に一般論だった回答

### inferred_feedback_logs

```sql
inferred_feedback_logs (
  id TEXT PRIMARY KEY,
  turn_id TEXT,
  predicted_satisfaction REAL,
  issue_type TEXT,
  issue_detail TEXT,
  evidence TEXT,
  confidence REAL,
  created_at TEXT
)
```

issue_type 例：

```text
shallow_answer
misunderstanding
wrong_memory
tool_failure
latency
hallucination
too_verbose
too_abstract
ignored_context
unsafe_action
format_mismatch
```

## 7.8 明示フィードバック

ユーザーが任意でフィードバックを残せる。

```sql
explicit_feedback_logs (
  id TEXT PRIMARY KEY,
  turn_id TEXT,
  rating INTEGER,
  label TEXT,
  comment TEXT,
  created_at TEXT
)
```

rating：

```text
5: とても良い
4: 良い
3: 普通
2: 微妙
1: 不満
```

## 7.9 会話終了時サマリー

セッション終了時に、以下を自動生成する。

```json
{
  "session_summary": "...",
  "user_goals": ["..."],
  "successful_points": ["..."],
  "frustration_points": ["..."],
  "memory_updates": ["..."],
  "future_improvements": ["..."]
}
```

これにより、単なるログではなく、後で分析しやすい単位にまとめる。

## 7.10 Dashboard

後からログを分析するための簡易ダッシュボードを用意する。

表示項目：

- 日別利用回数
- 平均満足度
- 推定不満ランキング
- tool call 成功率
- memory retrieval 成功率
- 応答レイテンシ
- よく発生する issue_type
- 「やり直し」が多いタスク
- 長期記憶が使われたターンの満足度

## 8. Tool Use

初期実装は安全なツールに限定する。

### Phase 1

```text
filesystem.list
filesystem.read
memory.search
memory.write
```

### Phase 2

```text
web.search
browser.open
browser.read
```

### Phase 3

```text
desktop.screenshot
desktop.click
desktop.type
desktop.scroll
```

安全要件：

- ファイル削除は禁止
- sudo禁止
- rm禁止
- credential操作禁止
- パスワード欄への入力禁止
- 外部送信はユーザー確認必須
- デスクトップ操作は原則確認付き

## 9. ログ保存ポリシー

### 原則

このシステムでは、ユーザーとAIの対話を研究・改善目的で保存する。

### 保存するもの

- ユーザー入力
- AI応答
- ツール呼び出し
- 参照された記憶
- 書き込まれた記憶
- 明示フィードバック
- 推定フィードバック
- セッション要約
- レイテンシ
- エラー

### 注意するもの

- 個人情報
- 認証情報
- パスワード
- APIキー
- 秘密文書
- 外部に出してはいけない研究データ

### 必須機能

- ログ保存ON/OFF
- セッション単位の削除
- 特定ログの削除
- export
- local only mode
- private mode

## 10. 非機能要件

## 10.1 ローカルファースト

- LLMはローカルOllamaを基本とする
- DBもローカル保存
- ログもローカル保存
- 外部APIを使う場合は明示する

## 10.2 観測可能性

各ターンについて以下を追跡できる。

```text
何を入力したか
何を返したか
どの記憶を使ったか
どのツールを使ったか
どれくらい時間がかかったか
ユーザーは満足したか
何に不満だったか
```

## 10.3 拡張性

- memory
- tools
- analytics
- avatar
- llm

を疎結合にする。

## 11. 推奨ディレクトリ構成

```text
avatar-desktop-agent/
├── apps/
│   ├── ui/
│   └── bridge/
├── packages/
│   ├── schema/
│   ├── llm/
│   ├── memory/
│   ├── tools/
│   ├── avatar/
│   ├── tts/
│   ├── logger/
│   └── analytics/
├── storage/
│   ├── memory/
│   │   ├── memory.sqlite
│   │   └── vector/
│   ├── sessions/
│   ├── logs/
│   └── exports/
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── memory-design.md
│   ├── interaction-analytics.md
│   └── research.md
└── README.md
```

## 12. 実装フェーズ

## Phase 8: Gemma 31B 対応

- `.env` でモデル指定
- Gemma 3 31B 対応
- JSON出力安定化
- ストリーミング維持

## Phase 9: Interaction Logging v1

- 全ターン保存
- tool call 保存
- memory access 保存
- latency 保存
- JSONLからSQLiteへ拡張

完了条件：

```text
1ターンごとに、入力・出力・モデル・時間・エラーが保存される
```

## Phase 10: Explicit Feedback

- 👍 / 👎 ボタン
- rating
- comment
- issue label

完了条件：

```text
ユーザーが各応答に評価を付けられる
```

## Phase 11: Memory v2

- SQLite memory
- Vector Store
- profile / episodic / task / semantic 分離
- 再起動後も保持

## Phase 12: Memory Retrieval / Write

- 関連記憶検索
- プロンプト注入
- 会話後の記憶抽出
- memory access log 保存

## Phase 13: Interaction Analytics v1

- 不満推定
- issue_type分類
- confidence保存
- evidence保存

完了条件：

```text
各ターンに対して、満足度推定と不満理由が保存される
```

## Phase 14: Dashboard

- セッション一覧
- turn一覧
- feedback一覧
- issue_type集計
- tool成功率
- memory使用率
- latency可視化

## Phase 15: Tool Use v1

- filesystem.list
- filesystem.read
- memory.search
- memory.write

## Phase 16: Web / Browser Tool

- web search
- browser read
- source保存
- 調査ログ保存

## Phase 17: TTS / Avatar強化

- TTS
- 口パク同期
- 表情制御
- AITuber風演出

## 13. MVP定義

MVPは以下とする。

```text
Gemma 3 31B / Ollama
+ テキスト入力
+ アバター応答
+ 全対話ログ保存
+ 明示フィードバック
+ 推定不満分析
+ 長期記憶
+ memory access log
```

初期MVPでは、TTS、Web検索、デスクトップ操作は必須ではない。

## 14. 成功基準

### エージェントとしての成功

- テキスト会話ができる
- 過去の内容を覚えている
- 必要な記憶を取り出せる
- アバターとして自然に応答する

### 分析基盤としての成功

- すべての会話が保存される
- 不満が明示・推定の両方で保存される
- 後から「なぜ不満だったか」を追える
- tool / memory / latency と満足度の関係を分析できる
- 改善前後の比較ができる

## 15. 研究化ポイント

このシステムは、以下の研究基盤になる。

- 長期記憶はユーザー満足度を上げるか
- エージェントの失敗はどの種類に分類できるか
- ユーザーの再質問や訂正から不満を推定できるか
- 記憶利用が逆に不満を生むケースは何か
- Tool Use失敗は満足度にどう影響するか
- ローカルLLMエージェントは長期利用で改善できるか
- Human-Agent Interaction Dataset として利用できるか

## 16. 最重要方針

このエージェントは、単なる便利ツールではなく、ユーザーとAIの長期的な関係を観測するためのシステムである。

したがって、最優先すべき実装順は以下である。

```text
1. 全対話ログ
2. 明示フィードバック
3. 推定不満分析
4. 長期記憶
5. ツール利用
6. アバター演出
```

これで、かなり研究基盤寄りになりました。特に **Interaction Analytics** を独立モジュールにしたのがポイントです。

---

## 発言 22 — 👤 石垣（ユーザー）

保存しないもののの中に一時的な雑談があるけど

これは保存したい、というか、そんなに研究寄りに構えないで自然なインタラクションを観測するのが目的なので

例えばなにかの感想をllmに話したりしたい

というか基本全部保存して良い
なぜなら全部ローカルに完結させるから

---

## 発言 23 — 🤖 ChatGPT

はい、その方針の方が自然です。

要件定義は以下のように修正するのがよいです。

```text
原則：
ユーザーとAIの全インタラクションを保存する。

保存対象：
- 研究相談
- 作業依頼
- 雑談
- 感想
- 愚痴
- 好き嫌い
- その場限りの話題
- アバターへの反応
- エージェントへの不満
- 訂正
- 再質問
- 沈黙・中断・やり直し
- ツール呼び出し
- 記憶参照
- 応答レイテンシ

保存しないもの：
- パスワード
- APIキー
- 認証トークン
- 秘密鍵
- クレジットカード番号
- 明示的に「保存しないで」と言った内容
```

特に、Memory と Log を分けるのが大事です。

```text
Interaction Log
  全部保存する
  雑談も感想も保存する
  後から分析するための生ログ

Long-term Memory
  応答に使うための抽出記憶
  全ログから必要なものだけ昇格する
```

つまり、

```text
全部保存する
↓
ただし全部を毎回思い出すわけではない
↓
応答に使う記憶だけ別途抽出する
```

です。

要件定義の該当箇所はこう差し替えでよいです。

```text
## ログ保存ポリシー

本システムでは、ローカル完結を前提として、ユーザーとAIの全インタラクションを保存する。

保存対象は研究相談や作業依頼に限定しない。雑談、感想、愚痴、違和感、アバターへの反応、その場限りの会話も含めて保存する。

目的は、研究用に整ったデータだけを集めることではなく、ユーザーがAIとどのように自然に関わるのかを長期的に観測することである。

ただし、以下は保存対象から除外、または自動マスクする。

- パスワード
- APIキー
- 認証トークン
- 秘密鍵
- クレジットカード番号
- 明示的に「保存しないで」と言った内容

また、ログ保存と長期記憶は分離する。

Interaction Log は原則すべて保存する。
Long-term Memory は、応答時に利用するために抽出・要約された記憶であり、すべてのログをそのままプロンプトに入れるわけではない。
```

この方向だと、システムの主目的はかなり明確になります。

**「自然なAIとの生活内インタラクションをローカルに蓄積し、あとから分析できるデスクトップエージェント」**

です。

---

## 発言 24 — 👤 石垣（ユーザー）

ディープリサーチ結果です

これを含めて最終版要件定義(冗長でOK)を作成してください

# ローカルLLMデスクトップコンパニオンエージェント調査報告

## 要旨

2026年6月16日時点の一次情報で最も重要な前提整理は、**Gemma 3 の公式サイズは 270M / 1B / 4B / 12B / 27B であり、31B は Gemma 4 系のサイズ**だという点です。Ollama の Gemma 3 ライブラリも 27B を最大サイズとして掲載しているため、本報告では、ユーザー要件の「Gemma 3 31B」は実務上 **`gemma3:27b` を中心に検討するのが自然**だと解釈します。もし本当に 31B を使いたいなら、それは Gemma 4 への切り替えになります。 

結論から言うと、**ローカル実行重視・テキスト入力・長期記憶必須**という条件では、最も堅い設計は「**テキストUI + オーケストレータ + Ollama 上の Gemma 3 27B + ハイブリッド長期記憶 + 必要時のみ TTS/アバター制御**」です。長期記憶は単一方式ではなく、**Profile memory、Semantic collection、Episodic summary、Task/procedural memory** を分離し、Profile は“現在の真実”、Episodic は“過去の出来事”、Task は“うまくいった作業手順”として扱うのが、研究・OSS・実装事例の共通パターンでした。 

OSS選定では、**長期記憶そのものを研究対象にするなら Letta、独自制御と実験自由度を重視するなら LangGraph、アバター付きローカルAIコンパニオンの具体的参照実装としては Open-LLM-VTuber** が有力です。一方で、OpenHands / Open Interpreter / Browser Use は強力ですが、初期MVPの重心を「デスクトップ・コンパニオン」「記憶」に置くなら、早い段階で組み込みすぎると複雑性と安全性の負債が増えやすいです。 

## 標準アーキテクチャ

テキスト入力型のデスクトップコンパニオンエージェントを、今回の要件に合わせて最小限に抽象化すると、構成は次のようになります。

```text
Desktop Chat UI
  -> Agent Orchestrator
    -> Working Memory / Session State
    -> Long-Term Memory Manager
    -> Ollama Inference Layer
    -> Optional Tool Layer
    -> Optional TTS Layer
    -> Optional Avatar Control Layer
  -> Local Persistence
```

この形は、研究面では **CoALA の「作業記憶を中核に、長期記憶と外界行動を接続する構図」** に対応し、実装面では **LangGraph の stateful workflow、Letta の memory blocks と archival memory、Open-LLM-VTuber の LLM/TTS/Live2D/MCP の分離** と整合します。つまり、デスクトップ・コンパニオンで必要なのは「単なるチャットUI」ではなく、**作業記憶・長期記憶・外部行動・出力表現の責務分離**です。 

研究側の視点では、CoALA は言語エージェントを **working memory、long-term memory、internal actions、external actions** の組として整理しており、内部行動は **retrieval・reasoning・learning** に分解されます。これはデスクトップ・コンパニオンにそのまま移植しやすく、**ユーザーが入力したテキストに対し、まず作業記憶で現在の会話状態を保持し、必要に応じて長期記憶を検索し、最後に返答やアバター動作を選ぶ** という流れに落とし込めます。 

OSS側の視点では、Letta は **常時プロンプトに見える memory blocks** と、**必要時検索の archival memory** を明確に分けています。memory blocks は「常時見せるべき状態」、archival memory は「必要時に意味検索する長期保存」という設計で、デスクトップ・コンパニオンでは前者を **ユーザー名、現在の関係設定、返信ルール、会話方針** に、後者を **過去会話から抽出した事実・出来事・知識** に割り当てるのが自然です。 

アプリケーション参照実装としては Open-LLM-VTuber がかなり近く、**オフライン動作、Ollama対応、デスクトップクライアント、Lettaベース長期記憶、Live2D、MCPツール、ブラウザ制御** を既に統合しています。ただし同プロジェクトは **音声対話を主軸** にしており、長期記憶を有効化すると **会話遅延が増える** と明記しています。今回の要件では ASR は不要なので、そこを最初から切り落として **テキストUI主導・音声とアバターは後付けアダプタ** にするのが、より堅実な標準アーキテクチャです。 

## 長期記憶研究と設計原則

長期記憶研究の系譜を整理すると、**MemGPT / Letta、Generative Agents、MemoryBank、LongMem、Reflexion、Voyager** は、それぞれ別の記憶問題を強く押し出しています。MemGPT は **main context と external context の間で LLM が自律的に情報移送する OS 比喩** を打ち出し、会話の一貫性を測る DMR タスクで固定コンテキスト基線を大きく上回りました。Generative Agents は **observation・planning・reflection** を揃え、経験記録から高次の反省を生成し、それを次の行動計画へ使う構造を示しました。MemoryBank は **Ebbinghaus の忘却曲線** を取り入れ、重要度と時間経過に応じた記憶保持を試みています。LongMem は **凍結した本体モデル + 残差 side-network** による長期記憶拡張、Reflexion は **失敗からの言語的反省を episodic memory buffer に蓄積する学習様式**、Voyager は **実行可能コードの ever-growing skill library** による procedural memory を強調しています。 

この流れをまとめる理論枠組みとして CoALA は有用で、既存エージェントを **semantic / episodic / procedural memory** と **grounding / reasoning / retrieval / learning** の組み合わせとして比較可能にしました。さらに 2026 年のサーベイは、LLM エージェント記憶の進化を **Storage → Reflection → Experience** の三段階で整理しており、単なる保存から、要約・反省・経験抽象へ重心が移っていると指摘しています。デスクトップ・コンパニオンを研究テーマ化するなら、まさにこの「Storage を越えて Experience に近づける」ことが核心になります。 

設計上の含意は明快です。**一種類のメモリだけで長期記憶を実装しようとしないこと** が重要です。LangMem も、長期記憶を **semantic / episodic / procedural** で分け、semantic の中でも **Profile と Collection** を区別しています。Profile は「最新状態を表す単一文書」、Collection は「無制限に増える個別記録」、Eepisodic は「過去の成功事例や会話要約」、Procedural は「ルールやスタイルや方針」です。この分割は、コンパニオン用途で非常に実装しやすいです。 

実務的には、今回の用途に最も適した記憶設計は次の対応関係になります。**Profile memory** はユーザーの呼び名、話し方の好み、禁止事項、現在の活性タスク。**Semantic memory** は学籍、研究テーマ、端末環境、好みのアプリのような安定事実。**Episodic memory** は「前回この問題で何をして失敗したか」の会話要約。**Task / procedural memory** は「Git の衝突時にはまず status を見てから…」のような行動上の定石です。Voyager の skill library や Reflexion の reflective text は、コンパニオン文脈では **“作業ノウハウの長期保持”** と読み替えると実装価値が高いです。 

Knowledge graph memory は、この基本設計の上位版です。Zep / Graphiti は **時間変化と出典を保持する temporal knowledge graph** を提案し、MemGPT の DMR と LongMemEval で優位だったと報告しています。デスクトップ・コンパニオンでは、単なるベクトルDBだけだと **「以前は研究室Aと言っていたが今は研究室B」「以前はWindows、今はLinux」** のような時間差・矛盾処理が弱いので、**変化する事実が多い対象だけ KG 化** するのは研究テーマとして非常に有望です。 

## 記憶の書き込みと読み出し

記憶の**書き込み対象**は、「全部の会話」ではなく、**後で効く情報だけを抽出する** 方がよいです。LangMem は Collection 型メモリで、過抽出だと検索精度が落ち、過少抽出だと再現率が落ちると説明しています。CrewAI も task output をそのまま大きな塊で保存するのではなく、**atomic facts に分解して remember する** 流れを推奨しています。したがってコンパニオンでは、**安定的なユーザー嗜好、重要な約束、継続中のプロジェクト状態、繰り返し有効だった手順、明示的に“覚えて”と言われた事項** を優先して保存し、雑談の全文は保存対象ではなく要約対象にすべきです。 

記憶の**書き込みタイミング**は二系統に分けるのが定石です。LangGraph / LangMem は、会話中に即座に保存する **hot path / conscious formation** と、会話後に反省・統合する **background / subconscious formation** を区別しています。Letta Code も `/remember` による明示記憶と、会話後に走る **dreaming / reflection subagents** を分けています。重要な事実やユーザーが明示した内容は hot path、要約や統合や重複排除は background に回す、という二段構えが最も自然です。 

**ユーザー許可**については、研究論文よりもフレームワーク設計が参考になります。Letta Code には明示的な `/remember` があり、LangMem の Profile は **手動編集しやすい単一文書** として設計されています。したがって、実装としては **非センシティブな task memory や一般的な嗜好は自動抽出、個人属性・長期保存したくない私的情報・関係性に関わる重要事項は明示許可またはユーザー編集可能な Profile に昇格** という方式が妥当です。つまり、「勝手に全部覚える」ではなく、「自動記憶 + 可視化 + 手動修正」をセットにするべきです。 

**忘却・更新・矛盾解決**も単一ルールでは足りません。Profile は、新情報が来たら **既存文書を更新して最新状態に寄せる** のに向いています。Collection は **delete / invalidate / update / consolidate** の調停問題を伴い、CrewAI には類似レコードをまとめる consolidation があり、MemoryBank は忘却曲線を導入しています。さらに、時間で真偽が変わる情報は、Zep のように **valid time と provenance を持つ temporal graph** の方が本質的に扱いやすいです。実装上のルールとしては、**現在状態は Profile を単一真実源に、履歴は Episodic に残し、矛盾する事実は消すのではなく superseded として時系列管理** が最も破綻しにくいです。 

記憶の**読み出し**は、類似検索だけでは不十分です。AutoGen の `ListMemory` は **時系列順の単純読み出し** を持ち、CrewAI は **semantic similarity・recency・importance** を合成したスコアを採用しています。LangMem も relevance は semantic similarity だけではなく、**importance と recently/frequently used で決まる強さ** を合わせるべきだとしています。コンパニオンにはこの三要素、すなわち **relevance / recency / importance** の三軸が必須です。直近の予定のようなものは recency が強く、人生史のような安定事実は importance が強く、専門知識や過去の障害対処は relevance が強い、という使い分けになります。 

**RAG との違い**も切り分けが必要です。AutoGen は memory を「各ステップの直前に有用な事実をコンテキストへ追加する仕組み」と説明し、その典型例として RAG を挙げていますが、CrewAI は **Knowledge を外部参照ライブラリ**、Memory を **エージェントが行動の中で保存・再利用する内部文脈** と分けています。したがって今回のコンパニオンでは、**RAG は外部資料やマニュアルを読むため、Memory はユーザーとエージェント自身の継続状態を扱うため** と明確に役割分担するのがよいです。 

## OSSの比較と採用方針

**Letta / MemGPT** は、今回のテーマに最も直接刺さる OSS です。Letta は memory blocks を **常時可視の文脈**、archival memory を **意味検索の長期記憶** として分離し、さらに Letta Code では **MemFS という git-backed なメモリファイルシステム、自己編集、反省 subagent、ローカルモード、Ollama 接続** を備えています。長期記憶そのものが研究対象なら、最初の比較基準として最も価値があります。欠点は、記憶機構が強いぶんシステム全体もやや重く、音声・Live2D・独自UIとの境界設計を自分で整理する必要があることです。 

**LangGraph** は、最も記憶特化というより、**長期間動く stateful workflow を自分で設計するための基盤** です。長期記憶の型、hot path と background の分離、Profile / Collection / Episodic / Procedural の設計指針は LangMem 側に整理されており、Ollama 連携も LangChain 側で既に提供されています。したがって、**“記憶の理論を活かしつつ、自前アーキテクチャを実験したい”** なら LangGraph が最も自由度が高いです。 

**AutoGen** は、RAG 的 memory protocol、時系列 `ListMemory`、そして旧系の Teachability のような **vector DB による教示記憶** を持っており、Ollama も OpenAI 互換経由で扱えます。ただし、Letta ほど「記憶第一の思想」は強くなく、どちらかというと **ツール実行や multi-agent の中に memory コンポーネントを挿す** 設計です。研究プロトタイプとしては有用ですが、長期記憶の中身を深く検証したいなら Letta / LangGraph より一段抽象度が高いです。 

**CrewAI** は、Memory を単一APIにまとめ、**semantic similarity・recency・importance の合成スコア** と、タスク出力からの **atomic fact 抽出**、類似記録の **consolidation** まで用意しています。記憶運用の思想はかなり実践的です。ただしドキュメント上の既定値では LLM 分析に `gpt-4o-mini`、保存に `lancedb`、埋め込みに OpenAI 既定が見えており、**強いローカル志向で使うには埋め込み・分析モデル・保存層を自前で差し替える前提** になります。 

**Open Interpreter** は、低コストモデル向けの coding/computer-use agent で、**ローカルの設定とセッション状態を `~/.openinterpreter` に保持** し、モデル harness を切り替えつつブラウザやネイティブアプリを操作できます。しかし、ドキュメント自身が **LLM生成コードの実行は本質的に危険** と述べ、確認プロンプトや sandbox を重視しています。したがって、これは「コンパニオンの記憶コア」ではなく、**後段で desktop action を追加したいときの参考実装** と見るのが適切です。 

**OpenHands** は、会話イベントを **append-only log** として保持し、Docker sandbox で任意コードを安全に実行する、非常に強い computer-use / software agent 基盤です。ただし OpenHands 公式は **ローカルL L Mでは機能制限があり、open-weight モデルは tool-use reliability と malformed JSON に課題がある** と明言しています。デスクトップ・コンパニオンのMVPには過剰装備で、**OS操作やコーディング自動化が研究対象になる段階で導入** するのがよいです。 

**Browser Use** は、ローカル MCP サーバとして動き、OpenAI 互換モデルを受けられ、ブラウザ制御・抽出・履歴・resumable sessions を備えています。ただし本質は **ブラウザ自動化基盤** であって、ユーザー長期記憶システムではありません。コンパニオンにウェブ操作を与えたい場合の tool layer としては非常に適していますが、**記憶の主役にはしない** 方が整理しやすいです。 

**Open-LLM-VTuber** は、今回の調査対象の中で最も“完成品に近い”参照実装です。**オフライン動作、Ollama、デスクトップクライアント、Live2D、TTS、Lettaベース長期記憶、デスクトップペットモード** をすでに備えており、Electron クライアントもあります。ただし、長期記憶は Letta 外部連携で **会話遅延が増え**、また設計思想は音声UI寄りです。したがって、**アバター/TTS/UI の参照実装としては最有力、記憶研究の中核には必ずしも最適化されていない** と評価できます。 

採用方針を一言でまとめると、**研究重視なら LangGraph または Letta を中核にし、VTuber 表現は Open-LLM-VTuber から借りる** のが一番バランスが良いです。逆に **最短で“動く AI VTuber”を作る** なら Open-LLM-VTuber を土台にしつつ、記憶部分だけ Letta 設計を厳密化する方が速いです。 

## Gemma 3 27B と Ollamaでの実装可能性

まずモデル面では、Gemma 3 自体は Google の公開時点で **function calling と structured output をサポートする** と案内されています。さらに Ollama は **tool calling** と **structured outputs** を公式機能として持ち、JSON Schema に従う出力制約を提供しています。そのため、**Gemma 3 27B + Ollama でツール利用と構造化出力を行うこと自体は可能** です。 

ただし、**“可能”と“安定”は別** です。Google が 2025年12月に **FunctionGemma** を別途公開したこと自体、Gemma 3 系で function calling の信頼性をさらに高める余地があったことを示しています。OpenHands も、一般に open-weight / local models では **tool-use reliability が大きく揺れ、malformed JSON が起こりうる** と注意しています。したがって Gemma 3 27B を中核にする場合は、**JSON Schema 制約、バリデーション、再試行、repair step、失敗時の text fallback** を前提にすべきです。 

推論速度はハードウェア依存ですが、少なくとも一次情報から言えるのは、Ollama の `gemma3:27b` の既定量子化モデル（Q4_K_M）は **17GB** であり、Open-LLM-VTuber も **モデルファイルサイズが GPU メモリを超えると CPU 実行に落ちて非常に遅い** と明記しています。Google も Ollama / llama.cpp により Gemma は **GPUなしの小型計算機でも実行可能** としていますが、デスクトップ・コンパニオンとして快適な往復遅延を目指すなら、**27B を常用するには GPU で載る量子化前提** と考えるべきです。快適性を優先するなら 12B も十分に現実的です。 

量子化については、Ollama の Gemma 3 ページが **QAT モデルは BF16 と近い品質を保ちつつ、非量子化版比で約3分の1のメモリフットプリント** と説明しています。したがってローカル用途では、まず **`gemma3:27b` の量子化版** を基準線にし、速度が足りなければ **12B へ落とす**、精度が足りなければ **用途を要約・対話中心に絞る** のが現実的です。 

ローカル埋め込み・検索基盤については、Ollama 自身が **Embeddings API** を提供し、推薦モデルとして **EmbeddingGemma** を挙げています。保存先は、**Qdrant local mode** が「少量ベクトルを in-memory / on-disk で保持」でき、**Chroma** は persistent client で簡単に永続化でき、**FAISS** は最軽量な類似検索ライブラリとして使えます。単一ユーザーのデスクトップ・コンパニオンなら、**MVP は Chroma または Qdrant local mode、研究用途では Qdrant、超軽量なら FAISS** が妥当です。 

## MVP設計

今回の要件に対する **最小構成** は、意外に小さくできます。必要なのは **テキストUI、Ollama 接続、セッション履歴、Profile memory、Episodic summary、Semantic retrieval、応答生成** のみです。TTS と Live2D は、初期段階では必須ではなく、Open-LLM-VTuber も LLM / TTS / ASR をモジュール分離しているため、**まずテキストベースで記憶品質を固め、後から TTS とアバターを付ける** 方が失敗しにくいです。 

**推奨技術スタック**は、研究自由度を優先するなら「**Ollama + Gemma 3 27B、オーケストレーションは LangGraph、記憶設計は LangMem の型分割を採用、ベクトル永続化は Qdrant local mode または Chroma、埋め込みは EmbeddingGemma**」です。より“すぐ動く VTuber”を優先するなら、「**Open-LLM-VTuber を UI/アバター層として使い、長期記憶は Letta、ローカル推論は Ollama**」が近道です。TTS をローカルに寄せるなら **VOICEVOX はローカル HTTP API を持ち、sherpa-onnx もオフライン TTS を提供** しています。アバター制御先としては **VTube Studio の公開API** が扱いやすいです。 

**実装順序**は、記憶を最後に回さないことが重要です。順番としては、まず **Ollama との対話ループ** を安定化し、次に **Profile memory** を入れて「名前・口調・禁止事項」のような current state を保持し、その後に **Episodic summary + Semantic retrieval** を追加し、最後に **Task/procedural memory** を加えるのがよいです。Generative Agents、Reflexion、Voyager が示したように、エージェントの持続性は単なる事実記憶ではなく、**反省・要約・行動手順の蓄積** で大きく変わります。 

**失敗しやすい点**ははっきりしています。第一に、会話全文をそのままベクトル化して保存すると、LangMem が警告するように precision / recall のバランスが崩れます。第二に、hot path に書き込み処理を載せすぎると遅延が増えます。第三に、モデルが GPU に収まらないと CPU 実行で会話体験が崩れます。第四に、ローカル open-weight モデルでは JSON と tool use の破綻を前提に設計しないと不安定になります。第五に、Open Interpreter や OpenHands 系の computer-use を早く入れすぎると、安全性と制御不能性の問題が先に来ます。 

## 研究課題と限界

研究テーマとして最も筋がよいのは、**長期記憶の評価** です。既存ベンチマークには、会話長期記憶の **LoCoMo**、長期記憶能力を五つに分けて測る **LongMemEval**、環境経験に基づくエージェント記憶を測る **LongMemEval-V2**、MemGPT の **DMR** があります。しかし、**テキスト入力型デスクトップ・コンパニオンエージェント** に特化した評価は見当たりません。つまり、「ユーザー継続関係」「ローカル作業履歴」「デスクトップ上の反復タスク」という文脈に合わせた新規評価系を設計できる余地があります。 

次に重要なのは、**記憶の一貫性と更新** です。Profile は最新状態に強い一方、Episodic と Semantic は履歴を残すため、両者の間に矛盾が起こります。LangMem は Profile と Collection の使い分け、CrewAI は consolidation、MemoryBank は forgetting、Zep は temporal provenance を提案していますが、どの方式が **長期使用で最も壊れにくいか** はまだ決着していません。特に「古い事実を消すべきか、残して superseded にすべきか」は、コンパニオンの信頼性に直結します。 

さらに、**ユーザー依存パーソナライズ** は未解決です。Letta Code は `/remember` や memory self-edit を持ち、LangMem の Profile は手動編集しやすく設計されていますが、実際のユーザー体験としては「何を自動で覚え、何を確認し、何を忘れるか」の期待が人によって大きく異なります。したがって、学術的には **記憶精度だけでなく、ユーザーが“覚えられ方”をどれだけ受容するか**、つまり訂正負荷・可視性・可制御性まで測る必要があります。 

最後に、**Desktop Agent における記憶利用の有効性評価** も有望です。LongMemEval-V2 は、エージェントが環境経験を内在化できるかを測る方向へ進んでいます。これをデスクトップ領域へ移して、**メモリなし、semantic のみ、semantic+episodic、semantic+episodic+task** のアブレーションを行い、**次セッション継続率、再指示回数、タスク完了率、応答遅延、ユーザー信頼度** を比較すれば、今回のテーマはそのまま研究になります。MemGPT、Generative Agents、Voyager が示した“記憶が行動品質を変える”という主張を、デスクトップ環境で検証し直す価値は高いです。 

本調査の限界も明示しておきます。**Gemma 3 27B を Ollama 上で使ったときの tool use / JSON 安定性の厳密な定量ベンチマーク** は、今回確認した一次資料には十分揃っていませんでした。そのため、本報告の「Gemma 3 27B は実装可能だが堅牢化が必要」という評価は、Google と Ollama の公式機能説明、および OpenHands など周辺 OSS の運用上の注意を総合した工学的結論です。また、Open-LLM-VTuber は活発に更新中で、現行ドキュメント自体も「active development」と明記しています。 

総合すると、今回の要件に対する最善の方針は、**Gemma 3 系では `gemma3:27b` を前提にし、LangGraph あるいは Letta を記憶コアに置き、Profile / Episodic / Semantic / Task の四層記憶を分け、ブラウザ操作や computer use は MVP 後に追加する** ことです。AI VTuber 表現を重視するなら Open-LLM-VTuber の UI/アバター層は非常に有力ですが、研究価値の中核は **“記憶をどう書くか、どう読むか、どう更新するか”** にあります。

---

## 発言 25 — 🤖 ChatGPT

調査結果の重要な修正点として、モデル前提は「Gemma 3 31B」ではなく **Gemma 3 27B / 必要なら Gemma 4 31B** に直します。さらに、前回の「研究寄りに保存対象を絞る」方針はやめて、**ローカル完結なので原則すべて保存し、Memoryへの昇格だけを選別する**形にします。

---

## 発言 26 — 🤖 ChatGPT

以下が最終版です。`docs/requirements.md` にそのまま置ける粒度で書いています。

# avatar-desktop-agent 最終版要件定義

## 1. 概要

本プロジェクトは、ローカルLLMを用いたテキスト入力型デスクトップコンパニオンエージェントを構築することを目的とする。

ユーザーはデスクトップ上のチャットUIからテキストでエージェントに話しかける。エージェントは、ローカルで動作するLLM、長期記憶、対話ログ、ツール利用、アバター表現を組み合わせて応答する。

本システムの特徴は、単なるチャットボットやAI VTuberではなく、ユーザーとAIの自然なインタラクションをすべてローカルに記録し、後から分析できる点にある。

研究相談、作業依頼、雑談、感想、愚痴、違和感、不満、再質問、アバターへの反応など、ユーザーとAIの間で発生するやり取りを広く保存する。これにより、ユーザーがAIとどのように関わり、何に満足し、何に不満を持ち、どのような場面でエージェントが役に立ったかを長期的に観測できるようにする。

## 2. 基本方針

本システムの最重要方針は以下である。

```text
ローカルで動く
全部記録する
必要なものだけ記憶として昇格する
後から分析できる
自然な会話体験を壊さない
```

ここでいう「全部記録する」とは、研究相談や作業依頼だけでなく、雑談、感想、愚痴、一時的な話題、アバターへの反応も含めて保存するという意味である。

ただし、すべてのログを毎回LLMのプロンプトに入れるわけではない。

本システムでは、以下を明確に分離する。

```text
Interaction Log
  すべてのやり取りを保存する生ログ

Long-term Memory
  応答時に使うため、ログから抽出・要約・構造化された記憶

Profile
  現在のユーザー状態や設定を表す最新情報

Analytics
  満足・不満・失敗・改善点を後から分析するための派生データ
```

## 3. モデル前提

当初は「Gemma 3 31B」を想定していたが、調査結果を踏まえ、Gemma 3 系の実務上の前提は `gemma3:27b` とする。

Gemma 3 の公式サイズは 270M / 1B / 4B / 12B / 27B であり、31B を利用する場合は Gemma 4 系への切り替えとして扱う。

したがって、本要件定義では以下を標準とする。

```text
標準モデル:
  gemma3:27b

軽量・高速モード:
  gemma3:12b

将来候補:
  gemma4:31b 相当のモデル
```

モデル名は固定せず、`.env` で切り替え可能にする。

```env
BRAIN_BACKEND=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:27b
OLLAMA_TEMPERATURE=0.7
OLLAMA_MAX_TOKENS=1024
```

## 4. 対象システム

既存の `avatar-desktop-agent` リポジトリを土台にする。

既存実装には、以下の要素がすでに存在する。

```text
TypeScript monorepo
Electron UI
Fastify bridge
Ollama REST連携
OpenClaw連携
SSEストリーミング
アバター表示
表情・モーション制御
JSONLセッションログ
persona.md / user_profile.md による簡易メモリ
```

本要件定義では、この既存実装を破棄せず、Phase 8以降の拡張仕様として再構成する。

## 5. 目的

本システムの目的は大きく3つある。

### 5.1 デスクトップコンパニオンとして使えること

日常的に話しかけられるAIとして、自然なテキスト対話を行う。

例：

```text
今日やること整理して
```

```text
この論文の話、ちょっと聞いて
```

```text
今の回答ちょっと違う
```

```text
この映画の感想を話したい
```

### 5.2 長期記憶を持つこと

ユーザーの研究テーマ、作業スタイル、好み、過去の会話、継続中のタスクなどを保持し、必要に応じて応答に反映する。

ただし、ログと記憶は分離する。

すべての会話はログとして保存するが、応答に使う記憶は、ログから抽出・要約・構造化されたものに限定する。

### 5.3 インタラクション分析基盤になること

ユーザーがAIを使っていて、どこに不満を持ったのか、どの応答が役に立ったのか、どのツール利用が失敗したのかを後から分析できるようにする。

分析対象には以下を含める。

```text
再質問
訂正
否定
不満
やり直し要求
応答の浅さ
文脈無視
記憶の取り違え
ツール失敗
レイテンシ
アバターへの違和感
```

## 6. 対象外

初期段階では以下を対象外とする。

```text
音声入力
ASR
完全自律型エージェント
危険なOS操作
ユーザー確認なしの外部送信
SNSや配信サイトへの自動投稿
Big Five人格方向ベクトル
```

TTSやLive2Dは将来的に重要だが、MVPでは必須ではない。

初期段階では、テキスト入力とログ・記憶・分析を優先する。

## 7. 全体アーキテクチャ

標準アーキテクチャは以下とする。

```text
Desktop Chat UI
  ↓
Fastify Bridge
  ↓
Agent Orchestrator
  ↓
Interaction Logger
  ↓
Working Memory / Session State
  ↓
Long-Term Memory Manager
  ↓
Ollama Inference Layer
  ↓
Tool Router
  ↓
Response Generator
  ↓
Memory Writer
  ↓
Interaction Analyzer
  ↓
SSE Streaming
  ↓
Text UI / Avatar / Optional TTS
  ↓
Local Persistence
```

責務は以下のように分離する。

```text
UI Layer
  ユーザー入力、応答表示、フィードバックUI、アバター表示

Bridge Layer
  UIとAgent Coreの通信、SSE、API提供

Agent Orchestrator
  会話状態、記憶検索、LLM呼び出し、ツール呼び出しを制御

LLM Layer
  Ollama経由でGemmaを呼び出す

Memory Layer
  Profile / Semantic / Episodic / Task / Procedural memory を管理

Logger Layer
  全対話、ツール呼び出し、記憶参照、エラー、レイテンシを保存

Analytics Layer
  満足・不満・失敗・改善点を推定・分類する

Tool Layer
  filesystem, memory, web, browser, desktop操作などを提供

Avatar Layer
  表情、モーション、口パク、TTS連携を担当
```

## 8. CoALAに基づく設計整理

本システムは、言語エージェントを以下の構成として整理する。

```text
Working Memory
  現在の会話状態、直近のユーザー入力、現在のタスク

Long-Term Memory
  ユーザーに関する永続情報、過去会話、作業履歴、手順

Internal Actions
  retrieval, reasoning, reflection, summarization, memory write

External Actions
  filesystem, browser, desktop, avatar, TTS
```

本システムでは、Working Memoryを中心に、必要なタイミングでLong-Term Memoryを検索し、必要に応じてExternal Actionsを実行する。

## 9. ログと記憶の分離

本システムでは、Interaction Log と Long-term Memory を明確に分離する。

### 9.1 Interaction Log

Interaction Log は、ユーザーとAIのすべてのやり取りを保存する生ログである。

保存対象には以下を含む。

```text
研究相談
作業依頼
雑談
感想
愚痴
違和感
不満
好き嫌い
一時的な話題
アバターへの反応
再質問
訂正
やり直し要求
ツール呼び出し
記憶参照
応答レイテンシ
エラー
```

これは後から自然なAI利用の実態を観測するために保存する。

### 9.2 Long-term Memory

Long-term Memory は、Interaction Log から抽出・要約・構造化された、応答に利用するための記憶である。

すべてのログを記憶として扱うわけではない。

例えば、映画の感想を話した場合、会話全文はInteraction Logに保存する。一方で、ユーザーが特定の映画ジャンルを好む、ある作品を高く評価した、といった情報はLong-term Memoryに昇格する可能性がある。

### 9.3 原則

```text
ログ:
  原則すべて保存する

記憶:
  応答に使う価値があるものだけ抽出する

プロンプト:
  すべてのログではなく、関連記憶と必要な直近文脈だけ入れる
```

## 10. ローカル保存ポリシー

本システムはローカル完結を基本とする。

```text
LLM推論:
  Ollama

ログ保存:
  ローカルSQLite / JSONL

ベクトル検索:
  ローカルVector DB

記憶:
  ローカルファイル / SQLite / Vector Store

分析:
  ローカル実行

外部API:
  原則使用しない
```

外部APIを使用する場合は、明示的に設定し、ユーザーが把握できるようにする。

## 11. 保存しない、またはマスクするもの

原則としてインタラクションはすべて保存するが、以下は保存しない、または自動マスクする。

```text
パスワード
APIキー
認証トークン
秘密鍵
クレジットカード番号
2FAコード
セッションCookie
明示的に「保存しないで」と言われた内容
```

ただし、初期MVPでは完全な秘密情報検出は難しいため、最低限以下を実装する。

```text
ログ保存ON/OFF
Private Mode
セッション削除
特定ターン削除
手動マスク
エクスポート前確認
```

## 12. 長期記憶設計

長期記憶は単一方式にしない。

以下の複数の記憶タイプを分離する。

```text
Profile Memory
Semantic Memory
Episodic Memory
Task Memory
Procedural Memory
Archival Memory
```

## 12.1 Profile Memory

Profile Memory は、現在のユーザー状態を表す単一の最新情報である。

例：

```text
ユーザーの呼び名
話し方の好み
返信の長さの好み
研究テーマ
現在の所属
作業スタイル
禁止事項
現在重視しているプロジェクト
```

Profile は「現在の真実」を表す。

そのため、古い情報と矛盾する新しい情報が来た場合は、Profileを更新する。

保存形式はMarkdownまたはSQLiteの単一レコードとする。

```text
storage/memory/profile.md
```

## 12.2 Semantic Memory

Semantic Memory は、ユーザーや環境に関する安定した事実を保存する。

例：

```text
ユーザーはLLMの知識編集を研究している
ユーザーはOllamaでローカルLLMを使っている
ユーザーはTypeScript monorepoを使っている
ユーザーは研究相談にもAIを使いたい
```

Semantic Memory はatomic factsとして保存する。

## 12.3 Episodic Memory

Episodic Memory は、過去の会話や出来事の要約を保存する。

例：

```text
2026-06-16、ユーザーはavatar-desktop-agentの要件定義を相談した。
その中で、長期記憶よりも自然なインタラクションログ保存を重視したいと述べた。
```

Episodic Memory は履歴であり、古くなっても削除せず、必要に応じて低優先度化する。

## 12.4 Task Memory

Task Memory は、未完了タスク、締切、進行中プロジェクト、次にやることを管理する。

例：

```text
avatar-desktop-agentにInteraction Loggingを追加する
memory schemaを設計する
Gemma 3 27B対応を.env化する
```

Task Memory にはstatusを持たせる。

```text
todo
in_progress
done
blocked
cancelled
```

## 12.5 Procedural Memory

Procedural Memory は、うまくいった作業手順や、繰り返し使えるノウハウを保存する。

例：

```text
新しい機能を追加するときは、まずschema packageを更新し、次にbridge APIを追加し、最後にUIをつなぐ。
```

これはVoyagerのskill libraryやReflexionの反省メモリに近い。

## 12.6 Archival Memory

Archival Memory は、大量の過去情報を検索可能に保存する領域である。

全文ログ、長文要約、過去セッション、古いプロジェクト情報などを保持する。

毎ターン常に読むのではなく、必要時のみ検索する。

## 13. Memory Blocks と Archival Memory

Lettaの設計を参考に、記憶を以下の2層に分ける。

```text
Memory Blocks
  常にプロンプトへ入る短い情報

Archival Memory
  必要時に検索して使う長期保存情報
```

Memory Blocksに入れるもの：

```text
ユーザー名
現在の会話方針
口調
保存ポリシー
重要な禁止事項
現在の主要プロジェクト
```

Archival Memoryに入れるもの：

```text
過去会話
作業履歴
感想
研究相談
古いタスク
詳細なエピソード
```

## 14. 記憶の書き込み

記憶の書き込みは、以下の2系統に分ける。

```text
Hot Path Memory Write
  会話中に即時保存する

Background Memory Consolidation
  会話後に要約・統合・整理する
```

## 14.1 Hot Path Memory Write

会話中に即時保存するもの。

```text
ユーザーが「覚えて」と言った内容
明確なタスク
明確な締切
設定変更
保存ポリシー変更
重要な訂正
```

## 14.2 Background Memory Consolidation

会話後に処理するもの。

```text
セッション要約
雑談から見える好み
感想の整理
不満の抽出
作業ノウハウの抽出
重複記憶の統合
古いProfileの更新
```

MVPでは完全な非同期実行ではなく、セッション終了時または明示操作で実行してよい。

## 15. 記憶の読み出し

記憶検索は類似検索だけに依存しない。

以下の3軸を使う。

```text
relevance
recency
importance
```

基本スコア：

```text
memory_score = α * relevance + β * recency + γ * importance
```

用途に応じて重みを変える。

```text
現在の予定:
  recencyを重視

研究テーマ:
  relevanceとimportanceを重視

ユーザーの基本設定:
  importanceを重視

直近の雑談:
  recencyを重視

過去の失敗:
  relevanceとepisodic contextを重視
```

## 16. RAGとMemoryの分離

本システムでは、RAGとMemoryを明確に分ける。

```text
RAG:
  外部資料、論文、マニュアル、README、Webページを参照するための仕組み

Memory:
  ユーザーとエージェント自身の継続状態を扱う仕組み
```

例：

```text
論文PDFを読む:
  RAG

前にその論文について何を話したか:
  Memory

ユーザーがその論文をどう評価したか:
  Memory

論文本文の該当箇所:
  RAG
```

## 17. Interaction Logging

本システムの最重要機能の一つとして、全ターンのインタラクションログを保存する。

## 17.1 Session Log

セッション単位のログを保存する。

```sql
sessions (
  id TEXT PRIMARY KEY,
  title TEXT,
  started_at TEXT,
  ended_at TEXT,
  summary TEXT,
  model TEXT,
  app_version TEXT,
  created_at TEXT
)
```

## 17.2 Turn Log

ターン単位のログを保存する。

```sql
turn_logs (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  turn_index INTEGER,
  timestamp TEXT,
  user_input TEXT,
  assistant_output TEXT,
  raw_assistant_output TEXT,
  model TEXT,
  prompt_tokens INTEGER,
  completion_tokens INTEGER,
  latency_ms INTEGER,
  emotion TEXT,
  motion TEXT,
  status TEXT,
  error TEXT,
  created_at TEXT
)
```

## 17.3 Prompt Log

プロンプト構築内容を保存する。

```sql
prompt_logs (
  id TEXT PRIMARY KEY,
  turn_id TEXT,
  system_prompt TEXT,
  memory_context TEXT,
  recent_context TEXT,
  tool_context TEXT,
  final_prompt TEXT,
  created_at TEXT
)
```

MVPでは`final_prompt`を保存するかどうかは設定可能にする。

理由は、プロンプトには個人情報や長文コンテキストが含まれやすいためである。

## 17.4 Tool Call Log

ツール呼び出しを保存する。

```sql
tool_call_logs (
  id TEXT PRIMARY KEY,
  turn_id TEXT,
  tool_name TEXT,
  input_json TEXT,
  output_json TEXT,
  status TEXT,
  latency_ms INTEGER,
  error TEXT,
  created_at TEXT
)
```

## 17.5 Memory Access Log

どの記憶が参照・更新されたかを保存する。

```sql
memory_access_logs (
  id TEXT PRIMARY KEY,
  turn_id TEXT,
  memory_id TEXT,
  access_type TEXT,
  relevance_score REAL,
  recency_score REAL,
  importance_score REAL,
  final_score REAL,
  reason TEXT,
  created_at TEXT
)
```

`access_type` は以下とする。

```text
read
write
update
delete
supersede
```

## 17.6 Avatar Event Log

アバター表現もログに残す。

```sql
avatar_event_logs (
  id TEXT PRIMARY KEY,
  turn_id TEXT,
  emotion TEXT,
  motion TEXT,
  tts_enabled INTEGER,
  tts_text TEXT,
  started_at TEXT,
  ended_at TEXT,
  created_at TEXT
)
```

これは、ユーザーがアバターにどう反応したかを分析するために利用する。

## 18. Interaction Analytics

Interaction Analytics は、ユーザーが何に満足し、何に不満を持ったかを分析するためのモジュールである。

## 18.1 明示フィードバック

各応答に対して、ユーザーが任意で評価できるようにする。

UI例：

```text
👍 良い
👎 微妙
🔁 やり直し
📝 理由を書く
```

保存スキーマ：

```sql
explicit_feedback_logs (
  id TEXT PRIMARY KEY,
  turn_id TEXT,
  rating INTEGER,
  label TEXT,
  comment TEXT,
  created_at TEXT
)
```

rating：

```text
5: とても良い
4: 良い
3: 普通
2: 微妙
1: 不満
```

label例：

```text
helpful
wrong
too_shallow
too_verbose
ignored_context
memory_error
tool_error
slow
format_bad
avatar_bad
```

## 18.2 暗黙フィードバック

ユーザーが明示的に評価しなくても、会話から不満や満足を推定する。

検出対象：

```text
違う
そうじゃない
浅い
もっと具体的に
前にも言った
それは不要
何言ってるの
もういい
やり直して
いいね
助かる
それでOK
```

保存スキーマ：

```sql
inferred_feedback_logs (
  id TEXT PRIMARY KEY,
  turn_id TEXT,
  predicted_satisfaction REAL,
  issue_type TEXT,
  issue_detail TEXT,
  evidence TEXT,
  confidence REAL,
  created_at TEXT
)
```

issue_type例：

```text
shallow_answer
misunderstanding
wrong_memory
tool_failure
latency
hallucination
too_verbose
too_abstract
ignored_context
format_mismatch
avatar_mismatch
over_automation
under_automation
```

## 18.3 セッション終了時分析

セッション終了時に以下を生成する。

```json
{
  "session_summary": "...",
  "main_topics": ["..."],
  "user_goals": ["..."],
  "successful_points": ["..."],
  "frustration_points": ["..."],
  "important_preferences": ["..."],
  "memory_candidates": ["..."],
  "task_candidates": ["..."],
  "future_improvements": ["..."]
}
```

これは、ログ分析と記憶更新の両方に使う。

## 19. 全保存方針における雑談の扱い

本システムでは、雑談や感想を重要な対象として扱う。

理由は、自然なコンパニオンエージェントでは、ユーザーの価値観、興味、好み、不満、話し方の癖は、作業依頼よりも雑談に現れやすいためである。

したがって、以下も保存対象とする。

```text
映画や本の感想
日常の出来事
ちょっとした愚痴
研究に関係ない相談
アバターへの反応
冗談
一時的な興味
言い直し
会話の脱線
```

ただし、これらをすべてLong-term Memoryに昇格するわけではない。

例：

```text
ユーザー:
  昨日見た映画、ちょっと微妙だった

Interaction Log:
  会話全文を保存

Episodic Memory:
  必要なら「ユーザーは2026-06-xxに映画Xを微妙だと感じた」と要約

Semantic Memory:
  複数回の傾向が見えた場合のみ「ユーザーは説明過多な映画を好まない可能性がある」などを保存
```

## 20. Tool Use

MVPでは安全なツールに限定する。

## 20.1 Phase 1 Tools

```text
memory.search
memory.write
filesystem.list
filesystem.read
```

## 20.2 Phase 2 Tools

```text
web.search
browser.open
browser.read
```

## 20.3 Phase 3 Tools

```text
desktop.screenshot
desktop.click
desktop.type
desktop.scroll
```

## 20.4 安全要件

```text
ファイル削除は禁止
sudoは禁止
rmは禁止
eval / execは禁止
認証情報へのアクセスは禁止
パスワード欄への入力は禁止
外部送信はユーザー確認必須
デスクトップ操作は原則確認付き
危険操作はdeny-listでブロック
```

Computer Use系の機能は、MVP後に導入する。

OpenHands / Open Interpreter / Browser Use は強力だが、初期段階で入れると安全性と複雑性の負債が大きいため、まずはログ・記憶・テキスト対話を安定させる。

## 21. Structured Output / Tool Calling

Gemma 3 27B + Ollamaでは、構造化出力とtool callingを利用できる前提で設計する。

ただし、ローカルopen-weightモデルではJSON崩れやtool use失敗が起こりうるため、以下を必須とする。

```text
JSON Schemaによる制約
出力バリデーション
repair step
再試行
失敗時のtext fallback
tool callログ
malformed JSONログ
```

LLM出力形式例：

```json
{
  "text": "いいですね。まずはログと記憶を分けて設計するのがよさそうです。",
  "emotion": "happy",
  "motion": "nod",
  "tool_calls": [],
  "memory_write_candidates": [],
  "analytics": {
    "predicted_satisfaction": 0.8,
    "issue_type": null
  }
}
```

## 22. アバター / TTS

アバターとTTSは、初期MVPでは必須ではないが、既存実装を維持する。

## 22.1 Avatar

既存の表情・モーション制御を継続利用する。

emotion例：

```text
neutral
happy
sad
surprised
confused
thinking
```

motion例：

```text
nod
wave
shake
bow_small
idle
none
```

## 22.2 TTS

TTSは任意機能とする。

候補：

```text
VOICEVOX
AivisSpeech
Style-Bert-VITS2
sherpa-onnx
Web Speech API
```

要件：

```text
ON/OFF可能
長文は文単位で分割
読み上げ中に口パク同期
テキストのみでも利用可能
```

## 23. Dashboard

ログと分析結果を後から確認できるダッシュボードを提供する。

MVPでは簡易UIでよい。

表示項目：

```text
セッション一覧
ターン一覧
全文ログ
明示フィードバック
暗黙フィードバック
issue_type集計
レイテンシ
tool call成功率
memory retrieval履歴
memory write履歴
よく話したトピック
よく出た不満
アバター反応ログ
```

将来的には以下も可視化する。

```text
日別利用回数
平均満足度
不満ランキング
記憶使用時/未使用時の満足度差
ツール別成功率
タスク種別ごとの不満
会話トピックの推移
```

## 24. Export / Analysis

ローカルに保存したログは、後から分析できる形式でエクスポート可能にする。

形式：

```text
JSONL
CSV
SQLite dump
Markdown summary
```

分析用途：

```text
自分がAIに何を相談しているか
どのような回答に不満を持つか
どのタスクでAIが役に立つか
どのタスクでAIが失敗するか
記憶が役に立ったか
アバターが会話体験に影響したか
```

## 25. データ保存先

推奨保存構成：

```text
avatar-desktop-agent/
├── storage/
│   ├── app.sqlite
│   ├── memory/
│   │   ├── profile.md
│   │   ├── persona.md
│   │   ├── semantic/
│   │   ├── episodic/
│   │   ├── task/
│   │   └── vector/
│   ├── logs/
│   │   ├── sessions/
│   │   └── jsonl/
│   ├── exports/
│   └── private/
```

## 26. Vector Store

MVPでは以下のいずれかを採用する。

```text
Chroma
  実装が簡単

Qdrant local mode
  研究用途・拡張性が高い

FAISS
  軽量だがDB機能は弱い
```

推奨は以下。

```text
MVP:
  Chroma

研究・拡張版:
  Qdrant local mode
```

埋め込みモデルはローカルで動作するものを優先する。

候補：

```text
EmbeddingGemma
nomic-embed-text
mxbai-embed-large
```

## 27. 推奨ディレクトリ構成

```text
avatar-desktop-agent/
├── apps/
│   ├── ui/
│   └── bridge/
├── packages/
│   ├── schema/
│   ├── llm/
│   ├── memory/
│   ├── tools/
│   ├── logger/
│   ├── analytics/
│   ├── avatar/
│   ├── tts/
│   └── utils/
├── storage/
│   ├── app.sqlite
│   ├── memory/
│   │   ├── profile.md
│   │   ├── persona.md
│   │   └── vector/
│   ├── logs/
│   └── exports/
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── memory-design.md
│   ├── interaction-logging.md
│   ├── interaction-analytics.md
│   └── research.md
└── README.md
```

## 28. 実装フェーズ

## Phase 8: モデル設定の再整理

目的：

```text
gemma3:27bを標準モデルとして扱えるようにする
```

作業：

```text
.envでモデル名を管理
qwen3.5:2b固定を解除
gemma3:27bをREADMEに明記
gemma3:12bも軽量モードとして用意
timeout調整
streaming維持
```

完了条件：

```text
OLLAMA_MODEL=gemma3:27b で起動できる
OLLAMA_MODEL=gemma3:12b に切り替えられる
既存UIで応答が表示される
```

## Phase 9: Interaction Logging v1

目的：

```text
全対話を保存する
```

作業：

```text
SQLite schema作成
sessions作成
turn_logs作成
JSONLログとの互換維持
user_input保存
assistant_output保存
latency保存
model保存
error保存
```

完了条件：

```text
すべてのターンがローカルDBに保存される
雑談も感想も保存される
セッション単位で後から読める
```

## Phase 10: Prompt / Tool / Memory Access Logging

目的：

```text
エージェントが何を見て、何を使って応答したかを追跡する
```

作業：

```text
prompt_logs作成
tool_call_logs作成
memory_access_logs作成
avatar_event_logs作成
```

完了条件：

```text
どの記憶が使われたか追える
どのツールが呼ばれたか追える
プロンプト構築過程を追える
```

## Phase 11: Explicit Feedback

目的：

```text
ユーザーが明示的に満足・不満を記録できるようにする
```

作業：

```text
👍 / 👎 ボタン
rating入力
comment入力
issue label選択
explicit_feedback_logs保存
```

完了条件：

```text
各応答に評価を付けられる
評価がログと紐づく
```

## Phase 12: Long-term Memory v1

目的：

```text
Profile / Semantic / Episodic / Task memoryを導入する
```

作業：

```text
profile.md整備
memoryテーブル作成
semantic facts保存
episodic summary保存
task memory保存
vector store導入
```

完了条件：

```text
過去情報を検索できる
Profileが更新できる
タスクが保持される
再起動後も記憶が残る
```

## Phase 13: Memory Retrieval

目的：

```text
応答前に関連記憶を検索する
```

作業：

```text
入力から検索クエリ生成
vector search
relevance / recency / importance scoring
prompt injection
memory access log保存
```

完了条件：

```text
過去の会話や設定を応答に反映できる
関係ない記憶を大量に入れない
```

## Phase 14: Memory Write / Consolidation

目的：

```text
ログから有用な記憶を抽出・統合する
```

作業：

```text
hot path memory write
session summary
background consolidation
duplicate merge
superseded管理
memory write log
```

完了条件：

```text
明示的に覚えてと言ったことが保存される
雑談から好みを抽出できる
古い情報と新しい情報を区別できる
```

## Phase 15: Interaction Analytics v1

目的：

```text
ユーザーの満足・不満・失敗パターンを推定する
```

作業：

```text
inferred_feedback_logs作成
issue_type分類
predicted_satisfaction推定
evidence保存
confidence保存
```

完了条件：

```text
各ターンに対して不満可能性を推定できる
再質問や訂正を検出できる
```

## Phase 16: Dashboard v1

目的：

```text
保存されたログを後から閲覧・分析できるようにする
```

作業：

```text
セッション一覧
ターン詳細
検索
フィードバック表示
issue_type集計
レイテンシ表示
memory access表示
```

完了条件：

```text
過去会話を検索できる
不満ログを一覧できる
どの記憶が使われたか見える
```

## Phase 17: Tool Use v1

目的：

```text
安全なツール利用を導入する
```

作業：

```text
filesystem.list
filesystem.read
memory.search
memory.write
tool schema
tool call validation
```

完了条件：

```text
ファイル一覧取得ができる
READMEなどを読める
ツール呼び出しがログに残る
```

## Phase 18: Web / Browser Tool

目的：

```text
必要時にWebやブラウザを利用できるようにする
```

作業：

```text
web.search
browser.open
browser.read
source保存
調査ログ保存
```

完了条件：

```text
Web検索結果を要約できる
参照元を保存できる
```

## Phase 19: Avatar / TTS強化

目的：

```text
デスクトップコンパニオンらしい表現を強化する
```

作業：

```text
TTS導入
口パク同期
表情精度向上
アバターイベントログ
```

完了条件：

```text
テキスト応答に合わせて自然に反応する
必要なら音声読み上げできる
```

## 29. MVP定義

最小完成形は以下とする。

```text
ElectronテキストUI
Fastify bridge
Ollama + gemma3:27b
SSE応答
全対話ログ保存
SQLite保存
明示フィードバック
Profile memory
Episodic summary
Semantic memory
Memory retrieval
Interaction analytics v1
簡易ダッシュボード
```

MVPでは以下は必須ではない。

```text
音声入力
TTS
Live2D強化
Web検索
完全なdesktop操作
OpenHands / Open Interpreter統合
```

ただし、既存のアバター表示機能は維持する。

## 30. 成功基準

## 30.1 エージェントとしての成功

```text
ローカルLLMで会話できる
過去の内容を必要に応じて思い出せる
ユーザーの好みや文脈を反映できる
応答がストリーミング表示される
アバター表現が壊れない
```

## 30.2 ログ基盤としての成功

```text
すべての対話が保存される
雑談も保存される
感想も保存される
不満も保存される
ツール利用も保存される
記憶参照も保存される
後から検索できる
```

## 30.3 分析基盤としての成功

```text
ユーザーが何に不満を持ったか追える
どのタスクで失敗しやすいか分かる
記憶が役に立ったか検証できる
応答遅延と満足度の関係を見られる
アバター表現への反応を見られる
```

## 31. 研究化ポイント

本システムは、以下の研究テーマに発展できる。

```text
自然なHuman-AI interactionの長期ログ分析
ローカルLLMエージェントにおける長期記憶の有効性
雑談からのユーザー嗜好抽出
明示フィードバックと暗黙フィードバックの差
記憶利用が満足度に与える影響
記憶の誤用が不満に与える影響
デスクトップコンパニオンにおけるアバター表現の効果
エージェントの失敗分類
ユーザー依存パーソナライズ
長期使用における記憶更新・忘却・矛盾解決
```

特に本システムの独自性は、ベンチマーク用に整形された会話ではなく、実際の生活・研究・作業・雑談の中で発生する自然なAI利用ログをローカルに蓄積できる点にある。

## 32. 設計上の注意点

## 32.1 全部保存するが、全部思い出さない

ログはすべて保存する。

しかし、すべてを応答に使うとノイズが大きくなる。

そのため、応答に使う情報は以下に限定する。

```text
Profile
関連Semantic Memory
関連Episodic Memory
現在のTask Memory
直近会話
```

## 32.2 記憶は更新可能でなければならない

ユーザーの状況や好みは変化する。

そのため、古い情報を単に削除するのではなく、以下のように扱う。

```text
Profile:
  最新状態に更新する

Episodic:
  履歴として残す

Semantic:
  supersededとして無効化可能にする

Task:
  done / cancelled / blocked に状態変更する
```

## 32.3 JSON出力は壊れる前提にする

ローカルLLMでは構造化出力が常に安定するとは限らない。

必ず以下を実装する。

```text
schema validation
retry
repair
fallback
error logging
```

## 32.4 Computer Useは後回しにする

OpenHands / Open Interpreter / Browser Use は強力だが、初期導入すると複雑性が大きい。

まずは以下を優先する。

```text
ログ
記憶
分析
テキスト対話
```

その後にWeb / Browser / Desktop操作を追加する。

## 33. 最重要実装順

最終的な優先順位は以下である。

```text
1. gemma3:27b対応
2. 全対話ログ保存
3. 明示フィードバック
4. 長期記憶の基本設計
5. Memory Retrieval
6. Memory Write / Consolidation
7. Interaction Analytics
8. Dashboard
9. 安全なTool Use
10. Web / Browser
11. TTS / Avatar強化
12. Desktop操作
```

## 34. 最終コンセプト

本システムは、単なるAIチャットでも、単なるAI VTuberでも、単なるデスクトップ自動操作ツールでもない。

最終的なコンセプトは以下である。

```text
ローカルLLMで動作し、
ユーザーとの自然なインタラクションをすべて保存し、
必要な情報だけを長期記憶として昇格し、
エージェント利用中の満足・不満・失敗を後から分析できる、
テキスト入力型デスクトップコンパニオンエージェント
```

この方針では、雑談や感想も重要なデータである。

なぜなら、ユーザーがAIをどう使いたいのか、どんな応答に安心するのか、どんなズレに不満を持つのかは、研究相談や作業依頼だけでなく、日常的で自然な会話の中に現れるからである。

ポイントは、**「全部保存する」けど「全部を記憶として使わない」**に整理したところです。これなら自然なインタラクション観測と、実用的な長期記憶が両立します。

---

## 発言 27 — 👤 石垣（ユーザー）

gemma 4か
すまん

先行研究でGitHubがあればクローンして使おう

https://qiita.com/usayamadausako/items/c8b5cca97554f6f64782
あとこの記事の話も組み込みたい

---

## 発言 28 — 🤖 ChatGPT

Gemma 4前提に直して、さらに「先行研究・OSSはGitHubがあればcloneして比較・流用する」という実装方針を要件に足します。Qiita記事も確認して、既存要件にどう組み込むべきか整理します。

---

## 発言 29 — 🤖 ChatGPT

はい、これはかなり組み込む価値があります。

要件定義上は、**Interaction Log / Long-term Memory とは別に「LLM Wiki」層を追加**するのがよいです。

位置づけはこうです。

```text
Interaction Log
  すべての生ログ

Long-term Memory
  応答時に使う抽出記憶

LLM Wiki
  人間もAIも読む、整理済みのMarkdown知識ベース
```

Qiita記事の要点は、Obsidian VaultをAI用wikiとして使い、プロジェクト固有の知識をMarkdownで保存すること。ただしKarpathy方式のように完全自動でノートを自己増殖させると、重複・古い情報・誤情報が増え、コンテキスト腐敗が起きやすいため、**書くタイミングと整理判断は人間が握る**という運用です。

最終要件定義に追加するなら、この節を入れるのがよいです。

## 追加要件: LLM Wiki / Obsidian Vault

### 1. 目的

本システムでは、全対話ログや自動抽出メモリとは別に、人間とAIの両方が読めるMarkdown形式の知識ベースとして `ai_wiki/` を持つ。

`ai_wiki/` は、セッションをまたいで作業を継続するための引き継ぎメモ、プロジェクト仕様、設計判断、調査結果、実装ノウハウを保存する場所である。

これは、LLMにすべてを自動記憶させるためではなく、ユーザーが確認・編集・整理できる形で、プロジェクト知識を蓄積するために使う。

### 2. 位置づけ

本システムの永続情報は、以下の4層に分ける。

```text
Interaction Log
  全会話・全イベントの生ログ

Long-term Memory
  応答時に使うために抽出・要約された記憶

LLM Wiki
  人間が読めるMarkdown知識ベース

Vector Store
  Log / Memory / Wiki を検索するための索引
```

`Interaction Log` は原則すべて保存する。

`Long-term Memory` は、応答に使いやすいように抽出された構造化記憶である。

`LLM Wiki` は、人間が読むことを前提に整理されたストック型知識である。

### 3. 基本方針

`ai_wiki/` は完全自動生成しない。

LLMが勝手にノートを自己増殖させると、以下の問題が起きる。

```text
古い情報が残る
重複が増える
誤った情報が混ざる
どこに何があるか分からなくなる
コンテキストが腐敗する
人間が読まなくなる
```

そのため、`ai_wiki/` への恒久保存は、原則としてユーザーの明示トリガーで行う。

例：

```text
ここまでの調査結果を ai_wiki に記録して

この設計を ai_wiki に残して

セッション切り替え用に ai_wiki に引き継ぎメモを書いて

この機能が固まったので investigations を整理して
```

### 4. 推奨ディレクトリ構成

```text
ai_wiki/
├── 00-Index.md
├── projects/
│   └── avatar-desktop-agent.md
├── architecture/
│   ├── overview.md
│   ├── memory.md
│   ├── logging.md
│   └── analytics.md
├── investigations/
│   ├── 2026-06-16-memory-design.md
│   ├── 2026-06-16-gemma4-ollama.md
│   └── archive/
├── decisions/
│   ├── 2026-06-16-use-local-first.md
│   └── 2026-06-16-log-everything.md
├── references/
│   ├── oss-comparison.md
│   ├── papers.md
│   └── qiita-llm-wiki.md
├── procedures/
│   ├── setup.md
│   ├── release-checklist.md
│   └── memory-maintenance.md
└── handoff/
    └── latest.md
```

### 5. 情報の寿命

`ai_wiki/` では、情報を寿命で分ける。

```text
investigations/
  作業中・調査中・仮説・一時的メモ

decisions/
  採用した設計判断

architecture/
  現在の正式な設計

procedures/
  繰り返し使う手順

references/
  外部資料・先行研究・OSS比較

handoff/
  セッション切り替え用の最新引き継ぎ
```

### 6. 整理ルール

作業中の情報は `investigations/` に置く。

仕様が固まったら、重要な情報だけを `architecture/`、`decisions/`、`procedures/` に昇格する。

不要になった調査メモは削除せず、まず `investigations/archive/` に移動する。

これにより、消しすぎを防ぎつつ、Indexや通常検索のノイズを減らす。

### 7. Index

`00-Index.md` は、AIと人間の入口として必ず維持する。

最低限、以下を含める。

```text
現在の主要プロジェクト
読むべき設計ドキュメント
現在の未完了タスク
最近の重要な決定
セッション再開時に読むファイル
archive扱いのファイルへの注意
```

### 8. Git管理

`ai_wiki/` は原則としてGit追跡対象外にする。

理由は、個人的な対話ログ、未整理の考え、研究アイデア、プライベートなメモが含まれるためである。

設定例：

```gitignore
ai_wiki/
storage/
```

または、リポジトリに影響させたくない場合は `.git/info/exclude` や global gitignore に追加する。

### 9. エージェントからの利用

エージェントは、必要に応じて `ai_wiki/00-Index.md` を読み、関連ファイルを辿る。

ただし、毎ターンすべてのWikiを読むことは禁止する。

読み出し方は以下とする。

```text
1. 00-Index.md を読む
2. 現在タスクに関係するファイルだけ読む
3. 必要なら Vector Store で検索する
4. 読んだファイルを memory_access_logs または wiki_access_logs に記録する
```

### 10. Wiki書き込みトリガー

Wikiへの書き込みは、以下の場合に行う。

```text
ユーザーが明示的に依頼したとき
セッション切り替え用メモを作るとき
調査結果を恒久保存したいとき
設計判断が固まったとき
機能実装が一区切りついたとき
```

自動で毎ターン書くことは禁止する。

### 11. Wiki整理トリガー

以下のような依頼で整理を行う。

```text
〇〇機能はほぼ終わったので、ai_wiki/investigations を整理して

残すべき情報だけ decisions と architecture に昇格して

不要な作業メモは archive に移動して

リンク切れを直して

00-Index.md を更新して
```

### 12. ログ・メモリ・Wikiの使い分け

例：

```text
ユーザー:
  このQiita記事の運用を要件に入れたい

Interaction Log:
  会話全文を保存する

Long-term Memory:
  ユーザーはLLM Wiki方式に関心があり、自己増殖ではなく手動トリガー型を好む、と保存する

LLM Wiki:
  references/qiita-llm-wiki.md に記事要約を保存する
  decisions/use-ai-wiki-manual-trigger.md に採用判断を保存する
  architecture/memory.md に Log / Memory / Wiki の分離設計を反映する
```

### 13. 先行研究・OSS GitHub clone 方針

先行研究やOSSにGitHubリポジトリがある場合は、可能な範囲でcloneして調査・比較・流用する。

対象候補：

```text
Letta / MemGPT
LangGraph / LangMem
Open-LLM-VTuber
OpenHands
Open Interpreter
Browser Use
AutoGen
CrewAI
Zep / Graphiti
```

cloneしたリポジトリは、直接本体に混ぜない。

以下のように管理する。

```text
external/
├── letta/
├── langgraph/
├── open-llm-vtuber/
├── browser-use/
└── openhands/
```

または、巨大リポジトリはcloneせず、調査メモだけ `ai_wiki/references/oss-comparison.md` に記録する。

流用時は以下を確認する。

```text
ライセンス
依存関係
ローカルLLM対応
Ollama対応
メモリ設計
Tool calling設計
UI/Avatar層の分離
セキュリティ設計
```

### 14. 要件への反映

最終的な永続化設計は以下とする。

```text
storage/
  生ログ、DB、ベクトル、アプリ内部データ

ai_wiki/
  人間が読む整理済みMarkdown知識

external/
  参考実装としてcloneしたOSS

docs/
  リポジトリに含める公式仕様書
```

`storage/` と `ai_wiki/` は基本的にGit管理しない。

`docs/` はGit管理する。

`external/` は必要に応じてGit管理外にする。

Gemmaについては、要件定義全体の表現をこう置き換えるのがよさそうです。

```text
標準モデル:
  Gemma 4 31B 相当をOllamaで利用する

フォールバック:
  gemma3:27b
  gemma3:12b

注意:
  Gemma 3系は27Bが最大なので、31Bを使う場合はGemma 4系として扱う。
```

これで、設計の軸はかなり綺麗になります。

```text
Interaction Log  = 全部保存
Long-term Memory = 応答に使う抽出記憶
LLM Wiki         = 人間が整理・編集するMarkdown知識
External OSS     = GitHub cloneして比較・流用
```

特にQiita記事の思想は、あなたの「全部保存したい」と矛盾しません。

違いはここです。

```text
全部保存する:
  生ログとして保存する

全部Wiki化する:
  しない
```

つまり、**ログは全保存、Wikiは手動昇格**です。これが一番腐敗しにくいです。

---

## 会話中に参照された出典 URL 一覧

ChatGPT が Web 検索・ナビゲーションで参照したソース（計 37 件）。`utm_source` は除去済み。

### 本人リポジトリ / 取り込み記事
- [GitHub - ishigaki0302/avatar-desktop-agent: ローカルLLM（Ollama）とOpenClawを連携し、2Dスプライトで表情・口パク付きのデスクトップエージェントを動かす。 · GitHub](https://github.com/ishigaki0302/avatar-desktop-agent) — GitHub
- [GitHub - ishigaki0302/avatar-desktop-agent: ローカルLLM（Ollama）とOpenClawを連携し、2Dスプライトで表情・口パク付きのデスクトップエージェントを動かす。 · GitHub](https://github.com/ishigaki0302/avatar-desktop-agent.git) — GitHub
- [Claude Code x Obsidianで、LLM Wiki構築 | セッションを切り替えても会話を続けられる方法 #ClaudeCode - Qiita](https://qiita.com/usayamadausako/items/c8b5cca97554f6f64782) — Qiita
- https://github.com/openclaw/openclaw

### Web 検索で参照されたソース
- [https://github.com/Mirix-AI/MIRIX/tree/desktop-agent](https://github.com/Mirix-AI/MIRIX/tree/desktop-agent) — github.com
- [lahfir/agent-desktop: Native desktop automation CLI for AI ...](https://github.com/lahfir/agent-desktop) — github.com
- [digitaldemocracy2030/idobata-sns-agent](https://github.com/digitaldemocracy2030/idobata-sns-agent) — github.com
- [PC Agent: While You Sleep, AI Works - A Cognitive ...](https://github.com/GAIR-NLP/PC-Agent) — github.com
- [mks0601/ExAvatar_RELEASE: Official PyTorch ...](https://github.com/mks0601/ExAvatar_RELEASE) — github.com
- [heshengtao/super-agent-party: ⭐ All-in-one AI companion! ...](https://github.com/heshengtao/super-agent-party) — github.com
- [agents/examples/avatar_agents/liveavatar/agent_worker. ...](https://github.com/livekit/agents/blob/main/examples/avatar_agents/liveavatar/agent_worker.py) — github.com
- [agentscope-ai/QwenPaw: Your Personal AI Assistant ...](https://github.com/agentscope-ai/QwenPaw) — github.com
- [(NeurIPS 2024) AvaTaR: Optimizing LLM Agents for Tool ...](https://github.com/zou-group/avatar) — github.com
- [agentsea/agentdesk: A desktop for AI agents](https://github.com/agentsea/agentdesk) — github.com
- [A High-Fidelity Open Embodied Avatar with Lip Syncing and Expression Capabilities](https://arxiv.org/abs/1909.08766) — arxiv.org
- [AvaTaR: Optimizing LLM Agents for Tool Usage via Contrastive Reasoning](https://arxiv.org/abs/2406.11200) — arxiv.org
- [AvatarCap: Animatable Avatar Conditioned Monocular Human Volumetric Capture](https://arxiv.org/abs/2207.02031) — arxiv.org
- [GitAgent: Facilitating Autonomous Agent with GitHub by Tool Extension](https://arxiv.org/abs/2312.17294) — arxiv.org
- [So... you wanna get started creating your own Neuro?](https://www.reddit.com/r/NeuroSama/comments/1jtte9s/so_you_wanna_get_started_creating_your_own_neuro/) — reddit.com
- [5 AI Agents Currently Attracting Attention [2025 Latest ...](https://note.com/arai0903/n/n51711d03c1f3?hl=en) — note.com
- [Access the Architectures Behind Leading Voice Models](https://www.hume.ai/model-architecture) — hume.ai
- [VTuber's Atelier: The Design Space, Challenges, and ...](https://www.researchgate.net/publication/391240459_VTuber%27s_Atelier_The_Design_Space_Challenges_and_Opportunities_for_VTubing) — researchgate.net
- [Best local AI agents 2026 - BitDeep](https://bitdeep.net/p/autonomous-ai-agents/local-ai-agents) — bitdeep.net
- [Research Topics - Lee Lab., NITech](https://www.slp.nitech.ac.jp/en/research/) — nitech.ac.jp
- [Top 10 AI Computer Use Agents 2025: Full Review & Guide](https://o-mega.ai/articles/top-10-computer-use-agents-ai-navigating-your-devices-full-review-2025) — o-mega.ai
- [Building a Fully Local LLM Voice Assistant](https://towardsai.net/p/machine-learning/building-a-fully-local-llm-voice-assistant-a-practical-architecture-guide) — towardsai.net
- [4 Types of LLM Agents you need to know in 2025](https://pub.towardsai.net/4-types-of-llm-agents-you-need-to-know-in-2025-58411dcd84f5) — towardsai.net
- [VTuber's Atelier: The Design Space, Challenges, and ...](https://dl.acm.org/doi/full/10.1145/3706598.3714107) — acm.org
- [Programming with LLM Agents in 2025](https://www.youtube.com/watch?v=WKF__cJTxvg) — youtube.com
- [Backend Architecture Overview - Open LLM Vtuber](https://open-llm-vtuber.github.io/en/docs/user-guide/backend/structure/) — open-llm-vtuber.github.io
- [AI Agents Explained: Everything You Need to Know in 2025](https://www.apideck.com/blog/ai-agents-explained-everything-you-need-to-know-in-2025) — apideck.com
- [Takeaways from Applying LLM Capabilities to Multiple ...](https://arxiv.org/pdf/2501.00168) — arxiv.org
- [Coming into focus: the State of the AI Agent Ecosystem in ...](https://natesnewsletter.substack.com/p/coming-into-focus-the-state-of-the) — substack.com
- [AutoGPT and Beyond: 6 Agents to Try in 2025 | by Modexa](https://medium.com/%40Modexa/autogpt-and-beyond-6-agents-to-try-in-2025-0c8c979ff89f) — medium.com
- [ARUNAGIRINATHAN-K/awesome-ai-agents-2026](https://github.com/ARUNAGIRINATHAN-K/awesome-ai-agents-2026) — GitHub
- [Neuro-sama](https://en.wikipedia.org/wiki/Neuro-sama) — ウィキペディア
- [Takeaways from Applying LLM Capabilities to Multiple Conversational Avatars in a VR Pilot Study](https://arxiv.org/abs/2501.00168) — arXiv
- [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) — GitHub

### その他に本文・データ中に出現した URL
- http://localhost:11434 （会話中のOllamaローカルエンドポイントURL）
