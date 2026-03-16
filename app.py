"""
Flask backend for GTFS audit interface.
"""
import io
import zipfile
import pandas as pd
from flask import Flask, request, jsonify, render_template
from audit_orchestrators import (
    audit_agency, audit_calendar, audit_calendar_dates,
    audit_routes, audit_stop_times, audit_stops, audit_trips,
)

app = Flask(__name__)

# Stockage des DataFrames en mémoire
GTFS_DATA = {}

# Fichiers GTFS supportés
SUPPORTED_FILES = [
    "agency.txt", "calendar.txt", "calendar_dates.txt",
    "routes.txt", "stop_times.txt", "stops.txt", "trips.txt",
]


# ============================================================
# SERIALISATION
# ============================================================

def serialize_check(check) -> dict:
    return {
        "check_id":        check.check_id,
        "label":           check.label,
        "category":        check.category,
        "status":          check.status,
        "weight":          check.weight,
        "score":           check.score,
        "message":         check.message,
        "affected_ids":    check.affected_ids,
        "affected_count":  check.affected_count,
        "total_count":     check.total_count,
        "details":         check.details,
    }

def serialize_category(cat) -> dict:
    return {
        "category":     cat.category,
        "score":        cat.score,
        "total_weight": cat.total_weight,
        "checks":       [serialize_check(c) for c in cat.checks],
    }

def serialize_file(fs) -> dict:
    return {
        "file":       fs.file,
        "score":      fs.score,
        "grade":      fs.grade,
        "categories": [serialize_category(cat) for cat in fs.categories],
    }


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    global GTFS_DATA
    GTFS_DATA = {}

    files = request.files.getlist("files")

    for f in files:
        filename = f.filename

        # Cas .zip
        if filename.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(f.read())) as z:
                for name in z.namelist():
                    if name.endswith(".txt") and name in SUPPORTED_FILES:
                        with z.open(name) as txt_file:
                            try:
                                GTFS_DATA[name] = pd.read_csv(txt_file, dtype=str)
                            except Exception:
                                pass

        # Cas .txt individuel
        elif filename in SUPPORTED_FILES:
            try:
                GTFS_DATA[filename] = pd.read_csv(io.BytesIO(f.read()), dtype=str)
            except Exception:
                pass

    return jsonify({"files": list(GTFS_DATA.keys())})


@app.route("/audit", methods=["POST"])
def audit():
    data     = request.get_json()
    target   = data.get("file", "all")
    results  = {}

    def get(name):
        return GTFS_DATA.get(name, None)

    auditors = {
        "agency.txt":         lambda: audit_agency(get("agency.txt"), get("routes.txt")),
        "calendar.txt":       lambda: audit_calendar(get("calendar.txt"), get("trips.txt")),
        "calendar_dates.txt": lambda: audit_calendar_dates(get("calendar_dates.txt"), get("calendar.txt")),
        "routes.txt":         lambda: audit_routes(get("routes.txt"), get("agency.txt"), get("trips.txt")),
        "stop_times.txt":     lambda: audit_stop_times(get("stop_times.txt"), get("trips.txt"), get("stops.txt")),
        "stops.txt":          lambda: audit_stops(get("stops.txt"), get("stop_times.txt")),
        "trips.txt":          lambda: audit_trips(get("trips.txt"), get("routes.txt"), get("calendar.txt"), get("calendar_dates.txt"), get("shapes.txt"), get("stop_times.txt")),
    }

    targets = SUPPORTED_FILES if target == "all" else [target]

    for name in targets:
        if name not in GTFS_DATA:
            continue
        if name not in auditors:
            continue
        try:
            results[name] = serialize_file(auditors[name]())
        except Exception as e:
            results[name] = {"error": str(e)}

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True)