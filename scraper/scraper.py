"""
MundialEnVivo AR — Scraper Automático Completo
Corre cada 2 horas via GitHub Actions
Actualiza:
  - Canales de TV (desde listas M3U)
  - Partidos del Mundial FIFA 2026
  - Grupos Libertadores 2026
  - Grupos Sudamericana 2026
"""

import requests
import re
import json
import os
import time
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, db as rtdb

# ══════════════════════════════════════════════════════════════════════════
#  CONEXIÓN FIREBASE
# ══════════════════════════════════════════════════════════════════════════
def conectar_firebase():
    try:
        sa = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        if not sa:
            raise Exception("No se encontró FIREBASE_SERVICE_ACCOUNT")
        cred = credentials.Certificate(json.loads(sa))
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://mundialenvivo-default-rtdb.firebaseio.com"
        })
        return rtdb.reference("/")
    except Exception as e:
        print(f"❌ Error Firebase: {e}")
        return None

# ══════════════════════════════════════════════════════════════════════════
#  CANALES DE TV
# ══════════════════════════════════════════════════════════════════════════
CANALES_FIJOS = [
    {"id":"c01","nombre":"TV Pública","categoria":"AIRE","url":"https://ola1.com.ar/tvp/index.m3u8","logo":"https://i.imgur.com/4hDCB1M.png","fallbacks":["https://www.youtube-nocookie.com/embed/live_stream?channel=UCj6PcyQrnc777S3S5n6F9eA&autoplay=1"]},
    {"id":"c02","nombre":"Telefe","categoria":"AIRE","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCZnFAF-hXiMV-BvhBv2KcPw&autoplay=1","logo":"https://i.imgur.com/WX0esjQ.png","fallbacks":[]},
    {"id":"c03","nombre":"América TV","categoria":"AIRE","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCONHhDxKSbKqXPLEMiL_LnQ&autoplay=1","logo":"https://i.imgur.com/YqTNXDf.png","fallbacks":["https://prepublish.f.qaotic.net/a07/americahls-100056/playlist_720p.m3u8"]},
    {"id":"c04","nombre":"El Trece","categoria":"AIRE","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCEgMuCKqMlBziFugJ_KXXSQ&autoplay=1","logo":"https://i.imgur.com/TrgBAdA.png","fallbacks":["https://live-01-02-eltrece.vodgc.net/eltrecetv/index.m3u8"]},
    {"id":"c05","nombre":"Canal 9 Litoral","categoria":"AIRE","url":"https://stream.arcast.live/ahora/ahora/playlist.m3u8","logo":"https://upload.wikimedia.org/wikipedia/commons/a/ad/Canal_9_Litoral_2021.png","fallbacks":[]},
    {"id":"c06","nombre":"Encuentro","categoria":"AIRE","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCW0_hNKzJmEpfI3AJQ7RVVg&autoplay=1","logo":"https://i.imgur.com/IyP2UIx.png","fallbacks":[]},
    {"id":"c07","nombre":"TyC Sports","categoria":"DEPORTES","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCo5RMRo3R3A9G-nFLn1QAYA&autoplay=1","logo":"https://i.imgur.com/5QDtnEW.png","fallbacks":["https://live-04-11-tyc24.vodgc.net/tyc24/index_tyc24_1080.m3u8"]},
    {"id":"c08","nombre":"DSports","categoria":"DEPORTES","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCPpnCA_1b-K4R1vGwU2gIew&autoplay=1","logo":"https://i.imgur.com/SFYhgrt.png","fallbacks":[]},
    {"id":"c09","nombre":"beIN Sports Xtra","categoria":"DEPORTES","url":"https://dc1644a9jazgj.cloudfront.net/beIN_Sports_Xtra_Espanol.m3u8","logo":"https://i.imgur.com/V562tpO.png","fallbacks":[]},
    {"id":"c10","nombre":"FIFA+ Español","categoria":"DEPORTES","url":"https://6c849fb3.wurl.com/master/f36d25e7e52f1ba8d7e56eb859c636563214f541/TEctbXhfRklGQVBsdXNTcGFuaXNoLTFfSExT/playlist.m3u8","logo":"https://i.imgur.com/FvEp1S2.png","fallbacks":[]},
    {"id":"c11","nombre":"DAZN Combat","categoria":"DEPORTES","url":"https://dazn-combat-rakuten.amagi.tv/hls/amagi_hls_data_rakutenAA-dazn-combat-rakuten/CDN/master.m3u8","logo":"https://i.postimg.cc/VsW3Jsrz/logo-DAZN-Combat.png","fallbacks":[]},
    {"id":"c12","nombre":"DeporTV","categoria":"DEPORTES","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCJQamPSBACMmFrK3QLuUxmw&autoplay=1","logo":"https://i.imgur.com/placeholder.png","fallbacks":["https://5fb24b460df87.streamlock.net/live-cont.ar/deportv/playlist.m3u8"]},
    # ── Bolaloca — canales deportivos embebibles ─────────────────────────
    {"id":"bola76","nombre":"ESPN Premium",  "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/76","logo":"https://i.imgur.com/JdqfPHX.png","fallbacks":[]},
    {"id":"bola77","nombre":"TyC Sports HD", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/77","logo":"https://i.imgur.com/5QDtnEW.png","fallbacks":[]},
    {"id":"bola78","nombre":"Fox Sports",    "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/78","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola79","nombre":"Fox Sports 2",  "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/79","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola80","nombre":"Fox Sports 3",  "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/80","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola81","nombre":"Deportes 81",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/81","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola82","nombre":"Deportes 82",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/82","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola83","nombre":"Deportes 83",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/83","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola84","nombre":"Deportes 84",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/84","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola85","nombre":"Deportes 85",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/85","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola86","nombre":"Deportes 86",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/86","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola87","nombre":"Deportes 87",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/87","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola88","nombre":"Deportes 88",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/88","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola89","nombre":"Deportes 89",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/89","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola90","nombre":"Deportes 90",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/90","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola91","nombre":"Deportes 91",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/91","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola92","nombre":"Deportes 92",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/92","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola93","nombre":"Deportes 93",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/93","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola94","nombre":"Deportes 94",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/94","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola95","nombre":"Deportes 95",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/95","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola96","nombre":"Deportes 96",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/96","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola97","nombre":"Deportes 97",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/97","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola98","nombre":"Deportes 98",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/98","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola99","nombre":"Deportes 99",   "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/99","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola100","nombre":"Deportes 100", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/100","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola101","nombre":"Deportes 101", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/101","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola102","nombre":"Deportes 102", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/102","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola103","nombre":"Deportes 103", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/103","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola104","nombre":"Deportes 104", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/104","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola105","nombre":"Deportes 105", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/105","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola106","nombre":"Deportes 106", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/106","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola107","nombre":"Deportes 107", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/107","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola108","nombre":"Deportes 108", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/108","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola109","nombre":"Deportes 109", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/109","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola110","nombre":"Deportes 110", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/110","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola111","nombre":"Deportes 111", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/111","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola112","nombre":"Deportes 112", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/112","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola113","nombre":"Deportes 113", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/113","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola114","nombre":"Deportes 114", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/114","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola115","nombre":"Deportes 115", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/115","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola116","nombre":"Deportes 116", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/116","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola117","nombre":"Deportes 117", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/117","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola118","nombre":"Deportes 118", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/118","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola119","nombre":"Deportes 119", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/119","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola120","nombre":"Deportes 120", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/120","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola121","nombre":"Deportes 121", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/121","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola122","nombre":"Deportes 122", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/122","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola123","nombre":"Deportes 123", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/123","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola124","nombre":"Deportes 124", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/124","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
    {"id":"bola125","nombre":"Deportes 125", "categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/125","logo":"https://i.imgur.com/placeholder.png","fallbacks":[]},
        # ── Bolaloca (50 canales deportes) ──────────────────────────────────
    {"id":"bol01","nombre":"Canal 76","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/76","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol02","nombre":"Canal 77","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/77","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol03","nombre":"Canal 78","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/78","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol04","nombre":"Canal 79","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/79","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol05","nombre":"Canal 80","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/80","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol06","nombre":"Canal 81","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/81","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol07","nombre":"Canal 82","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/82","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol08","nombre":"Canal 83","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/83","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol09","nombre":"Canal 84","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/84","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol10","nombre":"Canal 85","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/85","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol11","nombre":"Canal 86","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/86","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol12","nombre":"Canal 87","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/87","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol13","nombre":"Canal 88","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/88","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol14","nombre":"Canal 89","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/89","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol15","nombre":"Canal 90","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/90","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol16","nombre":"Canal 91","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/91","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol17","nombre":"Canal 92","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/92","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol18","nombre":"Canal 93","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/93","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol19","nombre":"Canal 94","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/94","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol20","nombre":"Canal 95","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/95","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol21","nombre":"Canal 96","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/96","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol22","nombre":"Canal 97","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/97","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol23","nombre":"Canal 98","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/98","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol24","nombre":"Canal 99","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/99","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol25","nombre":"Canal 100","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/100","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol26","nombre":"Canal 101","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/101","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol27","nombre":"Canal 102","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/102","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol28","nombre":"Canal 103","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/103","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol29","nombre":"Canal 104","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/104","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol30","nombre":"Canal 105","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/105","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol31","nombre":"Canal 106","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/106","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol32","nombre":"Canal 107","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/107","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol33","nombre":"Canal 108","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/108","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol34","nombre":"Canal 109","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/109","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol35","nombre":"Canal 110","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/110","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol36","nombre":"Canal 111","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/111","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol37","nombre":"Canal 112","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/112","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol38","nombre":"Canal 113","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/113","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol39","nombre":"Canal 114","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/114","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol40","nombre":"Canal 115","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/115","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol41","nombre":"Canal 116","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/116","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol42","nombre":"Canal 117","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/117","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol43","nombre":"Canal 118","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/118","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol44","nombre":"Canal 119","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/119","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol45","nombre":"Canal 120","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/120","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol46","nombre":"Canal 121","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/121","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol47","nombre":"Canal 122","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/122","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol48","nombre":"Canal 123","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/123","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol49","nombre":"Canal 124","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/124","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol50","nombre":"Canal 125","categoria":"DEPORTES","url":"https://bolaloca.my/player/capo/125","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"c13","nombre":"TN","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCEKv_4X5ER-3cLMhA5eN8tA&autoplay=1","logo":"https://i.imgur.com/CZ8LKmA.png","fallbacks":["https://mdstrm.com/live-stream-playlist/60b578b060947317de7b57ac.m3u8"]},
    {"id":"c14","nombre":"C5N","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCFjlSkMeNXvVPoPXf0oSWwg&autoplay=1","logo":"https://i.imgur.com/1l3t5jd.png","fallbacks":[]},
    {"id":"c15","nombre":"Canal 26","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCqC5sSVJgtCyxLNiCWgJxsQ&autoplay=1","logo":"https://i.imgur.com/bXHHtcb.png","fallbacks":["https://stream-gtlc.telecentro.net.ar/hls/canal26hls/main.m3u8"]},
    {"id":"c16","nombre":"A24","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCMXegZIiUQAMjvWSmRLZyiw&autoplay=1","logo":"https://i.imgur.com/Og17U9N.png","fallbacks":[]},
    {"id":"c17","nombre":"Crónica HD","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCSumMFNbHZDGqSmJsMQc2bQ&autoplay=1","logo":"https://i.imgur.com/agn47sQ.png","fallbacks":[]},
    {"id":"c18","nombre":"Canal E","categoria":"NOTICIAS","url":"https://unlimited1-us.dps.live/perfiltv/perfiltv.smil/playlist.m3u8","logo":"https://i.ibb.co/y4pkxH3/Qtc8-M2-PG-400x400.jpg","fallbacks":[]},
    {"id":"c19","nombre":"Cumbia Mix","categoria":"MUSICA","url":"https://cloud.tvomix.com/CUMBIAMIX/index.m3u8","logo":"https://qtrypzzcjebvfcihiynt.supabase.co/storage/v1/object/public/base44-prod/public/6901dfd41a05195b77301d7b/b306e57e4_Logo-TV-C.png","fallbacks":[]},
    {"id":"c20","nombre":"Pakapaka","categoria":"INFANTIL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCdh8IJMVRSu-eLFRLBLnPCg&autoplay=1","logo":"https://i.imgur.com/Q4zaCuM.png","fallbacks":[]},
]

def actualizar_canales(ref):
    print("\n📡 Actualizando canales...")
    ahora = datetime.utcnow().isoformat()
    data = {}
    for c in CANALES_FIJOS:
        data[c["id"]] = {
            "nombre":    c["nombre"],
            "url":       c["url"],
            "logo":      c["logo"],
            "categoria": c["categoria"],
            "fallbacks": c.get("fallbacks",[]),
            "fijo":      True,
            "actualizado": ahora,
        }
        print(f"  ✅ {c['nombre']}")
    ref.child("canales").set(data)
    print(f"  💾 {len(data)} canales guardados")

# ══════════════════════════════════════════════════════════════════════════
#  MUNDIAL FIFA 2026 — FIXTURE OFICIAL
# ══════════════════════════════════════════════════════════════════════════
MUNDIAL_PARTIDOS = [
    # GRUPO A
    {"id":"ga01","grupo":"A","local":"México","visitante":"Sudáfrica","bandera_local":"🇲🇽","bandera_visitante":"🇿🇦","fecha":"2026-06-11","hora":"16:00","sede":"Estadio Ciudad de México"},
    {"id":"ga02","grupo":"A","local":"Corea del Sur","visitante":"Por definir","bandera_local":"🇰🇷","bandera_visitante":"🏳️","fecha":"2026-06-11","hora":"23:00","sede":"Estadio Guadalajara"},
    {"id":"ga03","grupo":"A","local":"Sudáfrica","visitante":"Por definir","bandera_local":"🇿🇦","bandera_visitante":"🏳️","fecha":"2026-06-18","hora":"13:00","sede":"Atlanta Stadium"},
    {"id":"ga04","grupo":"A","local":"México","visitante":"Corea del Sur","bandera_local":"🇲🇽","bandera_visitante":"🇰🇷","fecha":"2026-06-19","hora":"22:00","sede":"Estadio Guadalajara"},
    {"id":"ga05","grupo":"A","local":"México","visitante":"Por definir","bandera_local":"🇲🇽","bandera_visitante":"🏳️","fecha":"2026-06-25","hora":"20:00","sede":"Dallas Stadium"},
    {"id":"ga06","grupo":"A","local":"Sudáfrica","visitante":"Corea del Sur","bandera_local":"🇿🇦","bandera_visitante":"🇰🇷","fecha":"2026-06-25","hora":"20:00","sede":"Kansas City Stadium"},
    # GRUPO B
    {"id":"gb01","grupo":"B","local":"Canadá","visitante":"Por definir (Europa)","bandera_local":"🇨🇦","bandera_visitante":"🏳️","fecha":"2026-06-12","hora":"16:00","sede":"Toronto Stadium"},
    {"id":"gb02","grupo":"B","local":"Qatar","visitante":"Suiza","bandera_local":"🇶🇦","bandera_visitante":"🇨🇭","fecha":"2026-06-13","hora":"16:00","sede":"San Francisco Bay Area"},
    {"id":"gb03","grupo":"B","local":"Suiza","visitante":"Por definir (Europa)","bandera_local":"🇨🇭","bandera_visitante":"🏳️","fecha":"2026-06-18","hora":"16:00","sede":"Los Angeles Stadium"},
    {"id":"gb04","grupo":"B","local":"Canadá","visitante":"Qatar","bandera_local":"🇨🇦","bandera_visitante":"🇶🇦","fecha":"2026-06-18","hora":"19:00","sede":"BC Place Vancouver"},
    {"id":"gb05","grupo":"B","local":"Canadá","visitante":"Suiza","bandera_local":"🇨🇦","bandera_visitante":"🇨🇭","fecha":"2026-06-26","hora":"20:00","sede":"Toronto Stadium"},
    {"id":"gb06","grupo":"B","local":"Qatar","visitante":"Por definir (Europa)","bandera_local":"🇶🇦","bandera_visitante":"🏳️","fecha":"2026-06-26","hora":"20:00","sede":"San Francisco Bay Area"},
    # GRUPO C
    {"id":"gc01","grupo":"C","local":"Brasil","visitante":"Marruecos","bandera_local":"🇧🇷","bandera_visitante":"🇲🇦","fecha":"2026-06-13","hora":"19:00","sede":"Nueva York New Jersey"},
    {"id":"gc02","grupo":"C","local":"Haití","visitante":"Escocia","bandera_local":"🇭🇹","bandera_visitante":"🏴󠁧󠁢󠁳󠁣󠁴󠁿","fecha":"2026-06-13","hora":"22:00","sede":"Boston Stadium"},
    {"id":"gc03","grupo":"C","local":"Brasil","visitante":"Haití","bandera_local":"🇧🇷","bandera_visitante":"🇭🇹","fecha":"2026-06-19","hora":"16:00","sede":"Miami Stadium"},
    {"id":"gc04","grupo":"C","local":"Marruecos","visitante":"Escocia","bandera_local":"🇲🇦","bandera_visitante":"🏴󠁧󠁢󠁳󠁣󠁴󠁿","fecha":"2026-06-19","hora":"19:00","sede":"Atlanta Stadium"},
    {"id":"gc05","grupo":"C","local":"Brasil","visitante":"Escocia","bandera_local":"🇧🇷","bandera_visitante":"🏴󠁧󠁢󠁳󠁣󠁴󠁿","fecha":"2026-06-26","hora":"20:00","sede":"Nueva York New Jersey"},
    {"id":"gc06","grupo":"C","local":"Marruecos","visitante":"Haití","bandera_local":"🇲🇦","bandera_visitante":"🇭🇹","fecha":"2026-06-26","hora":"20:00","sede":"Boston Stadium"},
    # GRUPO D
    {"id":"gd01","grupo":"D","local":"Estados Unidos","visitante":"Paraguay","bandera_local":"🇺🇸","bandera_visitante":"🇵🇾","fecha":"2026-06-12","hora":"22:00","sede":"Los Angeles Stadium"},
    {"id":"gd02","grupo":"D","local":"Australia","visitante":"Por definir (Europa)","bandera_local":"🇦🇺","bandera_visitante":"🏳️","fecha":"2026-06-13","hora":"01:00","sede":"BC Place Vancouver"},
    {"id":"gd03","grupo":"D","local":"Estados Unidos","visitante":"Australia","bandera_local":"🇺🇸","bandera_visitante":"🇦🇺","fecha":"2026-06-18","hora":"22:00","sede":"Dallas Stadium"},
    {"id":"gd04","grupo":"D","local":"Paraguay","visitante":"Por definir (Europa)","bandera_local":"🇵🇾","bandera_visitante":"🏳️","fecha":"2026-06-19","hora":"01:00","sede":"San Francisco Bay Area"},
    {"id":"gd05","grupo":"D","local":"Estados Unidos","visitante":"Por definir (Europa)","bandera_local":"🇺🇸","bandera_visitante":"🏳️","fecha":"2026-06-26","hora":"20:00","sede":"Philadelphia Stadium"},
    {"id":"gd06","grupo":"D","local":"Paraguay","visitante":"Australia","bandera_local":"🇵🇾","bandera_visitante":"🇦🇺","fecha":"2026-06-26","hora":"20:00","sede":"Houston Stadium"},
    # GRUPO E
    {"id":"ge01","grupo":"E","local":"Alemania","visitante":"Curazao","bandera_local":"🇩🇪","bandera_visitante":"🇨🇼","fecha":"2026-06-14","hora":"14:00","sede":"Houston Stadium"},
    {"id":"ge02","grupo":"E","local":"Costa de Marfil","visitante":"Ecuador","bandera_local":"🇨🇮","bandera_visitante":"🇪🇨","fecha":"2026-06-14","hora":"20:00","sede":"Philadelphia Stadium"},
    {"id":"ge03","grupo":"E","local":"Alemania","visitante":"Costa de Marfil","bandera_local":"🇩🇪","bandera_visitante":"🇨🇮","fecha":"2026-06-19","hora":"13:00","sede":"Seattle Stadium"},
    {"id":"ge04","grupo":"E","local":"Curazao","visitante":"Ecuador","bandera_local":"🇨🇼","bandera_visitante":"🇪🇨","fecha":"2026-06-19","hora":"22:00","sede":"Houston Stadium"},
    {"id":"ge05","grupo":"E","local":"Alemania","visitante":"Ecuador","bandera_local":"🇩🇪","bandera_visitante":"🇪🇨","fecha":"2026-06-27","hora":"20:00","sede":"Dallas Stadium"},
    {"id":"ge06","grupo":"E","local":"Costa de Marfil","visitante":"Curazao","bandera_local":"🇨🇮","bandera_visitante":"🇨🇼","fecha":"2026-06-27","hora":"20:00","sede":"Atlanta Stadium"},
    # GRUPO F
    {"id":"gf01","grupo":"F","local":"Países Bajos","visitante":"Japón","bandera_local":"🇳🇱","bandera_visitante":"🇯🇵","fecha":"2026-06-14","hora":"17:00","sede":"Dallas Stadium"},
    {"id":"gf02","grupo":"F","local":"Por definir (Europa)","visitante":"Túnez","bandera_local":"🏳️","bandera_visitante":"🇹🇳","fecha":"2026-06-14","hora":"23:00","sede":"Estadio Monterrey"},
    {"id":"gf03","grupo":"F","local":"Países Bajos","visitante":"Por definir (Europa)","bandera_local":"🇳🇱","bandera_visitante":"🏳️","fecha":"2026-06-20","hora":"16:00","sede":"Philadelphia Stadium"},
    {"id":"gf04","grupo":"F","local":"Túnez","visitante":"Japón","bandera_local":"🇹🇳","bandera_visitante":"🇯🇵","fecha":"2026-06-21","hora":"01:00","sede":"Estadio Monterrey"},
    {"id":"gf05","grupo":"F","local":"Países Bajos","visitante":"Túnez","bandera_local":"🇳🇱","bandera_visitante":"🇹🇳","fecha":"2026-06-27","hora":"20:00","sede":"Seattle Stadium"},
    {"id":"gf06","grupo":"F","local":"Por definir (Europa)","visitante":"Japón","bandera_local":"🏳️","bandera_visitante":"🇯🇵","fecha":"2026-06-27","hora":"20:00","sede":"Boston Stadium"},
    # GRUPO G
    {"id":"gg01","grupo":"G","local":"Bélgica","visitante":"Egipto","bandera_local":"🇧🇪","bandera_visitante":"🇪🇬","fecha":"2026-06-15","hora":"16:00","sede":"Seattle Stadium"},
    {"id":"gg02","grupo":"G","local":"Irán","visitante":"Nueva Zelanda","bandera_local":"🇮🇷","bandera_visitante":"🇳🇿","fecha":"2026-06-15","hora":"22:00","sede":"Los Angeles Stadium"},
    {"id":"gg03","grupo":"G","local":"Bélgica","visitante":"Irán","bandera_local":"🇧🇪","bandera_visitante":"🇮🇷","fecha":"2026-06-20","hora":"19:00","sede":"Miami Stadium"},
    {"id":"gg04","grupo":"G","local":"Egipto","visitante":"Nueva Zelanda","bandera_local":"🇪🇬","bandera_visitante":"🇳🇿","fecha":"2026-06-20","hora":"22:00","sede":"Dallas Stadium"},
    {"id":"gg05","grupo":"G","local":"Bélgica","visitante":"Nueva Zelanda","bandera_local":"🇧🇪","bandera_visitante":"🇳🇿","fecha":"2026-06-27","hora":"20:00","sede":"Kansas City Stadium"},
    {"id":"gg06","grupo":"G","local":"Egipto","visitante":"Irán","bandera_local":"🇪🇬","bandera_visitante":"🇮🇷","fecha":"2026-06-27","hora":"20:00","sede":"Seattle Stadium"},
    # GRUPO H
    {"id":"gh01","grupo":"H","local":"España","visitante":"Cabo Verde","bandera_local":"🇪🇸","bandera_visitante":"🇨🇻","fecha":"2026-06-15","hora":"13:00","sede":"Atlanta Stadium"},
    {"id":"gh02","grupo":"H","local":"Arabia Saudita","visitante":"Uruguay","bandera_local":"🇸🇦","bandera_visitante":"🇺🇾","fecha":"2026-06-15","hora":"19:00","sede":"Miami Stadium"},
    {"id":"gh03","grupo":"H","local":"España","visitante":"Arabia Saudita","bandera_local":"🇪🇸","bandera_visitante":"🇸🇦","fecha":"2026-06-20","hora":"13:00","sede":"Dallas Stadium"},
    {"id":"gh04","grupo":"H","local":"Cabo Verde","visitante":"Uruguay","bandera_local":"🇨🇻","bandera_visitante":"🇺🇾","fecha":"2026-06-21","hora":"01:00","sede":"Atlanta Stadium"},
    {"id":"gh05","grupo":"H","local":"España","visitante":"Uruguay","bandera_local":"🇪🇸","bandera_visitante":"🇺🇾","fecha":"2026-06-28","hora":"20:00","sede":"Miami Stadium"},
    {"id":"gh06","grupo":"H","local":"Arabia Saudita","visitante":"Cabo Verde","bandera_local":"🇸🇦","bandera_visitante":"🇨🇻","fecha":"2026-06-28","hora":"20:00","sede":"Atlanta Stadium"},
    # GRUPO I
    {"id":"gi01","grupo":"I","local":"Francia","visitante":"Senegal","bandera_local":"🇫🇷","bandera_visitante":"🇸🇳","fecha":"2026-06-16","hora":"16:00","sede":"Nueva York New Jersey"},
    {"id":"gi02","grupo":"I","local":"Repechaje 2","visitante":"Noruega","bandera_local":"🏳️","bandera_visitante":"🇳🇴","fecha":"2026-06-16","hora":"19:00","sede":"Boston Stadium"},
    {"id":"gi03","grupo":"I","local":"Francia","visitante":"Repechaje 2","bandera_local":"🇫🇷","bandera_visitante":"🏳️","fecha":"2026-06-21","hora":"16:00","sede":"Miami Stadium"},
    {"id":"gi04","grupo":"I","local":"Senegal","visitante":"Noruega","bandera_local":"🇸🇳","bandera_visitante":"🇳🇴","fecha":"2026-06-21","hora":"20:00","sede":"Nueva York New Jersey"},
    {"id":"gi05","grupo":"I","local":"Francia","visitante":"Noruega","bandera_local":"🇫🇷","bandera_visitante":"🇳🇴","fecha":"2026-06-28","hora":"20:00","sede":"Boston Stadium"},
    {"id":"gi06","grupo":"I","local":"Senegal","visitante":"Repechaje 2","bandera_local":"🇸🇳","bandera_visitante":"🏳️","fecha":"2026-06-28","hora":"20:00","sede":"Nueva York New Jersey"},
    # GRUPO J — ARGENTINA
    {"id":"gj01","grupo":"J","local":"Argentina","visitante":"Argelia","bandera_local":"🇦🇷","bandera_visitante":"🇩🇿","fecha":"2026-06-16","hora":"22:00","sede":"Kansas City Stadium"},
    {"id":"gj02","grupo":"J","local":"Austria","visitante":"Jordania","bandera_local":"🇦🇹","bandera_visitante":"🇯🇴","fecha":"2026-06-17","hora":"01:00","sede":"San Francisco Bay Area"},
    {"id":"gj03","grupo":"J","local":"Argentina","visitante":"Austria","bandera_local":"🇦🇷","bandera_visitante":"🇦🇹","fecha":"2026-06-21","hora":"19:00","sede":"Philadelphia Stadium"},
    {"id":"gj04","grupo":"J","local":"Argelia","visitante":"Jordania","bandera_local":"🇩🇿","bandera_visitante":"🇯🇴","fecha":"2026-06-22","hora":"01:00","sede":"Kansas City Stadium"},
    {"id":"gj05","grupo":"J","local":"Argentina","visitante":"Jordania","bandera_local":"🇦🇷","bandera_visitante":"🇯🇴","fecha":"2026-06-29","hora":"20:00","sede":"Miami Stadium"},
    {"id":"gj06","grupo":"J","local":"Argelia","visitante":"Austria","bandera_local":"🇩🇿","bandera_visitante":"🇦🇹","fecha":"2026-06-29","hora":"20:00","sede":"Boston Stadium"},
    # GRUPO K
    {"id":"gk01","grupo":"K","local":"Portugal","visitante":"Repechaje 1","bandera_local":"🇵🇹","bandera_visitante":"🏳️","fecha":"2026-06-17","hora":"14:00","sede":"Houston Stadium"},
    {"id":"gk02","grupo":"K","local":"Uzbekistán","visitante":"Colombia","bandera_local":"🇺🇿","bandera_visitante":"🇨🇴","fecha":"2026-06-17","hora":"23:00","sede":"Estadio Ciudad de México"},
    {"id":"gk03","grupo":"K","local":"Portugal","visitante":"Uzbekistán","bandera_local":"🇵🇹","bandera_visitante":"🇺🇿","fecha":"2026-06-22","hora":"16:00","sede":"Boston Stadium"},
    {"id":"gk04","grupo":"K","local":"Repechaje 1","visitante":"Colombia","bandera_local":"🏳️","bandera_visitante":"🇨🇴","fecha":"2026-06-22","hora":"22:00","sede":"Houston Stadium"},
    {"id":"gk05","grupo":"K","local":"Portugal","visitante":"Colombia","bandera_local":"🇵🇹","bandera_visitante":"🇨🇴","fecha":"2026-06-29","hora":"20:00","sede":"Estadio Ciudad de México"},
    {"id":"gk06","grupo":"K","local":"Uzbekistán","visitante":"Repechaje 1","bandera_local":"🇺🇿","bandera_visitante":"🏳️","fecha":"2026-06-29","hora":"20:00","sede":"Dallas Stadium"},
    # GRUPO L
    {"id":"gl01","grupo":"L","local":"Inglaterra","visitante":"Croacia","bandera_local":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","bandera_visitante":"🇭🇷","fecha":"2026-06-17","hora":"17:00","sede":"Dallas Stadium"},
    {"id":"gl02","grupo":"L","local":"Ghana","visitante":"Panamá","bandera_local":"🇬🇭","bandera_visitante":"🇵🇦","fecha":"2026-06-17","hora":"20:00","sede":"Toronto Stadium"},
    {"id":"gl03","grupo":"L","local":"Inglaterra","visitante":"Ghana","bandera_local":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","bandera_visitante":"🇬🇭","fecha":"2026-06-22","hora":"19:00","sede":"Nueva York New Jersey"},
    {"id":"gl04","grupo":"L","local":"Croacia","visitante":"Panamá","bandera_local":"🇭🇷","bandera_visitante":"🇵🇦","fecha":"2026-06-23","hora":"01:00","sede":"Seattle Stadium"},
    {"id":"gl05","grupo":"L","local":"Inglaterra","visitante":"Panamá","bandera_local":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","bandera_visitante":"🇵🇦","fecha":"2026-06-30","hora":"20:00","sede":"Dallas Stadium"},
    {"id":"gl06","grupo":"L","local":"Croacia","visitante":"Ghana","bandera_local":"🇭🇷","bandera_visitante":"🇬🇭","fecha":"2026-06-30","hora":"20:00","sede":"Toronto Stadium"},
]

def actualizar_mundial(ref):
    print("\n🌍 Actualizando Mundial 2026...")
    ahora = datetime.utcnow().isoformat()
    data = {}
    for p in MUNDIAL_PARTIDOS:
        pid = p["id"]
        # Preservar goles si ya existen en Firebase
        try:
            existing = ref.child(f"partidos/{pid}").get()
            goles_local     = existing.get("goles_local")     if existing else None
            goles_visitante = existing.get("goles_visitante") if existing else None
            estado          = existing.get("estado","PRÓXIMO") if existing else "PRÓXIMO"
        except Exception:
            goles_local = goles_visitante = None
            estado = "PRÓXIMO"

        data[pid] = {
            "grupo":             p["grupo"],
            "local":             p["local"],
            "visitante":         p["visitante"],
            "bandera_local":     p["bandera_local"],
            "bandera_visitante": p["bandera_visitante"],
            "fecha":             p["fecha"],
            "hora":              p["hora"],
            "sede":              p.get("sede",""),
            "estado":            estado,
            "goles_local":       goles_local,
            "goles_visitante":   goles_visitante,
            "actualizado":       ahora,
        }
    ref.child("partidos").set(data)
    print(f"  💾 {len(data)} partidos del Mundial guardados")

# ══════════════════════════════════════════════════════════════════════════
#  LIBERTADORES 2026
# ══════════════════════════════════════════════════════════════════════════
LIBERTADORES_GRUPOS = {
    "A": [
        {"nombre":"Flamengo",              "pais":"Brasil",   "bandera":"🇧🇷"},
        {"nombre":"Estudiantes LP",        "pais":"Argentina","bandera":"🇦🇷"},
        {"nombre":"Ind. Medellín",         "pais":"Colombia", "bandera":"🇨🇴"},
        {"nombre":"Cusco FC",              "pais":"Perú",     "bandera":"🇵🇪"},
    ],
    "B": [
        {"nombre":"Nacional",              "pais":"Uruguay",  "bandera":"🇺🇾"},
        {"nombre":"Coquimbo Unido",        "pais":"Chile",    "bandera":"🇨🇱"},
        {"nombre":"Deportes Tolima",       "pais":"Colombia", "bandera":"🇨🇴"},
        {"nombre":"Universitario",         "pais":"Perú",     "bandera":"🇵🇪"},
    ],
    "C": [
        {"nombre":"Bolívar",               "pais":"Bolivia",  "bandera":"🇧🇴"},
        {"nombre":"Ind. Rivadavia",        "pais":"Argentina","bandera":"🇦🇷"},
        {"nombre":"Dep. La Guaira",        "pais":"Venezuela","bandera":"🇻🇪"},
        {"nombre":"Athletico Paranaense",  "pais":"Brasil",   "bandera":"🇧🇷"},
    ],
    "D": [
        {"nombre":"Boca Juniors",          "pais":"Argentina","bandera":"🇦🇷"},
        {"nombre":"Cruzeiro",              "pais":"Brasil",   "bandera":"🇧🇷"},
        {"nombre":"Universidad Católica",  "pais":"Chile",    "bandera":"🇨🇱"},
        {"nombre":"Barcelona SC",          "pais":"Ecuador",  "bandera":"🇪🇨"},
    ],
    "E": [
        {"nombre":"Peñarol",               "pais":"Uruguay",  "bandera":"🇺🇾"},
        {"nombre":"Corinthians",           "pais":"Brasil",   "bandera":"🇧🇷"},
        {"nombre":"Santa Fe",              "pais":"Colombia", "bandera":"🇨🇴"},
        {"nombre":"Platense",              "pais":"Argentina","bandera":"🇦🇷"},
    ],
    "F": [
        {"nombre":"Palmeiras",             "pais":"Brasil",   "bandera":"🇧🇷"},
        {"nombre":"Cerro Porteño",         "pais":"Paraguay", "bandera":"🇵🇾"},
        {"nombre":"Junior",                "pais":"Colombia", "bandera":"🇨🇴"},
        {"nombre":"Sporting Cristal",      "pais":"Perú",     "bandera":"🇵🇪"},
    ],
    "G": [
        {"nombre":"Liga de Quito",         "pais":"Ecuador",  "bandera":"🇪🇨"},
        {"nombre":"Lanús",                 "pais":"Argentina","bandera":"🇦🇷"},
        {"nombre":"Always Ready",          "pais":"Bolivia",  "bandera":"🇧🇴"},
        {"nombre":"Mirassol",              "pais":"Brasil",   "bandera":"🇧🇷"},
    ],
    "H": [
        {"nombre":"Ind. del Valle",        "pais":"Ecuador",  "bandera":"🇪🇨"},
        {"nombre":"Libertad",              "pais":"Paraguay", "bandera":"🇵🇾"},
        {"nombre":"Rosario Central",       "pais":"Argentina","bandera":"🇦🇷"},
        {"nombre":"Universidad Central",   "pais":"Venezuela","bandera":"🇻🇪"},
    ],
}

SUDAMERICANA_GRUPOS = {
    "A": [
        {"nombre":"América de Cali",       "pais":"Colombia", "bandera":"🇨🇴"},
        {"nombre":"Tigre",                 "pais":"Argentina","bandera":"🇦🇷"},
        {"nombre":"Macará",                "pais":"Ecuador",  "bandera":"🇪🇨"},
        {"nombre":"Alianza Atlético",      "pais":"Perú",     "bandera":"🇵🇪"},
    ],
    "B": [
        {"nombre":"Atlético Mineiro",      "pais":"Brasil",   "bandera":"🇧🇷"},
        {"nombre":"Cienciano",             "pais":"Perú",     "bandera":"🇵🇪"},
        {"nombre":"Acad. Puerto Cabello",  "pais":"Venezuela","bandera":"🇻🇪"},
        {"nombre":"Juventud",              "pais":"Uruguay",  "bandera":"🇺🇾"},
    ],
    "C": [
        {"nombre":"San Pablo",             "pais":"Brasil",   "bandera":"🇧🇷"},
        {"nombre":"Millonarios",           "pais":"Colombia", "bandera":"🇨🇴"},
        {"nombre":"Boston River",          "pais":"Uruguay",  "bandera":"🇺🇾"},
        {"nombre":"O'Higgins",             "pais":"Chile",    "bandera":"🇨🇱"},
    ],
    "D": [
        {"nombre":"Santos",                "pais":"Brasil",   "bandera":"🇧🇷"},
        {"nombre":"San Lorenzo",           "pais":"Argentina","bandera":"🇦🇷"},
        {"nombre":"Dep. Cuenca",           "pais":"Ecuador",  "bandera":"🇪🇨"},
        {"nombre":"Recoleta",              "pais":"Paraguay", "bandera":"🇵🇾"},
    ],
    "E": [
        {"nombre":"Racing",                "pais":"Argentina","bandera":"🇦🇷"},
        {"nombre":"Caracas FC",            "pais":"Venezuela","bandera":"🇻🇪"},
        {"nombre":"Independiente",         "pais":"Bolivia",  "bandera":"🇧🇴"},
        {"nombre":"Botafogo",              "pais":"Brasil",   "bandera":"🇧🇷"},
    ],
    "F": [
        {"nombre":"Gremio",                "pais":"Brasil",   "bandera":"🇧🇷"},
        {"nombre":"Palestino",             "pais":"Chile",    "bandera":"🇨🇱"},
        {"nombre":"City Torque",           "pais":"Uruguay",  "bandera":"🇺🇾"},
        {"nombre":"Dep. Riestra",          "pais":"Argentina","bandera":"🇦🇷"},
    ],
    "G": [
        {"nombre":"Olimpia",               "pais":"Paraguay", "bandera":"🇵🇾"},
        {"nombre":"Vasco da Gama",         "pais":"Brasil",   "bandera":"🇧🇷"},
        {"nombre":"Audax Italiano",        "pais":"Chile",    "bandera":"🇨🇱"},
        {"nombre":"Barracas Central",      "pais":"Argentina","bandera":"🇦🇷"},
    ],
    "H": [
        {"nombre":"River Plate",           "pais":"Argentina","bandera":"🇦🇷"},
        {"nombre":"RB Bragantino",         "pais":"Brasil",   "bandera":"🇧🇷"},
        {"nombre":"Blooming",              "pais":"Bolivia",  "bandera":"🇧🇴"},
        {"nombre":"Carabobo",              "pais":"Venezuela","bandera":"🇻🇪"},
    ],
}

def actualizar_conmebol(ref):
    print("\n🏆 Actualizando CONMEBOL...")
    ahora = datetime.utcnow().isoformat()

    # Libertadores — preservar partidos y resultados si ya existen
    try:
        existing_lib = ref.child("libertadores").get() or {}
    except Exception:
        existing_lib = {}

    lib_data = {
        "grupos": {g: {"equipos": eqs} for g, eqs in LIBERTADORES_GRUPOS.items()},
        "partidos": existing_lib.get("partidos", {}),
        "bracket":  existing_lib.get("bracket", {}),
        "calendario": {
            "fecha1_inicio":  "2026-04-07",
            "fecha6_fin":     "2026-05-28",
            "octavos_ida":    "2026-08-11",
            "octavos_vuelta": "2026-08-18",
            "cuartos_ida":    "2026-09-08",
            "cuartos_vuelta": "2026-09-15",
            "semis_ida":      "2026-10-13",
            "semis_vuelta":   "2026-10-20",
            "final":          "2026-11-28",
            "sede_final":     "Estadio Centenario, Montevideo",
        },
        "actualizado": ahora,
    }
    ref.child("libertadores").set(lib_data)
    print("  💾 Libertadores guardada (8 grupos)")

    # Sudamericana
    try:
        existing_sud = ref.child("sudamericana").get() or {}
    except Exception:
        existing_sud = {}

    sud_data = {
        "grupos": {g: {"equipos": eqs} for g, eqs in SUDAMERICANA_GRUPOS.items()},
        "partidos": existing_sud.get("partidos", {}),
        "bracket":  existing_sud.get("bracket", {}),
        "calendario": {
            "fecha1_inicio": "2026-04-07",
            "fecha6_fin":    "2026-05-28",
            "octavos_ida":   "2026-08-11",
            "final":         "2026-11-21",
            "sede_final":    "Por confirmar",
        },
        "actualizado": ahora,
    }
    ref.child("sudamericana").set(sud_data)
    print("  💾 Sudamericana guardada (8 grupos)")

    # Recopa
    ref.child("recopa").set({
        "descripcion": "Se disputará entre el campeón de Libertadores 2026 y el campeón de Sudamericana 2026",
        "final_libertadores": "2026-11-28",
        "final_sudamericana": "2026-11-21",
        "sede_recopa": "2027 - Por confirmar",
        "actualizado": ahora,
    })
    print("  💾 Recopa guardada")

# ══════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 55)
    print("  🏆 MundialEnVivo AR — Scraper Automático Completo")
    print(f"  🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 55)

    ref = conectar_firebase()
    if not ref:
        exit(1)

    actualizar_canales(ref)
    actualizar_mundial(ref)
    actualizar_conmebol(ref)

    print("\n" + "=" * 55)
    print("  ✅ TODO ACTUALIZADO EN FIREBASE")
    print("=" * 55)

if __name__ == "__main__":
    main()