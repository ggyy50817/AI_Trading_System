"""
Opportunity Engine Data Models

Opportunity Engine does NOT define its own data schema.

The canonical contract of the entire AI Trading System is:

    TradingDecision

Produced by

    Scanner
    Replay
    Research
    Shadow Trading

Consumed by

    Opportunity Engine
    Validation
    Decision Dataset
    Replay Compare
    Future AI modules

Opportunity Engine observes TradingDecision only.

It never creates another schema.

Future

TradingDecision
        ↓
Opportunity Engine
        ↓
Logger
        ↓
Shadow Trading
        ↓
AI Memory
        ↓
Knowledge Analyzer
        ↓
AI Advisor
"""