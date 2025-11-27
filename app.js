const path = require('path');
const fs = require('fs');
const os = require('os');
const express = require('express');
const expressLayouts = require('express-ejs-layouts');
const session = require('express-session');
const { parse } = require('csv-parse/sync');
const { stringify } = require('csv-stringify/sync');

const APP_TITLE = 'STS - Spindle Takip Sistemi (Web)';
const USERNAME = 'BAKIM';
const PASSWORD = 'MAXIME';
const app = express();

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(expressLayouts);
app.set('layout', path.join('layouts', 'base'));
app.use(express.urlencoded({ extended: true }));
app.use(
  session({
    secret: process.env.SESSION_SECRET || 'change_this_secret',
    resave: false,
    saveUninitialized: false,
  })
);

function flashMiddleware(req, res, next) {
  const store = req.session.flash || {};
  req.session.flash = store;

  req.flash = (type, message) => {
    if (!store[type]) {
      store[type] = [];
    }
    store[type].push(message);
  };

  res.locals.flash = (type) => {
    const messages = store[type] || [];
    delete store[type];
    return messages;
  };

  next();
}

app.use(flashMiddleware);

app.use((req, res, next) => {
  res.locals.appTitle = APP_TITLE;
  res.locals.session = req.session;
  next();
});

function formatDate(date = new Date()) {
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  return `${day}-${month}-${year}`;
}

class DataManager {
  constructor(filename, headers) {
    this.filepath = path.join(__dirname, filename);
    this.headers = headers;
    this.ensureFile();
  }

  ensureFile() {
    if (!fs.existsSync(this.filepath)) {
      const csv = stringify([], { header: true, columns: this.headers });
      fs.writeFileSync(this.filepath, csv, 'utf8');
    }
  }

  readAll() {
    const content = fs.readFileSync(this.filepath, 'utf8');
    if (!content.trim()) {
      return [];
    }
    const rows = parse(content, { columns: true, skip_empty_lines: true });
    return rows.map((row) => {
      const normalized = {};
      this.headers.forEach((header) => {
        normalized[header] = row[header] ?? '';
      });
      return normalized;
    });
  }

  writeAll(rows) {
    const csv = stringify(rows, { header: true, columns: this.headers });
    fs.writeFileSync(this.filepath, csv, 'utf8');
  }

  nextId(rows) {
    if (!rows.length) {
      return 1;
    }
    return Math.max(...rows.map((row) => Number(row.id))) + 1;
  }

  addRecord(data) {
    const rows = this.readAll();
    const id = String(this.nextId(rows));
    rows.push({ id, ...data });
    this.writeAll(rows);
    return id;
  }

  updateRecord(recordId, data) {
    const rows = this.readAll();
    let updated = false;
    const newRows = rows.map((row) => {
      if (row.id === recordId) {
        updated = true;
        return { ...row, ...data };
      }
      return row;
    });
    if (updated) {
      this.writeAll(newRows);
    }
    return updated;
  }

  deleteRecord(recordId) {
    const rows = this.readAll();
    const filtered = rows.filter((row) => row.id !== recordId);
    const deleted = filtered.length !== rows.length;
    if (deleted) {
      this.writeAll(filtered);
    }
    return deleted;
  }

  search(filters) {
    const rows = this.readAll();
    return rows.filter((row) => {
      return Object.entries(filters).every(([key, value]) => {
        if (!value || !value.trim()) {
          return true;
        }
        return row[key]?.toLowerCase().includes(value.toLowerCase());
      });
    });
  }

  all() {
    return this.readAll();
  }
}

const spindleManager = new DataManager('spindle_data.csv', [
  'id',
  'Referans ID',
  'Çalışma Saati',
  'Takılı Olduğu Makine',
  'Makinaya Takıldığı Tarih',
  'Son Güncelleme',
]);

const yedekManager = new DataManager('yedek_data.csv', [
  'id',
  'Referans ID',
  'Açıklama',
  'Tamirde mi',
  'Bakıma Gönderilme',
  'Geri Dönme',
  'Söküldüğü Makine',
  'Sökülme Tarihi',
  'Son Güncelleme',
]);

function requireLogin(req, res, next) {
  if (req.session.loggedIn) {
    return next();
  }
  return res.redirect('/login');
}

app.get('/login', (req, res) => {
  res.render('login');
});

app.post('/login', (req, res) => {
  const username = (req.body.username || '').trim();
  const password = (req.body.password || '').trim();

  if (username === USERNAME && password === PASSWORD) {
    req.session.loggedIn = true;
    req.session.username = username;
    req.flash('success', 'Giriş başarılı.');
    return res.redirect('/spindles');
  }

  req.flash('danger', 'Kullanıcı adı veya şifre hatalı.');
  return res.redirect('/login');
});

app.get('/logout', (req, res) => {
  req.session.destroy(() => {
    res.redirect('/login');
  });
});

app.get('/', requireLogin, (req, res) => {
  res.redirect('/spindles');
});

app.get('/spindles', requireLogin, (req, res) => {
  const query = (req.query.q || '').trim();
  const rows = query
    ? spindleManager.search({ 'Referans ID': query })
    : spindleManager.all();

  res.render('spindles', { rows, query });
});

app.get('/spindles/add', requireLogin, (req, res) => {
  res.render('spindle_form', { mode: 'add', record: null, today: formatDate() });
});

app.post('/spindles/add', requireLogin, (req, res) => {
  const referansId = (req.body['Referans ID'] || '').trim();

  if (!referansId) {
    req.flash('danger', 'Referans ID zorunludur.');
    return res.redirect('/spindles/add');
  }

  const data = {
    'Referans ID': referansId,
    'Çalışma Saati': (req.body['Çalışma Saati'] || '').trim(),
    'Takılı Olduğu Makine': (req.body['Takılı Olduğu Makine'] || '').trim(),
    'Makinaya Takıldığı Tarih':
      (req.body['Makinaya Takıldığı Tarih'] || '').trim() || formatDate(),
    'Son Güncelleme': formatDate(),
  };

  spindleManager.addRecord(data);
  req.flash('success', 'Spindle kaydı eklendi.');
  res.redirect('/spindles');
});

app.get('/spindles/:id/edit', requireLogin, (req, res) => {
  const rows = spindleManager.all();
  const record = rows.find((row) => row.id === req.params.id);

  if (!record) {
    req.flash('danger', 'Kayıt bulunamadı.');
    return res.redirect('/spindles');
  }

  res.render('spindle_form', { mode: 'edit', record, today: formatDate() });
});

app.post('/spindles/:id/edit', requireLogin, (req, res) => {
  const referansId = (req.body['Referans ID'] || '').trim();

  if (!referansId) {
    req.flash('danger', 'Referans ID zorunludur.');
    return res.redirect(`/spindles/${req.params.id}/edit`);
  }

  const updated = {
    'Referans ID': referansId,
    'Çalışma Saati': (req.body['Çalışma Saati'] || '').trim(),
    'Takılı Olduğu Makine': (req.body['Takılı Olduğu Makine'] || '').trim(),
    'Makinaya Takıldığı Tarih': (req.body['Makinaya Takıldığı Tarih'] || '').trim(),
    'Son Güncelleme': formatDate(),
  };

  spindleManager.updateRecord(req.params.id, updated);
  req.flash('success', 'Spindle kaydı güncellendi.');
  res.redirect('/spindles');
});

app.post('/spindles/:id/delete', requireLogin, (req, res) => {
  if (spindleManager.deleteRecord(req.params.id)) {
    req.flash('success', 'Spindle kaydı silindi.');
  } else {
    req.flash('danger', 'Kayıt silinemedi.');
  }
  res.redirect('/spindles');
});

app.get('/yedeks', requireLogin, (req, res) => {
  const query = (req.query.q || '').trim();
  const rows = query ? yedekManager.search({ 'Referans ID': query }) : yedekManager.all();
  res.render('yedeks', { rows, query });
});

app.get('/yedeks/add', requireLogin, (req, res) => {
  res.render('yedek_form', { mode: 'add', record: null, today: formatDate() });
});

app.post('/yedeks/add', requireLogin, (req, res) => {
  const referansId = (req.body['Referans ID'] || '').trim();

  if (!referansId) {
    req.flash('danger', 'Referans ID zorunludur.');
    return res.redirect('/yedeks/add');
  }

  const today = formatDate();
  const data = {
    'Referans ID': referansId,
    'Açıklama': (req.body['Açıklama'] || '').trim(),
    'Tamirde mi': (req.body['Tamirde mi'] || '').trim(),
    'Bakıma Gönderilme': (req.body['Bakıma Gönderilme'] || '').trim() || today,
    'Geri Dönme': (req.body['Geri Dönme'] || '').trim() || today,
    'Söküldüğü Makine': (req.body['Söküldüğü Makine'] || '').trim(),
    'Sökülme Tarihi': (req.body['Sökülme Tarihi'] || '').trim() || today,
    'Son Güncelleme': today,
  };

  yedekManager.addRecord(data);
  req.flash('success', 'Yedek kaydı eklendi.');
  res.redirect('/yedeks');
});

app.get('/yedeks/:id/edit', requireLogin, (req, res) => {
  const rows = yedekManager.all();
  const record = rows.find((row) => row.id === req.params.id);

  if (!record) {
    req.flash('danger', 'Kayıt bulunamadı.');
    return res.redirect('/yedeks');
  }

  res.render('yedek_form', { mode: 'edit', record, today: formatDate() });
});

app.post('/yedeks/:id/edit', requireLogin, (req, res) => {
  const referansId = (req.body['Referans ID'] || '').trim();

  if (!referansId) {
    req.flash('danger', 'Referans ID zorunludur.');
    return res.redirect(`/yedeks/${req.params.id}/edit`);
  }

  const updated = {
    'Referans ID': referansId,
    'Açıklama': (req.body['Açıklama'] || '').trim(),
    'Tamirde mi': (req.body['Tamirde mi'] || '').trim(),
    'Bakıma Gönderilme': (req.body['Bakıma Gönderilme'] || '').trim(),
    'Geri Dönme': (req.body['Geri Dönme'] || '').trim(),
    'Söküldüğü Makine': (req.body['Söküldüğü Makine'] || '').trim(),
    'Sökülme Tarihi': (req.body['Sökülme Tarihi'] || '').trim(),
    'Son Güncelleme': formatDate(),
  };

  yedekManager.updateRecord(req.params.id, updated);
  req.flash('success', 'Yedek kaydı güncellendi.');
  res.redirect('/yedeks');
});

app.post('/yedeks/:id/delete', requireLogin, (req, res) => {
  if (yedekManager.deleteRecord(req.params.id)) {
    req.flash('success', 'Yedek kaydı silindi.');
  } else {
    req.flash('danger', 'Kayıt silinemedi.');
  }
  res.redirect('/yedeks');
});

app.get('/export', requireLogin, (req, res) => {
  const spindleRows = spindleManager.all();
  const yedekRows = yedekManager.all();

  const lines = [];
  lines.push(['--- Spindle Takip ---']);
  lines.push([
    'Referans ID',
    'Saat',
    'Takılı Olduğu Makine',
    'Takıldığı Tarih',
    'Son Güncelleme',
  ]);
  spindleRows.forEach((row) => {
    lines.push([
      row['Referans ID'] || '',
      row['Çalışma Saati'] || '',
      row['Takılı Olduğu Makine'] || '',
      row['Makinaya Takıldığı Tarih'] || '',
      row['Son Güncelleme'] || '',
    ]);
  });
  lines.push([]);
  lines.push(['--- Yedek Takip ---']);
  lines.push([
    'Referans ID',
    'Açıklama',
    'Tamirde',
    'Gönderildi',
    'Dönen',
    'Söküldüğü Makine',
    'Sökülme Tarihi',
    'Son Güncelleme',
  ]);
  yedekRows.forEach((row) => {
    lines.push([
      row['Referans ID'] || '',
      row['Açıklama'] || '',
      row['Tamirde mi'] || '',
      row['Bakıma Gönderilme'] || '',
      row['Geri Dönme'] || '',
      row['Söküldüğü Makine'] || '',
      row['Sökülme Tarihi'] || '',
      row['Son Güncelleme'] || '',
    ]);
  });

  const csv = stringify(lines);
  res.header('Content-Type', 'text/csv');
  res.attachment('takip_export.csv');
  res.send(csv);
});

function listAddresses(host, port) {
  const nets = os.networkInterfaces();
  const addresses = [];

  Object.values(nets).forEach((iface) => {
    iface?.forEach((details) => {
      if (details.family === 'IPv4' && !details.internal) {
        addresses.push(details.address);
      }
    });
  });

  console.log('Available LAN addresses:');
  if (!addresses.length) {
    console.log('  (none detected)');
    console.log(`Try http://${host}:${port}`);
    return;
  }

  addresses.forEach((addr) => {
    console.log(`  http://${addr}:${port}`);
  });
}

const HOST = process.env.HOST || '0.0.0.0';
const PORT = Number(process.env.PORT) || 5000;

app.listen(PORT, HOST, () => {
  console.log(`${APP_TITLE} çalışıyor.`);
  console.log(`Local:  http://localhost:${PORT}`);
  listAddresses(HOST, PORT);
});
