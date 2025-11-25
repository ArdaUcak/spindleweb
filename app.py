import csv
import os
import socket
from datetime import datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, send_file, session, url_for

APP_TITLE = "STS - Spindle Takip Sistemi (Web)"
USERNAME = "BAKIM"
PASSWORD = "MAXIME"
DATE_FORMAT = "%d-%m-%Y"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def resource_path(filename: str) -> str:
    return os.path.join(BASE_DIR, filename)


class DataManager:
    def __init__(self, filename, headers):
        self.filepath = resource_path(filename)
        self.headers = headers
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.headers)
                writer.writeheader()

    def _read_all(self):
        with open(self.filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def _write_all(self, rows):
        with open(self.filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writeheader()
            writer.writerows(rows)

    def _next_id(self):
        rows = self._read_all()
        if not rows:
            return 1
        return max(int(row["id"]) for row in rows) + 1

    def add_record(self, data):
        rows = self._read_all()
        data["id"] = str(self._next_id())
        rows.append(data)
        self._write_all(rows)
        return data["id"]

    def update_record(self, record_id, data):
        rows = self._read_all()
        updated = False
        for row in rows:
            if row["id"] == record_id:
                row.update(data)
                updated = True
                break
        if updated:
            self._write_all(rows)
        return updated

    def delete_record(self, record_id):
        rows = self._read_all()
        new_rows = [row for row in rows if row["id"] != record_id]
        if len(new_rows) != len(rows):
            self._write_all(new_rows)
            return True
        return False

    def search(self, **filters):
        rows = self._read_all()
        results = []
        for row in rows:
            match = True
            for key, value in filters.items():
                if value and value.strip():
                    if value.lower() not in row.get(key, "").lower():
                        match = False
                        break
            if match:
                results.append(row)
        return results

    def all_records(self):
        return self._read_all()


app = Flask(__name__)
app.secret_key = "change_this_to_random_secret"

spindle_manager = DataManager(
    "spindle_data.csv",
    [
        "id",
        "Referans ID",
        "Çalışma Saati",
        "Takılı Olduğu Makine",
        "Makinaya Takıldığı Tarih",
        "Son Güncelleme",
    ],
)

yedek_manager = DataManager(
    "yedek_data.csv",
    [
        "id",
        "Referans ID",
        "Açıklama",
        "Tamirde mi",
        "Bakıma Gönderilme",
        "Geri Dönme",
        "Söküldüğü Makine",
        "Sökülme Tarihi",
        "Son Güncelleme",
    ],
)


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username", "").strip()
        pw = request.form.get("password", "").strip()
        if user == USERNAME and pw == PASSWORD:
            session["logged_in"] = True
            session["username"] = user
            flash("Giriş başarılı.", "success")
            return redirect(url_for("spindles"))
        flash("Kullanıcı adı veya şifre hatalı.", "danger")
    return render_template("login.html", app_title=APP_TITLE)


@app.route("/logout")
def logout():
    session.clear()
    flash("Çıkış yapıldı.", "info")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return redirect(url_for("spindles"))


@app.route("/spindles")
@login_required
def spindles():
    query = request.args.get("q", "").strip()
    if query:
        rows = spindle_manager.search(**{"Referans ID": query})
    else:
        rows = spindle_manager.all_records()
    return render_template("spindles.html", rows=rows, query=query, app_title=APP_TITLE)


@app.route("/spindles/add", methods=["GET", "POST"])
@login_required
def spindle_add():
    if request.method == "POST":
        referans_id = request.form.get("Referans ID", "").strip()
        if not referans_id:
            flash("Referans ID zorunludur.", "danger")
            return redirect(request.url)

        data = {
            "Referans ID": referans_id,
            "Çalışma Saati": request.form.get("Çalışma Saati", "").strip(),
            "Takılı Olduğu Makine": request.form.get("Takılı Olduğu Makine", "").strip(),
            "Makinaya Takıldığı Tarih": request.form.get("Makinaya Takıldığı Tarih", "").strip()
            or datetime.now().strftime(DATE_FORMAT),
            "Son Güncelleme": datetime.now().strftime(DATE_FORMAT),
        }
        spindle_manager.add_record(data)
        flash("Spindle kaydı eklendi.", "success")
        return redirect(url_for("spindles"))

    today = datetime.now().strftime(DATE_FORMAT)
    return render_template("spindle_form.html", mode="add", today=today, app_title=APP_TITLE)


@app.route("/spindles/<record_id>/edit", methods=["GET", "POST"])
@login_required
def spindle_edit(record_id):
    rows = spindle_manager.all_records()
    record = next((r for r in rows if r["id"] == record_id), None)
    if not record:
        flash("Kayıt bulunamadı.", "danger")
        return redirect(url_for("spindles"))

    if request.method == "POST":
        referans_id = request.form.get("Referans ID", "").strip()
        if not referans_id:
            flash("Referans ID zorunludur.", "danger")
            return redirect(request.url)

        updated = {
            "Referans ID": referans_id,
            "Çalışma Saati": request.form.get("Çalışma Saati", "").strip(),
            "Takılı Olduğu Makine": request.form.get("Takılı Olduğu Makine", "").strip(),
            "Makinaya Takıldığı Tarih": request.form.get("Makinaya Takıldığı Tarih", "").strip(),
            "Son Güncelleme": datetime.now().strftime(DATE_FORMAT),
        }
        spindle_manager.update_record(record_id, updated)
        flash("Spindle kaydı güncellendi.", "success")
        return redirect(url_for("spindles"))

    return render_template("spindle_form.html", mode="edit", record=record, app_title=APP_TITLE)


@app.route("/spindles/<record_id>/delete", methods=["POST"])
@login_required
def spindle_delete(record_id):
    if spindle_manager.delete_record(record_id):
        flash("Spindle kaydı silindi.", "success")
    else:
        flash("Kayıt silinemedi.", "danger")
    return redirect(url_for("spindles"))


@app.route("/yedeks")
@login_required
def yedeks():
    query = request.args.get("q", "").strip()
    if query:
        rows = yedek_manager.search(**{"Referans ID": query})
    else:
        rows = yedek_manager.all_records()
    return render_template("yedeks.html", rows=rows, query=query, app_title=APP_TITLE)


@app.route("/yedeks/add", methods=["GET", "POST"])
@login_required
def yedek_add():
    if request.method == "POST":
        referans_id = request.form.get("Referans ID", "").strip()
        if not referans_id:
            flash("Referans ID zorunludur.", "danger")
            return redirect(request.url)

        today = datetime.now().strftime(DATE_FORMAT)
        data = {
            "Referans ID": referans_id,
            "Açıklama": request.form.get("Açıklama", "").strip(),
            "Tamirde mi": request.form.get("Tamirde mi", "").strip(),
            "Bakıma Gönderilme": request.form.get("Bakıma Gönderilme", "").strip() or today,
            "Geri Dönme": request.form.get("Geri Dönme", "").strip() or today,
            "Söküldüğü Makine": request.form.get("Söküldüğü Makine", "").strip(),
            "Sökülme Tarihi": request.form.get("Sökülme Tarihi", "").strip() or today,
            "Son Güncelleme": today,
        }
        yedek_manager.add_record(data)
        flash("Yedek kaydı eklendi.", "success")
        return redirect(url_for("yedeks"))

    today = datetime.now().strftime(DATE_FORMAT)
    return render_template("yedek_form.html", mode="add", today=today, app_title=APP_TITLE)


@app.route("/yedeks/<record_id>/edit", methods=["GET", "POST"])
@login_required
def yedek_edit(record_id):
    rows = yedek_manager.all_records()
    record = next((r for r in rows if r["id"] == record_id), None)
    if not record:
        flash("Kayıt bulunamadı.", "danger")
        return redirect(url_for("yedeks"))

    if request.method == "POST":
        referans_id = request.form.get("Referans ID", "").strip()
        if not referans_id:
            flash("Referans ID zorunludur.", "danger")
            return redirect(request.url)

        today = datetime.now().strftime(DATE_FORMAT)
        updated = {
            "Referans ID": referans_id,
            "Açıklama": request.form.get("Açıklama", "").strip(),
            "Tamirde mi": request.form.get("Tamirde mi", "").strip(),
            "Bakıma Gönderilme": request.form.get("Bakıma Gönderilme", "").strip(),
            "Geri Dönme": request.form.get("Geri Dönme", "").strip(),
            "Söküldüğü Makine": request.form.get("Söküldüğü Makine", "").strip(),
            "Sökülme Tarihi": request.form.get("Sökülme Tarihi", "").strip(),
            "Son Güncelleme": today,
        }
        yedek_manager.update_record(record_id, updated)
        flash("Yedek kaydı güncellendi.", "success")
        return redirect(url_for("yedeks"))

    return render_template("yedek_form.html", mode="edit", record=record, app_title=APP_TITLE)


@app.route("/yedeks/<record_id>/delete", methods=["POST"])
@login_required
def yedek_delete(record_id):
    if yedek_manager.delete_record(record_id):
        flash("Yedek kaydı silindi.", "success")
    else:
        flash("Kayıt silinemedi.", "danger")
    return redirect(url_for("yedeks"))


@app.route("/export")
@login_required
def export():
    export_path = resource_path("takip_export.csv")

    spindle_rows = spindle_manager.all_records()
    yedek_rows = yedek_manager.all_records()

    with open(export_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["--- Spindle Takip ---"])
        writer.writerow(
            ["Referans ID", "Saat", "Takılı Olduğu Makine", "Takıldığı Tarih", "Son Güncelleme"]
        )
        for row in spindle_rows:
            writer.writerow(
                [
                    row.get("Referans ID", ""),
                    row.get("Çalışma Saati", ""),
                    row.get("Takılı Olduğu Makine", ""),
                    row.get("Makinaya Takıldığı Tarih", ""),
                    row.get("Son Güncelleme", ""),
                ]
            )
        writer.writerow([])
        writer.writerow(["--- Yedek Takip ---"])
        writer.writerow(
            [
                "Referans ID",
                "Açıklama",
                "Tamirde",
                "Gönderildi",
                "Dönen",
                "Söküldüğü Makine",
                "Sökülme Tarihi",
                "Son Güncelleme",
            ]
        )
        for row in yedek_rows:
            writer.writerow(
                [
                    row.get("Referans ID", ""),
                    row.get("Açıklama", ""),
                    row.get("Tamirde mi", ""),
                    row.get("Bakıma Gönderilme", ""),
                    row.get("Geri Dönme", ""),
                    row.get("Söküldüğü Makine", ""),
                    row.get("Sökülme Tarihi", ""),
                    row.get("Son Güncelleme", ""),
                ]
            )

    return send_file(export_path, as_attachment=True, download_name="takip_export.csv")


if __name__ == "__main__":
    host = os.environ.get("APP_HOST", "0.0.0.0")
    port = int(os.environ.get("APP_PORT", 5000))

    def _lan_ip() -> str | None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except OSError:
            return None

    def _candidate_ips() -> list[str]:
        addresses: set[str] = set()
        try:
            infos = socket.getaddrinfo(socket.gethostname(), None, family=socket.AF_INET)
            for info in infos:
                ip = info[4][0]
                if not ip.startswith("127."):
                    addresses.add(ip)
        except OSError:
            pass
        lan = _lan_ip()
        if lan:
            addresses.add(lan)
        return sorted(addresses)

    lan_ip = _lan_ip()
    private_ips = _candidate_ips()
    print(f"Local access: http://127.0.0.1:{port}/login")
    if lan_ip:
        print(f"LAN access:   http://{lan_ip}:{port}/login")
    else:
        print("LAN access:   Use this machine's LAN IP (ipconfig/ifconfig).")
    if private_ips:
        print("Detected IPv4 addresses (use the one on your Wi‑Fi/Ethernet):")
        for ip in private_ips:
            print(f" - http://{ip}:{port}/login")
    print("If phones show 127.0.0.1 refused, use the LAN IP above instead.")

    app.run(host=host, port=port, debug=True)
