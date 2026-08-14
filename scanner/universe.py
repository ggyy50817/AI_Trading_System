import requests

from scanner.bingx_api import BASE_URL


CONTRACTS_ENDPOINT = "/openApi/swap/v2/quote/contracts"

EXCLUDED_PREFIXES = (
    "NC",
)


def is_api_tradable(contract):
    return (
        contract.get("currency") == "USDT"
        and contract.get("status") == 1
        and str(contract.get("apiStateOpen")).lower() == "true"
        and str(contract.get("apiStateClose")).lower() == "true"
    )


def is_crypto_candidate(contract):
    asset = str(contract.get("asset", ""))

    if not asset:
        return False

    if asset.startswith(EXCLUDED_PREFIXES):
        return False

    return True


def fetch_contracts(timeout=10):
    url = f"{BASE_URL}{CONTRACTS_ENDPOINT}"

    response = requests.get(
        url,
        timeout=timeout,
    )
    response.raise_for_status()

    payload = response.json()

    if payload.get("code") != 0:
        raise RuntimeError(
            f"BingX contracts API error: "
            f"code={payload.get('code')} "
            f"msg={payload.get('msg')}"
        )

    data = payload.get("data")

    if not isinstance(data, list):
        raise RuntimeError(
            "BingX contracts API returned invalid data"
        )

    return data


def build_dynamic_universe(contracts=None):
    if contracts is None:
        contracts = fetch_contracts()

    universe = []

    for contract in contracts:
        if not is_api_tradable(contract):
            continue

        if not is_crypto_candidate(contract):
            continue

        symbol = str(
            contract.get("symbol", "")
        ).strip()

        if not symbol:
            continue

        universe.append(symbol)

    return sorted(set(universe))


def get_universe_summary(contracts=None):
    if contracts is None:
        contracts = fetch_contracts()

    usdt_contracts = [
        contract
        for contract in contracts
        if contract.get("currency") == "USDT"
    ]

    api_tradable = [
        contract
        for contract in usdt_contracts
        if is_api_tradable(contract)
    ]

    excluded_nc = [
        contract
        for contract in api_tradable
        if not is_crypto_candidate(contract)
    ]

    universe = build_dynamic_universe(
        contracts
    )

    return {
        "all_contracts": len(contracts),
        "usdt_contracts": len(usdt_contracts),
        "api_tradable": len(api_tradable),
        "excluded_nc": len(excluded_nc),
        "dynamic_universe": len(universe),
    }


if __name__ == "__main__":
    contracts = fetch_contracts()
    summary = get_universe_summary(
        contracts
    )
    universe = build_dynamic_universe(
        contracts
    )

    print("=" * 80)
    print("Dynamic Universe V1")
    print("=" * 80)

    for key, value in summary.items():
        print(f"{key:20}: {value}")

    print()
    print("First 20:")
    for symbol in universe[:20]:
        print(symbol)

    print()
    print("Last 20:")
    for symbol in universe[-20:]:
        print(symbol)
