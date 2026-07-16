import json

from research.research_runner import run_research

LONG_VALUES = [70,75,80,85,90]
SHORT_VALUES = [70,75,80,85,90]

results=[]

for long_th in LONG_VALUES:

    for short_th in SHORT_VALUES:

        print(
            f"\nTesting LONG={long_th} SHORT={short_th}"
        )

        result=run_research(
            long_threshold=long_th,
            short_threshold=short_th,
            verbose=False
        )

        results.append(result)

print()
print("="*60)
print("Threshold Optimizer V1")
print("="*60)

results=sorted(
    results,
    key=lambda x:(
        -x["trades"],
        -x["signals"]
    )
)

for r in results:

    print(
        f'LONG={r["long_threshold"]}',
        f'SHORT={r["short_threshold"]}',
        f'Signals={r["signals"]}',
        f'Trades={r["trades"]}'
    )

with open(
    "research/output/threshold_results.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        indent=4,
        ensure_ascii=False
    )

print()
print("Saved:")
print("research/output/threshold_results.json")
