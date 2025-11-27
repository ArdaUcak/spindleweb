import csv
import os
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

APP_TITLE = "STS - Spindle Takip Sistemi (Web)"
USERNAME = "BAKIM"
PASSWORD = "MAXIME"
DATE_FORMAT = "%d-%m-%Y"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def resource_path(filename: str) -> str:
    return os.path.join(BASE_DIR, filename)


app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static"),
)
app.secret_key = os.environ.get("SECRET_KEY", "change_this_to_random_secret")


def ensure_template_exists(template_name: str) -> None:
    """Provide a clearer error if a template is missing on disk."""
    template_path = resource_path(os.path.join("templates", template_name))
    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"Beklenen şablon bulunamadı: {template_path}.\n"
            "Proje klasörünü eksiksiz kopyaladığınızdan ve 'templates' dizinini içerdiğinden emin olun."
        )


class DataManager:
    def __init__(self, filename: str, headers: list[str]):
        self.filepath = resource_path(filename)
        self.headers = headers
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=self.headers)
                writer.writeheader()

    def _read_all(self) -> list[dict]:
        with open(self.filepath, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return list(reader)

    def _write_all(self, rows: list[dict]) -> None:
        with open(self.filepath, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.headers)
            writer.writeheader()
            writer.writerows(rows)

    def _next_id(self) -> int:
        rows = self._read_all()
        if not rows:
            return 1
        return max(int(row["id"]) for row in rows) + 1

    def add_record(self, data: dict) -> str:
        rows = self._read_all()
        data["id"] = str(self._next_id())
        rows.append(data)
        self._write_all(rows)
        return data["id"]

    def update_record(self, record_id: str, data: dict) -> bool:
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

    def delete_record(self, record_id: str) -> bool:
        rows = self._read_all()
        new_rows = [row for row in rows if row["id"] != record_id]
        if len(new_rows) != len(rows):
            self._write_all(new_rows)
            return True
        return False

    def search(self, **filters: str) -> list[dict]:
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

    def all_records(self) -> list[dict]:
        return self._read_all()


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


def today_date() -> str:
    return datetime.now().strftime(DATE_FORMAT)


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


@app.context_processor
def inject_globals():
    return {"app_title": APP_TITLE}


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
    return render_template("login.html")


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
    return render_template("spindles.html", rows=rows, query=query)


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
            "Makinaya Takıldığı Tarih": request.form.get("Makinaya Takıldığı Tarih", "").strip() or today_date(),
            "Son Güncelleme": today_date(),
        }
        spindle_manager.add_record(data)
        flash("Spindle kaydı eklendi.", "success")
        return redirect(url_for("spindles"))

    return render_template("spindle_form.html", mode="add", today=today_date())


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
            "Son Güncelleme": today_date(),
        }
        spindle_manager.update_record(record_id, updated)
        flash("Spindle kaydı güncellendi.", "success")
        return redirect(url_for("spindles"))

    return render_template("spindle_form.html", mode="edit", record=record, today=today_date())


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
    return render_template("yedeks.html", rows=rows, query=query)


@app.route("/yedeks/add", methods=["GET", "POST"])
@login_required
def yedek_add():
    if request.method == "POST":
        referans_id = request.form.get("Referans ID", "").strip()
        if not referans_id:
            flash("Referans ID zorunludur.", "danger")
            return redirect(request.url)

        today = today_date()
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

    return render_template("yedek_form.html", mode="add", today=today_date())


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

        updated = {
            "Referans ID": referans_id,
            "Açıklama": request.form.get("Açıklama", "").strip(),
            "Tamirde mi": request.form.get("Tamirde mi", "").strip(),
            "Bakıma Gönderilme": request.form.get("Bakıma Gönderilme", "").strip(),
            "Geri Dönme": request.form.get("Geri Dönme", "").strip(),
            "Söküldüğü Makine": request.form.get("Söküldüğü Makine", "").strip(),
            "Sökülme Tarihi": request.form.get("Sökülme Tarihi", "").strip(),
            "Son Güncelleme": today_date(),
        }
        yedek_manager.update_record(record_id, updated)
        flash("Yedek kaydı güncellendi.", "success")
        return redirect(url_for("yedeks"))

    return render_template("yedek_form.html", mode="edit", record=record, today=today_date())


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

    with open(export_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["--- Spindle Takip ---"])
        writer.writerow([
            "Referans ID",
            "Saat",
            "Takılı Olduğu Makine",
            "Takıldığı Tarih",
            "Son Güncelleme",
        ])
        for row in spindle_rows:
            writer.writerow([
                row.get("Referans ID", ""),
                row.get("Çalışma Saati", ""),
                row.get("Takılı Olduğu Makine", ""),
                row.get("Makinaya Takıldığı Tarih", ""),
                row.get("Son Güncelleme", ""),
            ])
        writer.writerow([])
        writer.writerow(["--- Yedek Takip ---"])
        writer.writerow([
            "Referans ID",
            "Açıklama",
            "Tamirde",
            "Gönderildi",
            "Dönen",
            "Söküldüğü Makine",
            "Sökülme Tarihi",
            "Son Güncelleme",
        ])
        for row in yedek_rows:
            writer.writerow([
                row.get("Referans ID", ""),
                row.get("Açıklama", ""),
                row.get("Tamirde mi", ""),
                row.get("Bakıma Gönderilme", ""),
                row.get("Geri Dönme", ""),
                row.get("Söküldüğü Makine", ""),
                row.get("Sökülme Tarihi", ""),
                row.get("Son Güncelleme", ""),
            ])

    return send_file(export_path, as_attachment=True, download_name="takip_export.csv")


if __name__ == "__main__":
    # Ensure required templates exist when the server starts so users get a clear error
    for required_template in [
        "login.html",
        "spindles.html",
        "spindle_form.html",
        "yedeks.html",
        "yedek_form.html",
        "base.html",
    ]:
        ensure_template_exists(required_template)

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    print(f"\n{APP_TITLE} çalışıyor.")
    print(f"Local:  http://localhost:{port}")
    print("LAN erişimi için bu makinenin IP'sini kullanın (örn. ipconfig > IPv4).")
    app.run(host=host, port=port, debug=True)
