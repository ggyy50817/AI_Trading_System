from decision_dataset.reader import (
    count,
    load_all,
    load_last,
)


def main():
    print("Dataset Count:", count())

    print()

    print("Latest Record:")
    latest = load_last(1)
    print(latest)

    print()

    print("Load All:")
    print(load_all())


if __name__ == "__main__":
    main()