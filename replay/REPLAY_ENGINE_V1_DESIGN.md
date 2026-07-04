# Replay Engine V1 Design

## 目標
建立歷史回放系統，加速驗證 Strategy A。

## 原則
- 不影響 VST Bot
- 不真實下單
- 不呼叫 BingX 下單 API
- 不修改 scanner 核心交易邏輯
- Replay 只產生 replay log
- VST 繼續跑真實市場驗證

## V1 範圍
- 單一幣種
- 單一時間框
- 讀取歷史 K 線
- 模擬開倉
- 模擬 TP / SL
- 輸出 replay_trading_log.csv
- 可用 Validation Report 分析

## V1 不做
- 不做多幣
- 不做平行運算
- 不做 Monte Carlo
- 不做 Walk Forward
- 不接真實 BingX 下單
- 不改 VST Bot

## 預計檔案
replay/
- replay_config.py
- replay_data.py
- replay_position.py
- replay_logger.py
- replay_runner.py

## 資料流
Historical Kline
-> Replay Runner
-> AI Score / Context
-> Replay Position
-> TP / SL Simulation
-> replay_trading_log.csv
-> Validation Report

## Done Criteria
- 可執行 python3 replay/replay_runner.py
- 產生 replay_trading_log.csv
- 不影響 main.py
- 不影響 trading_log_v3.csv
