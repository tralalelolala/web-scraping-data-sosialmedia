# Threads Dynamic Web Scraper

Proyek ini adalah otomasi *web scraping* berbasis Python menggunakan **Playwright** untuk mengekstrak data dari platform *Single Page Application* (SPA) Threads. Proyek ini mendemonstrasikan penanganan elemen dinamis, *infinite scroll*, dan pembersihan data teks yang kotor.

## 📌 Informasi Target & Strategi
*   **Target Uji Coba:** `https://www.threads.net/@zuck` (Akun publik Mark Zuckerberg).
*   **Strategi Navigasi:** Menggunakan Playwright dalam mode *headless* yang disamarkan dengan *User-Agent* spesifik dan *Viewport* resolusi desktop agar tidak terdeteksi sebagai peramban bot konvensional.
*   **Logika Infinite Scroll:** Memanfaatkan evaluasi JavaScript `window.scrollBy` ke dasar dokumen diiringi dengan jeda asinkron acak (`random.uniform(2.5, 5.0)` detik) untuk meniru perilaku *human scrolling*. Proteksi batas maksimum scroll diterapkan (maksimal 20 *scroll attempts*) guna mencegah skrip terjebak *infinite loop*.
*   **Pemrosesan Elemen Dinamis:** Alih-alih mengandalkan class CSS yang dihasilkan secara acak (obfuscated CSS), skrip ini menggunakan lokator berbasis *Role* (seperti `article`) dan atribut baku (`data-pressable-container="true"`, `time[datetime]`) serta metode `wait_for_selector` untuk memastikan konten telah teresolusi secara asinkron.

## 🛡️ Analisis Tantangan Anti-Scraping
1.  **Rate-Limiting & IP Blocking:** Threads memonitor kecepatan permintaan data. Menggunakan jeda antar-scroll acak (2 hingga 5 detik) sangat krusial untuk mencegah pemblokiran.
2.  **Dynamic DOM & Obfuscated Classes:** Karena platform berbasis React, nama class (misal: `css-1v...`) berubah setiap rilis. Solusinya adalah menargetkan atribut HTML standar seperti `<time>`, *role* ARIA, atau properti direktif (`dir="auto"`).
3.  **Akses Tanpa Login:** Threads membatasi tampilan jika pengguna tidak *login*. Skrip difokuskan untuk mengakses halaman profil publik terlebih dahulu yang memiliki proteksi *login-wall* lebih longgar, dan prosesnya dihentikan tepat sebelum *modal pop-up login* memblokir DOM utama.

## 📊 Sampel Output (Data Cleaning)

### Sebelum Pembersihan (Raw Data)
*   Timestamp: `2j` atau `2023-11-01T14:30:00.000Z`
*   Konten: `Ini adalah post pertama. \n\n\n    Halo!   `
*   Metrik: `1,2 rb suka`

### Sesudah Pembersihan (Clean Data)
*   Timestamp: `2023-11-01 14:30:00` (Standar ISO 8601)
*   Konten: `Ini adalah post pertama. \n Halo!` (Hapus line break ganda dan *trim* spasi)
*   Metrik: `1200` (Tipe integer numerik murni)