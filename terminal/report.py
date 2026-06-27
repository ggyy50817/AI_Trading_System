import subprocess


def show():
    print("=" * 60)
    print("Milestone Report")
    print("=" * 60)

    try:
        output = subprocess.check_output(
            "python milestone_report.py",
            shell=True,
            text=True
        )

        print(output)

    except Exception as e:
        print("ERROR:", e)
