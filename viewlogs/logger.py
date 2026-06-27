from datetime import datetime

def log_message(message):

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log = f"[{current_time}] {message}"

    print(log)

    with open("viewlogs/system.log", "a", encoding="utf-8") as file:
        file.write(log + "\n")