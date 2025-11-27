# Spindle Web App (Flask)

LAN üzerinden tarayıcıdan erişilebilen, CSV tabanlı spindle ve yedek takip uygulaması.

## Kurulum
1) Python 3.10+ kurulu olduğundan emin olun.
2) Bağımlılıkları kurun:
   ```bash
   pip install flask
   ```
3) Sunucuyu başlatın (tüm arayüzlere dinler, LAN'den ulaşılabilir):
   ```bash
   python app.py
   ```
   > Not: `templates/` klasörü aynı dizinde olmalı; repo klasöründen çalıştırdığınızdan emin olun.

4) Konsolda yerel URL'yi görürsünüz (`http://localhost:5000`). Aynı ağdaki başka cihazdan erişmek için bu makinenin IPv4 adresini kullanın:
   ```
   http://<LAN_IP>:5000/login
   örn: http://192.168.1.13:5000/login
   ```
5) Varsayılan giriş bilgileri:
   - Kullanıcı adı: `BAKIM`
   - Şifre: `MAXIME`

> "127.0.0.1 refused to connect" hatası görürseniz, erişmeye çalıştığınız cihazın kendi kendisine bağlanmaya çalıştığı anlamına gelir. Sunucuyu çalıştıran bilgisayarın IPv4 adresini (örn. `ipconfig` çıktısındaki aktif adaptörün `IPv4 Address` değeri) kullanın ve güvenlik duvarının 5000 portuna izin verdiğinden emin olun.

## Özellikler
- Giriş korumalı spindle/yedek listeleri
- Referans ID ile arama
- Ekleme / düzenleme / silme
- CSV rapor dışa aktarımı (`/export`)
- Bootstrap ile hızlı arayüz
