import psycopg2

# Konfigurasi koneksi ke database
conn = psycopg2.connect(database='plat_nomor',
                        user='postgres',
                        password='Sanyhasany0908',
                        host='localhost', port='5432')
cur = conn.cursor()

# Membuat tabel hasil_deteksi
def hasil_deteksi():
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hasil_deteksi(
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            hasil_pembacaan TEXT,
            timestamp TIMESTAMPTZ DEFAULT NOW() -- This adds a timestamp field with the current timestamp
        );
    """)
    conn.commit()