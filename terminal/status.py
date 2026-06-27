import subprocess


def show():
    print("=" * 60)
    print("Bot Status")
    print("=" * 60)

    try:
        bot = subprocess.check_output(
            "ps -ef | grep main.py | grep -v grep",
            shell=True,
            text=True
        ).strip()

        print(bot if bot else "Bot Not Running")

    except:
        print("Bot Not Running")

    print()

    print("=" * 60)
    print("Tmux")
    print("=" * 60)

    try:
        tmux = subprocess.check_output(
            "tmux ls",
            shell=True,
            text=True
        ).strip()

        print(tmux)

    except:
        print("No tmux session")
