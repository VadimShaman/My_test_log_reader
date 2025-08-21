import argparse
import json
from collections import defaultdict
import pandas as pd


def setup_args():
    parser = argparse.ArgumentParser(description="Анализ лог-файлов JSON")
    parser.add_argument(
        "--file",
        required=True,
        nargs="+",
        help="Пути к JSON-лог файлам (один или несколько)",
    )
    parser.add_argument("--report", default="average.json", help="Имя файла для отчета")
    return parser.parse_args()


def read_log_file(file_path):
    logs = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        log_entry = json.loads(line)
                        logs.append(log_entry)
                    except json.JSONDecodeError as e:
                        print(f"Ошибка в файле {file_path}, строка {line_number}: {e}")
                        continue
    except FileNotFoundError:
        print(f"Файл {file_path} не найден!")
    return logs


def analyze_logs(logs):
    stats = defaultdict(lambda: {"count": 0, "total_time": 0.0})

    for log in logs:
        if "url" in log and "response_time" in log:
            endpoint = log["url"]
            response_time = log["response_time"]

            stats[endpoint]["count"] += 1
            stats[endpoint]["total_time"] += response_time

    for endpoint in stats:
        if stats[endpoint]["count"] > 0:
            stats[endpoint]["avg_response_time"] = (
                stats[endpoint]["total_time"] / stats[endpoint]["count"]
            )

    return stats


def save_report(stats, report_filename):
    report_data = {
        endpoint: {
            "count": data["count"],
            "avg_response_time": round(data["avg_response_time"], 2),
        }
        for endpoint, data in stats.items()
    }

    with open(report_filename, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)


def print_table(stats):
    table_data = []
    for endpoint, data in stats.items():
        table_data.append(
            {
                "handler": endpoint,
                "total": data["count"],
                "avg_response_time": round(data["avg_response_time"], 3),
            }
        )

    table_data.sort(key=lambda x: x["total"], reverse=True)

    df = pd.DataFrame(table_data)
    print(df.to_string(index=False))


def main():
    args = setup_args()

    all_logs = []
    for file_path in args.file:
        logs = read_log_file(file_path)
        all_logs.extend(logs)

    if not all_logs:
        print("Файлы пусты или не содержат валидных JSON-записей")
        return

    stats = analyze_logs(all_logs)

    save_report(stats, args.report)

    print_table(stats)

    print(f"\nОтчет также сохранен в файл: {args.report}")


if __name__ == "__main__":
    main()
