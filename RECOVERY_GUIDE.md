# AI Trading System Recovery Guide

## 1. 登入 VPS

登入 Hostinger VPS

## 2. 安裝 Git

apt update
apt install git -y

## 3. Clone 專案

git clone https://github.com/ggyy50817/AI_Trading_System.git

cd AI_Trading_System

## 4. 建立虛擬環境

python3 -m venv venv

source venv/bin/activate

## 5. 安裝套件

pip install -r requirements.txt

## 6. 建立 tmux

tmux new -s tradingbot

## 7. 啟動機器人

source venv/bin/activate

python3 main.py

## 8. 離開 tmux

Ctrl+B

D

## 9. 回到 tmux

tmux attach -t tradingbot

## 10. 查看機器人

ps aux | grep "python3 main.py"

