import glob
import os
import shutil
import sqlite3

patterns = [
    r'C:\Users\user\AppData\Local\Google\Chrome\User Data\*\History',
    r'C:\Users\user\AppData\Local\Microsoft\Edge\User Data\*\History',
    r'C:\Users\user\AppData\Local\Yandex\YandexBrowser\User Data\*\History',
    r'C:\Users\user\AppData\Roaming\Mozilla\Firefox\Profiles\*\places.sqlite',
]

for pat in patterns:
    for p in glob.glob(pat):
        print("Checking:", p)
        tmp = "scratch_hist.db"
        try:
            shutil.copyfile(p, tmp)
            conn = sqlite3.connect(tmp)
            cur = conn.cursor()
            if "places.sqlite" in p:
                cur.execute("SELECT url, title FROM moz_places WHERE url LIKE '%youtube.com/watch%' ORDER BY id DESC LIMIT 5")
            else:
                cur.execute("SELECT url, title FROM urls WHERE url LIKE '%youtube.com/watch%' ORDER BY id DESC LIMIT 5")
            for row in cur.fetchall():
                print("Found:", row)
            conn.close()
            os.remove(tmp)
        except Exception as e:
            print("Error on", p, e)
