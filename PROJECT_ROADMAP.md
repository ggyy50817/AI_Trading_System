# AI Trading System Roadmap

## 已完成

- TP State Engine V1
- Cooldown Engine V1
- GitHub Backup Milestone #2
- Recovery Guide V1
- .gitignore
- AI Score 80 Experiment Started

---

## 進行中

### AI Score Threshold Validation

目前：

70 -> 80

觀察：

- PnL
- TP1
- TP2
- TP3
- SL

目標：

確認 80 是否優於 70

---

## 下一階段

### Trading Statistics V1.1

新增：

- Gross PnL
- Net PnL
- Trading Fee
- Funding Fee
- Win Rate
- Average Win
- Average Loss
- LONG Win Rate
- SHORT Win Rate

---

### Market Regime Filter V2

BULL：
- 提高 SHORT 門檻

BEAR：
- 提高 LONG 門檻

RANGE：
- 僅允許高分單

---

### Position Size Engine

目標：

固定風險

MAX_SINGLE_RISK = 5%

MAX_TOTAL_RISK = 20%

---

### Risk Score Engine

評估：

- 波動
- 市場狀態
- 風險係數

---

### Black Swan Defense V1

保護系統避免極端行情

---

## 長期目標

### TP/SL V2

BingX 原生 TP1 / TP2 / TP3

同步層：

Bot <-> BingX

---

### News Risk Engine

ETF
監管
駭客事件
交易所公告

---

### Weight Optimizer

50+
200+
500+
1000+

交易樣本後啟動

---

### Multi Strategy

Strategy A
Strategy B
Strategy C

---

### LIVE Trading

完成所有驗證後啟動

---

### 第二交易所

完成 BingX 穩定後再考慮

