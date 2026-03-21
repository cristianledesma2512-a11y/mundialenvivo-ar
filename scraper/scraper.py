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
    # ── AIRE ─────────────────────────────────────────────────────────────
    {"id":"c01","nombre":"TV Pública","categoria":"AIRE",
     "url":"https://ola1.com.ar/tvp/index.m3u8",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Logo_Televisi%C3%B3n_P%C3%BAblica_Argentina.svg/200px-Logo_Televisi%C3%B3n_P%C3%BAblica_Argentina.svg.png",
     "fallbacks":["https://www.youtube-nocookie.com/embed/live_stream?channel=UCj6PcyQrnc777S3S5n6F9eA&autoplay=1"]},
    {"id":"c02","nombre":"Telefe","categoria":"AIRE",
     "url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCZnFAF-hXiMV-BvhBv2KcPw&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Telefe_2020.svg/200px-Telefe_2020.svg.png",
     "fallbacks":[]},
    {"id":"c03","nombre":"América TV","categoria":"AIRE",
     "url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCONHhDxKSbKqXPLEMiL_LnQ&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Am%C3%A9rica_TV_%28Nuevo_logo_Junio_2020%29.png/200px-Am%C3%A9rica_TV_%28Nuevo_logo_Junio_2020%29.png",
     "fallbacks":["https://prepublish.f.qaotic.net/a07/americahls-100056/playlist_720p.m3u8"]},
    {"id":"c04","nombre":"El Trece","categoria":"AIRE",
     "url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCEgMuCKqMlBziFugJ_KXXSQ&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/El_Trece_2020_logo.svg/200px-El_Trece_2020_logo.svg.png",
     "fallbacks":["https://live-01-02-eltrece.vodgc.net/eltrecetv/index.m3u8"]},
    {"id":"c05","nombre":"Canal 9 Litoral","categoria":"AIRE",
     "url":"https://stream.arcast.live/ahora/ahora/playlist.m3u8",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/a/ad/Canal_9_Litoral_2021.png",
     "fallbacks":[]},
    {"id":"c06","nombre":"Encuentro","categoria":"AIRE",
     "url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCW0_hNKzJmEpfI3AJQ7RVVg&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Canal_Encuentro_logo.svg/200px-Canal_Encuentro_logo.svg.png",
     "fallbacks":[]},
    # ── DEPORTES ──────────────────────────────────────────────────────────
    {"id":"c07","nombre":"TyC Sports","categoria":"DEPORTES",
     "url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCo5RMRo3R3A9G-nFLn1QAYA&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/TyC_Sports_logo.svg/200px-TyC_Sports_logo.svg.png",
     "fallbacks":["https://live-04-11-tyc24.vodgc.net/tyc24/index_tyc24_1080.m3u8"]},
    {"id":"c08","nombre":"DSports","categoria":"DEPORTES",
     "url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCPpnCA_1b-K4R1vGwU2gIew&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/DSports_logo.svg/200px-DSports_logo.svg.png",
     "fallbacks":[]},
    {"id":"c09","nombre":"beIN Sports Xtra","categoria":"DEPORTES",
     "url":"https://dc1644a9jazgj.cloudfront.net/beIN_Sports_Xtra_Espanol.m3u8",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/BeIN_Sports_logo.svg/200px-BeIN_Sports_logo.svg.png",
     "fallbacks":[]},
    {"id":"c10","nombre":"FIFA+ Español","categoria":"DEPORTES",
     "url":"https://6c849fb3.wurl.com/master/f36d25e7e52f1ba8d7e56eb859c636563214f541/TEctbXhfRklGQVBsdXNTcGFuaXNoLTFfSExT/playlist.m3u8",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/FIFA%2B_%282025%29.svg/200px-FIFA%2B_%282025%29.svg.png",
     "fallbacks":[]},
    {"id":"c11","nombre":"DAZN Combat","categoria":"DEPORTES",
     "url":"https://dazn-combat-rakuten.amagi.tv/hls/amagi_hls_data_rakutenAA-dazn-combat-rakuten/CDN/master.m3u8",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/DAZN_brand_logo.svg/200px-DAZN_brand_logo.svg.png",
     "fallbacks":[]},
    {"id":"c12","nombre":"DeporTV","categoria":"DEPORTES",
     "url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCJQamPSBACMmFrK3QLuUxmw&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/DeporTV_logo.svg/200px-DeporTV_logo.svg.png",
     "fallbacks":["https://5fb24b460df87.streamlock.net/live-cont.ar/deportv/playlist.m3u8"]},
    # ── NOTICIAS ──────────────────────────────────────────────────────────
    {"id":"c13","nombre":"TN","categoria":"NOTICIAS",
     "url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCEKv_4X5ER-3cLMhA5eN8tA&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/TN_-_Todo_Noticias_logo_%282020%29.svg/200px-TN_-_Todo_Noticias_logo_%282020%29.svg.png",
     "fallbacks":["https://mdstrm.com/live-stream-playlist/60b578b060947317de7b57ac.m3u8"]},
    {"id":"c14","nombre":"C5N","categoria":"NOTICIAS",
     "url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCFjlSkMeNXvVPoPXf0oSWwg&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/C5N_logo.svg/200px-C5N_logo.svg.png",
     "fallbacks":[]},
    {"id":"c15","nombre":"Canal 26","categoria":"NOTICIAS",
     "url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCqC5sSVJgtCyxLNiCWgJxsQ&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Canal_26_logo_%282022%29.svg/200px-Canal_26_logo_%282022%29.svg.png",
     "fallbacks":["https://stream-gtlc.telecentro.net.ar/hls/canal26hls/main.m3u8"]},
    {"id":"c16","nombre":"A24","categoria":"NOTICIAS",
     "url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCMXegZIiUQAMjvWSmRLZyiw&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/A24_TV_logo.svg/200px-A24_TV_logo.svg.png",
     "fallbacks":[]},
    {"id":"c17","nombre":"Crónica HD","categoria":"NOTICIAS",
     "url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCSumMFNbHZDGqSmJsMQc2bQ&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Cr%C3%B3nica_HD_logo.svg/200px-Cr%C3%B3nica_HD_logo.svg.png",
     "fallbacks":[]},
    {"id":"c18","nombre":"Canal E","categoria":"NOTICIAS",
     "url":"https://unlimited1-us.dps.live/perfiltv/perfiltv.smil/playlist.m3u8",
     "logo":"https://i.ibb.co/y4pkxH3/Qtc8-M2-PG-400x400.jpg",
     "fallbacks":[]},

    # ── Bolaloca via proxy Railway (sin alerta Chrome) ──────────────────
    {"id":"bol01","nombre":"Canal 1","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=1","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol02","nombre":"Canal 2","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=2","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol03","nombre":"Canal 3","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=3","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol04","nombre":"Canal 4","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=4","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol05","nombre":"Canal 5","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=5","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol06","nombre":"Canal 6","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=6","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol07","nombre":"Canal 7","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=7","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol08","nombre":"Canal 8","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=8","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol09","nombre":"Canal 9","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=9","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol10","nombre":"Canal 10","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=10","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol11","nombre":"Canal 11","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=11","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol12","nombre":"Canal 12","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=12","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol13","nombre":"Canal 13","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=13","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol14","nombre":"Canal 14","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=14","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol15","nombre":"Canal 15","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=15","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol16","nombre":"Canal 16","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=16","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol17","nombre":"Canal 17","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=17","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol18","nombre":"Canal 18","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=18","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol19","nombre":"Canal 19","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=19","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol20","nombre":"Canal 20","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=20","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol21","nombre":"Canal 21","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=21","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol22","nombre":"Canal 22","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=22","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol23","nombre":"Canal 23","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=23","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol24","nombre":"Canal 24","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=24","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol25","nombre":"Canal 25","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=25","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol26","nombre":"Canal 26","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=26","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol27","nombre":"Canal 27","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=27","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol28","nombre":"Canal 28","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=28","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol29","nombre":"Canal 29","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=29","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol30","nombre":"Canal 30","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=30","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol31","nombre":"Canal 31","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=31","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol32","nombre":"Canal 32","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=32","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol33","nombre":"Canal 33","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=33","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol34","nombre":"Canal 34","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=34","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol35","nombre":"Canal 35","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=35","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol36","nombre":"Canal 36","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=36","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol37","nombre":"Canal 37","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=37","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol38","nombre":"Canal 38","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=38","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol39","nombre":"Canal 39","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=39","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol40","nombre":"Canal 40","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=40","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol41","nombre":"Canal 41","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=41","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol42","nombre":"Canal 42","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=42","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol43","nombre":"Canal 43","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=43","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol44","nombre":"Canal 44","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=44","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol45","nombre":"Canal 45","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=45","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol46","nombre":"Canal 46","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=46","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol47","nombre":"Canal 47","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=47","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol48","nombre":"Canal 48","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=48","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol49","nombre":"Canal 49","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=49","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol50","nombre":"Canal 50","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=50","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol51","nombre":"Canal 51","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=51","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol52","nombre":"Canal 52","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=52","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol53","nombre":"Canal 53","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=53","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol54","nombre":"Canal 54","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=54","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol55","nombre":"Canal 55","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=55","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol56","nombre":"Canal 56","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=56","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol57","nombre":"Canal 57","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=57","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol58","nombre":"Canal 58","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=58","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol59","nombre":"Canal 59","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=59","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol60","nombre":"Canal 60","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=60","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol61","nombre":"Canal 61","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=61","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol62","nombre":"Canal 62","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=62","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol63","nombre":"Canal 63","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=63","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol64","nombre":"Canal 64","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=64","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol65","nombre":"Canal 65","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=65","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol66","nombre":"Canal 66","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=66","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol67","nombre":"Canal 67","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=67","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol68","nombre":"Canal 68","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=68","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol69","nombre":"Canal 69","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=69","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol70","nombre":"Canal 70","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=70","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol71","nombre":"Canal 71","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=71","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol72","nombre":"Canal 72","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=72","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol73","nombre":"Canal 73","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=73","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol74","nombre":"Canal 74","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=74","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol75","nombre":"Canal 75","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=75","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol76","nombre":"Canal 76","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=76","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol77","nombre":"Canal 77","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=77","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol78","nombre":"Canal 78","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=78","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol79","nombre":"Canal 79","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=79","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol80","nombre":"Canal 80","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=80","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol81","nombre":"Canal 81","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=81","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol82","nombre":"Canal 82","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=82","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol83","nombre":"Canal 83","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=83","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol84","nombre":"Canal 84","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=84","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol85","nombre":"Canal 85","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=85","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol86","nombre":"Canal 86","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=86","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol87","nombre":"Canal 87","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=87","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol88","nombre":"Canal 88","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=88","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol89","nombre":"Canal 89","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=89","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol90","nombre":"Canal 90","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=90","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol91","nombre":"Canal 91","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=91","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol92","nombre":"Canal 92","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=92","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol93","nombre":"Canal 93","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=93","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol94","nombre":"Canal 94","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=94","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol95","nombre":"Canal 95","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=95","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol96","nombre":"Canal 96","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=96","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol97","nombre":"Canal 97","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=97","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol98","nombre":"Canal 98","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=98","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"bol99","nombre":"Canal 99","categoria":"DEPORTES","url":"https://web-production-b498b.up.railway.app/canal?n=99","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},

    # ── MUSICA ────────────────────────────────────────────────────────────
    {"id":"c19","nombre":"Cumbia Mix","categoria":"MUSICA",
     "url":"https://cloud.tvomix.com/CUMBIAMIX/index.m3u8",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Music_note_icon.svg/200px-Music_note_icon.svg.png",
     "fallbacks":[]},
    # ── INFANTIL ──────────────────────────────────────────────────────────
    {"id":"c20","nombre":"Pakapaka","categoria":"INFANTIL",
     "url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCdh8IJMVRSu-eLFRLBLnPCg&autoplay=1",
     "logo":"https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Pakapaka_logo.svg/200px-Pakapaka_logo.svg.png",
     "fallbacks":[]},
]

TDT_CANALES = [
    {"id":"tdt001","nombre":"La 1","categoria":"AIRE","url":"https://dghxc56urunop.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-zabn6k211oedh/La1ES.m3u8","logo":"https://pbs.twimg.com/profile_images/2008842210414915584/zIp_go25_200x200.jpg","fallbacks":[]},
    {"id":"tdt002","nombre":"La 2","categoria":"AIRE","url":"https://d1yebix5w29z3v.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-haqfba85d1gvv/La2ES.m3u8","logo":"https://yt3.googleusercontent.com/ytc/AIdro_kqgHWySi5xprs1VFCNCX0IKNT8yXBLZC43JMoB8j0JUto=s200","fallbacks":[]},
    {"id":"tdt003","nombre":"TRECE","categoria":"AIRE","url":"https://play.cdn.enetres.net/091DB7AFBD77442B9BA2F141DCC182F5021/021/playlist.m3u8","logo":"https://graph.facebook.com/TRECEtves/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt004","nombre":"El Toro TV","categoria":"AIRE","url":"https://streaming-1.eltorotv.com/lb0/eltorotv-streaming-web/index.m3u8","logo":"https://graph.facebook.com/eltorotv.es/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt005","nombre":"RNE para todos","categoria":"AIRE","url":"https://rtvelivestream.rtve.es/rtvesec/rne/rne_para_todos_main.m3u8","logo":"https://graph.facebook.com/radionacionalrne/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt006","nombre":"24h","categoria":"NOTICIAS","url":"https://dpcj1q84r586o.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-zkqd2yaveiqbt/24HES.m3u8","logo":"https://pbs.twimg.com/profile_images/1634293543987453954/mb1Rzmso_200x200.jpg","fallbacks":[]},
    {"id":"tdt007","nombre":"Euronews","categoria":"NOTICIAS","url":"https://euronews-live-spa-es.fast.rakuten.tv/v1/master/0547f18649bd788bec7b67b746e47670f558b6b2/production-LiveChannel-6571/bitok/eyJzdGlkIjoiMDA0YjY0NTMtYjY2MC00ZTZkLTlkNzEtMTk3YTM3ZDZhZWIxIiwibWt0IjoiZXMiLCJjaCI6NjU3MSwicHRmIjoxfQ==/26034/euronews-es.m3u8","logo":"https://graph.facebook.com/es.euronews/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt008","nombre":"3Cat Info","categoria":"NOTICIAS","url":"https://directes-tv-int.3catdirectes.cat/live-content/canal324-hls/master.m3u8","logo":"https://pbs.twimg.com/profile_images/1968163923477098496/blka6O_j_200x200.jpg","fallbacks":[]},
    {"id":"tdt009","nombre":"El País","categoria":"NOTICIAS","url":"https://d2epgk1fomaa1g.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-9n8y4tw0bk3an/live/fast-channel-el-pais/fast-channel-el-pais.m3u8","logo":"https://graph.facebook.com/elpais/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt010","nombre":"La Vanguardia","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UClLLRs_mFTsNT5U-DqTYAGg&autoplay=1","logo":"https://graph.facebook.com/LaVanguardia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt011","nombre":"Agencia EFE","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCvJS-YNyaWyOucx8bGrHVvw&autoplay=1","logo":"https://graph.facebook.com/AgenciaEFEnoticias/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt012","nombre":"Libertad Digital TV","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCUS73_bjTYwBFAfXbvIjM8Q&autoplay=1","logo":"https://graph.facebook.com/libertad.digital.tv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt013","nombre":"Negocios TV","categoria":"NOTICIAS","url":"https://streaming013.gestec-video.com/hls/negociostv.m3u8","logo":"https://pbs.twimg.com/profile_images/1321367703731523584/bNMmbetI_200x200.jpg","fallbacks":[]},
    {"id":"tdt014","nombre":"El Confidencial","categoria":"NOTICIAS","url":"https://dgrfwaj8stp69.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-hmbd9k13g6zsa/live/fast-channel-elconfidencial/fast-channel-elconfidencial.m3u8","logo":"https://graph.facebook.com/elconfidencial/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt015","nombre":"Teledeporte","categoria":"DEPORTES","url":"https://d3fmp7j43g13qo.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-sxmelty1ewzcw/TeledeporteES.m3u8","logo":"https://graph.facebook.com/teledeporteRTVE/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt016","nombre":"Esport 3","categoria":"DEPORTES","url":"https://directes-tv-cat.3catdirectes.cat/live-origin/esport3-hls/master.m3u8","logo":"https://graph.facebook.com/Esport3/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt017","nombre":"ETB Deportes","categoria":"DEPORTES","url":"https://multimedia.eitb.eus/live-content/oka1hd-hls/master.m3u8","logo":"https://graph.facebook.com/deportes.eitb.kirolak/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt018","nombre":"Aragón Deporte","categoria":"DEPORTES","url":"https://cartv-streaming.aranova.es/hls/live/adeportes_deporte7.m3u8","logo":"https://graph.facebook.com/aragondeporte/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt019","nombre":"Vinx TV","categoria":"DEPORTES","url":"https://live.astreaming.es:5443/live/streams/vinxtv.m3u8","logo":"https://graph.facebook.com/VinxTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt020","nombre":"IB3 Esports","categoria":"DEPORTES","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCOmWJETLyAlFrHkmccOQ-3w&autoplay=1","logo":"https://graph.facebook.com/EsportsIB3/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt021","nombre":"Real Madrid TV","categoria":"DEPORTES","url":"https://rmtv.akamaized.net/hls/live/2043153/rmtv-es-web/master.m3u8","logo":"https://graph.facebook.com/RealMadrid/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt022","nombre":"Real Sociedad TV","categoria":"DEPORTES","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCfeqewEKWQ8CXY8OiXoMxxw&autoplay=1","logo":"https://graph.facebook.com/RealSociedadFutbol/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt023","nombre":"RCD Espanyol de Barcelona TV","categoria":"DEPORTES","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UClywhnD01yUU5kO6OgAeHUQ&autoplay=1","logo":"https://graph.facebook.com/RCDEspanyol/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt024","nombre":"MARCA","categoria":"DEPORTES","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCop57Z1sYHrtCyxCpE2z2Bg&autoplay=1","logo":"https://graph.facebook.com/MARCA/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt025","nombre":"El 10 del Barça","categoria":"DEPORTES","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UC4eDUzl7Ik9TlkltsqCXvDA&autoplay=1","logo":"https://pbs.twimg.com/profile_images/1580193356470226945/P2uP7_Y8_200x200.jpg","fallbacks":[]},
    {"id":"tdt026","nombre":"Tiempo de Juego COPE","categoria":"DEPORTES","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCMHb51gmuIuP8dVpsHr-uEw&autoplay=1","logo":"https://graph.facebook.com/tiempodejuego/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt027","nombre":"Kings League","categoria":"DEPORTES","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCtwslQPB_xJfaFuZv0OETNw&autoplay=1","logo":"https://graph.facebook.com/kingsleague.pro/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt028","nombre":"OKLIGA TV","categoria":"DEPORTES","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UC6RLLzXQJWy1yCAEysy1Wgw&autoplay=1","logo":"https://yt3.ggpht.com/ytc/AKedOLRCpkRZNcBfZLGvM1SO_Qf77p_xtv6OnU26aa23Vw=s200","fallbacks":[]},
    {"id":"tdt029","nombre":"FedHielo TV","categoria":"DEPORTES","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCuys7LUNfFcwwToSG3yMocw&autoplay=1","logo":"https://graph.facebook.com/fedhielo/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt030","nombre":"Mundo Náutica","categoria":"DEPORTES","url":"https://mundonautica.tv/playout/segments/live.m3u8","logo":"https://graph.facebook.com/MundoNautica/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt031","nombre":"Futsalmafer.tv","categoria":"DEPORTES","url":"https://play.agenciastreaming.com:8081/futsalmafertv/index.m3u8","logo":"https://graph.facebook.com/futsalmafer.tv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt032","nombre":"Clan","categoria":"INFANTIL","url":"https://d1wca51iywzyn1.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-e2jakfg63mh4b/ClanES.m3u8","logo":"https://graph.facebook.com/clantve/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt033","nombre":"SX3","categoria":"INFANTIL","url":"https://directes-tv-cat.3catdirectes.cat/live-content/super3-hls/master.m3u8","logo":"https://graph.facebook.com/SomSX3/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt034","nombre":"Pequeradio TV","categoria":"MUSICA","url":"https://canadaremar2.todostreaming.es/live/peque-pequetv.m3u8","logo":"https://graph.facebook.com/Pequeradio/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt035","nombre":"Pocoyó","categoria":"INFANTIL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCnB5W_ZJgiDFnklejRGADxw&autoplay=1","logo":"https://graph.facebook.com/pocoyo/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt036","nombre":"Warner Bros Kids","categoria":"INFANTIL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCB82v6uKp1S-I-DVoL2neDA&autoplay=1","logo":"https://graph.facebook.com/WarnerBrosPicturesEspana/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt037","nombre":"Cartoon Network Latino","categoria":"INFANTIL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCQySZQ6rrgJXRuonMwIIGMA&autoplay=1","logo":"https://graph.facebook.com/cartoonnetwork/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt038","nombre":"Nick Jr.","categoria":"INFANTIL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCaEb7kPgpldLuEzCRzFXsLw&autoplay=1","logo":"https://pbs.twimg.com/profile_images/1682087222537756680/BCh_FNy8_200x200.jpg","fallbacks":[]},
    {"id":"tdt039","nombre":"Bluey","categoria":"INFANTIL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCYvpkMpzo1S_rmcj2Axmbig&autoplay=1","logo":"https://graph.facebook.com/OfficialBlueyTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt040","nombre":"ZAZ TV","categoria":"INFANTIL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?network_id=16796&live=1","logo":"https://yt3.googleusercontent.com/-DMt5SrP3ObIrid5EHGZLUebeQLvRZeA64LWW3DaWd75gtK_JHjCe22Mn4EuxdlFa_EzqReCVg=s200","fallbacks":[]},
    {"id":"tdt041","nombre":"What a Toon TV","categoria":"INFANTIL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?cb=[CACHEBUSTER]&network_id=16111&live=1&avod=0&hls_marker=1&pod_duration=120&ssai_enabled=1&content_network=streamingconnect&position=preroll&app_bundle=com.streamingconnect.viva&app_domain=mirametv.live&app_category=linear_tv&content_cat=IAB9-11,IAB1-7,IAB1&content_channel=zaztv&content_genre=tv_broadcaster&content_id=mirametv_live&content_rating=TV-G&us_privacy=[US_PRIVACY]&gdpr=[GDPR]&min_ad_duration=6&max_ad_duration=120&ifa_type=[IFA_TYPE]","logo":"https://yt3.googleusercontent.com/Q8ajooLoUcC8rieersHieiDPHToDjytGCrECP_DxknEPRfnQgMdwcQ22ncDGuf4CffgEcpJaDw=s200","fallbacks":[]},
    {"id":"tdt042","nombre":"LEGO Friends","categoria":"INFANTIL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCP-Ng5SXUEt0VE-TXqRdL6g&autoplay=1","logo":"https://pbs.twimg.com/profile_images/378800000257143498/6dbc45c353f641ef85ca51f75533a7e1_200x200.jpeg","fallbacks":[]},
    {"id":"tdt043","nombre":"Talking Tom and Friends","categoria":"INFANTIL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCC9R-cxQeOpPhq2lAru0V8w&autoplay=1","logo":"https://yt3.ggpht.com/a/AATXAJwpm-5h1rjcPqno5uANZr75VhhCYKv4PS02gLUS0A=s200","fallbacks":[]},
    {"id":"tdt044","nombre":"Little Baby Bum","categoria":"INFANTIL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCHicabXz9rUMWLcdMqBtbxQ&autoplay=1","logo":"https://yt3.ggpht.com/a/AATXAJwn3r9U07S7ZOqoGZLUbuYHWiIqpE8xuLJsyg=s200","fallbacks":[]},
    {"id":"tdt045","nombre":"Masha y el Oso","categoria":"INFANTIL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCuSo4gcgxJRf4Bzu43wwVyg&autoplay=1","logo":"https://yt3.googleusercontent.com/gezE4GxPlSR2m2fQ16uL9qZKHhA8YXfHEOQ3-eLu8KadN55AzPSC9Z_ATsjesQBDrpuQXT_J1hY=s200","fallbacks":[]},
    {"id":"tdt046","nombre":"Conciertos Radio 3 (RTVE)","categoria":"MUSICA","url":"https://ztnr.rtve.es/ztnr/6924117.m3u8","logo":"https://graph.facebook.com/rtveplay/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt047","nombre":"Cuéntame (RTVE)","categoria":"AIRE","url":"https://ztnr.rtve.es/ztnr/6909843.m3u8","logo":"https://graph.facebook.com/rtveplay/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt048","nombre":"La promesa (RTVE)","categoria":"AIRE","url":"https://ztnr.rtve.es/ztnr/2472039.m3u8","logo":"https://graph.facebook.com/rtveplay/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt049","nombre":"La Revuelta (RTVE)","categoria":"AIRE","url":"https://ztnr.rtve.es/ztnr/16464388.m3u8","logo":"https://graph.facebook.com/rtveplay/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt050","nombre":"Saber y ganar (RTVE)","categoria":"AIRE","url":"https://ztnr.rtve.es/ztnr/6922467.m3u8","logo":"https://graph.facebook.com/rtveplay/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt051","nombre":"Somos Cine (RTVE)","categoria":"AIRE","url":"https://ztnr.rtve.es/ztnr/6909845.m3u8","logo":"https://graph.facebook.com/rtveplay/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt052","nombre":"Cocina (RTVE)","categoria":"AIRE","url":"https://ztnr.rtve.es/ztnr/16656232.m3u8","logo":"https://graph.facebook.com/rtveplay/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt053","nombre":"La moderna (RTVE)","categoria":"AIRE","url":"https://ztnr.rtve.es/ztnr/16464377.m3u8","logo":"https://graph.facebook.com/rtveplay/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt054","nombre":"En Play (RTVE)","categoria":"AIRE","url":"https://ztnr.rtve.es/ztnr/6712399.m3u8","logo":"https://graph.facebook.com/rtveplay/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt055","nombre":"La cárcel de los Gemelos","categoria":"AIRE","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCyOwWp6c30--i9_elAgef9g&autoplay=1","logo":"https://graph.facebook.com/LaCarcelDeLosGemelos/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt056","nombre":"Canal Parlamento","categoria":"AIRE","url":"https://congresodirecto.akamaized.net/hls/live/2037973/canalparlamento/master.m3u8","logo":"https://graph.facebook.com/CongresodelosDiputados/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt057","nombre":"Congreso de los Diputados","categoria":"AIRE","url":"https://congresodirecto.akamaized.net/hls/live/2038274/canal1/master.m3u8","logo":"https://graph.facebook.com/CongresodelosDiputados/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt058","nombre":"La Moncloa (Presidente)","categoria":"AIRE","url":"https://cdnswitch-mediahub.overon.es/stream/stream.m3u8?key=R6w5wbcxW3dLF9aNOGEsHuoNhqfSJoiRWNDWLLfNslI&pwd=QheEdHkaeHFGDHJgIwzUDoqcVjjFMef8TMGuGvkMets&stream=y3-IxQxNk4XjlfJDtBjIh7tfO628d9gbkd010uKioms&output=ginkIjHWeyffMLRZNMVovht3RnH_feedjshkMm7sr14&channel=D1tXjvcs_5NeEEMxP6mrmSggh3Uyu3kE5jyqGlgCZ4A&protocol=4CMm-Q0epGZ0SHQGeELoqqA2gfzFVCFwoiACYszyPM4&type=3pIgQ1TALsxZg7Zf0kZLkA4InWPfKONROAImuoufxKg","logo":"https://graph.facebook.com/PalaciodelaMoncloa/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt059","nombre":"La Moncloa (Ministros)","categoria":"AIRE","url":"https://cdnswitch-mediahub.overon.es/stream/stream.m3u8?key=R6w5wbcxW3dLF9aNOGEsHuoNhqfSJoiRWNDWLLfNslI&pwd=QheEdHkaeHFGDHJgIwzUDoqcVjjFMef8TMGuGvkMets&stream=o0RCNMRf-BPdBiuDSId7vbxANj4YFVpbXkxNkFKm35s&output=z3mwepuDBMOnja63VsgAcCGwmmOPD-I5yFYOiyCvBcc&channel=FBDoImE2NP77XpNbdycjnwCkI0YjxLeqTKr8QGV9bAI&protocol=4CMm-Q0epGZ0SHQGeELoqqA2gfzFVCFwoiACYszyPM4&type=3pIgQ1TALsxZg7Zf0kZLkA4InWPfKONROAImuoufxKg","logo":"https://graph.facebook.com/PalaciodelaMoncloa/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt060","nombre":"Senado","categoria":"AIRE","url":"https://senadolive.akamaized.net/hls/live/2006589/punto7/master.m3u8","logo":"https://pbs.twimg.com/profile_images/2015722457508810752/NpsKmNCK_200x200.jpg","fallbacks":[]},
    {"id":"tdt061","nombre":"Radio Nacional","categoria":"MUSICA","url":"https://ztnr.rtve.es/ztnr/6982891.m3u8","logo":"https://graph.facebook.com/radionacionalrne/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt062","nombre":"Radio 3","categoria":"MUSICA","url":"https://ztnr.rtve.es/ztnr/6982918.m3u8","logo":"https://graph.facebook.com/radio3/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt063","nombre":"Canal Sur Andalucía","categoria":"INTERNACIONAL","url":"https://live-24-canalsur.interactvty.pro/9bb0f4edcb8946e79f5017ddca6c02b0/26af5488cda642ed2eddd27a6328c93b9c03e9181b9d0a825147a7d978e69202.m3u8","logo":"https://graph.facebook.com/canalsurradioytv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt064","nombre":"Canal Sur 2 Accesible","categoria":"INTERNACIONAL","url":"https://cdnlive.codev8.net/rtvalive/smil:channel22.smil/playlist.m3u8","logo":"https://graph.facebook.com/canalsurradioytv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt065","nombre":"Canal Sur Más Noticias","categoria":"NOTICIAS","url":"https://cdnlive.codev8.net/rtvalive/smil:channel42.smil/playlist.m3u8","logo":"https://graph.facebook.com/CanalSurNoticias/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt066","nombre":"7TV Andalucía","categoria":"INTERNACIONAL","url":"https://especial7tv.gestec-video.com/hls/regional.m3u8","logo":"https://graph.facebook.com/7TelevisionAndalucia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt067","nombre":"7TV Almería","categoria":"INTERNACIONAL","url":"https://streaming004.gestec-video.com/hls/7TVALMERIA.m3u8","logo":"https://graph.facebook.com/7TelevisionAndalucia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt068","nombre":"7TV Cádiz","categoria":"INTERNACIONAL","url":"https://streaming004.gestec-video.com/hls/7TVCADIZ.m3u8","logo":"https://graph.facebook.com/7TelevisionAndalucia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt069","nombre":"7TV Córdoba","categoria":"INTERNACIONAL","url":"https://streaming004.gestec-video.com/hls/7TVCORDOBA.m3u8","logo":"https://graph.facebook.com/7TelevisionAndalucia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt070","nombre":"7TV Granada","categoria":"INTERNACIONAL","url":"https://streaming004.gestec-video.com/hls/7TVGRANADA.m3u8","logo":"https://graph.facebook.com/7TelevisionAndalucia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt071","nombre":"7TV Huelva","categoria":"INTERNACIONAL","url":"https://streaming004.gestec-video.com/hls/regional.m3u8","logo":"https://graph.facebook.com/7TelevisionAndalucia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt072","nombre":"7TV Jaén","categoria":"INTERNACIONAL","url":"https://streaming004.gestec-video.com/hls/7TVJAEN.m3u8","logo":"https://graph.facebook.com/7TelevisionAndalucia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt073","nombre":"7TV Málaga","categoria":"INTERNACIONAL","url":"https://streaming004.gestec-video.com/hls/7TVMALAGA.m3u8","logo":"https://graph.facebook.com/7TelevisionAndalucia/picture?width=200&0height=200","fallbacks":[]},
    {"id":"tdt074","nombre":"7TV Sevilla","categoria":"INTERNACIONAL","url":"https://especial7tv.gestec-video.com/hls/7TVSEVILLA.m3u8","logo":"https://graph.facebook.com/7TelevisionAndalucia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt075","nombre":"7TV Aljarafe","categoria":"INTERNACIONAL","url":"https://streaming004.gestec-video.com/hls/7TVALJARAFE.m3u8","logo":"https://graph.facebook.com/7TelevisionAndalucia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt076","nombre":"7TV Arcos","categoria":"INTERNACIONAL","url":"https://streaming004.gestec-video.com/hls/7TVARCOS.m3u8","logo":"https://graph.facebook.com/7TelevisionAndalucia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt077","nombre":"7TV Campo de Gibraltar","categoria":"INTERNACIONAL","url":"https://streaming004.gestec-video.com/hls/7TVALGECIRAS.m3u8","logo":"https://graph.facebook.com/7TelevisionAndalucia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt078","nombre":"7TV Linares","categoria":"INTERNACIONAL","url":"https://streaming004.gestec-video.com/hls/7TVLINARES.m3u8","logo":"https://graph.facebook.com/7TelevisionAndalucia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt079","nombre":"7TV Jerez","categoria":"INTERNACIONAL","url":"https://streaming004.gestec-video.com/hls/7TVJEREZ.m3u8","logo":"https://graph.facebook.com/7TelevisionAndalucia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt080","nombre":"7TV San Fernando","categoria":"INTERNACIONAL","url":"https://streaming004.gestec-video.com/hls/7TVSANFERNANDO.m3u8","logo":"https://graph.facebook.com/7TelevisionAndalucia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt081","nombre":"7TV Rota","categoria":"INTERNACIONAL","url":"https://streaming004.gestec-video.com/hls/7TVROTA.m3u8","logo":"https://graph.facebook.com/7TelevisionAndalucia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt082","nombre":"Jerez TV","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCHVquS6wXQAsESO2bwZ7esw&autoplay=1","logo":"https://graph.facebook.com/jerez.television/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt083","nombre":"101TV Málaga","categoria":"INTERNACIONAL","url":"https://liveingesta318.cdnmedia.tv/101weblive/smil:malaga.smil/playlist.m3u8","logo":"https://graph.facebook.com/101tvmalaga/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt084","nombre":"Onda Cádiz","categoria":"INTERNACIONAL","url":"https://ondacadiztv.es:30443/octv/directo_multi/playlist.m3u8","logo":"https://graph.facebook.com/ondacadiz/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt085","nombre":"Andalucía Cocina","categoria":"INTERNACIONAL","url":"https://cloud.fastchannel.es/mic/manifiest/hls/acocina/acocina.m3u8","logo":"https://yt3.googleusercontent.com/ytc/APkrFKb6DZpbxOMbN_VANCdenLck4ceg7gxMk5tnkjmM=s200","fallbacks":[]},
    {"id":"tdt086","nombre":"Andalucía Turismo","categoria":"INTERNACIONAL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?&network_id=12685&live=1","logo":"https://yt3.googleusercontent.com/ytc/APkrFKYsl5e6jEIMtXIoTUHvkJqXxDfASrvQP_QFRRww=s200","fallbacks":[]},
    {"id":"tdt087","nombre":"8TV Sierra de Cádiz","categoria":"INTERNACIONAL","url":"https://s.emisoras.tv:8081/sierradecadiz/index.m3u8","logo":"https://graph.facebook.com/8tvChiclana/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt088","nombre":"8TV Chiclana","categoria":"INFANTIL","url":"https://s.emisoras.tv:8081/chiclana/index.m3u8","logo":"https://graph.facebook.com/8tvChiclana/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt089","nombre":"M95 Marbella","categoria":"INTERNACIONAL","url":"https://limited2.todostreaming.es/live/m95-livestream.m3u8","logo":"https://graph.facebook.com/m95tvmarbella/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt090","nombre":"PTV Málaga","categoria":"INTERNACIONAL","url":"https://streamer.zapitv.com/PTV-malaga/index.m3u8","logo":"https://graph.facebook.com/PTVMalaga/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt091","nombre":"Tuya La Janda TV","categoria":"INTERNACIONAL","url":"https://nimble.tuyapro.es/app/tv/playlist.m3u8","logo":"https://graph.facebook.com/tuyalajandatv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt092","nombre":"Onda Algeciras TV","categoria":"DEPORTES","url":"https://cloudtv.provideo.es/live/algecirastv-livestream.m3u8","logo":"https://graph.facebook.com/ondaalgecirastv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt093","nombre":"Canal 45 TV","categoria":"INTERNACIONAL","url":"https://nlb1-live.emitstream.com/hls/625csn5et2iszm9oze65/master.m3u8","logo":"https://graph.facebook.com/canal45television/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt094","nombre":"Costa Noroeste TV","categoria":"INTERNACIONAL","url":"https://limited31.todostreaming.es/live/noroestetv-livestream.m3u8","logo":"https://graph.facebook.com/Costanoroestetv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt095","nombre":"Teleonuba","categoria":"INTERNACIONAL","url":"https://5f71743aa95e4.streamlock.net:1936/Teleonuba/endirecto/playlist.m3u8","logo":"https://graph.facebook.com/Teleonuba/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt096","nombre":"Córdoba TV","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCxNWrznyWiIMZfcjazVRDjg&autoplay=1","logo":"https://graph.facebook.com/cordobatvonline/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt097","nombre":"101TV Sevilla","categoria":"INTERNACIONAL","url":"https://liveingesta318.cdnmedia.tv/101weblive/smil:sevilla.smil/playlist.m3u8","logo":"https://graph.facebook.com/101TVSevilla/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt098","nombre":"CanalCosta","categoria":"INTERNACIONAL","url":"https://5f71743aa95e4.streamlock.net:1936/CanalcostaTV/endirecto/playlist.m3u8","logo":"https://graph.facebook.com/canalcosta/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt099","nombre":"Condavisión","categoria":"INTERNACIONAL","url":"https://5f71743aa95e4.streamlock.net:1936/Condavision/endirecto/playlist.m3u8","logo":"https://graph.facebook.com/condavision/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt100","nombre":"Canal Doñana","categoria":"INTERNACIONAL","url":"https://secure5.todostreaming.es/live/division-alm.m3u8","logo":"https://graph.facebook.com/donanacomunica/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt101","nombre":"Interalmería TV","categoria":"INTERNACIONAL","url":"https://interalmeria.tv/directo/live.m3u8","logo":"https://graph.facebook.com/Interalmeriatv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt102","nombre":"Almería 24h TV","categoria":"NOTICIAS","url":"https://broadcast.radioponiente.org:9443/live/smil:almeria24h.smil/playlist.m3u8","logo":"https://graph.facebook.com/107654981928274/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt103","nombre":"Marbella TV","categoria":"INTERNACIONAL","url":"https://streaming.rtvmarbella.tv/hls/streamingweb.m3u8","logo":"https://graph.facebook.com/RTVMarbella/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt104","nombre":"Estepona TV","categoria":"INTERNACIONAL","url":"https://cloudvideo.servers10.com:8081/8022/index.m3u8","logo":"https://graph.facebook.com/esteponatelevision/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt105","nombre":"Axarquía TV","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UC0N3U1saaQQWMt2rRPbU0DQ&autoplay=1","logo":"https://graph.facebook.com/AxarquiaTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt106","nombre":"Más Jerez","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCOoSrqLzlo_S5yQK3OmFqWw&autoplay=1","logo":"https://graph.facebook.com/masjerez/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt107","nombre":"TV Centro Andalucía","categoria":"INTERNACIONAL","url":"https://video0.rogohosting.com:19360/8050/8050.m3u8","logo":"https://graph.facebook.com/TVCentroAndalucia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt108","nombre":"Canal San Roque","categoria":"INTERNACIONAL","url":"https://cdnlivevlc.codev8.net/aytosanroquelive/smil:channel1.smil/playlist.m3u8","logo":"https://yt3.googleusercontent.com/6SgTMpyVCJlMGBcip6gvloYy2u-BP4vY-H2paJ2zO471owJq_YcgPhUUB0tBaKIKlNUKzeRf=s200","fallbacks":[]},
    {"id":"tdt109","nombre":"Televisión Alhaurín","categoria":"INTERNACIONAL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?network_id=13354&live=1","logo":"https://graph.facebook.com/Rtvalhaurin/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt110","nombre":"Canal Luz Televisión","categoria":"INTERNACIONAL","url":"https://5f71743aa95e4.streamlock.net:1936/CanalLuz/enDirecto/playlist.m3u8","logo":"https://graph.facebook.com/canalluztelevision/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt111","nombre":"TeleQuivir","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCW-d2GjwGd8AT5AU9LQBbeQ&autoplay=1","logo":"https://graph.facebook.com/telequivirtv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt112","nombre":"101TV Antequera","categoria":"INTERNACIONAL","url":"https://liveingesta318.cdnmedia.tv/101weblive/smil:antequera.smil/playlist.m3u8","logo":"https://graph.facebook.com/101tvAntequera/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt113","nombre":"PTV Linares","categoria":"INTERNACIONAL","url":"https://streamer.zapitv.com/ptv-linarez/index.m3u8","logo":"https://graph.facebook.com/tvlinares/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt114","nombre":"Torremolinos TV","categoria":"INTERNACIONAL","url":"https://cdnlivevlc.codev8.net/canaltorremolinoslive/smil:channel1.smil/playlist.m3u8","logo":"https://graph.facebook.com/torremolinostv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt115","nombre":"Telemotril","categoria":"INTERNACIONAL","url":"https://5940924978228.streamlock.net/8431/8431/playlist.m3u8","logo":"https://graph.facebook.com/telemotriltv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt116","nombre":"Telécija","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCt1NlIsb2Ld59S20rvAeihg&autoplay=1","logo":"https://graph.facebook.com/telecija.televisioncomarcal/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt117","nombre":"TG7","categoria":"INTERNACIONAL","url":"https://flu-01.hucame.es/TG7/index.fmp4.m3u8","logo":"https://graph.facebook.com/TG7tv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt118","nombre":"RTV Tarifa","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCx5_sA41mFHsZio4umTH3Qw&autoplay=1","logo":"https://graph.facebook.com/RTVTARIFA/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt119","nombre":"Sal TV","categoria":"INTERNACIONAL","url":"https://play.agenciastreaming.com:8081/saltv/index.m3u8","logo":"https://graph.facebook.com/SalTelevision/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt120","nombre":"Manilva TV","categoria":"INTERNACIONAL","url":"https://stream.castr.com/627a72d21914543be01c1720/live_e2ae1780dc2a11eca660b7b17b7952a5/tracks-v1a1/mono.m3u8","logo":"https://graph.facebook.com/rtvmanilva/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt121","nombre":"Canal Málaga","categoria":"INTERNACIONAL","url":"https://canalmalaga-tv-live.flumotion.com/playlist.m3u8","logo":"https://graph.facebook.com/CanalMalagaRTVMunicipal/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt122","nombre":"101TV Axarquía","categoria":"INTERNACIONAL","url":"https://www.streaming101tv.es:19360/axarquia/axarquia.m3u8","logo":"https://graph.facebook.com/101tvandalucia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt123","nombre":"9 la Loma TV","categoria":"INTERNACIONAL","url":"https://9laloma.tv/live.m3u8","logo":"https://graph.facebook.com/9laloma/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt124","nombre":"PTV Sevilla","categoria":"INTERNACIONAL","url":"https://streamer.zapitv.com/PTV_sevilla/index.m3u8","logo":"https://graph.facebook.com/SevillaPTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt125","nombre":"Fuengirola TV","categoria":"INTERNACIONAL","url":"https://streaming004.gestec-video.com/hls/FTV.m3u8","logo":"https://graph.facebook.com/fuengirolatvoficial/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt126","nombre":"PTV Granada","categoria":"INTERNACIONAL","url":"https://streamer.zapitv.com/PTV-granada/index.m3u8","logo":"https://graph.facebook.com/PTVGranada/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt127","nombre":"PTV Córdoba","categoria":"INTERNACIONAL","url":"https://streamer.zapitv.com/PTV_CORDOBA/index.m3u8","logo":"https://graph.facebook.com/PTVCOR/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt128","nombre":"Mijas 3.40 TV","categoria":"INTERNACIONAL","url":"https://streaming004.gestec-video.com/hls/MIJAS.m3u8","logo":"https://graph.facebook.com/Mijas340TV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt129","nombre":"Canal Coín","categoria":"INTERNACIONAL","url":"https://canalcoin.garjim.es/hls/directo.m3u8","logo":"https://graph.facebook.com/106272064368271/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt130","nombre":"Diez TV Andújar","categoria":"INTERNACIONAL","url":"https://streaming.cloud.innovasur.es/mmj_andujar/index.m3u8","logo":"https://graph.facebook.com/dieztv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt131","nombre":"Diez TV Las Villas","categoria":"INTERNACIONAL","url":"https://streaming.cloud.innovasur.es/mmj2/index.m3u8","logo":"https://graph.facebook.com/dieztv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt132","nombre":"Diez TV Úbeda","categoria":"INTERNACIONAL","url":"https://streaming.cloud.innovasur.es/mmj/index.m3u8","logo":"https://graph.facebook.com/dieztv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt133","nombre":"TVM Córdoba","categoria":"INTERNACIONAL","url":"https://d16pwlnz9msuji.cloudfront.net/wct-dad9c712-1c61-4a61-aeee-8be9f5c9e6e9/continuous/8fbfd2f5-30c2-4d48-a24e-73f5d35ba491/index.m3u8","logo":"https://graph.facebook.com/TVM.Cordoba/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt134","nombre":"101TV Costa del Sol","categoria":"INTERNACIONAL","url":"https://liveingesta318.cdnmedia.tv/101weblive/smil:sol.smil/playlist.m3u8","logo":"https://graph.facebook.com/101tvmalaga/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt135","nombre":"101TV Granada","categoria":"INTERNACIONAL","url":"https://liveingesta318.cdnmedia.tv/101weblive/smil:granada.smil/playlist.m3u8","logo":"https://graph.facebook.com/101tvgranada/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt136","nombre":"PTV Almería","categoria":"INTERNACIONAL","url":"https://streamer.zapitv.com/ptv_almeria/index.m3u8","logo":"https://pbs.twimg.com/profile_images/1612490465005142019/AU1R7Q6q_200x200.jpg","fallbacks":[]},
    {"id":"tdt137","nombre":"TeleGranada","categoria":"INTERNACIONAL","url":"https://telegranada.es/hls/stream.m3u8","logo":"https://graph.facebook.com/Telegranada/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt138","nombre":"Cartaya TV","categoria":"INTERNACIONAL","url":"https://video3.lhdserver.es/cartayatv/live.m3u8","logo":"https://graph.facebook.com/radiocartaya/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt139","nombre":"Cofradias 24h","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCv5WgSisSDgI90g8-E5rU7Q&autoplay=1","logo":"https://yt3.ggpht.com/eM_41EMbfLT9omch7MIGSlwg71gjSrsrPpS7TuBlFjYXLrC5pIIx8zx9SJ0q2Gvf2Gj3nblYFAw=s200","fallbacks":[]},
    {"id":"tdt140","nombre":"Parlamento de Andalucía","categoria":"INTERNACIONAL","url":"https://stream1.parlamentodeandalucia.es/realizacion1/realizacion1/playlist.m3u8","logo":"https://graph.facebook.com/parlamentodeandalucia.es/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt141","nombre":"Junta de Andalucía","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCTuxa7i4GXpGSsXC_N3s0KQ&autoplay=1","logo":"https://graph.facebook.com/AndaluciaJunta/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt142","nombre":"Aragón TV","categoria":"INTERNACIONAL","url":"https://cartv.streaming.aranova.es/hls/live/aragontv_canal1.m3u8","logo":"https://graph.facebook.com/AragonTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt143","nombre":"Aragón Noticias","categoria":"NOTICIAS","url":"https://cartv-streaming.aranova.es/hls/live/anoticias_canal3.m3u8","logo":"https://graph.facebook.com/AragonNoticias/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt144","nombre":"Calamocha TV","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCl03PpRWoRjkiK5VT4uDKgA&autoplay=1","logo":"https://graph.facebook.com/CalamochaTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt145","nombre":"Canal 25 Barbastro TV","categoria":"INTERNACIONAL","url":"https://limited49.todostreaming.es/live/tvbarbastro-livestream.m3u8","logo":"https://graph.facebook.com/tvbarbastro/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt146","nombre":"Antena Aragón","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCk4-yZ_grYVb2N4ZcAnCApA&autoplay=1","logo":"https://yt3.ggpht.com/ytc/AL5GRJWC1oJVC1hgcGBN1OHnroVVoe_pcgLvGJWvOA8aGQ=s200","fallbacks":[]},
    {"id":"tdt147","nombre":"Cortes de Aragón","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCyBXbc0UicHRPJLmHppjpgQ&autoplay=1","logo":"https://graph.facebook.com/@cortesdearagon/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt148","nombre":"Gobierno de Aragón","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCEIuOP1ex5JjB4JhtJ4Sbjg&autoplay=1","logo":"https://graph.facebook.com/GobAragon/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt149","nombre":"TV Canaria (RTVC)","categoria":"INTERNACIONAL","url":"https://d1oyt3v08gcy18.cloudfront.net/index-events.m3u8","logo":"https://graph.facebook.com/188600904655/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt150","nombre":"La 1 Canarias","categoria":"INTERNACIONAL","url":"https://ztnr.rtve.es/ztnr/5190066.m3u8","logo":"https://pbs.twimg.com/profile_images/2008842210414915584/zIp_go25_200x200.jpg","fallbacks":[]},
    {"id":"tdt151","nombre":"La 2 Canarias","categoria":"INTERNACIONAL","url":"https://ztnr.rtve.es/ztnr/5468585.m3u8","logo":"https://yt3.googleusercontent.com/ytc/AIdro_kqgHWySi5xprs1VFCNCX0IKNT8yXBLZC43JMoB8j0JUto=s200","fallbacks":[]},
    {"id":"tdt152","nombre":"24h Canarias","categoria":"NOTICIAS","url":"https://ztnr.rtve.es/ztnr/5473142.m3u8","logo":"https://pbs.twimg.com/profile_images/1634293543987453954/mb1Rzmso_200x200.jpg","fallbacks":[]},
    {"id":"tdt153","nombre":"Mírame TV","categoria":"INTERNACIONAL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?cb=[CACHEBUSTER]&network_id=16100&live=1&avod=0&hls_marker=1&position=preroll&pod_duration=120&app_bundle=com.streamingconnect.viva&ssai_enabled=true&content_channel=mirametv&app_domain=mirametv.live&app_category=linear_tv&content_cat=IAB1&content_genre=tv_broadcaster&content_network=streamingconnect&content_rating=TV-G&us_privacy=[US_PRIVACY]&gdpr=[GDPR]&ifa_type=[IFA_TYPE]&min_ad_duration=6&max_ad_duration=120&content_id=mirametv_live","logo":"https://graph.facebook.com/mirametvcom/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt154","nombre":"GranCanariaTV.com","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCDdnBGLNmifjQqHjAA_DUrA&autoplay=1","logo":"https://pbs.twimg.com/profile_images/1274358153921138695/yLxVSp3h_200x200.jpg","fallbacks":[]},
    {"id":"tdt155","nombre":"Canal 4 Tenerife","categoria":"INTERNACIONAL","url":"https://videoserver.tmcreativos.com:19360/wwzthqpupr/wwzthqpupr.m3u8","logo":"https://graph.facebook.com/CANAL4TENERIFE/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt156","nombre":"Lancelot TV","categoria":"INTERNACIONAL","url":"https://5c0956165db0b.streamlock.net:8090/directo/_definst_/lancelot.television/master.m3u8","logo":"https://graph.facebook.com/LancelotTelevision/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt157","nombre":"Tenerife Plus+ TV","categoria":"INTERNACIONAL","url":"https://k20.usastreams.com:8081/tenerifeplus/index.m3u8","logo":"https://graph.facebook.com/tenerifeplustv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt158","nombre":"RTV Mogán","categoria":"INTERNACIONAL","url":"https://cloudvideo.servers10.com:8081/8028/index.m3u8","logo":"https://graph.facebook.com/radiotelevisionmogan/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt159","nombre":"Noroeste TV","categoria":"INTERNACIONAL","url":"https://stream.castr.com/5d1f649bed75c92e40481734/live_19364d50fbcd11ed91bd012c3488eabc/index.fmp4.m3u8","logo":"https://graph.facebook.com/noroestetvladesiempre/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt160","nombre":"Fuerteventura TV","categoria":"INTERNACIONAL","url":"https://5c0956165db0b.streamlock.net/ftv/directo/.m3u8","logo":"https://yt3.ggpht.com/qj92f7GsPI7R-YCYzsFj5mDoSCduHSgh8lwCWHFXbHAx6rNmLsB78RZlmfiqbjYzQdNh1Fj9sQ=s200","fallbacks":[]},
    {"id":"tdt161","nombre":"Factoría de Carnaval","categoria":"INTERNACIONAL","url":"https://eu1.servers10.com:8081/8116/index.m3u8","logo":"https://pbs.twimg.com/profile_images/1498617906560737281/iOri7Ujk_200x200.jpg","fallbacks":[]},
    {"id":"tdt162","nombre":"Afortunadas TV","categoria":"DEPORTES","url":"https://cloudvideo.servers10.com:8081/8108/index.m3u8","logo":"https://graph.facebook.com/afortunadastv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt163","nombre":"Radio Calima TV","categoria":"MUSICA","url":"https://nrvideo1.newradio.it:443/calimafm/calimafm/playlist.m3u8","logo":"https://graph.facebook.com/calimafm/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt164","nombre":"Parlamento de Canarias","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCv7xnuWoLWJNEXNWIGkP19g&autoplay=1","logo":"https://graph.facebook.com/parlamentodecanarias/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt165","nombre":"Gobierno de Canarias","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCOfVTY15POTQM37WNlHRCgQ&autoplay=1","logo":"https://graph.facebook.com/PRES.Gobcan/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt166","nombre":"Cantabria TV","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UC0sXB5ZoIoXWvqdizegaifg&autoplay=1","logo":"https://graph.facebook.com/vegavisiontvcantabria/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt167","nombre":"11 TV Laredo","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCuPHaVBv7cd-wWx3ztpALQw&autoplay=1","logo":"https://graph.facebook.com/11TvCantabria/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt168","nombre":"De Laredu Lin TV","categoria":"INTERNACIONAL","url":"https://eu1.servers10.com:8081/8034/index.m3u8","logo":"https://graph.facebook.com/delaredulintv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt169","nombre":"Popular TV Cantabria","categoria":"INTERNACIONAL","url":"https://limited12.todostreaming.es/live/ptvcantabria-livestream.m3u8","logo":"https://graph.facebook.com/populartvcantabria/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt170","nombre":"Tevecan 9","categoria":"INTERNACIONAL","url":"https://streamlov.alsolnet.com/jarbhouse/live/playlist.m3u8","logo":"https://static.wixstatic.com/media/4d3432_610170cea6c747a986bbea4137f5c15f~mv2.png/v1/fill/w_200,h_200,al_c,q_85,usm_0.66_1.00_0.01,enc_auto/mosca%20logo%209_transparente.png","fallbacks":[]},
    {"id":"tdt171","nombre":"Saja Nansa TV","categoria":"INTERNACIONAL","url":"https://streamlov.alsolnet.com/sajanansatv/live/playlist.m3u8","logo":"https://graph.facebook.com/ondaoccidental/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt172","nombre":"Parlamento de Cantabria","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCn3GTIMs_v8p2s4vVBG_8PA&autoplay=1","logo":"https://graph.facebook.com/parlamentodecantabria/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt173","nombre":"Gobierno de Cantabria","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCyzBoaIJN13fi2b4yDKes5A&autoplay=1","logo":"https://graph.facebook.com/gobcantabria/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt174","nombre":"Castilla-La Mancha Media","categoria":"INTERNACIONAL","url":"https://cdnapisec.kaltura.com/p/2288691/sp/228869100/playManifest/entryId/1_gnz6ity9/protocol/https/format/applehttp/a.m3u8","logo":"https://graph.facebook.com/CMMediaes/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt175","nombre":"Castilla-La Mancha Radio","categoria":"MUSICA","url":"https://cdnapisec.kaltura.com/p/2288691/sp/228869100/playManifest/entryId/1_belryxvp/protocol/https/format/applehttp/a.m3u8","logo":"https://graph.facebook.com/RadioCLMes/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt176","nombre":"TV Hellín","categoria":"INTERNACIONAL","url":"https://5940924978228.streamlock.net/directohellin/directohellin/playlist.m3u8","logo":"https://graph.facebook.com/tvhellin/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt177","nombre":"Guada TV Media","categoria":"INTERNACIONAL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?network_id=12689&live=1","logo":"https://graph.facebook.com/GuadaTV.TV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt178","nombre":"Visión 6 TV","categoria":"INTERNACIONAL","url":"https://streaming.proceso.info:8888/vision6-web/stream.m3u8","logo":"https://graph.facebook.com/104927246235553/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt179","nombre":"Imás TV","categoria":"INTERNACIONAL","url":"https://secure3.todostreaming.es/live/imastv-livestream.m3u8","logo":"https://graph.facebook.com/television.imas/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt180","nombre":"Ciudad Real TV","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCNxFBlUBOaI3iQW37T3hFww&autoplay=1","logo":"https://graph.facebook.com/1765736930414544/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt181","nombre":"Alcarria TV","categoria":"INTERNACIONAL","url":"https://cls.alcarria.tv/live/alcarriatv-livestream.m3u8","logo":"https://graph.facebook.com/AlcarriaTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt182","nombre":"Canal 4 Mancha Centro","categoria":"INTERNACIONAL","url":"https://5924d3ad0efcf.streamlock.net/canal4/canal4live/playlist.m3u8","logo":"https://graph.facebook.com/canal4villarrobledo/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt183","nombre":"TeleToledo","categoria":"INTERNACIONAL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?network_id=12688&live=1","logo":"https://graph.facebook.com/Teletoledo/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt184","nombre":"Cortes de Castilla-La Mancha","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCnv_UB9qXkE8YWpDOp6_p2g&autoplay=1","logo":"https://graph.facebook.com/cortesclm/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt185","nombre":"987 Live","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UC41bdA6AiwEb34_S7KcMHOw&autoplay=1","logo":"https://graph.facebook.com/987tv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt186","nombre":"Canal 54","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCkydC921pCeunWf8Xdgsdvw&autoplay=1","logo":"https://graph.facebook.com/Canal54Burgos/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt187","nombre":"TV Aranda","categoria":"INTERNACIONAL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?network_id=12686&live=1","logo":"https://graph.facebook.com/575943555801687/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt188","nombre":"Cortes de Castilla y León","categoria":"INTERNACIONAL","url":"https://directo.ccyl.es/Hemiciclo/smil:Hemiciclo.smil/playlist.m3u8","logo":"https://graph.facebook.com/cortesdecastillayleon/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt189","nombre":"Junta Castilla y León","categoria":"INTERNACIONAL","url":"https://16escalones-live2.flumotion.com/chunks.m3u8","logo":"https://graph.facebook.com/juntadecastillayleon/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt190","nombre":"TV3","categoria":"INTERNACIONAL","url":"https://directes3-tv-cat.3catdirectes.cat/live-content/tv3-hls/master.m3u8","logo":"https://pbs.twimg.com/profile_images/1269286508625891328/rVes9BS__200x200.png","fallbacks":[]},
    {"id":"tdt191","nombre":"33","categoria":"INTERNACIONAL","url":"https://directes-tv-cat.3catdirectes.cat/live-origin/c33-super3-hls/master.m3u8","logo":"https://graph.facebook.com/Canal33/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt192","nombre":"3CAT Exclusiu 1","categoria":"INTERNACIONAL","url":"https://directes-tv-cat.3catdirectes.cat/live-content/oca1-hls/master.m3u8","logo":"https://graph.facebook.com/som3Cat/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt193","nombre":"3CAT Exclusiu 2","categoria":"INTERNACIONAL","url":"https://directes-tv-cat.3catdirectes.cat/live-content/oca2-hls/master.m3u8","logo":"https://graph.facebook.com/som3Cat/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt194","nombre":"3CAT Exclusiu 3","categoria":"INTERNACIONAL","url":"https://directes-tv-cat.3catdirectes.cat/live-content/oca3-hls/master.m3u8","logo":"https://graph.facebook.com/som3Cat/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt195","nombre":"3CAT El búnquer","categoria":"INTERNACIONAL","url":"https://fast-tailor.3catdirectes.cat/v1/channel/bunquer/hls.m3u8","logo":"https://graph.facebook.com/som3Cat/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt196","nombre":"3CAT Plats bruts","categoria":"INTERNACIONAL","url":"https://fast-tailor.3catdirectes.cat/v1/channel/ccma-channel2/hls.m3u8","logo":"https://graph.facebook.com/som3Cat/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt197","nombre":"3CAT Vinagreta","categoria":"INTERNACIONAL","url":"https://fast-tailor.3catdirectes.cat/v1/channel/vinagreta/hls.m3u8","logo":"https://graph.facebook.com/som3Cat/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt198","nombre":"3CAT Joc de Cartes","categoria":"INTERNACIONAL","url":"https://fast-tailor.3catdirectes.cat/v1/channel/joc-de-cartes/hls.m3u8","logo":"https://graph.facebook.com/som3Cat/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt199","nombre":"La 1 Catalunya","categoria":"INTERNACIONAL","url":"https://rtvelivestream.rtve.es/rtvesec/cat/la1_cat_main_dvr.m3u8","logo":"https://pbs.twimg.com/profile_images/2008842210414915584/zIp_go25_200x200.jpg","fallbacks":[]},
    {"id":"tdt200","nombre":"La 2 Catalunya","categoria":"INTERNACIONAL","url":"https://rtvelivestream.rtve.es/rtvesec/cat/la2_cat_main_dvr.m3u8","logo":"https://yt3.googleusercontent.com/ytc/AIdro_kqgHWySi5xprs1VFCNCX0IKNT8yXBLZC43JMoB8j0JUto=s200","fallbacks":[]},
    {"id":"tdt201","nombre":"24h Catalunya","categoria":"NOTICIAS","url":"https://ztnr.rtve.es/ztnr/4952053.m3u8","logo":"https://pbs.twimg.com/profile_images/1634293543987453954/mb1Rzmso_200x200.jpg","fallbacks":[]},
    {"id":"tdt202","nombre":"Ràdio 4","categoria":"INTERNACIONAL","url":"https://ztnr.rtve.es/ztnr/6982935.m3u8","logo":"https://graph.facebook.com/Radio4RNE/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt203","nombre":"Bon Dia TV","categoria":"INTERNACIONAL","url":"https://directes-tv-int.3catdirectes.cat/live-content/bondia-hls/master.m3u8","logo":"https://i2.wp.com/blocs.mesvilaweb.cat/wp-content/uploads/sites/1858/2018/11/BONDIA.png","fallbacks":[]},
    {"id":"tdt204","nombre":"betevé","categoria":"INTERNACIONAL","url":"https://cdnapisec.kaltura.com/p/2346171/sp/234617100/playManifest/entryId/1_vfibi2fe/protocol/https/format/applehttp/a.m3u8?referrer=aHR0cHM6Ly9iZXRldmUuY2F0","logo":"https://graph.facebook.com/betevecat/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt205","nombre":"Canal 4 TV Cataluña","categoria":"INTERNACIONAL","url":"https://5caf24a595d94.streamlock.net:1937/8014/8014/playlist.m3u8","logo":"https://graph.facebook.com/GRUP4COM/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt206","nombre":"Canal Terres de l'Ebre","categoria":"INTERNACIONAL","url":"https://ingest1-video.streaming-pro.com/canalteABR/ctestream/playlist.m3u8","logo":"https://graph.facebook.com/canal.terresdelebre/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt207","nombre":"Canal Reus TV","categoria":"INTERNACIONAL","url":"https://ingest2-video.streaming-pro.com/creus/stream/playlist.m3u8","logo":"https://graph.facebook.com/canalreus.cat/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt208","nombre":"Empordà TV","categoria":"INTERNACIONAL","url":"https://video3.lhdserver.es/empordatv2/live.m3u8","logo":"https://graph.facebook.com/empordatv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt209","nombre":"BDN","categoria":"INTERNACIONAL","url":"https://liveingesta318.cdnmedia.tv/badalonatvlive/smil:live.smil/playlist.m3u8?DVR","logo":"https://pbs.twimg.com/profile_images/1993636082642976768/7YX0mFB8_200x200.jpg","fallbacks":[]},
    {"id":"tdt210","nombre":"TAC 12","categoria":"INTERNACIONAL","url":"https://ingest1-video.streaming-pro.com/tac12_ABR/stream/playlist.m3u8","logo":"https://graph.facebook.com/tacdotze/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt211","nombre":"Canal Terrassa","categoria":"INTERNACIONAL","url":"https://ingest2-video.streaming-pro.com/canalterrassa/stream/playlist.m3u8","logo":"https://graph.facebook.com/canalterrassa/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt212","nombre":"Lleida TV","categoria":"INTERNACIONAL","url":"https://liveingesta318.cdnmedia.tv/lleidatvlive/smil:live.smil/playlist.m3u8?DVR","logo":"https://graph.facebook.com/LleidaTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt213","nombre":"TV Costa Brava","categoria":"INTERNACIONAL","url":"https://liveingesta318.cdnmedia.tv/costabravatvlive/smil:live.smil/playlist.m3u8","logo":"https://graph.facebook.com/tvcostabrava/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt214","nombre":"Canal Taronja Central","categoria":"INTERNACIONAL","url":"https://ingest1-video.streaming-pro.com/canaltaronja/central/playlist.m3u8","logo":"https://graph.facebook.com/taronja.cat/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt215","nombre":"TV L'Hospitalet","categoria":"INTERNACIONAL","url":"https://liveingesta318.cdnmedia.tv/tvhospitaletlive/smil:tvhospitalet.smil/playlist.m3u8?DVR","logo":"https://graph.facebook.com/lhdigital/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt216","nombre":"RTV El Vendrell","categoria":"INTERNACIONAL","url":"https://liveingesta318.cdnmedia.tv/tvvendrelllive/smil:directe.smil/playlist.m3u8","logo":"https://graph.facebook.com/rtvelvendrell/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt217","nombre":"Canal Taronja Anoia","categoria":"INTERNACIONAL","url":"https://ingest1-video.streaming-pro.com/canaltaronja/anoia/playlist.m3u8","logo":"https://graph.facebook.com/canaltaronjaanoia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt218","nombre":"VOTV","categoria":"INTERNACIONAL","url":"https://ingest2-video.streaming-pro.com/votv/streaming_web/playlist.m3u8","logo":"https://graph.facebook.com/votv.cat/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt219","nombre":"Canal Taronja Osona i Moianés","categoria":"INTERNACIONAL","url":"https://ingest1-video.streaming-pro.com/canaltaronja/osona/playlist.m3u8","logo":"https://graph.facebook.com/TaronjaTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt220","nombre":"Penedès TV","categoria":"INTERNACIONAL","url":"https://liveingesta318.cdnmedia.tv/rtvvilafrancalive/smil:live.smil/playlist.m3u8?DVR","logo":"https://graph.facebook.com/rtvvilafranca/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt221","nombre":"Piera TV","categoria":"INTERNACIONAL","url":"https://5d776b1861da1.streamlock.net/piera/smil:piera.smil/playlist.m3u8","logo":"https://yt3.ggpht.com/Yo_LIch5OT5hTA24FMlshk7MtHpuUbVoOd8U2HJGw6el7-cCkAhH8_ISKmww17wHn37FCOF_rg=s200","fallbacks":[]},
    {"id":"tdt222","nombre":"RTV Cardedeu","categoria":"INTERNACIONAL","url":"https://liveingesta318.cdnmedia.tv/tvcardedeulive/smil:rtmp01.smil/playlist.m3u8?DVR","logo":"https://graph.facebook.com/TelevisioCardedeu/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt223","nombre":"Canal 10 Empordà","categoria":"INTERNACIONAL","url":"https://ventdelnord.tv:8080/escala/directe.m3u8","logo":"https://graph.facebook.com/canal10emporda/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt224","nombre":"Vallès Visió","categoria":"INTERNACIONAL","url":"https://liveingesta318.cdnmedia.tv/vallesvisiotvlive/smil:live.smil/playlist.m3u8?DVR","logo":"https://graph.facebook.com/tvvallesvisio/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt225","nombre":"etv","categoria":"INTERNACIONAL","url":"https://liveingesta318.cdnmedia.tv/tvetvlive/smil:rtmp01.smil/playlist.m3u8?DVR","logo":"https://graph.facebook.com/etv.llobregat/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt226","nombre":"Mar TV","categoria":"INTERNACIONAL","url":"https://rfe-ingest.akamaized.net/hls/live/2033043/tvmc05/master.m3u8","logo":"https://graph.facebook.com/martelevisio/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt227","nombre":"TV Sant Cugat","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCO_HcwAMD_XcZWfqidMtfgw&autoplay=1","logo":"https://graph.facebook.com/tvsantcugat/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt228","nombre":"TV Sabadell Vallès","categoria":"INTERNACIONAL","url":"https://ingest1-video.streaming-pro.com/canaltaronja/sabadell/playlist.m3u8","logo":"https://graph.facebook.com/tvsabadellvalles/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt229","nombre":"3CAT Càmeres del temps","categoria":"INTERNACIONAL","url":"https://directes-tv-int.3catdirectes.cat/live-content/beauties-hls/master.m3u8","logo":"https://graph.facebook.com/som3Cat/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt230","nombre":"Govern de la Generalitat de Catalunya","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCLaqEt7ZJeqFCI2WB6XLz8w&autoplay=1","logo":"https://graph.facebook.com/governcat/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt231","nombre":"El Faro","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCJkirQzX68T-DiLB4-YP-TA&autoplay=1","logo":"https://graph.facebook.com/ElFarodeCeuta/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt232","nombre":"Teleganés","categoria":"INTERNACIONAL","url":"https://live.emitstream.com/hls/5z6oj7ziwxzfnj78vg2m/master.m3u8","logo":"https://graph.facebook.com/1423419417957760/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt233","nombre":"Canal Red","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCky112obBMG68Nw5MrSNNPA&autoplay=1","logo":"https://graph.facebook.com/canalredtelevision/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt234","nombre":"Distrito TV","categoria":"INTERNACIONAL","url":"https://live.emitstream.com/hls/3mn7wpcv7hbmxmdzaxap/master.m3u8","logo":"https://graph.facebook.com/2004860103163343/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt235","nombre":"Déjate de Historias TV","categoria":"DEPORTES","url":"https://limited44.todostreaming.es/live/dejatedeh-livestream.m3u8","logo":"https://graph.facebook.com/DejateDeHistoriasTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt236","nombre":"EsTuTele","categoria":"INTERNACIONAL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?network_id=16818&live=1&avod=1&cb=[CACHEBUSTER]&site_page=https%3A%2F%2Ftdtchannels.com&site_name=tdtchannels&hls_marker=1&content_cat=IAB1&content_genre=Entertainment&content_id=Estutele&content_language=es&content_rating=TV-G&content_title=Estutele&coppa=0&ssai_enabled=1","logo":"https://graph.facebook.com/Estutele/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt237","nombre":"iPROtv","categoria":"INTERNACIONAL","url":"https://59ec5453559f0.streamlock.net/iprotv/iprotv/playlist.m3u8","logo":"https://graph.facebook.com/iprotvspain/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt238","nombre":"C33 Madrid","categoria":"INTERNACIONAL","url":"https://media2.streambrothers.com:1936/8140/8140/.m3u8","logo":"https://graph.facebook.com/Canal33Madrid/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt239","nombre":"LIRA TV","categoria":"INTERNACIONAL","url":"https://cloud2.streaminglivehd.com:1936/liratv/liratv/playlist.m3u8","logo":"https://graph.facebook.com/liratvlive/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt240","nombre":"Asamblea de Madrid","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCqACQgeFG_-PmQCn3tdAFpg&autoplay=1","logo":"https://graph.facebook.com/asambleamadrid/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt241","nombre":"Gobierno de la Comunidad de Madrid","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCTS_hF6ho1Vsjz7266Qik2w&autoplay=1","logo":"https://graph.facebook.com/ComunidadMadrid/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt242","nombre":"TeleRibera","categoria":"INTERNACIONAL","url":"https://video3.lhdserver.es/teleribera/live.m3u8","logo":"https://pbs.twimg.com/profile_images/780539549239902208/g2MfVVuY_200x200.jpg","fallbacks":[]},
    {"id":"tdt243","nombre":"Parlamento de Navarra","categoria":"INTERNACIONAL","url":"https://broadcasting.parlamentodenavarra.es/live/canal1/playlist.m3u8?DVR","logo":"https://pbs.twimg.com/profile_images/1517046445030924289/r4OIw84T_200x200.jpg","fallbacks":[]},
    {"id":"tdt244","nombre":"Gobierno de Navarra","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCBeUe-p0YNNP0trYcC3EKJg&autoplay=1","logo":"https://graph.facebook.com/GobiernoNavarra/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt245","nombre":"8 La Marina TV","categoria":"INTERNACIONAL","url":"https://streaming005.gestec-video.com/hls/canal24.m3u8","logo":"https://graph.facebook.com/8lamarinatelevision/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt246","nombre":"Intercomarcal TV","categoria":"DEPORTES","url":"https://streamingtvi.gestec-video.com/hls/tvixa.m3u8","logo":"https://graph.facebook.com/Intercomarcal.Television/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt247","nombre":"7 TeleValencia","categoria":"INTERNACIONAL","url":"https://play.cdn.enetres.net/9E9557EFCEBB43A89CEC8FBD3C500247022/028/playlist.m3u8","logo":"https://pbs.twimg.com/profile_images/1876660632478437376/rbEqYeqC_200x200.jpg","fallbacks":[]},
    {"id":"tdt248","nombre":"TeleElx","categoria":"INTERNACIONAL","url":"https://tvdirecto.teleelx.es/stream/teleelx.m3u8","logo":"https://graph.facebook.com/teleelx/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt249","nombre":"Ribera TV","categoria":"INTERNACIONAL","url":"https://common01.todostreaming.es/live/ribera-livestream.m3u8","logo":"https://graph.facebook.com/grup.televisio/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt250","nombre":"La 8 Mediterráneo","categoria":"INTERNACIONAL","url":"https://newscript.gestec-video.com/hls/8TVEVENTOS.m3u8","logo":"https://graph.facebook.com/la8mediterraneo/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt251","nombre":"Alacantí TV","categoria":"INTERNACIONAL","url":"https://streaming01.gestec-video.com/hls/artequatreAlacanti.m3u8","logo":"https://graph.facebook.com/alacantitv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt252","nombre":"12TV Alicante","categoria":"INTERNACIONAL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?cb=[CACHEBUSTER]&network_id=16126&live=1&avod=0&hls_marker=1&position=preroll&pod_duration=120&app_bundle=com.streamingconnect.viva&ssai_enabled=1&content_channel=12tv&app_domain=mirametv.live&app_category=linear_tv&content_cat=IAB1&content_genre=tv_broadcaster&content_network=streamingconnect&content_rating=TV-G&us_privacy=[US_PRIVACY]&gdpr=[GDPR]&ifa_type=[IFA_TYPE]&min_ad_duration=6&max_ad_duration=120&content_id=mirametv_live","logo":"https://graph.facebook.com/12tv.es/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt253","nombre":"TV Artequatre","categoria":"INTERNACIONAL","url":"https://streaming007.gestec-video.com/hls/artequatreTVA.m3u8","logo":"https://graph.facebook.com/tvArtequatre/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt254","nombre":"Maestrat TV","categoria":"INTERNACIONAL","url":"https://stream.maestrat.tv/hls/stream.m3u8","logo":"https://graph.facebook.com/maestrat.tv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt255","nombre":"Burriana TV","categoria":"INTERNACIONAL","url":"https://www.burrianateve.com/hls/btv.m3u8","logo":"https://graph.facebook.com/burrianateve/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt256","nombre":"TV 4 La Vall","categoria":"INTERNACIONAL","url":"https://valldeuxo.gestec-video.com/hls/lavall.m3u8","logo":"https://graph.facebook.com/TV4LaVall/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt257","nombre":"Distrito TV Valencia","categoria":"INTERNACIONAL","url":"https://live.emitstream.com/hls/3mn7wpcv7hbmxmdzaxap/master.m3u8","logo":"https://graph.facebook.com/2004860103163343/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt258","nombre":"Elche 7 TV","categoria":"INTERNACIONAL","url":"https://elche7tv.gestec-video.com/hls/canal2.m3u8","logo":"https://pbs.twimg.com/profile_images/1543985670066245632/cX_NvIkT_200x200.jpg","fallbacks":[]},
    {"id":"tdt259","nombre":"Tele Safor","categoria":"INTERNACIONAL","url":"https://video.telesafor.com/hls/video.m3u8","logo":"https://yt3.ggpht.com/ytc/APkrFKZ5UffEAeHVZWc1fbQsPu4VNureSfNMwlMoRmgH=s200","fallbacks":[]},
    {"id":"tdt260","nombre":"Canal 56","categoria":"INTERNACIONAL","url":"https://videos.canal56.com/directe/stream/index.m3u8","logo":"https://graph.facebook.com/canal56televisio/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt261","nombre":"Univers TV","categoria":"INTERNACIONAL","url":"https://cloud2.streaminglivehd.com:1936/universfaller/universfaller/playlist.m3u8","logo":"https://graph.facebook.com/UniversValenciaDigital/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt262","nombre":"Radio Buñol TV","categoria":"MUSICA","url":"https://castor.streamthatvideo.co:8081/radiobunyol/tracks-v1a1/mono.m3u8","logo":"https://graph.facebook.com/radiobunyol/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt263","nombre":"TV Almassora","categoria":"INTERNACIONAL","url":"https://play.turesportmedia.com/hls/abr_tvalmassora/index.m3u8","logo":"https://yt3.ggpht.com/IYhYKEgINXNgQGLhReOrma2Pcl151M7Ray9SYDWissgAAZQJUhrRPEe7tLBT9XlsjwChuTNW=s200","fallbacks":[]},
    {"id":"tdt264","nombre":"Punt 3 Vall Uixó","categoria":"INTERNACIONAL","url":"https://bit.controlstreams.com:5443/LiveApp/streams/punt3.m3u8","logo":"https://graph.facebook.com/Punt3Television/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt265","nombre":"Onda 15 TV","categoria":"INTERNACIONAL","url":"https://cloudvideo.servers10.com:8081/8034/index.m3u8","logo":"https://pbs.twimg.com/profile_images/452144347593465856/NWj5Y9hn_200x200.png","fallbacks":[]},
    {"id":"tdt266","nombre":"Canal 3 Biar","categoria":"INTERNACIONAL","url":"https://avantstreaming.es/hls/canal3.m3u8","logo":"https://yt3.googleusercontent.com/ytc/AIdro_nQt5rluj5KRX0HGcMvHLxSUJuhjZe4Y1GfuA0NjpHf5Q=s200","fallbacks":[]},
    {"id":"tdt267","nombre":"Ciudades Del Ocio TV","categoria":"INTERNACIONAL","url":"https://cloudvideo.servers10.com:8081/8024/index.m3u8","logo":"https://graph.facebook.com/CiudadesDelOcioTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt268","nombre":"Onda Valencia","categoria":"INTERNACIONAL","url":"https://cloudvideo.servers10.com:8081/8116/index.m3u8","logo":"https://graph.facebook.com/ondavalenciatv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt269","nombre":"Une Vinalopó","categoria":"INTERNACIONAL","url":"https://streamingtvi.gestec-video.com/hls/unesd.m3u8","logo":"https://graph.facebook.com/UneVinalopo/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt270","nombre":"33TV Valencia","categoria":"INTERNACIONAL","url":"https://limited43.todostreaming.es/live/simbana-livestream.m3u8","logo":"https://karyganet.com/wp-content/uploads/tv-33.jpg","fallbacks":[]},
    {"id":"tdt271","nombre":"Corts Valencianes","categoria":"INTERNACIONAL","url":"https://streamserver3.seneca.tv/cval_live/cdn_enc_3/master.m3u8","logo":"https://graph.facebook.com/cortsval/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt272","nombre":"Generalitat Valenciana","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UC7K6JEaXU--Ky356DgE1m-Q&autoplay=1","logo":"https://graph.facebook.com/generalitatvalenciana/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt273","nombre":"Canal Extremadura","categoria":"INTERNACIONAL","url":"https://canalextremadura-live.flumotion.cloud/canalextremadura/live_all/playlist_dvr.m3u8","logo":"https://graph.facebook.com/CanalExtremadura/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt274","nombre":"Villafranca TV","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCIp5TEcJidiaN3p_mguOrTQ&autoplay=1","logo":"https://pbs.twimg.com/profile_images/1180389927709810688/BgzpxkjA_200x200.jpg","fallbacks":[]},
    {"id":"tdt275","nombre":"Asamblea de Extremadura","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCDRei0Imqv9iV8mHQdYwGdQ&autoplay=1","logo":"https://graph.facebook.com/AsambleaExtremadura/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt276","nombre":"Junta de Extremadura","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCjFp79A_UFcx01_4N0gwoSg&autoplay=1","logo":"https://graph.facebook.com/JuntaDeExtremadura/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt277","nombre":"TVG","categoria":"INTERNACIONAL","url":"https://crtvg-europa.flumotion.cloud/playlist.m3u8","logo":"https://graph.facebook.com/CRTVG/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt278","nombre":"TVG 2","categoria":"INTERNACIONAL","url":"https://crtvg-tvg2.flumotion.cloud/playlist.m3u8","logo":"https://graph.facebook.com/CRTVG/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt279","nombre":"TVG Xabarin","categoria":"INTERNACIONAL","url":"https://crtvg-infantil-schlive.flumotion.cloud/crtvglive/smil:channel5PRG.smil/playlist.m3u8","logo":"https://graph.facebook.com/oxabarinclub/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt280","nombre":"TVG Pequerrech@s","categoria":"INTERNACIONAL","url":"https://crtvg-xabarinr1-schlive.flumotion.cloud/crtvglive/smil:channel6PRG.smil/playlist.m3u8","logo":"https://graph.facebook.com/oxabarinclub/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt281","nombre":"TVG Cativ@s","categoria":"INTERNACIONAL","url":"https://crtvg-xabarinr2-schlive.flumotion.cloud/crtvglive/smil:channel7PRG.smil/playlist.m3u8","logo":"https://graph.facebook.com/oxabarinclub/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt282","nombre":"TVG Mociñ@s","categoria":"INTERNACIONAL","url":"https://crtvg-xabarinr3-schlive.flumotion.cloud/crtvglive/smil:channel8PRG.smil/playlist.m3u8","logo":"https://graph.facebook.com/oxabarinclub/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt283","nombre":"TVG Eventos","categoria":"INTERNACIONAL","url":"https://crtvg-events1.flumotion.cloud/playlist.m3u8","logo":"https://graph.facebook.com/CRTVG/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt284","nombre":"TVG Mira Radio Galega","categoria":"MUSICA","url":"https://crtvg-mirarg-schlive.flumotion.cloud/crtvglive/smil:channel1PRG.smil/playlist.m3u8","logo":"https://graph.facebook.com/CRTVG/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt285","nombre":"Corenta anos da TVG","categoria":"INTERNACIONAL","url":"https://crtvg-40-anos-crtvg-schlive.flumotion.cloud/crtvglive/smil:channel9PRG.smil/playlist.m3u8","logo":"https://graph.facebook.com/CRTVG/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt286","nombre":"TV Ferrol","categoria":"INTERNACIONAL","url":"https://directo.tvferrol.es/tv.m3u8","logo":"https://graph.facebook.com/tvferrol/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt287","nombre":"TeleVigo","categoria":"INTERNACIONAL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?cb=[CACHEBUSTER]&network_id=16113&live=1&avod=0&hls_marker=1&position=preroll&pod_duration=120&app_bundle=com.streamingconnect.viva&app_domain=mirametv.live&app_category=linear_tv&ssai_enabled=1&content_cat=IAB1&content_channel=televigo&content_genre=tv_broadcaster&content_network=streamingconnect&content_rating=TV-G&us_privacy=[US_PRIVACY]&gdpr=[GDPR]&ifa_type=[IFA_TYPE]&min_ad_duration=6&max_ad_duration=120&content_id=[CONTENT_ID]","logo":"https://graph.facebook.com/televigo/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt288","nombre":"Telemiño","categoria":"INTERNACIONAL","url":"https://laregionlive.flumotion.cloud/laregionlive/smil:channel1.smil/playlist.m3u8","logo":"https://graph.facebook.com/teleminho/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt289","nombre":"Anove TV","categoria":"INTERNACIONAL","url":"https://cloud.streamingconnect.tv/hls/anove/anove.m3u8","logo":"https://graph.facebook.com/anove.tv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt290","nombre":"Auria TV","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UC4xDk-vc3i4CB45U7_wmm5g&autoplay=1","logo":"https://yt3.ggpht.com/a-/AAuE7mBbJ5XfzqqDgg1IkOk23GJ6JZntYZtYT-n1CA=s200","fallbacks":[]},
    {"id":"tdt291","nombre":"Parlamento de Galicia","categoria":"INTERNACIONAL","url":"https://pgalicia-live.akamaized.net/hls/live/2040697/pleno/playlist.m3u8","logo":"https://graph.facebook.com/parlamentodegalicia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt292","nombre":"Xunta de Galicia","categoria":"INTERNACIONAL","url":"https://xuntalive.akamaized.net/hls/live/2032287/streamxunta/bitrate_2.m3u8","logo":"https://graph.facebook.com/@xuntadegalicia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt293","nombre":"IB3 Global","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCff_CBVJDTHP4wOHPjP5BMg&autoplay=1","logo":"https://graph.facebook.com/IB3org/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt294","nombre":"TEF","categoria":"INTERNACIONAL","url":"https://tef.servertv.online:3268/live/teflive.m3u8","logo":"https://graph.facebook.com/TEFTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt295","nombre":"Canal 4 TV Mallorca","categoria":"INTERNACIONAL","url":"https://5caf24a595d94.streamlock.net:1937/8110/8110/playlist.m3u8","logo":"https://graph.facebook.com/GRUP4COM/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt296","nombre":"Fibwi Diario","categoria":"INTERNACIONAL","url":"https://hostcdn3.fibwi.com/fibwi_diario/index.fmp4.m3u8","logo":"https://pbs.twimg.com/profile_images/1937439289270288384/qFK2qqCW_200x200.jpg","fallbacks":[]},
    {"id":"tdt297","nombre":"Parlament de les Illes Balears","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCpLm25L3R1VVOQDFiSCCmDA&autoplay=1","logo":"https://pbs.twimg.com/profile_images/1628713790303879168/hOxkqhuJ_200x200.jpg","fallbacks":[]},
    {"id":"tdt298","nombre":"Govern de les Illes Balears","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCWq6paV7LGHW7YdR0kYLx_w&autoplay=1","logo":"https://graph.facebook.com/GovernIllesBalears/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt299","nombre":"TV Rioja","categoria":"INTERNACIONAL","url":"https://5924d3ad0efcf.streamlock.net/riojatv/riojatvlive/playlist.m3u8","logo":"https://graph.facebook.com/tvrtelevision/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt300","nombre":"Parlamento de La Rioja","categoria":"INTERNACIONAL","url":"https://media.parlamento-larioja.org/live/parlarioja/playlist.m3u8","logo":"https://graph.facebook.com/ParlamentodeLaRioja/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt301","nombre":"Cocina Familiar","categoria":"INTERNACIONAL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?cb=[CACHEBUSTER]&network_id=16114&live=1&avod=0&hls_marker=1&pod_duration=120&position=preroll&app_bundle=com.streamingconnect.viva&app_category=linear_tv&content_cat=IAB8&content_channel=cocinafamiliar&content_genre=tv_broadcaster&content_network=streamingconnect&content_rating=TV-G&us_privacy=[US_PRIVACY]&gdpr=[GDPR]&ifa_type=[IFA_TYPE]&ssai_enabled=1&content_id=mirametv_live&min_ad_duration=6&max_ad_duration=120&app_domain=mirametv.live","logo":"https://graph.facebook.com/cocinafamiliarjr/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt302","nombre":"Gobierno de La Rioja","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCm0tq4vpa3bWZCr5sgiA6rQ&autoplay=1","logo":"https://graph.facebook.com/lariojaorg/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt303","nombre":"Popular TV Melilla","categoria":"INTERNACIONAL","url":"https://5940924978228.streamlock.net/8009/ngrp:8009_all/playlist.m3u8","logo":"https://pbs.twimg.com/profile_images/61224728/populartvtwitter_200x200.png","fallbacks":[]},
    {"id":"tdt304","nombre":"ETB 1","categoria":"INTERNACIONAL","url":"https://cdn1.etbon.eus/etb1/index.m3u8","logo":"https://graph.facebook.com/eitb/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt305","nombre":"ETB 2","categoria":"INTERNACIONAL","url":"https://cdn1.etbon.eus/etb2/index.m3u8","logo":"https://graph.facebook.com/eitb/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt306","nombre":"ETB1 ON","categoria":"INTERNACIONAL","url":"https://cdn1.etbon.eus/etb1on/index.m3u8","logo":"https://play-lh.googleusercontent.com/GUW-ipQpsCCLhoJwWarfUDYO_vr3-5rpxhfipNSHAAvlaaWdfBwdUtVVUzs3PPyQzrSBVepKSqPzNAwDHvljII0=w200","fallbacks":[]},
    {"id":"tdt307","nombre":"ETB2 ON","categoria":"INTERNACIONAL","url":"https://cdn1.etbon.eus/etb2on/index.m3u8","logo":"https://play-lh.googleusercontent.com/GUW-ipQpsCCLhoJwWarfUDYO_vr3-5rpxhfipNSHAAvlaaWdfBwdUtVVUzs3PPyQzrSBVepKSqPzNAwDHvljII0=w200","fallbacks":[]},
    {"id":"tdt308","nombre":"ETB Eventos 1","categoria":"INTERNACIONAL","url":"https://cdn1.etbon.eus/oc1/index.m3u8","logo":"https://graph.facebook.com/eitb/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt309","nombre":"ETB Eventos 2","categoria":"INTERNACIONAL","url":"https://cdn1.etbon.eus/oc2/index.m3u8","logo":"https://graph.facebook.com/eitb/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt310","nombre":"Euskadi Meteo (ETB On)","categoria":"INTERNACIONAL","url":"https://cdn1.etbon.eus/meteo/index.m3u8","logo":"https://play-lh.googleusercontent.com/GUW-ipQpsCCLhoJwWarfUDYO_vr3-5rpxhfipNSHAAvlaaWdfBwdUtVVUzs3PPyQzrSBVepKSqPzNAwDHvljII0=w200","fallbacks":[]},
    {"id":"tdt311","nombre":"Hamaika TV","categoria":"INTERNACIONAL","url":"https://cdn3.wowza.com/1/RERMR282dnU5eE5Z/OHY0dVFs/hls/live/playlist.m3u8","logo":"https://graph.facebook.com/HamaikaTb/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt312","nombre":"Tele 7","categoria":"INTERNACIONAL","url":"https://ingest2-video.streaming-pro.com/tele7_ABR/stream/playlist.m3u8","logo":"https://graph.facebook.com/Tele7Radio7/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt313","nombre":"Goiena Eus","categoria":"INTERNACIONAL","url":"https://zuzenean.goienamedia.eus/goiena-telebista.m3u8","logo":"https://graph.facebook.com/goiena.eus/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt314","nombre":"Durangaldeko TV","categoria":"INTERNACIONAL","url":"https://live.emitstream.com/hls/5f9asjsehd7gmyxsdpzu/master.m3u8","logo":"https://graph.facebook.com/dotbDurangaldekoTelebista/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt315","nombre":"Goierri Irrati TV","categoria":"INTERNACIONAL","url":"https://streaming.gitb.eus/hls/z.m3u8","logo":"https://graph.facebook.com/GoierriIrratiTelebista/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt316","nombre":"28 Kanala","categoria":"INTERNACIONAL","url":"https://streaming.28kanala.eus/hls/z.m3u8","logo":"https://graph.facebook.com/28kanala/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt317","nombre":"TeleBilbao","categoria":"INTERNACIONAL","url":"https://player.telebilbao.es/hls/web-public/live.m3u8","logo":"https://graph.facebook.com/312994995454199/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt318","nombre":"GUKA TB","categoria":"INTERNACIONAL","url":"https://streaming.ukt.eus/hls/test.m3u8","logo":"https://graph.facebook.com/guka.eus/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt319","nombre":"Oizmendi TV","categoria":"INTERNACIONAL","url":"https://zuzenean.oizmendi.eus/hls/z.m3u8","logo":"https://graph.facebook.com/oizmenditelebista/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt320","nombre":"Urola TV","categoria":"INTERNACIONAL","url":"https://5940924978228.streamlock.net/j_Directo2/j_Directo2/playlist.m3u8","logo":"https://graph.facebook.com/urolatelebista/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt321","nombre":"STZ Telebista","categoria":"INTERNACIONAL","url":"https://cloudvideo.servers10.com:8081/stztelebista/index.m3u8","logo":"https://graph.facebook.com/StzGrupo/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt322","nombre":"Eusko Legebiltzarra","categoria":"INTERNACIONAL","url":"https://bideoak.legebiltzarra.eus/zuzenean/stream-3_channel-1/playlist.m3u8","logo":"https://graph.facebook.com/legebiltzarra/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt323","nombre":"Junta General del Principado de Asturias","categoria":"INTERNACIONAL","url":"https://wmserver.jgpa.es/live/_definst_/livestream2/playlist.m3u8","logo":"https://pbs.twimg.com/profile_images/2030898420681232384/TBZNbHLJ_200x200.jpg","fallbacks":[]},
    {"id":"tdt324","nombre":"Gobierno del Principado de Asturias","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCyssDZ4splBnG9_jD-FOpFA&autoplay=1","logo":"https://graph.facebook.com/gobiernodeasturias/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt325","nombre":"7 R. de Murcia","categoria":"INTERNACIONAL","url":"https://rtv-murcia-live.globalmest.com/secundario/smil:secundario.smil/playlist.m3u8","logo":"https://graph.facebook.com/la7tele/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt326","nombre":"Popular TV Murcia","categoria":"INTERNACIONAL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?network_id=12690&live=1","logo":"https://pbs.twimg.com/profile_images/61224728/populartvtwitter_200x200.png","fallbacks":[]},
    {"id":"tdt327","nombre":"Canal 1 Mar Menor Torre Pacheco","categoria":"INTERNACIONAL","url":"https://directo.tuwebtv.es/canal1.m3u8","logo":"https://graph.facebook.com/tuwebtv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt328","nombre":"Arabí TV","categoria":"INTERNACIONAL","url":"https://streamtv2.elitecomunicacion.cloud:3628/live/arabitv2025live.m3u8","logo":"https://graph.facebook.com/arabitvyecla/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt329","nombre":"Canal 6 Totana","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCO_V53zJvyne-sroV8RzU2A&autoplay=1","logo":"https://graph.facebook.com/TotanaWeb/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt330","nombre":"Asamblea Regional de Murcia","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCGWt3Hunyq2i8Qso_de8x5g&autoplay=1","logo":"https://graph.facebook.com/asambleamurcia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt331","nombre":"Consejo de Gobierno de la Región de Murcia","categoria":"INTERNACIONAL","url":"https://crmlive.redctnet.es/liveedge/ConsejoGob/playlist.m3u8","logo":"https://graph.facebook.com/RegiondeMurciaRM/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt332","nombre":"TVE Int. Europa","categoria":"INTERNACIONAL","url":"https://rtvelivestream.rtve.es/rtvesec/int/tvei_eu_main_dvr.m3u8","logo":"https://graph.facebook.com/tveInternacional/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt333","nombre":"Star TVE Europa","categoria":"INTERNACIONAL","url":"https://rtvelivestream.rtve.es/rtvesec/int/star_main_dvr.m3u8","logo":"https://graph.facebook.com/STARTVEInternacional/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt334","nombre":"TV3.CAT","categoria":"INTERNACIONAL","url":"https://directes3-tv-int.3catdirectes.cat/live-content/tvi-hls/master.m3u8","logo":"https://pbs.twimg.com/profile_images/1269286508625891328/rVes9BS__200x200.png","fallbacks":[]},
    {"id":"tdt335","nombre":"TVG Europa","categoria":"INTERNACIONAL","url":"https://crtvg-europa.flumotion.cloud/playlist_dvr.m3u8","logo":"https://graph.facebook.com/CRTVG/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt336","nombre":"Telemadrid Internacional","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCv2BcgqxHSrl2QQfIkjR5Eg&autoplay=1","logo":"https://graph.facebook.com/telemadrid/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt337","nombre":"GCM Internacional","categoria":"INTERNACIONAL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?cb=[CACHEBUSTER]&network_id=16149&live=1&avod=0&hls_marker=1&pod_duration=120&app_bundle=com.streamingconnect.viva&app_category=linear_tv&app_domain=mirametv.live&content_cat=IAB1&content_genre=tv_broadcaster&content_network=streamingconnect&content_rating=TV-G&content_channel=GCMI&content_id=mirametv_live&us_privacy=[US_PRIVACY]&gdpr=[GDPR]&ifa_type=[IFA_TYPE]&position=[POSITION]&min_ad_duration=6&max_ad_duration=120&ssai_enabled=1","logo":"https://pbs.twimg.com/profile_images/1752299087402041344/eAHH3L02_200x200.jpg","fallbacks":[]},
    {"id":"tdt338","nombre":"ATV Andorra","categoria":"INTERNACIONAL","url":"https://livesg1.rtva.hiway.media/65cea6ac-6944-4e45-b661-9dd47ea45c48/manifest.m3u8","logo":"https://graph.facebook.com/rtva.andorra/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt339","nombre":"Lòria TV Andorra","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCCCnrECJpv84QKM4olodZOQ&autoplay=1","logo":"https://graph.facebook.com/LoriaTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt340","nombre":"Euronews Internacional","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCSrZ3UV4jOidv8ppoVuvW9Q&autoplay=1","logo":"https://graph.facebook.com/es.euronews/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt341","nombre":"CNN Internacional","categoria":"INTERNACIONAL","url":"https://ds2c506obo7m8.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-7zjq3tdqasbg8/index.m3u8","logo":"https://graph.facebook.com/cnninternational/picture?width=320&height=320","fallbacks":[]},
    {"id":"tdt342","nombre":"Bloomberg Europe","categoria":"INTERNACIONAL","url":"https://www.bloomberg.com/media-manifest/streams/eu.m3u8","logo":"https://pbs.twimg.com/profile_images/991792042094354432/DG1Ruupb_200x200.jpg","fallbacks":[]},
    {"id":"tdt343","nombre":"France 24 Francia","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCUdOoVWuWmgo1wByzcsyKDQ&autoplay=1","logo":"https://graph.facebook.com/FRANCE24/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt344","nombre":"BFM TV Francia","categoria":"MUSICA","url":"https://live-cdn-stream-euw1.bfmtv.bct.nextradiotv.com/master.m3u8","logo":"https://graph.facebook.com/BFMTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt345","nombre":"franceinfo: Francia","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCO6K_kkdP-lnSCiO3tPx7WA&autoplay=1","logo":"https://pbs.twimg.com/profile_images/1019886363515211776/D2TBSqHw_200x200.jpg","fallbacks":[]},
    {"id":"tdt346","nombre":"Sport Italia","categoria":"DEPORTES","url":"https://origin-001.streamup.eu/sportitalia/sihd_abr2/playlist.m3u8","logo":"https://graph.facebook.com/sportitaliatv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt347","nombre":"La7 Italia","categoria":"INTERNACIONAL","url":"https://d1chghleocc9sm.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-evfku205gqrtf/Live.m3u8","logo":"https://graph.facebook.com/tgla7/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt348","nombre":"DW Alemania","categoria":"INTERNACIONAL","url":"https://dwamdstream104.akamaized.net/hls/live/2015530/dwstream104/index.m3u8","logo":"https://graph.facebook.com/dw.espanol/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt349","nombre":"Tagesschau24 Alemania","categoria":"INTERNACIONAL","url":"https://tagesschau.akamaized.net/hls/live/2020115/tagesschau/tagesschau_1/master.m3u8","logo":"https://graph.facebook.com/tagesschau/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt350","nombre":"ARD Das Erste Alemania","categoria":"INTERNACIONAL","url":"https://daserste-live.ard-mcdn.de/daserste/live/hls/int/master.m3u8","logo":"https://pbs.twimg.com/profile_images/1605959306435756038/_EiuBjQ8_200x200.png","fallbacks":[]},
    {"id":"tdt351","nombre":"WDR Westdeutschen Alemania","categoria":"INTERNACIONAL","url":"https://wdrfsww247.akamaized.net/hls/live/2009628/wdr_msl4_fs247ww/master.m3u8","logo":"https://graph.facebook.com/WDR/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt352","nombre":"NDR Niedersachsen Alemania","categoria":"INTERNACIONAL","url":"https://ndrint.akamaized.net/hls/live/2020766/ndr_int/master.m3u8","logo":"https://graph.facebook.com/ndrniedersachsen/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt353","nombre":"BR Bayerischer Alemania","categoria":"INTERNACIONAL","url":"https://mcdn.br.de/br/fs/bfs_sued/hls/int/master.m3u8","logo":"https://graph.facebook.com/BR24/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt354","nombre":"HR Hessenschau Alemania","categoria":"INTERNACIONAL","url":"https://hr-live.ard-mcdn.de/hr/live/hls/de/master.m3u8","logo":"https://graph.facebook.com/Hessenschau/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt355","nombre":"SR Saarland Alemania","categoria":"INTERNACIONAL","url":"https://srfs.akamaized.net/hls/live/689649/srfsgeo/index.m3u8","logo":"https://graph.facebook.com/SRinfo.sr/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt356","nombre":"GB News Reino Unido","categoria":"NOTICIAS","url":"https://amg01076-lightningintern-gbnews-samsunguk-0lu52.amagi.tv/playlist/amg01076-lightningintern-gbnews-samsunguk/playlist.m3u8","logo":"https://graph.facebook.com/GBNewsOnline/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt357","nombre":"LN24 Bélgica","categoria":"INTERNACIONAL","url":"https://live-ln24.digiteka.com/1911668011/index.m3u8","logo":"https://graph.facebook.com/LN24LesNews24/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt358","nombre":"Digi24 Rumanía","categoria":"INTERNACIONAL","url":"https://pubads.g.doubleclick.net/ssai/event/OQfdjUhHSDSlb1fJVzehsQ/master.m3u8","logo":"https://graph.facebook.com/Digi24HD/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt359","nombre":"TRT World Turquía","categoria":"INTERNACIONAL","url":"https://tv-trtworld.medya.trt.com.tr/master.m3u8","logo":"https://graph.facebook.com/trtworld/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt360","nombre":"RTCG SAT Montenegro","categoria":"INTERNACIONAL","url":"https://rtcg-live-open.morescreens.com/RTCG_1_004/playlist.m3u8","logo":"https://graph.facebook.com/RTCG.me/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt361","nombre":"RÚV Islandia","categoria":"INTERNACIONAL","url":"https://ruv-web-live.akamaized.net/streymi/ruverl/ruverl.m3u8","logo":"https://graph.facebook.com/RUVohf/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt362","nombre":"San Marino RTV","categoria":"INTERNACIONAL","url":"https://d2hrvno5bw6tg2.cloudfront.net/smrtv-ch01/_definst_/smil:ch-01.smil/master.m3u8","logo":"https://graph.facebook.com/SanMarinoRTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt363","nombre":"VizionPlus Albania","categoria":"INTERNACIONAL","url":"https://tringliveviz.akamaized.net/delta/105/out/u/qwaszxerdfcvrtryuy.m3u8","logo":"https://graph.facebook.com/vizionplustv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt364","nombre":"ICTV Ucrania","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCG26bSkEjJc7SqGsxoHNnbA&autoplay=1","logo":"https://graph.facebook.com/ICTVchannel/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt365","nombre":"Current Time TV","categoria":"INTERNACIONAL","url":"https://rferl-ingest.akamaized.net/hls/live/2121657/tvmc05/playlist.m3u8","logo":"https://graph.facebook.com/currenttimetv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt366","nombre":"FOX Live Now USA","categoria":"INTERNACIONAL","url":"https://fox-foxnewsnow-samsungus.amagi.tv/playlist.m3u8","logo":"https://graph.facebook.com/livenowfox/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt367","nombre":"ABC News USA","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCBi2mrWuNuyYy4gbM6fU18Q&autoplay=1","logo":"https://graph.facebook.com/ABCNews/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt368","nombre":"NBC News USA","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCeY0bbntWzzVIaj2z3QigXg&autoplay=1","logo":"https://graph.facebook.com/NBCNews/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt369","nombre":"CBS News USA","categoria":"NOTICIAS","url":"https://cbsn-us.cbsnstream.cbsnews.com/out/v1/55a8648e8f134e82a470f83d562deeca/master.m3u8","logo":"https://graph.facebook.com/CBSNews/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt370","nombre":"Cheddar USA","categoria":"INTERNACIONAL","url":"https://livestream.chdrstatic.com/b93e5b0d43ea306310a379971e384964acbe4990ce193c0bd50078275a9a657d/cheddar-42620/cheddarweblive/cheddar/index.m3u8","logo":"https://graph.facebook.com/cheddar/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt371","nombre":"Bloomberg USA","categoria":"INTERNACIONAL","url":"https://www.bloomberg.com/media-manifest/streams/us.m3u8","logo":"https://pbs.twimg.com/profile_images/991792042094354432/DG1Ruupb_200x200.jpg","fallbacks":[]},
    {"id":"tdt372","nombre":"CourtTV USA","categoria":"INTERNACIONAL","url":"https://content.uplynk.com/channel/6c0bd0f94b1d4526a98676e9699a10ef.m3u8","logo":"https://graph.facebook.com/courttv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt373","nombre":"NASA TV Public","categoria":"INTERNACIONAL","url":"https://ntv1.akamaized.net/hls/live/2014075/NASA-NTV1-HLS/master.m3u8","logo":"https://graph.facebook.com/NASA/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt374","nombre":"NASA TV Media","categoria":"INTERNACIONAL","url":"https://ntv2.akamaized.net/hls/live/2013923/NASA-NTV2-HLS/master.m3u8","logo":"https://graph.facebook.com/NASA/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt375","nombre":"WeatherNation USA","categoria":"INTERNACIONAL","url":"https://d2ferbiwcx1539.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-8zd06wicndthf-ssai-prd/WNNationalSamsung/WNNationalSamsung.m3u8","logo":"https://graph.facebook.com/WeatherNation/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt376","nombre":"America's Voice USA","categoria":"INTERNACIONAL","url":"https://d2jiqiw4g5lj5k.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/AmericasVoiceChannel-prod/AVSamsung/AVSamsung.m3u8","logo":"https://graph.facebook.com/RealAmericasVoice/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt377","nombre":"BUZZR TV USA","categoria":"INTERNACIONAL","url":"https://buzzrota-ono.amagi.tv/playlist.m3u8","logo":"https://graph.facebook.com/BUZZRtv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt378","nombre":"Newsmax TV USA","categoria":"NOTICIAS","url":"https://nmxlive.akamaized.net/hls/live/529965/Live_1/index.m3u8","logo":"https://graph.facebook.com/newsmax/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt379","nombre":"Noticias Telemundo USA","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCRwA1NUcUnwsly35ikGhp0A&autoplay=1","logo":"https://graph.facebook.com/NoticiasTelemundo/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt380","nombre":"Noticias Univision USA","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UC32TdiIsh_5X8tKr_9rKQyA&autoplay=1","logo":"https://yt3.googleusercontent.com/Nmmjyjg_haweMTgH27iza810trmWay24hZosL8UhE29fGkDn6yPqUlnSjeuyos5JMK2H-MiVFg=s200","fallbacks":[]},
    {"id":"tdt381","nombre":"America TeVe USA","categoria":"INTERNACIONAL","url":"https://live.gideo.video/americateve2/master.m3u8","logo":"https://graph.facebook.com/americateve/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt382","nombre":"TV Florida USA","categoria":"INTERNACIONAL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?cb=[CACHEBUSTER]&network_id=16147&live=1&avod=0&hls_marker=1&pod_duration=120&ssai_enabled=1&content_network=streamingconnect&position=preroll&app_bundle=com.streamingconnect.viva&app_category=linear_tv&app_domain=mirametv.live&content_cat=IAB1&content_channel=tvflorida&content_genre=tv_broadcaster&content_rating=TV-G&content_id=mirametv_live&us_privacy=[US_PRIVACY]&gdpr=[GDPR]&min_ad_duration=6&max_ad_duration=120&ifa_type=[IFA_TYPE]","logo":"https://graph.facebook.com/tvfloridausa/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt383","nombre":"NTN24 América","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCEJs1fTF3KszRJGxJY14VrA&autoplay=1","logo":"https://graph.facebook.com/NTN24/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt384","nombre":"Canal 6 Multimedios Mexico","categoria":"INTERNACIONAL","url":"https://mdstrm.com/live-stream-playlist/57b4dbf5dbbfc8f16bb63ce1.m3u8","logo":"https://graph.facebook.com/multimediostv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt385","nombre":"Milenio Mexico","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCFxHplbcoJK9m70c4VyTIxg&autoplay=1","logo":"https://graph.facebook.com/MilenioDiario/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt386","nombre":"Excelsior Mexico","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UClqo4ZAAZ01HQdCTlovCgkA&autoplay=1","logo":"https://graph.facebook.com/ExcelsiorMex/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt387","nombre":"ADN Noticias Mexico","categoria":"NOTICIAS","url":"https://mdstrm.com/live-stream-playlist/60b578b060947317de7b57ac.m3u8","logo":"https://pbs.twimg.com/profile_images/1968512728059850752/KUWD445m_400x400.jpg","fallbacks":[]},
    {"id":"tdt388","nombre":"Canal Once Mexico","categoria":"INTERNACIONAL","url":"https://vivo.canaloncelive.tv/oncedos/ngrp:pruebachunks_all/playlist.m3u8","logo":"https://graph.facebook.com/CANALONCETV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt389","nombre":"Quiero TV Mexico","categoria":"INTERNACIONAL","url":"https://stream.ontvmx.com/ontv/ghxTYEQmKkB2UJyVuW/playlist.m3u8","logo":"https://graph.facebook.com/quierotvGDL/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt390","nombre":"Mexico Travel TV","categoria":"INTERNACIONAL","url":"https://5ca9af4645e15.streamlock.net/mexicotravel/videomexicotravel/playlist.m3u8","logo":"https://graph.facebook.com/MexicoTravelChannelTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt391","nombre":"Estrella TV Mexico","categoria":"INTERNACIONAL","url":"https://cdn-uw2-prod.tsv2.amagi.tv/linear/amg00567-estrellamedia-estrellatv-estrellamedia/playlist.m3u8","logo":"https://graph.facebook.com/EstrellaTVNetwork/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt392","nombre":"TELE 10 Nayarit Mexico","categoria":"INTERNACIONAL","url":"https://live.iplanay.gob.mx/hls/nayarittv.m3u8","logo":"https://graph.facebook.com/Tele10Nayarit/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt393","nombre":"Teleantioquia Colombia","categoria":"INTERNACIONAL","url":"https://liveingesta118.cdnmedia.tv/teleantioquialive/smil:dvrlive.smil/playlist_DVR.m3u8","logo":"https://graph.facebook.com/CanalTeleantioquia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt394","nombre":"Canal Capital Colombia","categoria":"INTERNACIONAL","url":"https://mdstrm.com/live-stream-playlist/6952dc88cb62083467eb6ab4.m3u8","logo":"https://graph.facebook.com/CanalCapitalOficial/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt395","nombre":"Señal Colombia","categoria":"INTERNACIONAL","url":"https://streaming.rtvc.gov.co/TV_Senal_Colombia_live/smil:live.smil/playlist.m3u8","logo":"https://graph.facebook.com/senalcolombiapaginaoficial/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt396","nombre":"Telepacifico Colombia","categoria":"INTERNACIONAL","url":"https://live-edge-eu-1.cdn.enetres.net/6E5C615AA5FF4123ACAF0DAB57B7B8DC021/live-telepacifico/index.m3u8","logo":"https://graph.facebook.com/TelepacificoTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt397","nombre":"Canal Telecaribe Colombia","categoria":"INTERNACIONAL","url":"https://liveingesta118.cdnmedia.tv/telecaribetvlive/smil:rtmp01.smil/playlist.m3u8?DVR","logo":"https://graph.facebook.com/telecaribeEnvivo/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt398","nombre":"Canal TRO Colombia","categoria":"INTERNACIONAL","url":"https://liveingesta118.cdnmedia.tv/canaltro2live/smil:live.smil/playlist.m3u8","logo":"https://graph.facebook.com/canaltro/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt399","nombre":"Citytv Colombia","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCv5Oy_TJFvGKXjeNzzJE_PQ&autoplay=1","logo":"https://graph.facebook.com/citytv.com.co/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt400","nombre":"Todo Noticias Argentina","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCj6PcyLvpnIRT_2W_mwa9Aw&autoplay=1","logo":"https://graph.facebook.com/todonoticias/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt401","nombre":"Telefé Noticias Argentina","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UChxGASjdNEYHhVKpl667Huw&autoplay=1","logo":"https://graph.facebook.com/telefe/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt402","nombre":"La Nación Argentina","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCba3hpU7EFBSk817y9qZkiA&autoplay=1","logo":"https://graph.facebook.com/lanacion/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt403","nombre":"América TV Argentina","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UC6NVDkuzY2exMOVFw4i9oHw&autoplay=1","logo":"https://graph.facebook.com/AmericaTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt404","nombre":"C5N Argentina","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCFgk2Q2mVO1BklRQhSv6p0w&autoplay=1","logo":"https://graph.facebook.com/C5N.Noticias/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt405","nombre":"TV Pública Argentina","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCs231K71Bnu5295_x0MB5Pg&autoplay=1","logo":"https://graph.facebook.com/TVPublica/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt406","nombre":"A24 Argentina","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCR9120YBAqMfntqgRTKmkjQ&autoplay=1","logo":"https://graph.facebook.com/A24com/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt407","nombre":"Crónica TV Argentina","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCT7KFGv6s2a-rh2Jq8ZdM1g&autoplay=1","logo":"https://graph.facebook.com/cronicatelevision/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt408","nombre":"Exitosa Noticias Perú","categoria":"NOTICIAS","url":"https://luna-4-video.mediaserver.digital/exitosatv_233b-4b49-a726-5a451262/index.m3u8","logo":"https://graph.facebook.com/Exitosanoticias/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt409","nombre":"Panamericana Perú","categoria":"INTERNACIONAL","url":"https://live.cdnlivecdn.com/live/cde7c1935927ca1cf540d70c835deb58aca3fd15.m3u8","logo":"https://graph.facebook.com/panamericana.pe/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt410","nombre":"TV Perú","categoria":"INTERNACIONAL","url":"https://cdnhd.iblups.com/hls/777b4d4cc0984575a7d14f6ee57dbcaf7.m3u8","logo":"https://graph.facebook.com/TVPeruOficial/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt411","nombre":"TV Perú Noticias","categoria":"NOTICIAS","url":"https://cdnhd.iblups.com/hls/902c1a0395264f269f1160efa00660e47.m3u8","logo":"https://graph.facebook.com/noticias.tvperu/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt412","nombre":"Canal IPe Perú","categoria":"INTERNACIONAL","url":"https://cdnhd.iblups.com/hls/3f2cb1658d114f2693eff18d83199e677.m3u8","logo":"https://graph.facebook.com/canalipe/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt413","nombre":"Latina Perú","categoria":"INTERNACIONAL","url":"https://redirector.rudo.video/hls-video/567ffde3fa319fadf3419efda25619456231dfea/latina/latina.smil/playlist.m3u8","logo":"https://graph.facebook.com/Latina.pe/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt414","nombre":"Cosmos TV Perú","categoria":"INTERNACIONAL","url":"https://videoserver.tmcreativos.com:19360/tvcosmos/tvcosmos.m3u8","logo":"https://pbs.twimg.com/profile_images/1904206504753811457/66CbqvH1_200x200.jpg","fallbacks":[]},
    {"id":"tdt415","nombre":"TeleSUR Venezuela","categoria":"INTERNACIONAL","url":"https://mblesmain01.telesur.ultrabase.net/mbliveMain/hd/playlist.m3u8","logo":"https://graph.facebook.com/teleSUR/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt416","nombre":"Globovision Venezuela","categoria":"INTERNACIONAL","url":"https://59d39900ebfb8.streamlock.net/globo-720p/globo-720p/playlist.m3u8","logo":"https://graph.facebook.com/globovision/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt417","nombre":"Televen TV Venezuela","categoria":"INTERNACIONAL","url":"https://d39cdj6x0ssnqk.cloudfront.net/out/v1/ae3f5ad3ac9d4bcfbedc1894a62782b4/index.m3u8","logo":"https://graph.facebook.com/TelevenTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt418","nombre":"VPI TV Venezuela","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCVFiIRuxJ2GmJLUkHmlmj4w&autoplay=1","logo":"https://graph.facebook.com/vpitv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt419","nombre":"24h Chile","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCTXNz3gjAypWp3EhlIATEJQ&autoplay=1","logo":"https://graph.facebook.com/24horas.cl/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt420","nombre":"TELE13 Chile","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCsRnhjcUCR78Q3Ud6OXCTNg&autoplay=1","logo":"https://graph.facebook.com/teletrece/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt421","nombre":"Meganoticias Chile","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCkccyEbqhhM3uKOI6Shm-4Q&autoplay=1","logo":"https://graph.facebook.com/meganoticiascl/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt422","nombre":"TeleAmazonas Ecuador","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCCwRtme3lumNRQXMO2EvCvw&autoplay=1","logo":"https://graph.facebook.com/TeleamazonasEcuador/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt423","nombre":"Ecuador TV Ecuador","categoria":"INTERNACIONAL","url":"https://samson.streamerr.co:8081/shogun/tracks-v1a1/mono.m3u8","logo":"https://pbs.twimg.com/profile_images/1962545090485784576/uXP9DhVk_200x200.jpg","fallbacks":[]},
    {"id":"tdt424","nombre":"Oromar TV Ecuador","categoria":"INTERNACIONAL","url":"https://stream.oromar.tv/hls/oromartv_hi/index.m3u8","logo":"https://graph.facebook.com/oromartv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt425","nombre":"Pat Bolivia","categoria":"INTERNACIONAL","url":"https://www.redpat.tv:8000/play/12/74929205.m3u8","logo":"https://graph.facebook.com/patboliviahd/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt426","nombre":"Cubavisión TV Cuba","categoria":"INTERNACIONAL","url":"https://cdn.teveo.cu/live/video/A36pWmuWvZBQskuZ/ngrp:gppfydfzpSUn9Udy.stream/playlist.m3u8","logo":"https://graph.facebook.com/CubavisionInternacional/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt427","nombre":"ABC TV Paraguay","categoria":"INTERNACIONAL","url":"https://cdn.jwplayer.com/live/broadcast/aide2636.m3u8","logo":"https://graph.facebook.com/ABCTVpy/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt428","nombre":"WTV Nicaragua","categoria":"INTERNACIONAL","url":"https://cloudvideo.servers10.com:8081/8130/index.m3u8","logo":"https://graph.facebook.com/WTVNicaraguacanal20/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt429","nombre":"TeleDiario Costa Rica","categoria":"NOTICIAS","url":"https://mdstrm.com/live-stream-playlist/5a7b1e63a8da282c34d65445.m3u8","logo":"https://graph.facebook.com/MultimediosCR/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt430","nombre":"WIPR Puerto Rico","categoria":"INTERNACIONAL","url":"https://streamwipr.pr/hls/stream/index.m3u8","logo":"https://graph.facebook.com/wiprtv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt431","nombre":"CNN Brasil","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCvdwhh_fDyWccR42-rReZLw&autoplay=1","logo":"https://graph.facebook.com/cnnbrasil/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt432","nombre":"TV Cultura Brasil","categoria":"INTERNACIONAL","url":"https://player-tvcultura.stream.uol.com.br/live/tvcultura.m3u8","logo":"https://graph.facebook.com/tvcultura/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt433","nombre":"Record News Brasil","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCuiLR4p6wQ3xLEm15pEn1Xw&autoplay=1","logo":"https://graph.facebook.com/recordnews/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt434","nombre":"Rede Massa Brasil","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCX0P-o4zRG7vkGl226MfRYg&autoplay=1","logo":"https://graph.facebook.com/RedeMassa/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt435","nombre":"CGTN China","categoria":"INTERNACIONAL","url":"https://espanol-livews.cgtn.com/hls/LSveOGBaBw41Ea7ukkVAUdKQ220802LSTexu6xAuFH8VZNBLE1ZNEa220802cd/playlist.m3u8","logo":"https://graph.facebook.com/cgtnenespanol/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt436","nombre":"CGTN News China","categoria":"NOTICIAS","url":"https://english-livebkali.cgtn.com/live/encgtn.m3u8","logo":"https://graph.facebook.com/ChinaGlobalTVNetwork/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt437","nombre":"CGTN Documentary China","categoria":"INTERNACIONAL","url":"https://english-livebkali.cgtn.com/live/doccgtn.m3u8","logo":"https://graph.facebook.com/ChinaGlobalTVNetwork/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt438","nombre":"Al Jazeera Catar","categoria":"INTERNACIONAL","url":"https://live-hls-web-aje-gcp.thehlive.com/AJE/index.m3u8","logo":"https://graph.facebook.com/aljazeera/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt439","nombre":"NHK World Japón","categoria":"INTERNACIONAL","url":"https://media-tyo.hls.nhkworld.jp/hls/w/live/master.m3u8","logo":"https://graph.facebook.com/nhkworld/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt440","nombre":"Nippon News TV Japón","categoria":"NOTICIAS","url":"https://n24-cdn-live-x.ntv.co.jp/ch01/index.m3u8?","logo":"https://graph.facebook.com/ntvnews24/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt441","nombre":"KBS World Corea del Sur","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UC5BMQOsAB8hKUyHu9KI6yig&autoplay=1","logo":"https://graph.facebook.com/KBSWORLD/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt442","nombre":"Arirang TV Corea del Sur","categoria":"INTERNACIONAL","url":"https://amdlive-ch01-g-ctnd-com.akamaized.net/arirang_1gch/smil:arirang_1gch.smil/playlist.m3u8","logo":"https://graph.facebook.com/arirangtv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt443","nombre":"Chung T'ien CTI News Taiwán","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UC5l1Yto5oOIgRXlI4p4VKbw&autoplay=1","logo":"https://graph.facebook.com/52news/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt444","nombre":"EBC News Taiwán","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCR3asjvr_WAaxwJYEDV_Bfw&autoplay=1","logo":"https://graph.facebook.com/news.ebc/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt445","nombre":"Al Arabiya Emiratos Árabes","categoria":"INTERNACIONAL","url":"https://live.alarabiya.net/alarabiapublish/alarabiya.smil/playlist.m3u8","logo":"https://graph.facebook.com/AlArabiya/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt446","nombre":"Ary News Pakistan","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCMmpLL2ucRHAXbNHiCPyIyg&autoplay=1","logo":"https://graph.facebook.com/arynewsasia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt447","nombre":"Geo News Pakistan","categoria":"NOTICIAS","url":"https://jk3lz82elw79-hls-live.5centscdn.com/newgeonews/07811dc6c422334ce36a09ff5cd6fe71.sdp/playlist.m3u8","logo":"https://graph.facebook.com/GeoUrduDotTv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt448","nombre":"Express News Pakistan","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCTur7oM6mLL0rM2k0znuZpQ&autoplay=1","logo":"https://graph.facebook.com/expressnewspk/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt449","nombre":"India Today","categoria":"INTERNACIONAL","url":"https://indiatodaylive.akamaized.net/hls/live/2014320/indiatoday/indiatodaylive/playlist.m3u8","logo":"https://graph.facebook.com/IndiaToday/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt450","nombre":"New Delhi TV 24x7 India","categoria":"INTERNACIONAL","url":"https://ndtv24x7elemarchana.akamaized.net/hls/live/2003678/ndtv24x7/ndtv24x7master.m3u8","logo":"https://graph.facebook.com/ndtv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt451","nombre":"Times Now India","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCckHqySbfy5FcPP6MD_S-Yg&autoplay=1","logo":"https://graph.facebook.com/Timesnow/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt452","nombre":"Republic World TV India","categoria":"INTERNACIONAL","url":"https://vg-republictvlive.akamaized.net/v1/master/611d79b11b77e2f571934fd80ca1413453772ac7/vglive-sk-366023/main.m3u8","logo":"https://graph.facebook.com/RepublicWorld/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt453","nombre":"Hispan TV Iran","categoria":"INTERNACIONAL","url":"https://live.presstv.ir/hls/hispantv_5_482/index.m3u8","logo":"https://pbs.twimg.com/profile_images/1645382928422109184/lUdeHBAs_200x200.jpg","fallbacks":[]},
    {"id":"tdt454","nombre":"Channel NewsAsia","categoria":"NOTICIAS","url":"https://d2e1asnsl7br7b.cloudfront.net/7782e205e72f43aeb4a48ec97f66ebbe/index.m3u8","logo":"https://graph.facebook.com/ChannelNewsAsia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt455","nombre":"TVBS News Taiwán","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UC5nwNW4KdC0SzrhF9BXEYOQ&autoplay=1","logo":"https://graph.facebook.com/tvbsfb/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt456","nombre":"SET News Taiwán","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UC2TuODJhC03pLgd6MpWP0iw&autoplay=1","logo":"https://graph.facebook.com/setnews/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt457","nombre":"UNTV News & Rescue Filipinas","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UC3XaG-7UVi2vD8ZZEMNnnpw&autoplay=1","logo":"https://graph.facebook.com/UNTVNewsRescue/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt458","nombre":"TVK Camboya","categoria":"INTERNACIONAL","url":"https://live.kh.malimarcdn.com/live/tvk.stream/playlist.m3u8","logo":"https://play-lh.googleusercontent.com/vleeuJK2i7TYUHvqoQfsujviGBQ1EdFw4kZXlMh6f2V07YQfdK5nDBWeWY5o1IrIQw=w200","fallbacks":[]},
    {"id":"tdt459","nombre":"RTHK 31 32 Hong Kong","categoria":"INTERNACIONAL","url":"https://www.rthk.hk/feeds/dtt/rthktv31_https.m3u8","logo":"https://graph.facebook.com/RTHK.HK/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt460","nombre":"Teledifusão de Macau","categoria":"INTERNACIONAL","url":"https://live5.tdm.com.mo/ch2/ch2.live/playlist.m3u8","logo":"https://graph.facebook.com/Canal.Macau/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt461","nombre":"Medi1 TV Marruecos","categoria":"INTERNACIONAL","url":"https://cdn.live.easybroadcast.io/abr_corp/83_medi1tv-arabic_g90v4ec/playlist_dvr.m3u8","logo":"https://graph.facebook.com/Medi1TV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt462","nombre":"AfricaNews","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UC1_E8NeF5QHY2dtdLRBCCLA&autoplay=1","logo":"https://graph.facebook.com/africanews.channel/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt463","nombre":"Joy News TV Ghana","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UChd1DEecCRlxaa0-hvPACCw&autoplay=1","logo":"https://graph.facebook.com/JoyNewsOnTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt464","nombre":"Channels TV Nigeria","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCEXGDNclvmg6RW0vipJYsTQ&autoplay=1","logo":"https://graph.facebook.com/channelsforum/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt465","nombre":"TVGE 1 Guinea Ecuatorial","categoria":"INTERNACIONAL","url":"https://rrsatrtmp.tulix.tv/tvge1/tvge1multi.smil/playlist.m3u8","logo":"https://pbs.twimg.com/profile_images/1382981938231775232/-lv9ymLe_200x200.jpg","fallbacks":[]},
    {"id":"tdt466","nombre":"RASD TV","categoria":"INTERNACIONAL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?network_id=12830&live=1","logo":"https://graph.facebook.com/televisionsaharaui/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt467","nombre":"SenTV Senegal","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCKbMNmSR3KlI9v3xeInHEYA&autoplay=1","logo":"https://graph.facebook.com/sentvtelevision/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt468","nombre":"ABC News Australia","categoria":"NOTICIAS","url":"https://abc-news-dmd-streams-1.akamaized.net/out/v1/abc83881886746b0802dc3e7ca2bc792/index.m3u8","logo":"https://graph.facebook.com/abcnews.au/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt469","nombre":"Bloomberg Quicktake","categoria":"INTERNACIONAL","url":"https://www.bloomberg.com/media-manifest/streams/qt.m3u8","logo":"https://yt3.ggpht.com/fTP5oS376nZhVbS55-OocogCJCDH4UXIyRrirF6keIya4AN4I54TmLkFnnjvE4FRq5UMv8BO=s200","fallbacks":[]},
    {"id":"tdt470","nombre":"Tastemade","categoria":"INTERNACIONAL","url":"https://cdn-uw2-prod.tsv2.amagi.tv/linear/amg00047-tastemade-tastemadees16international24i-ono/playlist.m3u8","logo":"https://graph.facebook.com/TastemadeEs/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt471","nombre":"Fashion TV","categoria":"INTERNACIONAL","url":"https://ftv1.b-cdn.net/bfdbb576-83f7-11f0-9f89-0200170e3e04_1000028043_HLS/manifest.m3u8","logo":"https://graph.facebook.com/FTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt472","nombre":"Miami TV Fashion","categoria":"INTERNACIONAL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?cb=[CACHEBUSTER]&network_id=16284&live=1&avod=0&hls_marker=1&pod_duration=120&position=preroll&app_bundle=com.streamingconnect.viva&app_category=linear_tv&content_cat=IAB8&content_channel=cocinafamiliar&content_genre=tv_broadcaster&content_network=streamingconnect&content_rating=TV-G&us_privacy=[US_PRIVACY]&gdpr=[GDPR]&ifa_type=[IFA_TYPE]&ssai_enabled=1&content_id=mirametv_live&min_ad_duration=6&max_ad_duration=120&app_domain=mirametv.live&ua=[%UA%]&device_type=[DEVICE_TYPE]&min_ad_duration=6&max_ad_duration=120&ip=[IP]","logo":"https://miamitv.com/images/669a96975172d_Miami%20TV%20Fashion.jpg","fallbacks":[]},
    {"id":"tdt473","nombre":"Miami TV Gold","categoria":"INTERNACIONAL","url":"https://8f4cbe9fa8d44aa3bfd4283527a9effd.mediatailor.us-east-2.amazonaws.com/v1/master/c3d3fd1c31fa281b88eab2cd253e2ca576b6628b/fast_gold/playlist.m3u8","logo":"https://miamitv.com/images/1718230773.jpg","fallbacks":[]},
    {"id":"tdt474","nombre":"Miami TV Latino","categoria":"INTERNACIONAL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?cb=[CACHEBUSTER]&network_id=16285&live=1&avod=0&hls_marker=1&pod_duration=120&position=preroll&app_bundle=com.streamingconnect.viva&app_category=linear_tv&content_cat=IAB8&content_channel=cocinafamiliar&content_genre=tv_broadcaster&content_network=streamingconnect&content_rating=TV-G&us_privacy=[US_PRIVACY]&gdpr=[GDPR]&ifa_type=[IFA_TYPE]&ssai_enabled=1&content_id=mirametv_live&min_ad_duration=6&max_ad_duration=120&app_domain=mirametv.live&ua=[%25UA%25]&device_type=[DEVICE_TYPE]&min_ad_duration=6&max_ad_duration=120&ip=[IP]","logo":"https://miamitv.com/images/1718228333.jpg","fallbacks":[]},
    {"id":"tdt475","nombre":"Miami TV Jenny Live","categoria":"INTERNACIONAL","url":"https://bdc8100df748400cabc7e133824c8ceb.mediatailor.us-east-2.amazonaws.com/v1/master/c3d3fd1c31fa281b88eab2cd253e2ca576b6628b/fast-jennylive/playlist.m3u8","logo":"https://miamitv.com/images/1718228364.jpg","fallbacks":[]},
    {"id":"tdt476","nombre":"Agrotendencia","categoria":"INTERNACIONAL","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?cb=[CACHEBUSTER]&network_id=16427&hls_marker=1&position=preroll&pod_duration=120&app_bundle=com.streamingconnect.viva&ssai_enabled=1&content_channel=mirametv&app_domain=mirametv.live&app_category=linear_tv&content_cat=IAB1&content_genre=tv_broadcaster&content_network=streamingconnect&content_rating=TV-G&gdpr=[GDPR]&content_id=mirametv_live&device_type=[DEVICE_TYPE]&ip=[IP]&min_ad_duration=6&max_ad_duration=120&ua=[UA]","logo":"https://graph.facebook.com/agrotendencia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt477","nombre":"Classic Arts Showcase","categoria":"INTERNACIONAL","url":"https://classicarts.akamaized.net/hls/live/1024257/CAS/master.m3u8","logo":"https://pbs.twimg.com/profile_images/956583141245775872/2en3-8Ag_200x200.jpg","fallbacks":[]},
    {"id":"tdt478","nombre":"Mr Bean 24h","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCEwIUtFBhaI2L2PuKv0KL2g&autoplay=1","logo":"https://graph.facebook.com/MrBean/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt479","nombre":"AKC TV Dogs","categoria":"INTERNACIONAL","url":"https://install.akctvcontrol.com/speed/broadcast/138/desktop-playlist.m3u8","logo":"https://graph.facebook.com/WatchAKCTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt480","nombre":"ServusTV WetterPanorama","categoria":"INTERNACIONAL","url":"https://rbmn-live.akamaized.net/hls/live/665268/Wetterpanorama/master.m3u8","logo":"https://graph.facebook.com/ServusTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt481","nombre":"Red Bull TV","categoria":"INTERNACIONAL","url":"https://rbmn-live.akamaized.net/hls/live/590964/BoRB-AT/master.m3u8","logo":"https://graph.facebook.com/RedBull/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt482","nombre":"Motorsport.tv","categoria":"DEPORTES","url":"https://7daa9e4f.wurl.com/master/f36d25e7e52f1ba8d7e56eb859c636563214f541/U3BvcnRzVHJpYmFsLWV1X01vdG9yc3BvcnR0dl9ITFM/playlist.m3u8","logo":"https://graph.facebook.com/Motorsport.tvUK/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt483","nombre":"Meridiano Venezuela","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCcYfZbinuodyF8rVkl4u7Lw&autoplay=1","logo":"https://graph.facebook.com/Meridiano.Dearmas/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt484","nombre":"Stadium USA","categoria":"INTERNACIONAL","url":"https://2d006483e2aa43fe812f7b464cb2916d.mediatailor.us-east-1.amazonaws.com/v1/master/44f73ba4d03e9607dcd9bebdcb8494d86964f1d8/Samsung_Stadium/playlist.m3u8","logo":"https://pbs.twimg.com/profile_images/1912970794524610560/M1vEMVlm_200x200.jpg","fallbacks":[]},
    {"id":"tdt485","nombre":"Garage TV Argentina","categoria":"INTERNACIONAL","url":"https://stream1.sersat.com/hls/garagetv.m3u8","logo":"https://pbs.twimg.com/profile_images/1169992187314167808/TeabGtEB_200x200.jpg","fallbacks":[]},
    {"id":"tdt486","nombre":"MoreThanSports TV","categoria":"DEPORTES","url":"https://mts1.iptv-playoutcenter.de/mts/mts-web/playlist.m3u8","logo":"https://graph.facebook.com/mtssportstv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt487","nombre":"Int. Table Soccer Federation","categoria":"INTERNACIONAL","url":"https://stream.ads.ottera.tv/playlist.m3u8?network_id=7333","logo":"https://graph.facebook.com/ITSF.tablesoccer/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt488","nombre":"Bike Channel","categoria":"INTERNACIONAL","url":"https://stream.prod-01.milano.nxmedge.net/argocdn/bikechannel/video.m3u8","logo":"https://graph.facebook.com/bikechannelofficial/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt489","nombre":"Sol Música España","categoria":"MUSICA","url":"https://d2glyu450vvghm.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-21u4g5cjglv02/sm.m3u8","logo":"https://graph.facebook.com/solmusica/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt490","nombre":"Café del Mar Ibiza España","categoria":"MUSICA","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCha0QKR45iw7FCUQ3-1PnhQ&autoplay=1","logo":"https://graph.facebook.com/cafedelmaribizaofficialpage/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt491","nombre":"Activa TV España","categoria":"MUSICA","url":"https://streamtv.mediasector.es/hls/activatv/index.m3u8","logo":"https://graph.facebook.com/activafm.radiomusical/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt492","nombre":"Molahits TV España","categoria":"MUSICA","url":"https://ventdelnord.tv:8080/mola/directe.m3u8","logo":"https://graph.facebook.com/molahitstv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt493","nombre":"Verbena TV España","categoria":"MUSICA","url":"https://streamtv2.elitecomunicacion.cloud:3144/live/verbenatvlive.m3u8","logo":"https://pbs.twimg.com/profile_images/1463159511133442059/uVV15n4k_200x200.jpg","fallbacks":[]},
    {"id":"tdt494","nombre":"Cadena Elite España","categoria":"MUSICA","url":"https://cloudvideo.servers10.com:8081/8004/index.m3u8","logo":"https://graph.facebook.com/cadena.elitegranada/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt495","nombre":"Spektra TV España","categoria":"MUSICA","url":"https://cloudvideo.servers10.com:8081/8026/tracks-v1a1/index.m3u8","logo":"https://graph.facebook.com/spektramusictv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt496","nombre":"Radio Italia TV","categoria":"MUSICA","url":"https://radioitaliatv.akamaized.net/hls/live/2093117/RadioitaliaTV/master.m3u8","logo":"https://graph.facebook.com/radioitalia/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt497","nombre":"RTL 102.5 Italia","categoria":"MUSICA","url":"https://dd782ed59e2a4e86aabf6fc508674b59.msvdn.net/live/S97044836/tbbP8T1ZRPBL/playlist_video.m3u8","logo":"https://graph.facebook.com/RTL102.5/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt498","nombre":"RTL Radio Freccia Italia","categoria":"MUSICA","url":"https://dd782ed59e2a4e86aabf6fc508674b59.msvdn.net/live/S3160845/0tuSetc8UFkF/playlist_video.m3u8","logo":"https://graph.facebook.com/RTL102.5/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt499","nombre":"RTL Zeta Italia","categoria":"MUSICA","url":"https://dd782ed59e2a4e86aabf6fc508674b59.msvdn.net/live/S9346184/XEx1LqlYbNic/playlist_video.m3u8","logo":"https://graph.facebook.com/RTL102.5/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt500","nombre":"RTL 102.5 Best Italia","categoria":"MUSICA","url":"https://dd782ed59e2a4e86aabf6fc508674b59.msvdn.net/live/S76960628/OEPHRUIctA0M/playlist_video.m3u8","logo":"https://graph.facebook.com/RTL102.5/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt501","nombre":"RTL 102.5 Disco Italia","categoria":"MUSICA","url":"https://dd782ed59e2a4e86aabf6fc508674b59.msvdn.net/live/S51100361/0Fb4R3k82b5Z/playlist_video.m3u8","logo":"https://graph.facebook.com/RTL102.5/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt502","nombre":"RTL 102.5 Caliente Italia","categoria":"MUSICA","url":"https://dd782ed59e2a4e86aabf6fc508674b59.msvdn.net/live/S8448465/zTYa1Z5Op9ue/playlist_video.m3u8","logo":"https://graph.facebook.com/RTL102.5/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt503","nombre":"RTL 102.5 Bro&Sis Italia","categoria":"MUSICA","url":"https://dd782ed59e2a4e86aabf6fc508674b59.msvdn.net/live/S75007890/MUGHuxc9dQ3b/playlist_video.m3u8","logo":"https://graph.facebook.com/RTL102.5/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt504","nombre":"RTL 102.5 Napulè Italia","categoria":"MUSICA","url":"https://dd782ed59e2a4e86aabf6fc508674b59.msvdn.net/live/S27134503/0f9AhuwKlhnZ/playlist_video.m3u8","logo":"https://graph.facebook.com/RTL102.5/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt505","nombre":"RTL 102.5 Traffic Italia","categoria":"MUSICA","url":"https://dd782ed59e2a4e86aabf6fc508674b59.msvdn.net/live/S38122967/2lyQRIAAGgRR/playlist_video.m3u8","logo":"https://graph.facebook.com/RTL102.5/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt506","nombre":"RDS Social TV Italia","categoria":"MUSICA","url":"https://stream.rdstv.radio/index.m3u8","logo":"https://graph.facebook.com/rds.grandisuccessi/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt507","nombre":"m2o Italia","categoria":"MUSICA","url":"https://4c4b867c89244861ac216426883d1ad0.msvdn.net/live/S62628868/uhdWBlkC1AoO/playlist.m3u8","logo":"https://graph.facebook.com/radiom2o/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt508","nombre":"Radio Capital Italia","categoria":"MUSICA","url":"https://4c4b867c89244861ac216426883d1ad0.msvdn.net/live/S35394734/Z6U2wGoDYANk/playlist.m3u8","logo":"https://graph.facebook.com/RadioCapitalfm/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt509","nombre":"70-80's Italia","categoria":"MUSICA","url":"https://585b674743bbb.streamlock.net/9050/9050/playlist.m3u8","logo":"https://play-lh.googleusercontent.com/OwKy6Ef_hOsjuSYtgh5aOHndFs2uo9evgrrjO4DYiOwXiAtWtSZiFMWY_OIcLU170NA=w200","fallbacks":[]},
    {"id":"tdt510","nombre":"On TV Portugal","categoria":"MUSICA","url":"https://5ce9406b73c33.streamlock.net/ONFM/livestream/master.m3u8","logo":"https://graph.facebook.com/ONFM93.8/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt511","nombre":"Kronehit Austria","categoria":"MUSICA","url":"https://bitcdn-kronehit.bitmovin.com/v2/hls/playlist.m3u8","logo":"https://graph.facebook.com/kronehit/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt512","nombre":"QMusic Países Bajos","categoria":"MUSICA","url":"https://stream.qmusic.nl/qmusic/videohls.m3u8","logo":"https://graph.facebook.com/QmusicNL/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt513","nombre":"Ocko Chequia","categoria":"MUSICA","url":"https://ocko-live.ssl.cdn.cra.cz/channels/ocko/playlist/cze/live_hq.m3u8","logo":"https://graph.facebook.com/tvocko/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt514","nombre":"Star Chequia","categoria":"MUSICA","url":"https://ocko-live.ssl.cdn.cra.cz/channels/ocko_gold/playlist/cze/live_hq.m3u8","logo":"https://graph.facebook.com/ockostar/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt515","nombre":"Expres Chequia","categoria":"MUSICA","url":"https://ocko-live.ssl.cdn.cra.cz/channels/ocko_expres/playlist/cze/live_hq.m3u8","logo":"https://graph.facebook.com/OckoExpres/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt516","nombre":"4FUN TV Polonia","categoria":"MUSICA","url":"https://stream.4fun.tv:8888/hls/4f_high/index.m3u8","logo":"https://graph.facebook.com/4FUN.TV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt517","nombre":"Number1 FM Turquía","categoria":"MUSICA","url":"https://b01c02nl.mediatriple.net/videoonlylive/mtkgeuihrlfwlive/broadcast_5c9e17cd59e8b.smil/playlist.m3u8","logo":"https://graph.facebook.com/Number1FM/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt518","nombre":"Power TV Turquía","categoria":"MUSICA","url":"https://livetv.powerapp.com.tr/powerTV/powerhd.smil/playlists.m3u8","logo":"https://graph.facebook.com/powerapp/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt519","nombre":"NRG91 Grecia","categoria":"MUSICA","url":"https://5c389faa13be3.streamlock.net:9553/onweb/live/playlist.m3u8","logo":"https://yt3.ggpht.com/KGxBhcmGT-UX_3Hhnfw7Gwnypyn4XzUQ3_OElJuNKllBcZmE58-z_FpozwfIxl9fA7z9RPnVBwE=s200","fallbacks":[]},
    {"id":"tdt520","nombre":"CMC Croacia","categoria":"MUSICA","url":"https://stream.cmctv.hr:49998/cmc/live.m3u8","logo":"https://graph.facebook.com/CroatianMusicChannel/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt521","nombre":"Sky Folk Macedonia","categoria":"MUSICA","url":"https://eu.live.skyfolk.mk/live.m3u8","logo":"https://graph.facebook.com/skyfolk.mk/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt522","nombre":"Tropical Moon TV","categoria":"MUSICA","url":"https://stream-us-east-1.getpublica.com/playlist.m3u8?cb=[CACHEBUSTER]&network_id=16185&live=1&avod=0&hls_marker=1&pod_duration=120&position=preroll&app_bundle=com.streamingconnect.viva&app_category=linear_tv&content_channel=salsatv&content_cat=IAB14&content_genre=tv_broadcaster&content_id=mirametv_live&content_network=streamingconnect&content_rating=TV-G&ssai_enabled=1&us_privacy=[US_PRIVACY]&gdpr=[GDPR]&ifa_type=[IFA_TYPE]&min_ad_duration=6&max_ad_duration=120&app_domain=mirametv.live","logo":"https://graph.facebook.com/tropicalmoonfm/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt523","nombre":"VM Latino Costa Rica","categoria":"MUSICA","url":"https://59ef525c24caa.streamlock.net/vmtv/vmlatino/playlist.m3u8","logo":"https://graph.facebook.com/vmlatinocr/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt524","nombre":"Venus Media Paraguay","categoria":"MUSICA","url":"https://tigocloud.desdeparaguay.net/venusmedia/venusmedia/playlist.m3u8","logo":"https://pbs.twimg.com/profile_images/1986542413016412160/5a7Yf8-f_200x200.jpg","fallbacks":[]},
    {"id":"tdt525","nombre":"La Mega Mundial USA","categoria":"MUSICA","url":"https://server40.servistreaming.com:3477/stream/play.m3u8","logo":"https://graph.facebook.com/lamegaworldwide/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt526","nombre":"Retro Plus TV Chile","categoria":"MUSICA","url":"https://scl.edge.grupoz.cl/retroplustvuno/live/playlist.m3u8","logo":"https://graph.facebook.com/retroplustv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt527","nombre":"Portal Foxmix Chile","categoria":"MUSICA","url":"https://panel.tvstream.cl:1936/8040/8040/playlist.m3u8","logo":"https://yt3.ggpht.com/ytc/AAUvwnj90kC8kqjZ69oiVT718JUs9iedB5o1w9cKfApo=s200","fallbacks":[]},
    {"id":"tdt528","nombre":"30A Music USA","categoria":"MUSICA","url":"https://30a-tv.com/feeds/ceftech/30atvmusic.m3u8","logo":"https://graph.facebook.com/30atv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt529","nombre":"Ditty TV USA","categoria":"MUSICA","url":"https://0ba805a2403b4660bbb05c0a210ebbdc.mediatailor.us-east-1.amazonaws.com/v1/master/04fd913bb278d8775298c26fdca9d9841f37601f/ONO_DittyTV/playlist.m3u8","logo":"https://graph.facebook.com/DittyTV/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt530","nombre":"Spirit TV USA","categoria":"MUSICA","url":"https://cdnlive.myspirit.tv/LS-ATL-43240-2/index.m3u8","logo":"https://graph.facebook.com/MySpirittv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt531","nombre":"RadioU TV USA","categoria":"MUSICA","url":"https://1826200335.rsc.cdn77.org/1826200335/index.m3u8","logo":"https://graph.facebook.com/RadioU/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt532","nombre":"Dance TV Estonia","categoria":"MUSICA","url":"https://m1b2.worldcast.tv/dancetelevisionone/2/dancetelevisionone.m3u8","logo":"https://pbs.twimg.com/profile_images/1268129322730127364/OJlQBZpS_200x200.jpg","fallbacks":[]},
    {"id":"tdt533","nombre":"V2Beat TV","categoria":"MUSICA","url":"https://abr.de1se01.v2beat.live/playlist.m3u8","logo":"https://graph.facebook.com/vtwobeat/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt534","nombre":"Tomorrowland TV","categoria":"MUSICA","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCsN8M73DMWa8SPp5o_0IAQQ&autoplay=1","logo":"https://graph.facebook.com/tomorrowland/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt535","nombre":"The K-POP Korea","categoria":"MUSICA","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCoRXPcv8XK5fAplLbk9PTww&autoplay=1","logo":"https://pbs.twimg.com/profile_images/1942537722054225920/QrqP6eqf_200x200.jpg","fallbacks":[]},
    {"id":"tdt536","nombre":"Radio María España","categoria":"MUSICA","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCbX1IDSwem3w0HfBP4F_BYw&autoplay=1","logo":"https://graph.facebook.com/RadioMariaSpa/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt537","nombre":"Abadia de Montserrat España","categoria":"INTERNACIONAL","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCFrlaCzXVVlK_eiVNvYoezA&autoplay=1","logo":"https://graph.facebook.com/AbadiaMontserrat/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt538","nombre":"Ecclesia COPE España","categoria":"INTERNACIONAL","url":"https://cope-religion-video.flumotion.com/playlist.m3u8","logo":"https://graph.facebook.com/ecclesiacope/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt539","nombre":"Solidaria TV España","categoria":"INTERNACIONAL","url":"https://canadaremar2.todostreaming.es/live/solidariatv-webhd.m3u8","logo":"https://graph.facebook.com/solidariatv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt540","nombre":"RTV Vida España","categoria":"INTERNACIONAL","url":"https://vidartv2.todostreaming.es/live/radiovida-emisiontvhd.m3u8","logo":"https://pbs.twimg.com/profile_images/1359486927406321664/WZXLfd2h_200x200.jpg","fallbacks":[]},
    {"id":"tdt541","nombre":"RTV Diocesana Toledo España","categoria":"INTERNACIONAL","url":"https://live.emitstream.com/hls/5i3pxfuz4az356yu22ij/master.m3u8","logo":"https://pbs.twimg.com/profile_images/1730156030795939840/NtRBSxdr_200x200.jpg","fallbacks":[]},
    {"id":"tdt542","nombre":"TBN España","categoria":"INTERNACIONAL","url":"https://edge.xn--tbnespaa-j3a.es/LiveApp/streams/tbnlive.m3u8","logo":"https://graph.facebook.com/TBNEspana/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt543","nombre":"María Visión España y Mexico","categoria":"INTERNACIONAL","url":"https://1601580044.rsc.cdn77.org/live/_jcn_/amls:Italiatre/playlist.m3u8","logo":"https://graph.facebook.com/mariavision/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt544","nombre":"Vatican News","categoria":"NOTICIAS","url":"https://www.youtube-nocookie.com/embed/live_stream?channel=UCnB5vfb9FMMNTnC6-kAT3fQ&autoplay=1","logo":"https://graph.facebook.com/vaticannews.es/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt545","nombre":"EWTN","categoria":"INTERNACIONAL","url":"https://cdn3.wowza.com/1/SmVrQmZCUXZhVDgz/b3J3MFJv/hls/live/playlist.m3u8","logo":"https://graph.facebook.com/ewtnespanol/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt546","nombre":"Enlace TV Costa Rica","categoria":"INTERNACIONAL","url":"https://livecdn.enlace.plus/enlace/smil:enlace-hd.smil/playlist.m3u8","logo":"https://graph.facebook.com/enlacetv/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt547","nombre":"Redevida Brasil","categoria":"INTERNACIONAL","url":"https://d12e4o88jd8gex.cloudfront.net/out/v1/cea3de0b76ac4e82ab8ee0fd3f17ce12/index.m3u8","logo":"https://graph.facebook.com/redevida/picture?width=200&height=200","fallbacks":[]},
    {"id":"tdt548","nombre":"3ABN USA","categoria":"INTERNACIONAL","url":"https://3abn.bozztv.com/3abn2/Lat_live/smil:Lat_live.smil/playlist.m3u8","logo":"https://graph.facebook.com/3abn.org/picture?width=200&height=200","fallbacks":[]},
]

def buscar_canales_m3u(max_por_fuente=200, max_total=800):
    print("\n\U0001F50D Escaneando fuentes M3U...")
    nombres_existentes = {c["nombre"].upper() for c in CANALES_FIJOS + TDT_CANALES}
    encontrados = []
    ids_vistos  = set()
    headers = {"User-Agent": "Mozilla/5.0 (compatible; IPTV-scraper/1.0)"}

    for fuente in FUENTES_M3U:
        if len(encontrados) >= max_total:
            break
        try:
            print(f"  \U0001F4E5 {fuente[:65]}...")
            r = requests.get(fuente, timeout=20, headers=headers)
            if r.status_code != 200:
                print(f"     \u274C HTTP {r.status_code}")
                continue
            texto  = r.text
            lineas = texto.split("\n")
            i      = 0
            agregados = 0
            while i < len(lineas) - 1:
                linea = lineas[i].strip()
                if not linea.startswith("#EXTINF"):
                    i += 1
                    continue
                url_linea = lineas[i+1].strip()
                if not url_linea.startswith("https"):
                    i += 2
                    continue
                # Parse tvg-logo
                logo_m = re.search(r'tvg-logo="([^"]*)"', linea)
                logo   = logo_m.group(1) if logo_m else ""
                # Parse group-title
                grp_m  = re.search(r'group-title="([^"]*)"', linea)
                grp    = grp_m.group(1).upper() if grp_m else ""
                # Parse name (after last comma)
                nombre = linea.split(",")[-1].strip() if "," in linea else ""
                if not nombre:
                    i += 2
                    continue
                key = nombre.upper()
                if key in nombres_existentes or key in ids_vistos:
                    i += 2
                    continue
                n = nombre.upper()
                if any(x in grp+n for x in ["SPORT","DEPORT","FUTBOL","FOOTBALL","LIGA","COPA","MOTORS"]):
                    cat = "DEPORTES"
                elif any(x in grp+n for x in ["NEWS","NOTICIAS","INFO","24H"]):
                    cat = "NOTICIAS"
                elif any(x in grp+n for x in ["MUSIC","MUSICA","HITS"]):
                    cat = "MUSICA"
                elif any(x in grp+n for x in ["KIDS","INFANTIL","CHILDREN","CARTOON","DISNEY","NICK"]):
                    cat = "INFANTIL"
                else:
                    cat = "INTERNACIONAL"
                ids_vistos.add(key)
                encontrados.append({
                    "nombre": nombre, "url": url_linea,
                    "logo": logo or "https://cdn-icons-png.flaticon.com/512/716/716429.png",
                    "categoria": cat,
                })
                agregados += 1
                i += 2
                if agregados >= max_por_fuente or len(encontrados) >= max_total:
                    break
            print(f"     \u2705 {agregados} canales nuevos")
        except Exception as e:
            print(f"     \u274C {str(e)[:60]}")
    print(f"  \U0001F4CA Total M3U extra: {len(encontrados)}")
    return encontrados


def actualizar_canales(ref):
    print("\n📡 Actualizando canales...")
    ahora = datetime.utcnow().isoformat()
    data  = {}

    # 1. Canales fijos argentinos
    for c in CANALES_FIJOS:
        data[c["id"]] = {
            "nombre":    c["nombre"],
            "url":       c["url"],
            "logo":      c["logo"],
            "categoria": c["categoria"],
            "fallbacks": c.get("fallbacks", []),
            "fijo":      True,
            "actualizado": ahora,
        }

    # 2. Canales TDTChannels (España + Internacional)
    for c in TDT_CANALES:
        data[c["id"]] = {
            "nombre":    c["nombre"],
            "url":       c["url"],
            "logo":      c["logo"],
            "categoria": c["categoria"],
            "fallbacks": [],
            "fijo":      False,
            "actualizado": ahora,
        }

    # 3. Canales extra de fuentes M3U
    extra = buscar_canales_m3u(max_por_fuente=150, max_total=800)
    for i, c in enumerate(extra):
        data[f"ext{i+1:04d}"] = {
            "nombre":    c["nombre"],
            "url":       c["url"],
            "logo":      c["logo"],
            "categoria": c["categoria"],
            "fallbacks": [],
            "fijo":      False,
            "actualizado": ahora,
        }

    ref.child("canales").set(data)
    total = len(data)
    print(f"  💾 {total} canales guardados ({len(CANALES_FIJOS)} AR + {len(TDT_CANALES)} TDT + {len(extra)} M3U extra)")

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