import json

from src.data.json_report_repository import JsonReportRepository


def test_load_all_returns_saved_reports(tmp_path):
    report_path = tmp_path / "reports.json"
    reports = [
        {"sender_email": "alerts@example.com", "severity": "NEEDS_REVIEW"},
        {"sender_email": "notice@example.com", "severity": "LOG_ONLY"},
    ]
    report_path.write_text(json.dumps(reports), encoding="utf-8")

    repository = JsonReportRepository(report_path)

    assert repository.load_all() == reports


def test_load_all_returns_empty_list_for_empty_history(tmp_path):
    report_path = tmp_path / "reports.json"
    report_path.write_text("[]", encoding="utf-8")

    repository = JsonReportRepository(report_path)

    assert repository.load_all() == []