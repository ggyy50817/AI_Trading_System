import time

from scanner.bingx_api import (
    get_klines,
    klines_to_dataframe,
)
from scanner.universe import build_dynamic_universe


DEFAULT_INTERVAL = "15m"
DEFAULT_LIMIT = 100
DEFAULT_TOP_N = 100


def analyze_symbol(
    symbol,
    interval=DEFAULT_INTERVAL,
    limit=DEFAULT_LIMIT,
):
    klines = get_klines(
        symbol=symbol,
        interval=interval,
        limit=limit,
    )

    df = klines_to_dataframe(klines)

    if len(df) < 20:
        raise ValueError(
            f"Insufficient Kline data: {len(df)}"
        )

    latest = df.iloc[-1]

    close = float(latest["Close"])
    ma20 = float(latest["MA20"])
    atr = float(latest["ATR"])
    volume = float(latest["Volume"])
    volume_ratio = float(
        latest["VolumeRatio"]
    )

    if close <= 0:
        raise ValueError("Invalid close price")

    if atr <= 0:
        raise ValueError("Invalid ATR")

    return {
        "symbol": symbol,
        "close": close,
        "ma20": ma20,
        "atr": atr,
        "atr_percent": (
            atr / close * 100
        ),
        "volume": volume,
        "volume_ratio": volume_ratio,
        "ma20_position": (
            "ABOVE"
            if close > ma20
            else "BELOW"
        ),
    }


def candidate_rank_key(item):
    return (
        item["volume_ratio"],
        item["atr_percent"],
    )


def build_candidate_pool(
    symbols=None,
    top_n=DEFAULT_TOP_N,
):
    if symbols is None:
        symbols = build_dynamic_universe()

    started = time.perf_counter()

    valid = []
    failed = []

    for index, symbol in enumerate(
        symbols,
        start=1,
    ):
        try:
            result = analyze_symbol(symbol)
            valid.append(result)

        except Exception as exc:
            failed.append({
                "symbol": symbol,
                "error": (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            })

        if (
            index % 50 == 0
            or index == len(symbols)
        ):
            print(
                f"Progress "
                f"{index}/{len(symbols)}"
            )

    ranked = sorted(
        valid,
        key=candidate_rank_key,
        reverse=True,
    )

    candidates = ranked[:top_n]

    elapsed = time.perf_counter() - started

    return {
        "universe_count": len(symbols),
        "valid_count": len(valid),
        "failed_count": len(failed),
        "candidate_count": len(candidates),
        "elapsed_seconds": round(
            elapsed,
            2,
        ),
        "candidates": candidates,
        "failed": failed,
    }


if __name__ == "__main__":
    result = build_candidate_pool()

    print()
    print("=" * 90)
    print("Candidate Pre-Scanner V1")
    print("=" * 90)

    print(
        "Universe   :",
        result["universe_count"],
    )
    print(
        "Valid      :",
        result["valid_count"],
    )
    print(
        "Failed     :",
        result["failed_count"],
    )
    print(
        "Candidates :",
        result["candidate_count"],
    )
    print(
        "Elapsed    :",
        result["elapsed_seconds"],
        "seconds",
    )

    print()
    print("===== TOP 30 =====")

    for item in result["candidates"][:30]:
        print(
            f"{item['symbol']:20} "
            f"VOL={item['volume_ratio']:8.3f} "
            f"ATR%={item['atr_percent']:8.3f} "
            f"MA20={item['ma20_position']}"
        )

    print()
    print("===== FAILED =====")

    if not result["failed"]:
        print("None")
    else:
        for item in result["failed"]:
            print(
                item["symbol"],
                item["error"],
            )
