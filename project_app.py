from io import StringIO
import csv
import sys
from pathlib import Path

LOCAL_SITE_PACKAGES = Path(__file__).resolve().parent / "venv" / "Lib" / "site-packages"
if LOCAL_SITE_PACKAGES.exists():
    sys.path.insert(0, str(LOCAL_SITE_PACKAGES))

from flask import Flask, Response, render_template, request

from services.benefit_service import get_dashboard_data


app = Flask(__name__)


@app.route("/")
def index():
    dashboard = get_dashboard_data(request.args)
    return render_template("index.html", **dashboard)


@app.route("/download.csv")
def download_csv():
    dashboard = get_dashboard_data(request.args)
    output = StringIO()
    fieldnames = [
        "title",
        "provider",
        "source_type",
        "category",
        "province",
        "district",
        "region",
        "money_type",
        "target",
        "summary",
        "matched_reason",
        "score",
        "url",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for benefit in dashboard["benefits"]:
        writer.writerow({key: benefit.get(key, "") for key in fieldnames})

    csv_text = "\ufeff" + output.getvalue()
    return Response(
        csv_text,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=benefit_results.csv"},
    )


if __name__ == "__main__":
    app.run(debug=False, port=5001, use_reloader=False)
