from replay.replay_engine import replay
from replay.replay_validation_engine import validate


def main():
    print("Replay Start\n")

    for record in replay():

        errors = validate(record)

        if errors:
            print("❌ Validation Failed")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✅ Validation OK")
            print(record["symbol"], record["side"])

    print("\nReplay Finished")


if __name__ == "__main__":
    main()