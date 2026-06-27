import subprocess
import sys

def show():
    print("=" * 60)
    print("New Validation Statistics")
    print("=" * 60)

    try:
        print(subprocess.check_output(
            [sys.executable, "validation_report.py"],
            text=True
        ))
    except Exception as e:
        print("ERROR:", e)
