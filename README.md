# Cyber Pathfinder & Grid Duel

Aplikasi web interaktif untuk memvisualisasikan algoritma navigasi agen cerdas (Pathfinding) dan bermain mini game strategi turn-based kompetitif melawan AI Guardian. Proyek ini dikembangkan menggunakan **Python Flask** di backend dan **HTML/CSS/JS** kustom premium di frontend.

---

## Fitur Utama

1. **Simulasi Navigasi Agen Cerdas**:
   - Pilihan algoritma pencarian rute: **A\* Search** (dengan Heuristik Manhattan/Euclidean), **Dijkstra's Algorithm**, **Breadth-First Search (BFS)**, dan **Depth-First Search (DFS)**.
   - Pilihan ukuran grid dinamis: 5x5, 8x8, 10x10, 12x12, dan 15x15.
   - Menggambar dinding rintangan (Walls) secara interaktif dengan menahan klik dan menggeser mouse.
   - Menggeser posisi Start (Robot) dan Goal (Bintang) dengan drag-and-drop.
   - Kontrol kecepatan simulasi dan pelacakan statistik rute secara real-time.

2. **Mini Game Strategi Turn-Based ("Tactical Guardian Duel")**:
   - Terpicu secara otomatis saat agen mencapai titik tujuan (Goal) atau melalui tombol langsung.
   - Menggunakan sistem pertarungan taktis 5x5 dengan pool 3 AP (Action Points) per giliran.
   - Pilihan aksi: **Move** (1 AP), **Shield** (1 AP), **Attack** (2 AP), dan **Heal** (2 AP, dengan cooldown 2 turn).
   - **Kecerdasan Buatan (AI) Guardian**: Logika pengambilan keputusan AI dijalankan pada server backend Python menggunakan analisis utilitas heuristik berbasis aksi untuk memaksimalkan performa mengalahkan pemain secara kompetitif.

---

## Struktur Direktori

```text
Project/
│
├── app.py                 # Backend Flask & Algoritma AI
├── README.md              # Panduan Penggunaan Aplikasi
│
├── templates/
│   └── index.html         # Struktur UI Utama
│
└── static/
    ├── css/
    │   └── style.css      # Desain Visual & Animasi
    └── js/
        └── main.js        # Logika Klien & Kontrol Interaksi UI
```

---

## Cara Menjalankan Aplikasi

Aplikasi server Flask Anda saat ini **sedang berjalan di latar belakang**. Anda dapat langsung membukanya di browser:
👉 [http://127.0.0.1:5000](http://127.0.0.1:5000)

Jika ingin menjalankannya secara manual di kemudian hari:

1. Buka terminal/PowerShell di direktori proyek ini:
   ```bash
   python app.py
   ```
2. Buka browser dan arahkan ke alamat `http://127.0.0.1:5000`.

---

## Cara Bermain Mini Game

Ketika agen Anda mencapai titik Goal, sebuah modal game akan muncul:
- **Giliran Anda**: Anda memiliki 3 AP. Anda dapat memilih tombol aksi di panel strategi kanan, lalu mengklik grid arena untuk melaksanakannya.
  - *Move:* Klik MOVE, lalu klik sel tetangga yang disorot biru untuk bergerak (1 AP).
  - *Attack:* Klik ATTACK, lalu klik sel Guardian (jika berjarak maksimal 1 sel) untuk menyerang (2 AP).
  - *Shield:* Klik SHIELD untuk mengaktifkan perisai penahan damage 50% (1 AP).
  - *Heal:* Klik HEAL untuk memulihkan 25 HP (2 AP, cooldown 2 turn).
- **Giliran AI**: Setelah AP Anda habis, giliran beralih secara otomatis. AI Guardian akan bertindak pintar dengan menghitung kombinasi langkah terbaik dari server backend Flask.
- **Kondisi Menang**: Kalahkan AI Guardian (HP = 0) untuk mengamankan wilayah tujuan!
