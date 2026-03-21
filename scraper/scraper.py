"""
MundialEnVivo AR - Scraper automático
Corre cada 2 horas via GitHub Actions
- Escanea listas M3U públicas de Argentina
- Verifica cada stream
- Actualiza Firebase Realtime Database
"""

import requests
import re
import json
import os
import time
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, db as rtdb

def conectar_firebase():
    try:
        service_account = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        if not service_account:
            raise Exception("No se encontró FIREBASE_SERVICE_ACCOUNT")
        cred_dict = json.loads(service_account)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://mundialenvivo-default-rtdb.firebaseio.com"
        })
        return rtdb.reference("/")
    except Exception as e:
        print(f"❌ Error conectando Firebase: {e}")
        return None

# ── Canales fijos con YouTube como respaldo ───────────────────────────────
CANALES_FIJOS = [
    {"id":"c01","nombre":"TV Pública","categoria":"AIRE",
     "url":"https://ola1.com.ar/tvp/index.m3u8",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/TV_P%C3%BAblica_Argentina_logo_2022.svg/200px-TV_P%C3%BAblica_Argentina_logo_2022.svg.png",
     "fallbacks":["https://www.youtube.com/embed/live_stream?channel=UCj6PcyQrnc777S3S5n6F9eA&autoplay=1"]},
    {"id":"c02","nombre":"Telefe","categoria":"AIRE",
     "url":"https://www.youtube.com/embed/live_stream?channel=UCZnFAF-hXiMV-BvhBv2KcPw&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Telefe_2020.svg/200px-Telefe_2020.svg.png",
     "fallbacks":[]},
    {"id":"c03","nombre":"América TV","categoria":"AIRE",
     "url":"https://www.youtube.com/embed/live_stream?channel=UCONHhDxKSbKqXPLEMiL_LnQ&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Am%C3%A9rica_TV_%28Nuevo_logo_Junio_2020%29.png/200px-Am%C3%A9rica_TV_%28Nuevo_logo_Junio_2020%29.png",
     "fallbacks":["https://prepublish.f.qaotic.net/a07/americahls-100056/playlist_720p.m3u8"]},
    {"id":"c04","nombre":"El Trece","categoria":"AIRE",
     "url":"https://www.youtube.com/embed/live_stream?channel=UCEgMuCKqMlBziFugJ_KXXSQ&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/El_Trece_2020_logo.svg/200px-El_Trece_2020_logo.svg.png",
     "fallbacks":["https://live-01-02-eltrece.vodgc.net/eltrecetv/index.m3u8"]},
    {"id":"c05","nombre":"Canal 9 Litoral","categoria":"AIRE",
     "url":"https://stream.arcast.live/ahora/ahora/playlist.m3u8",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/a/ad/Canal_9_Litoral_2021.png",
     "fallbacks":[]},
    {"id":"c06","nombre":"Encuentro","categoria":"AIRE",
     "url":"https://www.youtube.com/embed/live_stream?channel=UCW0_hNKzJmEpfI3AJQ7RVVg&autoplay=1",
     "logo":"https://i.imgur.com/IyP2UIx.png","fallbacks":[]},
    {"id":"c07","nombre":"TyC Sports","categoria":"DEPORTES",
     "url":"https://www.youtube.com/embed/live_stream?channel=UCo5RMRo3R3A9G-nFLn1QAYA&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/TyC_Sports_logo.svg/200px-TyC_Sports_logo.svg.png",
     "fallbacks":["https://live-04-11-tyc24.vodgc.net/tyc24/index_tyc24_1080.m3u8"]},
    {"id":"c08","nombre":"DSports","categoria":"DEPORTES",
     "url":"https://www.youtube.com/embed/live_stream?channel=UCPpnCA_1b-K4R1vGwU2gIew&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/DSports_logo.svg/200px-DSports_logo.svg.png",
     "fallbacks":[]},
    {"id":"c09","nombre":"beIN Sports Xtra","categoria":"DEPORTES",
     "url":"https://dc1644a9jazgj.cloudfront.net/beIN_Sports_Xtra_Espanol.m3u8",
     "logo":"https://i.imgur.com/V562tpO.png","fallbacks":[]},
    {"id":"c10","nombre":"FIFA+ Español","categoria":"DEPORTES",
     "url":"https://6c849fb3.wurl.com/master/f36d25e7e52f1ba8d7e56eb859c636563214f541/TEctbXhfRklGQVBsdXNTcGFuaXNoLTFfSExT/playlist.m3u8",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/FIFA%2B_%282025%29.svg/200px-FIFA%2B_%282025%29.svg.png",
     "fallbacks":[]},
    {"id":"c11","nombre":"DAZN Combat","categoria":"DEPORTES",
     "url":"https://dazn-combat-rakuten.amagi.tv/hls/amagi_hls_data_rakutenAA-dazn-combat-rakuten/CDN/master.m3u8",
     "logo":"https://i.postimg.cc/VsW3Jsrz/logo-DAZN-Combat.png","fallbacks":[]},
    {"id":"c12","nombre":"Alkass One","categoria":"DEPORTES",
     "url":"https://liveeu-gcp.alkassdigital.net/alkass1-p/main.m3u8",
     "logo":"https://i.imgur.com/10mmlha.png",
     "fallbacks":["https://liveeu-gcp.alkassdigital.net/alkass2-p/main.m3u8"]},
    {"id":"c13","nombre":"Alkass Two","categoria":"DEPORTES",
     "url":"https://liveeu-gcp.alkassdigital.net/alkass2-p/main.m3u8",
     "logo":"https://i.imgur.com/8w61kFX.png","fallbacks":[]},
    {"id":"c14","nombre":"Alkass Three","categoria":"DEPORTES",
     "url":"https://liveeu-gcp.alkassdigital.net/alkass3-p/main.m3u8",
     "logo":"https://i.imgur.com/d57BdFh.png","fallbacks":[]},
    {"id":"c15","nombre":"TN","categoria":"NOTICIAS",
     "url":"https://www.youtube.com/embed/live_stream?channel=UCEKv_4X5ER-3cLMhA5eN8tA&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/TN_-_Todo_Noticias_logo_%282020%29.svg/200px-TN_-_Todo_Noticias_logo_%282020%29.svg.png",
     "fallbacks":["https://mdstrm.com/live-stream-playlist/60b578b060947317de7b57ac.m3u8"]},
    {"id":"c16","nombre":"C5N","categoria":"NOTICIAS",
     "url":"https://www.youtube.com/embed/live_stream?channel=UCFjlSkMeNXvVPoPXf0oSWwg&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/C5N_logo.svg/200px-C5N_logo.svg.png",
     "fallbacks":[]},
    {"id":"c17","nombre":"Canal 26","categoria":"NOTICIAS",
     "url":"https://www.youtube.com/embed/live_stream?channel=UCqC5sSVJgtCyxLNiCWgJxsQ&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Canal_26_logo_%282022%29.svg/200px-Canal_26_logo_%282022%29.svg.png",
     "fallbacks":["https://stream-gtlc.telecentro.net.ar/hls/canal26hls/main.m3u8"]},
    {"id":"c18","nombre":"A24","categoria":"NOTICIAS",
     "url":"https://www.youtube.com/embed/live_stream?channel=UCMXegZIiUQAMjvWSmRLZyiw&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/A24_TV_logo.svg/200px-A24_TV_logo.svg.png",
     "fallbacks":[]},
    {"id":"c19","nombre":"Crónica HD","categoria":"NOTICIAS",
     "url":"https://www.youtube.com/embed/live_stream?channel=UCSumMFNbHZDGqSmJsMQc2bQ&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Cr%C3%B3nica_HD_logo.svg/200px-Cr%C3%B3nica_HD_logo.svg.png",
     "fallbacks":[]},
    {"id":"c20","nombre":"Canal E","categoria":"NOTICIAS",
     "url":"https://unlimited1-us.dps.live/perfiltv/perfiltv.smil/playlist.m3u8",
     "logo":"https://i.ibb.co/y4pkxH3/Qtc8-M2-PG-400x400.jpg","fallbacks":[]},
    {"id":"c21","nombre":"Cumbia Mix","categoria":"MUSICA",
     "url":"https://cloud.tvomix.com/CUMBIAMIX/index.m3u8",
     "logo":"https://qtrypzzcjebvfcihiynt.supabase.co/storage/v1/object/public/base44-prod/public/6901dfd41a05195b77301d7b/b306e57e4_Logo-TV-C.png",
     "fallbacks":[]},
    {"id":"c22","nombre":"Pakapaka","categoria":"INFANTIL",
     "url":"https://www.youtube.com/embed/live_stream?channel=UCdh8IJMVRSu-eLFRLBLnPCg&autoplay=1",
     "logo":"https://i.imgur.com/Q4zaCuM.png","fallbacks":[]},
]

FUENTES_M3U   = ["https://iptv-org.github.io/iptv/countries/ar.m3u"]
PALABRAS_CLAVE = ["TELEFE","TV PUBLICA","CANAL 9","AMERICA","TN ","C5N","ESPN",
                  "FOX SPORTS","DSPORTS","TNT","DEPORTV","LN+","A24","CRONICA",
                  "CANAL 26","CANAL 7","CANAL 10","CANAL 13","EL TRECE","TYCSPORTS"]

def verificar_url(url, timeout=5):
    if "youtube.com" in url or "embed" in url:
        return True
    try:
        h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.head(url, timeout=timeout, headers=h, allow_redirects=True)
        if r.status_code < 400: return True
        r = requests.get(url, timeout=timeout, headers=h, stream=True)
        r.close()
        return r.status_code < 400
    except Exception:
        return False

def limpiar_nombre(n):
    n = re.sub(r'[\(\[].*?[\)\]]', '', n)
    n = re.sub(r'\b(HD|FHD|4K|SD|720|1080|480|360)\b', '', n, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', n).strip()

def categorizar(n):
    n = n.upper()
    if any(x in n for x in ["ESPN","TYC","FOX","DSPORT","TNT","DEPORTV","BEIN","FIFA"]): return "DEPORTES"
    if any(x in n for x in ["TN ","C5N","LN+","A24","CRONICA","CANAL 26","INFOBAE"]): return "NOTICIAS"
    if any(x in n for x in ["PAKAPAKA","DISNEY","CARTOON","NICKELODEON"]): return "INFANTIL"
    if any(x in n for x in ["CUMBIA","MUSICA","HITS"]): return "MUSICA"
    return "AIRE"

def buscar_canales_m3u():
    print("\n🔍 Escaneando listas M3U...")
    nombres_fijos = {c["nombre"].upper() for c in CANALES_FIJOS}
    encontrados   = []

    for fuente in FUENTES_M3U:
        try:
            print(f"  📥 {fuente}")
            r = requests.get(fuente, timeout=15)
            if r.status_code != 200: continue
            matches = re.findall(r'tvg-logo="(.*?)".*?,(.*?)\n(https?.*?\.m3u8)', r.text)
            print(f"  🧪 {len(matches)} streams")
            for logo, nombre, url in matches:
                nu = nombre.strip().upper()
                if not url.startswith("https"): continue
                if not any(pc in nu for pc in PALABRAS_CLAVE): continue
                nl = limpiar_nombre(nombre.strip())
                if nl.upper() in nombres_fijos: continue
                encontrados.append({
                    "nombre": nl, "url": url.strip(),
                    "logo": logo.strip().replace("http://","https://"),
                    "categoria": categorizar(nl),
                })
        except Exception as e:
            print(f"  ❌ {e}")
    return encontrados

def actualizar_firebase(ref, fijos, extra):
    print("\n💾 Actualizando Firebase...")
    ahora = datetime.utcnow().isoformat()
    data  = {}

    for canal in fijos:
        ok = verificar_url(canal["url"])
        print(f"  {'✅' if ok else '⚠️ '} {canal['nombre']}")
        data[canal["id"]] = {
            "nombre":    canal["nombre"],   "url":       canal["url"],
            "logo":      canal["logo"],     "categoria": canal["categoria"],
            "fallbacks": canal.get("fallbacks", []),
            "verificado": ok, "fijo": True, "actualizado": ahora,
        }
        time.sleep(0.2)

    idx = len(fijos) + 1
    procesados = set()
    for canal in extra:
        key = re.sub(r'[^a-z0-9]', '', canal["nombre"].lower())
        if key in procesados or not key: continue
        data[f"m{idx:03d}"] = {
            "nombre":    canal["nombre"],   "url":       canal["url"],
            "logo":      canal["logo"],     "categoria": canal["categoria"],
            "fallbacks": [], "verificado": False, "fijo": False, "actualizado": ahora,
        }
        procesados.add(key)
        idx += 1

    ref.child("canales").set(data)
    print(f"\n✅ {len(data)} canales guardados en Firebase")
    return len(data)

def main():
    print("=" * 50)
    print("  🏆 MundialEnVivo AR — Scraper Automático")
    print(f"  🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 50)

    ref = conectar_firebase()
    if not ref: exit(1)

    extra = buscar_canales_m3u()
    total = actualizar_firebase(ref, CANALES_FIJOS, extra)

    print(f"\n{'='*50}")
    print(f"  ✅ COMPLETADO — {total} canales en Firebase")
    print("=" * 50)

if __name__ == "__main__":
    main()