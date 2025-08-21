import pytest
import json
import os
import tempfile
from unittest.mock import patch, mock_open
from main import read_log_file, analyze_logs, save_report, print_table, setup_args


class TestReadLogFile:

    def test_read_valid_log_file(self):
        test_data = [
            '{"url": "/api/users", "response_time": 100}\n',
            '{"url": "/api/products", "response_time": 200}\n',
        ]

        with patch("builtins.open", mock_open(read_data="".join(test_data))):
            result = read_log_file("dummy_path.log")

        assert len(result) == 2
        assert result[0]["url"] == "/api/users"
        assert result[1]["response_time"] == 200

    def test_read_empty_file(self):
        with patch("builtins.open", mock_open(read_data="")):
            result = read_log_file("empty.log")
            assert len(result) == 0

    def test_read_file_with_invalid_json(self, capsys):
        test_data = [
            '{"url": "/api/users", "response_time": 100}\n',
            "invalid json here\n",
            '{"url": "/api/products", "response_time": 200}\n',
        ]

        with patch("builtins.open", mock_open(read_data="".join(test_data))):
            result = read_log_file("invalid.log")

        captured = capsys.readouterr()
        assert "Ошибка" in captured.out
        assert len(result) == 2

    def test_file_not_found(self, capsys):
        result = read_log_file("non_existent_file.log")
        captured = capsys.readouterr()
        assert "не найден" in captured.out
        assert len(result) == 0


class TestAnalyzeLogs:

    def test_analyze_logs_basic(self):
        test_logs = [
            {"url": "/api/users", "response_time": 100},
            {"url": "/api/users", "response_time": 200},
            {"url": "/api/products", "response_time": 50},
        ]

        result = analyze_logs(test_logs)

        assert "/api/users" in result
        assert "/api/products" in result
        assert result["/api/users"]["count"] == 2
        assert result["/api/users"]["total_time"] == 300
        assert result["/api/users"]["avg_response_time"] == 150
        assert result["/api/products"]["avg_response_time"] == 50

    def test_analyze_logs_missing_fields(self):
        test_logs = [
            {"url": "/api/users", "response_time": 100},
            {"url": "/api/products"},
            {"response_time": 200},
        ]

        result = analyze_logs(test_logs)

        assert len(result) == 1
        assert "/api/users" in result

    def test_analyze_empty_logs(self):
        result = analyze_logs([])
        assert result == {}


class TestSaveReport:

    def test_save_report(self):
        test_stats = {
            "/api/users": {"count": 2, "avg_response_time": 150.0},
            "/api/products": {"count": 1, "avg_response_time": 50.0},
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp:
            tmp_path = tmp.name

        try:
            save_report(test_stats, tmp_path)

            assert os.path.exists(tmp_path)

            with open(tmp_path, "r") as f:
                saved_data = json.load(f)

            assert "/api/users" in saved_data
            assert saved_data["/api/users"]["count"] == 2
            assert saved_data["/api/users"]["avg_response_time"] == 150.0
            assert saved_data["/api/products"]["avg_response_time"] == 50.0

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestPrintTable:
    def test_print_table(self, capsys):
        test_stats = {
            "/api/users": {"count": 2, "avg_response_time": 150.0},
            "/api/products": {"count": 1, "avg_response_time": 50.0},
        }

        print_table(test_stats)

        captured = capsys.readouterr()
        output = captured.out

        assert "handler" in output
        assert "total" in output
        assert "avg_response_time" in output
        assert "/api/users" in output
        assert "2" in output


class TestSetupArgs:
    def test_setup_args_basic(self):
        test_args = [
            "main.py",
            "--file",
            "example1.log",
            "example2.log",
            "--report",
            "output.json",
        ]

        with patch("sys.argv", test_args):
            args = setup_args()

        assert args.file == ["example1.log", "example2.log"]
        assert args.report == "output.json"

    def test_setup_args_multiple_files(self):
        test_args = [
            "main.py",
            "--file",
            "example1.log",
            "example2.log",
            "--report",
            "output.json",
        ]

        with patch("sys.argv", test_args):
            args = setup_args()

        assert args.file == ["example1.log", "example2.log"]
        assert args.report == "output.json"

    def test_setup_args_default_report(self):
        test_args = ["main.py", "--file", "example1.log", "example2.log"]

        with patch("sys.argv", test_args):
            args = setup_args()

        assert args.file == ["example1.log", "example2.log"]
        assert args.report == "average.json"


class TestIntegration:

    def test_full_integration(self, tmp_path):
        test_log_content = """
        {"url": "/api/users", "response_time": 100}
        {"url": "/api/users", "response_time": 200}
        {"url": "/api/products", "response_time": 50}
        """

        log_file1 = tmp_path / "example1.log"
        log_file2 = tmp_path / "example2.log"
        report_file = tmp_path / "report.json"

        with open(log_file1, "w") as f1, open(log_file2, "w") as f2:
            f1.write(test_log_content)
            f2.write(test_log_content)

        logs = read_log_file(str(log_file1))
        stats = analyze_logs(logs)
        save_report(stats, str(report_file))

        assert len(logs) == 3
        assert os.path.exists(report_file)

        with open(report_file, "r") as f:
            report_data = json.load(f)

        assert report_data["/api/users"]["count"] == 2
        assert report_data["/api/users"]["avg_response_time"] == 150.0


def test_division_by_zero_protection():
    result = analyze_logs([])
    assert result == {}
