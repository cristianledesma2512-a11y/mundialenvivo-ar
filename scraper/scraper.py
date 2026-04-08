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
            "databaseURL": "https://mundialenvivo-ar-default-rtdb.firebaseio.com/"
        })
        return rtdb.reference("/")
    except Exception as e:
        print(f"❌ Error Firebase: {e}")
        return None

# ══════════════════════════════════════════════════════════════════════════
#  CANALES DE TV
# ══════════════════════════════════════════════════════════════════════════
CANALES_FIJOS = [
    
    # ── StreamTP (canales premium sin proxy) ────────────────────────────
    {"id":"stp01",
        "nombre":"ESPN Premium",
        "categoria":"NOTICIAS",
        "url":"https://streamtpnew.com/global1.php?stream=espnpremium",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"stp02",
        "nombre":"ESPN",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=espn",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"stp03",
        "nombre":"ESPN 2",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=espn2",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"stp04",
        "nombre":"ESPN 3",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=espn3",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"stp05",
        "nombre":"ESPN 4",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=espn4",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"stp06",
        "nombre":"ESPN 5",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=espn5",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"stp07",
        "nombre":"ESPN 6",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=espn6",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"stp08",
        "nombre":"ESPN 7",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=espn7",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"stp09",
        "nombre":"TyC Sports",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=tycsports",
        "logo":"https://images.seeklogo.com/logo-png/34/1/tyc-sports-logo-png_seeklogo-340604.png",
        "fallbacks":[]},
    {"id":"stp10",
        "nombre":"Fox Sports 1",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=fox1ar",
        "logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png",
        "fallbacks":[]},
    {"id":"stp11",
        "nombre":"Fox Sports 2",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=fox2ar",
        "logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png",
        "fallbacks":[]},
    {"id":"stp12",
        "nombre":"Fox Sports 3",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=fox3ar",
        "logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png",
        "fallbacks":[]},
    {"id":"stp13",
        "nombre":"DSports",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=dsports",
        "logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png",
        "fallbacks":[]},
    {"id":"stp14",
        "nombre":"DSports 2",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=dsports2",
        "logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png",
        "fallbacks":[]},
    {"id":"stp15",
        "nombre":"DSports Plus",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=dsportsplus",
        "logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png",
        "fallbacks":[]},
    {"id":"stp16",
        "nombre":"Win Sports+",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=winplus",
        "logo":"https://images.seeklogo.com/logo-png/64/1/win-sports-logo-png_seeklogo-644046.png",
        "fallbacks":[]},
    {"id":"stp17",
        "nombre":"TNT Sports",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=tntsports",
        "logo":"https://images.seeklogo.com/logo-png/51/1/tnt-sports-logo-png_seeklogo-519540.png",
        "fallbacks":[]},
    {"id":"stp18",
        "nombre":"Max 1",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=max1",
        "logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks":[]},
    {"id":"stp19",
        "nombre":"TyC Internacional",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=tycinternacional",
        "logo":"https://images.seeklogo.com/logo-png/34/1/tyc-sports-logo-png_seeklogo-340604.png",
        "fallbacks":[]},
    {"id":"stp20",
        "nombre":"FuTV",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=futv",
        "logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks":[]},
    {"id":"stp21",
        "nombre":"Fox Sports MX",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=foxsportsmx",
        "logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png",
        "fallbacks":[]},
    {"id":"stp22",
        "nombre":"Fox Sports 2 MX",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=foxsports2mx",
        "logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png",
        "fallbacks":[]},
    {"id":"stp23",
        "nombre":"Fox Sports 3 MX",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=foxsports3mx",
        "logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png",
        "fallbacks":[]},
    {"id":"stp24",
        "nombre":"ESPN MX",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=espnmx",
        "logo":"https://images.seeklogo.com/logo-png/22/1/espn-deportes-logo-png_seeklogo-226943.png",
        "fallbacks":[]},
    {"id":"stp25",
        "nombre":"ESPN 2 MX",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=espn2mx",
        "logo":"https://images.seeklogo.com/logo-png/22/1/espn-deportes-logo-png_seeklogo-226943.png",
        "fallbacks":[]},
    {"id":"stp26",
        "nombre":"ESPN 3 MX",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=espn3mx",
        "logo":"https://images.seeklogo.com/logo-png/22/1/espn-deportes-logo-png_seeklogo-226943.png",
        "fallbacks":[]},
    {"id":"stp27",
        "nombre":"TUDN MX",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=tudnmx",
        "logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks":[]},
    {"id":"stp28",
        "nombre":"Fox Sports USA",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=fox_1_usa",
        "logo":"https://images.seeklogo.com/logo-png/28/1/fox-sports-hd-logo-png_seeklogo-284627.png",
        "fallbacks":[]},
    {"id":"stp29",
        "nombre":"Fox Sports 2 USA",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=fox_2_usa",
        "logo":"https://images.seeklogo.com/logo-png/28/1/fox-sports-hd-logo-png_seeklogo-284627.png",
        "fallbacks":[]},
    {"id":"stp30",
        "nombre":"Fox Deportes USA",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=fox_deportes_usa",
        "logo":"https://images.seeklogo.com/logo-png/28/1/fox-sports-hd-logo-png_seeklogo-284627.png",
        "fallbacks":[]},
    {"id":"stp31",
        "nombre":"TUDN USA",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=tudn_usa",
        "logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks":[]},
    {"id":"stp32",
        "nombre":"Univision USA",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=univision_usa",
        "logo":"https://images.seeklogo.com/logo-png/30/1/univision-deportes-logo-png_seeklogo-301745.png",
        "fallbacks":[]},
    {"id":"stp33",
        "nombre":"Universo USA",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=universo_usa",
        "logo":"https://images.seeklogo.com/logo-png/30/1/univision-deportes-logo-png_seeklogo-301745.png",
        "fallbacks":[]},
    {"id":"stp34",
        "nombre":"SporTV Brasil 1",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=sporttvbr1",
        "logo":"https://images.seeklogo.com/logo-png/13/1/sportv-logo-png_seeklogo-130897.png",
        "fallbacks":[]},
    {"id":"stp35",
        "nombre":"SporTV Brasil 2",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=sporttvbr2",
        "logo":"https://images.seeklogo.com/logo-png/13/1/sportv-logo-png_seeklogo-130897.png",
        "fallbacks":[]},
    {"id":"stp36","nombre":"SporTV Brasil 3","categoria":"DEPORTES","url":"https://streamtpnew.com/global1.php?stream=sporttvbr3","logo":"https://images.seeklogo.com/logo-png/13/1/sportv-logo-png_seeklogo-130897.png","fallbacks":[]},
    {"id":"stp37","nombre":"Premiere 1","categoria":"DEPORTES","url":"https://streamtpnew.com/global1.php?stream=premiere1","logo":"https://images.seeklogo.com/logo-png/11/1/premiere-sport-1-logo-png_seeklogo-111685.png","fallbacks":[]},
    {"id":"stp38","nombre":"Premiere 2","categoria":"DEPORTES","url":"https://streamtpnew.com/global1.php?stream=premiere2","logo":"https://images.seeklogo.com/logo-png/11/1/premiere-sport-2-logo-png_seeklogo-111686.png","fallbacks":[]},
    {"id":"stp39","nombre":"Premiere 3","categoria":"DEPORTES","url":"https://streamtpnew.com/global1.php?stream=premiere3","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"stp40","nombre":"Liga 1 Max","categoria":"DEPORTES","url":"https://streamtpnew.com/global1.php?stream=liga1max","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"stp41","nombre":"La Liga Hypermotion","categoria":"DEPORTES","url":"https://streamtpnew.com/global1.php?stream=laligahypermotion","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"stp42","nombre":"Tigo Sports Paraguay","categoria":"DEPORTES","url":"https://streamtpnew.com/global1.php?stream=tigosportsparaguay","logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png","fallbacks":[]},
    {"id":"stp43",
        "nombre":"Telefe",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=telefe",
        "logo":"https://images.seeklogo.com/logo-png/45/1/telefe-tv-logo-png_seeklogo-451860.png",
        "fallbacks":[]},
    {"id":"stp44",
        "nombre":"TV Pública",
        "categoria":"AIRE",
        "url":"https://streamtpnew.com/global1.php?stream=tv_publica",
        "logo":"https://images.seeklogo.com/logo-png/18/1/tv-publica-logo-png_seeklogo-180741.png",
        "fallbacks":[]},
    {"id":"stp45",
        "nombre":"Disney 1",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=disney1",
        "logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png",
        "fallbacks":[]},
    {"id":"stp46",
        "nombre":"Disney 2",
        "categoria":"DEPORTES",
        "url":"https://streamtpnew.com/global1.php?stream=disney2",
        "logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png",
        "fallbacks":[]},

    # ── Bolaloca via proxy Railway ────────────────────────────────────

    {"id":"bol01",
        "nombre":"TYC SPORT",
        "categoria":"AIRE",
        "url":"https://bolaloca.my/player/1/77",
        "logo":"https://images.seeklogo.com/logo-png/34/1/tyc-sports-logo-png_seeklogo-340604.png",
        "fallbacks":[]},
    {"id":"bol02",
        "nombre":"ESPN PREMIUM",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/76",
        "logo":"https://images.seeklogo.com/logo-png/4/1/espn-logo-png_seeklogo-49194.png",
        "fallbacks":[]},
    {"id":"bol03",
        "nombre":"TNT SPORT",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/75",
        "logo":"https://images.seeklogo.com/logo-png/51/1/tnt-sports-logo-png_seeklogo-519540.png",
        "fallbacks":[]},
    {"id":"bol04",
        "nombre":"DSPORT",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/94",
        "logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png",
        "fallbacks":[]},
    {"id":"bol05",
        "nombre":"DSPORT2",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/95",
        "logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png",
        "fallbacks":[]},
    {"id":"bol06",
        "nombre":"DSPORT+",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/96",
        "logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png",
        "fallbacks":[]},
    {"id":"bol07",
        "nombre":"+FOOT",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/12",
        "logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks":[]},
    {"id":"bol08",
        "nombre":"+SPORT",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/13",
        "logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks":[]},
    {"id":"bol09",
        "nombre":"+SPORT360",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/14",
        "logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks":[]},
    {"id":"bol10",
        "nombre":"EUROSPORT1",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/15",
        "logo":"https://images.seeklogo.com/logo-png/27/1/eurosport-logo-png_seeklogo-270286.png",
        "fallbacks":[]},
    {"id":"bol11",
        "nombre":"EUROSPORT","categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/16",
        "logo":"https://images.seeklogo.com/logo-png/27/1/eurosport-logo-png_seeklogo-270286.png",
        "fallbacks":[]},
    {"id":"bol12",
        "nombre":"RMC SPORT1",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/17",
        "logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks":[]},
    {"id":"bol13",
        "nombre":"CM",
        "categoria":"NOTICIAS",
        "url":"https://bolaloca.my/player/1/18",
        "logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks":[]},
    {"id":"bol14",
        "nombre":"TUDN",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/68",
        "logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks":[]},
    {"id":"bol15",
        "nombre":"FOX DEPORTES",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/70",
        "logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png",
        "fallbacks":[]},
    {"id":"bol16",
        "nombre":"LAS B",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/74",
        "logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks":[]},
    {"id":"bol17",
        "nombre":"FOXSPORT",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/78",
        "logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png",
        "fallbacks":[]},
    {"id":"bol18",
        "nombre":"FOXSPORT2",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/79",
        "logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png",
        "fallbacks":[]},
    {"id":"bol19",
        "nombre":"FOXSPORT3",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/80",
        "logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png",
        "fallbacks":[]},
    {"id":"bol20",
        "nombre":"WINSPORT",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/81",
        "logo":"https://images.seeklogo.com/logo-png/64/1/win-sports-logo-png_seeklogo-644046.png",
        "fallbacks":[]},
    {"id":"bol21",
        "nombre":"TNTSPORT PREMIUM",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/83",
        "logo":"https://images.seeklogo.com/logo-png/37/1/tnt-sports-logo-png_seeklogo-373020.png",
        "fallbacks":[]},
    {"id":"bol22",
        "nombre":"ESPN",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/87",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"bol23",
        "nombre":"ESPN2",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/88",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"bol24",
        "nombre":"ESPN3",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/89",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"bol25",
        "nombre":"ESPN4",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/90",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"bol26",
        "nombre":"ESPN5",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/91",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"bol27",
        "nombre":"ESPN6",
        "categoria":"DEPORTES",
        "url":"https://bolaloca.my/player/1/92",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
      # fin Bolaloca via proxy Railway (sin alerta Chrome) ──────────────────
    
]
TDT_CANALES = [
    {"id":"tdt003","nombre":"TRECE","categoria":"AIRE","url":"https://play.cdn.enetres.net/091DB7AFBD77442B9BA2F141DCC182F5021/021/playlist.m3u8","logo":"https://graph.facebook.com/TRECEtves/picture?width=200&height=200","fallbacks":[]},
     ]


FUENTES_M3U = [
   
]

FUENTES_SIN_FILTRO = []


def buscar_canales_m3u(max_por_fuente=200, max_total=800):
    print("\n\U0001F50D Escaneando fuentes M3U...")
    nombres_existentes = {c["nombre"].upper() for c in CANALES_FIJOS}
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

    # Preservar el campo "activo" si fue modificado manualmente en el panel
    try:
        existentes = ref.child("canales").get()
        if existentes:
            for cid, canal in data.items():
                if cid in existentes and "activo" in existentes[cid]:
                    canal["activo"] = existentes[cid]["activo"]
                else:
                    canal["activo"] = True  # nuevo canal = activo por defecto
        else:
            for canal in data.values():
                canal["activo"] = True
    except Exception as e:
        print(f"  ⚠️  No se pudo verificar campo activo: {e}")
        for canal in data.values():
            canal["activo"] = True

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