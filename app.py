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

# A minimal baked-in set of templates so the app can recover even if the
# templates directory was not copied when the project was moved/extracted.
DEFAULT_TEMPLATES: dict[str, str] = {
    "base.html": """<!doctype html>\n<html lang=\"tr\">\n<head>\n  <meta charset=\"utf-8\">\n  <title>{{ app_title }}</title>\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n  <!-- Bootstrap CDN -->\n  <link\n    href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css\"\n    rel=\"stylesheet\">\n</head>\n<body class=\"bg-light\">\n\n<nav class=\"navbar navbar-expand-lg navbar-dark bg-primary mb-4\">\n  <div class=\"container-fluid\">\n    <a class=\"navbar-brand\" href=\"{{ url_for('spindles') }}\">STS</a>\n    {% if session.get('logged_in') %}\n    <div>\n      <a href=\"{{ url_for('spindles') }}\" class=\"btn btn-outline-light btn-sm me-2\">Spindle</a>\n      <a href=\"{{ url_for('yedeks') }}\" class=\"btn btn-outline-light btn-sm me-2\">Yedek</a>\n      <a href=\"{{ url_for('export') }}\" class=\"btn btn-outline-light btn-sm me-2\">Excel'e Aktar</a>\n      <a href=\"{{ url_for('logout') }}\" class=\"btn btn-light btn-sm text-primary\">Çıkış</a>\n    </div>\n    {% endif %}\n  </div>\n</nav>\n\n<div class=\"container mb-4\">\n  {% with messages = get_flashed_messages(with_categories=true) %}\n    {% if messages %}\n      {% for category, msg in messages %}\n        <div class=\"alert alert-{{ category }} alert-dismissible fade show\" role=\"alert\">\n          {{ msg }}\n          <button type=\"button\" class=\"btn-close\" data-bs-dismiss=\"alert\"></button>\n        </div>\n      {% endfor %}\n    {% endif %}\n  {% endwith %}\n\n  {% block content %}{% endblock %}\n</div>\n\n<script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js\"></script>\n</body>\n</html>\n""",
    "login.html": """{% extends \"base.html\" %}\n{% block content %}\n<div class=\"row justify-content-center\">\n  <div class=\"col-md-4\">\n    <div class=\"card shadow-sm\">\n      <div class=\"card-header text-center\">\n        <h5 class=\"mb-0\">Giriş Ekranı</h5>\n      </div>\n      <div class=\"card-body\">\n        <form method=\"post\">\n          <div class=\"mb-3\">\n            <label class=\"form-label\">Kullanıcı Adı</label>\n            <input type=\"text\" name=\"username\" class=\"form-control\" autofocus>\n          </div>\n          <div class=\"mb-3\">\n            <label class=\"form-label\">Şifre</label>\n            <input type=\"password\" name=\"password\" class=\"form-control\">\n          </div>\n          <button class=\"btn btn-primary w-100\" type=\"submit\">Giriş</button>\n        </form>\n      </div>\n      <div class=\"card-footer text-end small text-muted\">\n        Created by: Arda UÇAK\n      </div>\n    </div>\n  </div>\n</div>\n{% endblock %}\n""",
    "spindles.html": """{% extends \"base.html\" %}\n{% block content %}\n<div class=\"d-flex justify-content-between align-items-center mb-3\">\n  <h4>Spindle Takip Sistemi</h4>\n  <a href=\"{{ url_for('spindle_add') }}\" class=\"btn btn-success\">Spindle Ekle</a>\n</div>\n\n<form class=\"row gy-2 gx-2 align-items-center mb-3\" method=\"get\">\n  <div class=\"col-auto\">\n    <label class=\"col-form-label\">Referans ID ile Ara:</label>\n  </div>\n  <div class=\"col-auto\">\n    <input type=\"text\" name=\"q\" class=\"form-control\" value=\"{{ query }}\">\n  </div>\n  <div class=\"col-auto\">\n    <button class=\"btn btn-primary\" type=\"submit\">Ara</button>\n    <a href=\"{{ url_for('spindles') }}\" class=\"btn btn-secondary\">Temizle</a>\n  </div>\n</form>\n\n<div class=\"card shadow-sm\">\n  <div class=\"card-body p-0\">\n    <div class=\"table-responsive\">\n      <table class=\"table table-striped table-hover mb-0\">\n        <thead class=\"table-light\">\n          <tr>\n            <th>ID</th>\n            <th>Referans ID</th>\n            <th>Çalışma Saati</th>\n            <th>Takılı Olduğu Makine</th>\n            <th>Makinaya Takıldığı Tarih</th>\n            <th>Son Güncelleme</th>\n            <th class=\"text-end\">İşlemler</th>\n          </tr>\n        </thead>\n        <tbody>\n          {% for row in rows %}\n          <tr>\n            <td>{{ row[\"id\"] }}</td>\n            <td>{{ row[\"Referans ID\"] }}</td>\n            <td>{{ row[\"Çalışma Saati\"] }}</td>\n            <td>{{ row[\"Takılı Olduğu Makine\"] }}</td>\n            <td>{{ row[\"Makinaya Takıldığı Tarih\"] }}</td>\n            <td>{{ row[\"Son Güncelleme\"] }}</td>\n            <td class=\"text-end\">\n              <a href=\"{{ url_for('spindle_edit', record_id=row['id']) }}\" class=\"btn btn-sm btn-outline-primary\">Düzenle</a>\n              <form action=\"{{ url_for('spindle_delete', record_id=row['id']) }}\" method=\"post\" style=\"display:inline-block\" onsubmit=\"return confirm('Silmek istediğinize emin misiniz?');\">\n                <button class=\"btn btn-sm btn-outline-danger\" type=\"submit\">Sil</button>\n              </form>\n            </td>\n          </tr>\n          {% else %}\n          <tr>\n            <td colspan=\"7\" class=\"text-center py-3\">Kayıt bulunamadı.</td>\n          </tr>\n          {% endfor %}\n        </tbody>\n      </table>\n    </div>\n  </div>\n</div>\n{% endblock %}\n""",
    "spindle_form.html": """{% extends \"base.html\" %}\n{% block content %}\n<h4>{{ \"Spindle Ekle\" if mode == \"add\" else \"Spindle Düzenle\" }}</h4>\n\n<div class=\"card shadow-sm mt-3\">\n  <div class=\"card-body\">\n    <form method=\"post\">\n      <div class=\"mb-3\">\n        <label class=\"form-label\">Referans ID</label>\n        <input type=\"text\" name=\"Referans ID\" class=\"form-control\"\n               value=\"{{ record['Referans ID'] if record else '' }}\" required>\n      </div>\n\n      <div class=\"mb-3\">\n        <label class=\"form-label\">Çalışma Saati</label>\n        <input type=\"text\" name=\"Çalışma Saati\" class=\"form-control\"\n               value=\"{{ record['Çalışma Saati'] if record else '' }}\">\n      </div>\n\n      <div class=\"mb-3\">\n        <label class=\"form-label\">Takılı Olduğu Makine</label>\n        <input type=\"text\" name=\"Takılı Olduğu Makine\" class=\"form-control\"\n               value=\"{{ record['Takılı Olduğu Makine'] if record else '' }}\">\n      </div>\n\n      <div class=\"mb-3\">\n        <label class=\"form-label\">Makinaya Takıldığı Tarih</label>\n        <input type=\"text\" name=\"Makinaya Takıldığı Tarih\" class=\"form-control\"\n               placeholder=\"gg-aa-yyyy\"\n               value=\"{% if record %}{{ record['Makinaya Takıldığı Tarih'] }}{% else %}{{ today }}{% endif %}\">\n      </div>\n\n      <button type=\"submit\" class=\"btn btn-primary\">Kaydet</button>\n      <a href=\"{{ url_for('spindles') }}\" class=\"btn btn-secondary\">İptal</a>\n    </form>\n  </div>\n</div>\n{% endblock %}\n""",
    "yedeks.html": """{% extends \"base.html\" %}\n{% block content %}\n<div class=\"d-flex justify-content-between align-items-center mb-3\">\n  <h4>Yedek Takip Sistemi</h4>\n  <a href=\"{{ url_for('yedek_add') }}\" class=\"btn btn-success\">Yedek Ekle</a>\n</div>\n\n<form class=\"row gy-2 gx-2 align-items-center mb-3\" method=\"get\">\n  <div class=\"col-auto\">\n    <label class=\"col-form-label\">Referans ID ile Ara:</label>\n  </div>\n  <div class=\"col-auto\">\n    <input type=\"text\" name=\"q\" class=\"form-control\" value=\"{{ query }}\">\n  </div>\n  <div class=\"col-auto\">\n    <button class=\"btn btn-primary\" type=\"submit\">Ara</button>\n    <a href=\"{{ url_for('yedeks') }}\" class=\"btn btn-secondary\">Temizle</a>\n  </div>\n</form>\n\n<div class=\"card shadow-sm\">\n  <div class=\"card-body p-0\">\n    <div class=\"table-responsive\">\n      <table class=\"table table-striped table-hover mb-0\">\n        <thead class=\"table-light\">\n          <tr>\n            <th>ID</th>\n            <th>Referans ID</th>\n            <th>Açıklama</th>\n            <th>Tamirde mi</th>\n            <th>Bakıma Gönderilme</th>\n            <th>Geri Dönme</th>\n            <th>Söküldüğü Makine</th>\n            <th>Sökülme Tarihi</th>\n            <th>Son Güncelleme</th>\n            <th class=\"text-end\">İşlemler</th>\n          </tr>\n        </thead>\n        <tbody>\n        {% for row in rows %}\n          <tr>\n            <td>{{ row[\"id\"] }}</td>\n            <td>{{ row[\"Referans ID\"] }}</td>\n            <td>{{ row[\"Açıklama\"] }}</td>\n            <td>{{ row[\"Tamirde mi\"] }}</td>\n            <td>{{ row[\"Bakıma Gönderilme\"] }}</td>\n            <td>{{ row[\"Geri Dönme\"] }}</td>\n            <td>{{ row[\"Söküldüğü Makine\"] }}</td>\n            <td>{{ row[\"Sökülme Tarihi\"] }}</td>\n            <td>{{ row[\"Son Güncelleme\"] }}</td>\n            <td class=\"text-end\">\n              <a href=\"{{ url_for('yedek_edit', record_id=row['id']) }}\" class=\"btn btn-sm btn-outline-primary\">Düzenle</a>\n              <form action=\"{{ url_for('yedek_delete', record_id=row['id']) }}\" method=\"post\" style=\"display:inline-block\" onsubmit=\"return confirm('Silmek istediğinize emin misiniz?');\">\n                <button class=\"btn btn-sm btn-outline-danger\" type=\"submit\">Sil</button>\n              </form>\n            </td>\n          </tr>\n        {% else %}\n          <tr>\n            <td colspan=\"10\" class=\"text-center py-3\">Kayıt bulunamadı.</td>\n          </tr>\n        {% endfor %}\n        </tbody>\n      </table>\n    </div>\n  </div>\n</div>\n{% endblock %}\n""",
    "yedek_form.html": """{% extends \"base.html\" %}\n{% block content %}\n<h4>{{ \"Yedek Ekle\" if mode == \"add\" else \"Yedek Düzenle\" }}</h4>\n\n<div class=\"card shadow-sm mt-3\">\n  <div class=\"card-body\">\n    <form method=\"post\">\n      <div class=\"mb-3\">\n        <label class=\"form-label\">Referans ID</label>\n        <input type=\"text\" name=\"Referans ID\" class=\"form-control\"\n               value=\"{{ record['Referans ID'] if record else '' }}\" required>\n      </div>\n\n      <div class=\"mb-3\">\n        <label class=\"form-label\">Açıklama</label>\n        <input type=\"text\" name=\"Açıklama\" class=\"form-control\"\n               value=\"{{ record['Açıklama'] if record else '' }}\">\n      </div>\n\n      <div class=\"mb-3\">\n        <label class=\"form-label\">Tamirde mi</label>\n        <select name=\"Tamirde mi\" class=\"form-select\">\n          {% set current = record['Tamirde mi'] if record else 'Hayır' %}\n          <option value=\"Evet\" {{ \"selected\" if current == \"Evet\" }}>Evet</option>\n          <option value=\"Hayır\" {{ \"selected\" if current == \"Hayır\" }}>Hayır</option>\n        </select>\n      </div>\n\n      <div class=\"mb-3\">\n        <label class=\"form-label\">Bakıma Gönderilme</label>\n        <input type=\"text\" name=\"Bakıma Gönderilme\" class=\"form-control\"\n               placeholder=\"gg-aa-yyyy\"\n               value=\"{% if record %}{{ record['Bakıma Gönderilme'] }}{% else %}{{ today }}{% endif %}\">\n      </div>\n\n      <div class=\"mb-3\">\n        <label class=\"form-label\">Geri Dönme</label>\n        <input type=\"text\" name=\"Geri Dönme\" class=\"form-control\"\n               placeholder=\"gg-aa-yyyy\"\n               value=\"{% if record %}{{ record['Geri Dönme'] }}{% else %}{{ today }}{% endif %}\">\n      </div>\n\n      <div class=\"mb-3\">\n        <label class=\"form-label\">Söküldüğü Makine</label>\n        <input type=\"text\" name=\"Söküldüğü Makine\" class=\"form-control\"\n               value=\"{{ record['Söküldüğü Makine'] if record else '' }}\">\n      </div>\n\n      <div class=\"mb-3\">\n        <label class=\"form-label\">Sökülme Tarihi</label>\n        <input type=\"text\" name=\"Sökülme Tarihi\" class=\"form-control\"\n               placeholder=\"gg-aa-yyyy\"\n               value=\"{% if record %}{{ record['Sökülme Tarihi'] }}{% else %}{{ today }}{% endif %}\">\n      </div>\n\n      <button type=\"submit\" class=\"btn btn-primary\">Kaydet</button>\n      <a href=\"{{ url_for('yedeks') }}\" class=\"btn btn-secondary\">İptal</a>\n    </form>\n  </div>\n</div>\n{% endblock %}\n""",
}


def resource_path(filename: str) -> str:
    return os.path.join(BASE_DIR, filename)


app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static"),
)
app.secret_key = os.environ.get("SECRET_KEY", "change_this_to_random_secret")


def ensure_template_exists(template_name: str) -> str:
    """Ensure a template file is present; recreate it from defaults if needed."""
    os.makedirs(resource_path("templates"), exist_ok=True)
    template_path = resource_path(os.path.join("templates", template_name))

    if not os.path.exists(template_path):
        default_content = DEFAULT_TEMPLATES.get(template_name)
        if default_content is None:
            raise FileNotFoundError(
                f"Beklenen şablon bulunamadı: {template_path}.\n"
                "Proje klasörünü eksiksiz kopyaladığınızdan ve 'templates' dizinini içerdiğinden emin olun."
            )

        with open(template_path, "w", encoding="utf-8") as file:
            file.write(default_content)

    return template_path


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
    missing_created = []
    for required_template in [
        "login.html",
        "spindles.html",
        "spindle_form.html",
        "yedeks.html",
        "yedek_form.html",
        "base.html",
    ]:
        template_path = ensure_template_exists(required_template)
        if os.path.exists(template_path) and required_template in DEFAULT_TEMPLATES:
            # If the file was freshly created, record it for the startup log.
            # We check file size to see whether it already existed with content.
            if os.path.getsize(template_path) == len(DEFAULT_TEMPLATES[required_template].encode("utf-8")):
                missing_created.append(template_path)

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    print(f"\n{APP_TITLE} çalışıyor.")
    print(f"Local:  http://localhost:{port}")
    if missing_created:
        print("\nAşağıdaki şablonlar eksikti, varsayılan içerikle oluşturuldu:")
        for created in missing_created:
            print(f" - {created}")

    print("LAN erişimi için bu makinenin IP'sini kullanın (örn. ipconfig > IPv4).")
    app.run(host=host, port=port, debug=True)
