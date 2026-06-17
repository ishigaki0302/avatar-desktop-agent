# ローカルエージェントに「Claude Code のように探させる」ための参考文献

> 目的: avatar-desktop-agent のローカル LLM(gemma4:31b)エージェントが、Claude Code の
> ように「諦めずに・賢く探す」ようにするための論文/記事の調査メモ。
> 調査日: 2026-06-17 / 調査者: Claude Code（Web 検索）

---

## 背景（なぜ調べたか）

会話からの agentic tool-calling（#69, `brain.ts` の `runAgentLoop`）を入れたが、ファイル検索で
**同じ検索を3回繰り返して諦める**挙動が観測された（`tool_call_logs` で確認）:

```
filesystem.search {"pattern":"*自己紹介*.pptx"} → []   ×3（同一・広げない）
```

原因は、ループが **(1) 会話履歴を計画ステップに渡していない / (2) 「どの引数で何を試したか」を
フィードバックしていない** こと。下記の知見でこれを設計し直す。

---

## ① エージェントの基本ループ（土台）

- **ReAct: Synergizing Reasoning and Acting in Language Models** — Yao et al., ICLR 2023。
  「思考(Thought)→行動(Act)→観察(Observation)」を反復する agentic ループの原典。`runAgentLoop` の基礎。
  - 論文: https://arxiv.org/abs/2210.03629 （PDF: https://arxiv.org/pdf/2210.03629 ）
  - 解説: https://research.google/blog/react-synergizing-reasoning-and-acting-in-language-models/

## ② 失敗から学んで再試行する（今の詰まりの直接の解）

- **Reflexion: Language Agents with Verbal Reinforcement Learning** — Shinn et al., NeurIPS 2023。
  失敗を**言語で振り返り（self-reflection）、その要約を次試行のコンテキストに足す**ことで改善。
  HumanEval pass@1 91%（GPT-4 80% を上回る）。「同じ検索を繰り返さず引数を変える」の理論的裏付け。
  - 論文: https://arxiv.org/abs/2303.11366
  - OpenReview: https://openreview.net/forum?id=vAElhFcKW6

## ③ Claude Code の実際の「探し方」（本命）

- **Claude Code Doesn't Index Your Codebase. Here's What It Does Instead.** — Vadim's blog。
  インデックス/ベクタを作らず、**毎回ライブで grep して絞り込む** agentic loop の解説。
  - https://vadim.blog/claude-code-no-indexing/
- **Why Claude Code Chose ripgrep Over Vector Search** — rust-trends。状態を持たず即動ける利点。
  - https://rust-trends.com/posts/ripgrep-claude-code/
- **The Secret Behind Claude Code's Retrieval: Why Live Search Fits Better than RAG** — Towards AI（Florian June, 2026-05）。
  - https://pub.towardsai.net/the-secret-behind-claude-codes-retrieval-why-live-search-fits-better-than-rag-530b2a8c67cd
- **Why Coding Agents Still Use grep as Their Search Backbone** — yage.ai。
  - https://yage.ai/share/why-coding-agents-still-use-grep-en-20260327.html
- **Agentic Search Over Vector Embeddings（パターン集）** — agentic-patterns.com。
  - https://www.agentic-patterns.com/patterns/agentic-search-over-vector-embeddings/

## ④ エージェント専用の道具立て（ツール設計）

- **SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering** — Yang et al., NeurIPS 2024。
  LLM 向けに**閲覧/検索/編集を簡潔なアクション + ガードレール + 毎ターンの明確なフィードバック**で設計（ACI）。
  GPT-4 Turbo で SWE-bench 12.47% 解決（当時 SOTA 3.8% を大幅更新）。我々の tools 層設計の指針。
  - 論文: https://arxiv.org/abs/2405.15793
  - mini-swe-agent（100行・SWE-bench verified 74%超）: https://github.com/SWE-agent/mini-swe-agent

## ⑤ ローカル/小型モデルでのツール使用

- **The biggest local LLM on your machine is useless if it can't call a single tool** — XDA Developers。
  小型ローカルモデルの tool-calling 信頼性の実情（Mistral 7B は native function-calling、Llama 3.2 3B は
  複雑な ReAct でツールを一度も呼べないことがある）。gemma4 でツール選択が不安定な時の参考。
  - https://www.xda-developers.com/biggest-local-llm-machine-useless-cant-call-single-tool-how-many-parameters/
- **Build ReAct Agents using SLMs from Scratch** — Akshay Ballal。小型モデル向け ReAct 実装。
  - https://www.akshaymakes.com/blogs/build-react-agents-slms-scratch
- **What is a ReAct Agent?** — IBM。ReAct は function-calling 非対応の LLM でも動く利点。
  - https://www.ibm.com/think/topics/react-agent
- **LangChain Tool-Calling Agent vs ReAct Agent**（アーキ比較, 2025） — Medium / Dzianis Vashchuk。
  - https://medium.com/@dzianisv/vibe-engineering-langchains-tool-calling-agent-vs-react-agent-and-modern-llm-agent-architectures-bdd480347692

---

## 我々のプロジェクトへの示唆（設計方針）

1. **方向性は正しい**: `filesystem.search` はインデックス無しのライブ検索＝Claude Code 流（③）。RAG/ベクタは不要。
2. **詰まりの解は Reflexion（②）**: 計画ステップに以下を毎回渡す:
   - **会話履歴**（follow-up の文脈: 「いつ見つかる？」「もっと探して」を理解する）
   - **これまでに試したツールと引数と結果**（`filesystem.search {"pattern":"*自己紹介*.pptx"} → 0件` の形）
   - 「同じ tool+args を繰り返すな・空なら広げろ/別手段」の明示指示
3. **道具は単純・明確に + 毎回フィードバック（④ SWE-agent ACI）**: 結果件数や失敗理由を簡潔に返す。
4. **小型モデル前提（⑤）**: gemma4 のツール選択は不安定になりうる前提で、プロンプト例示・ガードレール・
   リトライ上限を持つ（既に MAX_AGENT_STEPS あり）。

### 直近の実装タスク（このリサーチに基づく）
- `runAgentLoop`: 各ステップで **会話履歴 + 試行履歴(引数つき)** を計画呼び出しに渡す
- `executeTools`: 結果ブロックに**呼び出し引数**を含める（`## filesystem.search {"pattern":...}\n<結果>`)
- `AGENT_STEP_PROMPT`: 「同一検索を繰り返さない／空なら引数を変える・広げる」を明示
- （任意）検索0件時に拡張子だけへ自動フォールバック、候補一覧の提示
