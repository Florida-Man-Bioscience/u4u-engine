import sqlite3
try:
    conn = sqlite3.connect("data/rsid_cache.db")
    cur = conn.cursor()
    cur.execute("SELECT rsid FROM rsid_cache")
    rsids = [r[0] for r in cur.fetchall()]
    print(rsids)
except Exception as e:
    print(e)
