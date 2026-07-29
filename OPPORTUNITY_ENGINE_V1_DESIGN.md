# Opportunity Engine V1 Design

Version: V1

Status: Design

Priority: P0 (Highest)

Author: User + ChatGPT

---

# 1. Purpose

即使 Bot 沒有開任何一筆交易，

也必須持續學習市場。

Opportunity Engine 不負責下單。

Opportunity Engine 只負責：

- 紀錄
- 觀察
- 建立 Shadow Trade
- 驗證 Shadow 結果
- 累積 AI Memory
- 提供 AI Advisor 建議

任何策略修改，

仍需 Human Approval。

---

# 2. Core Principles

Trading Engine

```
↓
```

Opportunity Engine

```
↓
```

Knowledge

```
↓
```

Suggestion

```
↓
```

Human Approval

```
↓
```

Strategy Update

Bot 永遠不得自動修改：

- AI Score Threshold
- Weight
- Leverage
- Risk
- Stop Loss
- Take Profit

---

# 3. Development Roadmap

Commit 1

Opportunity Framework

Commit 2

Opportunity Logger

Commit 3

Shadow Trading

Commit 4

Shadow Validator

Commit 5

AI Memory

Commit 6

Knowledge Analyzer

Commit 7

AI Advisor

---

# 4. Opportunity Engine Structure

Opportunity Engine

├── Opportunity Logger

紀錄每一次 Scanner Decision

├── Shadow Trading

建立虛擬交易

├── Shadow Validator

驗證 TP / SL / Timeout

├── AI Memory

累積歷史知識

├── Knowledge Analyzer

分析歷史

└── AI Advisor

提出建議

---

# 5. Future Vision

Replay Lab

↓

Opportunity Engine

↓

Validation

↓

Knowledge

↓

AI Advisor

↓

Human Approval

↓

Weight Optimizer

↓

LIVE