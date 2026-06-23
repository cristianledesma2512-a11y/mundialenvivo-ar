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
from bs4 import BeautifulSoup

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
    #── DISNEY 
    {"id":"stp01","nombre":"Disney","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=disney","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    
    # ── FANATIZ 
    {"id":"stp17","nombre":"Fanatiz","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=fanatiz","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
      

    #  ESPN  
    {"id":"stp33","nombre":"ESPN","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global1.php?stream=espn","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    

    #  DSPORTS 
    {"id":"stp49","nombre":"DSports","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=dsports","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    
  #  TUDN USA 
    {"id":"stp65","nombre":"TUDN USA","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=tudn_usa","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
   
    #  MAX 
    {"id":"stp81","nombre":"Max","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=max","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
   
    
    
    #   TyC sport
    {"id":"stp97","nombre":"TyC Sports","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=tycsports","logo":"https://images.seeklogo.com/logo-png/34/1/tyc-sports-logo-png_seeklogo-340604.png","fallbacks":[]},
    {"id":"stp125","nombre":"TyC Sports Inter","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=tycinternacional","logo":"https://images.seeklogo.com/logo-png/34/1/tyc-sports-logo-png_seeklogo-340604.png","fallbacks":[]},


    


    #  paramount
    {"id":"stp98","nombre":"paramount1","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=paramount1","logo":"https://images.seeklogo.com/logo-png/10/1/paramount-logo-png_seeklogo-106080.png","fallbacks":[]},
      
    

    #  espn mx
    {"id":"stp108","nombre":"espn mx","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=espnmx","logo":"https://1000logos.net/wp-content/uploads/2017/01/espn-symbol.jpg","fallbacks":[]},     
    {"id":"stp109","nombre":"espn 2mx","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=espn2mx","logo":"https://1000logos.net/wp-content/uploads/2017/01/espn-symbol.jpg","fallbacks":[]}, 	
    {"id":"stp110","nombre":"espn 3mx","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=espn3mx","logo":"https://1000logos.net/wp-content/uploads/2017/01/espn-symbol.jpg","fallbacks":[]},


    #  fox sport
    {"id":"stp111","nombre":"Fox Sports 1","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=fox1ar","logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png","fallbacks":[]},
    

    
   
    
    
    #   ESPN Premium
    {"id":"stp121","nombre":"ESPN Premium","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=espnpremium","logo":"https://librefutbol.com.ar/wp-content/uploads/2025/03/espn-premium-logo.png","fallbacks":[]},

    #   ESPN deportes
    {"id":"stp122","nombre":"ESPN deportes","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=espndeportes","logo":"https://2.bp.blogspot.com/-RG0tX1-q0VM/UZ5RRl910eI/AAAAAAAAAKg/RasxwojGhHo/s1600/espndeportes.jpg","fallbacks":[]},

    #   DSPORT PLUS
    {"id":"stp123","nombre":"DSPORT Plus","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=dsportsplus","logo":"https://i0.wp.com/trucosonline.com/wp-content/uploads/2022/11/613.png","fallbacks":[]},


    #   TNT sport
    {"id":"stp124","nombre":"TNT Sports","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=tntsports","logo":"https://images.seeklogo.com/logo-png/51/1/tnt-sports-logo-png_seeklogo-519540.png","fallbacks":[]},
    # TEKEMUNDO
  {"id":"stp125","nombre":"Telemundo usa","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=telemundousa","logo":"https://images.seeklogo.com/logo-png/24/1/telemundo-logo-png_seeklogo-247570.png","fallbacks":[]},
  
  
    # ── Bolaloca via proxy Railway ────────────────────────────────────

    
      # canales XXX──────────────────
{"id":"xxx01",
        "nombre":"LIVECAMS",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/livecams.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},

{"id":"xxx02",
        "nombre":"MILF",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/milf.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx03",
        "nombre":"BIGDICK",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/bigdick.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx04",
        "nombre":"BIGTITS",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/bigtits.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx05",
        "nombre":"FETISH",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/fetish.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx06",
        "nombre":"PORNSTAR",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/pornstar.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx07",
        "nombre":"BIGASS",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/bigass.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx08",
        "nombre":"INTERRACIAL",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/interracial.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx09",
        "nombre":"COL",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/latina.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx10",
        "nombre":"POV",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/pov.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx11",
        "nombre":"BLOWJOB",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/blowjob.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx12",
        "nombre":"TEENS",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/teen.m3u88",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx13",
        "nombre":"HARDCORE",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/hardcore.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx14",
        "nombre":"CUCKOLD",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/cuckold.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx15",
        "nombre":"THREESOME",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/threesome.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx16",
        "nombre":"RUSSIAN",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/russian.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx17",
        "nombre":"LESBIAN",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/lesbian.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx18",
        "nombre":"ROUGH",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/rough.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx19",
        "nombre":"GANGBANG",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/gangbang.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx20",
        "nombre":"ANAL",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/anal.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx21",
        "nombre":"COMPILATION",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/compilation.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx21",
        "nombre":"BRUNETTE",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/brunette.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx22",
        "nombre":"BLONDE",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/blonde.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx23",
        "nombre":"GAY",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/gay.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
{"id":"xxx24",
        "nombre":"ASIAN",
        "categoria":"ADULTOS",
        "url":"https://live.adultiptv.net/asian.m3u8",
        "logo":"https://images.seeklogo.com/logo-png/15/1/xxx-logo-png_seeklogo-154781.png",
        "fallbacks":[]},
      
      
          
]
TDT_CANALES = [
   
      ]


FUENTES_M3U = [
    {"nombre": "Gist Canales Personalizados", "url": "https://gist.githubusercontent.com/frantdse/f6989518c73826ade6734c63c367af4c/raw/", "categoria": "DEPORTES", "confianza": "alta", "adultos": False},
    {"nombre": "IPTV Argentina Oficial", "url": "https://iptv-org.github.io/iptv/countries/ar.m3u", "categoria": "DEPORTES", "confianza": "alta", "adultos": False},
    #{"nombre": "TDTChannels Eventos Globales", "url": "https://www.tdtchannels.com/lists/events.m3u8", "categoria": "DEPORTES", "confianza": "alta", "adultos": False},
    #{"nombre": "Free-TV IPTV Master", "url": "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8", "categoria": "OTROS", "confianza": "alta", "adultos": False},
    #{"nombre": "Fluxus TV Deportes", "url": "https://raw.githubusercontent.com/fluxustv/IPTV/main/sports.m3u", "categoria": "DEPORTES", "confianza": "media", "adultos": False},
   # {"nombre": "Fluxus TV Cine", "url": "https://raw.githubusercontent.com/fluxustv/IPTV/main/movies.m3u", "categoria": "CINE", "confianza": "media", "adultos": False},
    #{"nombre": "IPTV Global Open List", "url": "https://raw.githubusercontent.com/dzh0ni/iPTV-FREE-LIST/master/iPTV-Free-List_TV.m3u", "categoria": "OTROS", "confianza": "baja", "adultos": False},
    #{"nombre": "IPTV Adultos Global Premium", "url": "https://iptv-org.github.io/iptv/categories/xxx.m3u", "categoria": "ADULTOS", "confianza": "alta", "adultos": True},
    {"nombre": "Fluxus TV Adultos Core", "url": "https://raw.githubusercontent.com/fluxustv/IPTV/main/xxx.m3u", "categoria": "ADULTOS", "confianza": "media", "adultos": True},
    {"nombre": "lista hot", "url": "https://tecnotv.club/tusw/listahot.m3u", "categoria": "ADULTOS", "confianza": "media", "adultos": True},
    {"nombre": "Pastebin Raw 1", "url": "https://pastebin.com/raw/ze9LRSJJ", "categoria": "DEPORTES", "confianza": "alta"},
    {"nombre": "Pastebin Raw 2", "url": "https://pastebin.com/raw/x9xSPugA", "categoria": "DEPORTES", "confianza": "alta"},
  
   {"nombre": "TecnoTV Lista Principal", "url": "https://tecnotv.club/tusw/lista.m3u", "categoria": "OTROS", "confianza": "media"},
    {"nombre": "TecnoTV Deportes", "url": "https://tecnotv.club/tusw/deportes.m3u", "categoria": "DEPORTES", "confianza": "media"},
    {"nombre": "TecnoTV Lista 1", "url": "https://tecnotv.club/tusw/lista1.m3u", "categoria": "OTROS", "confianza": "media"},
    {"nombre": "TecnoTV Lista 2", "url": "https://tecnotv.club/tusw/lista2.m3u", "categoria": "OTROS", "confianza": "media"},
    {"nombre": "TecnoTV Lista 3", "url": "https://tecnotv.club/tusw/lista3.m3u", "categoria": "OTROS", "confianza": "media"},
    {"nombre": "TecnoTV Lista 4", "url": "https://tecnotv.club/tusw/lista4.m3u", "categoria": "OTROS", "confianza": "media"},
    {"nombre": "TecnoTV Android Core", "url": "https://tecnotv.club/tusw/android.m3u", "categoria": "OTROS", "confianza": "media"},
    {"nombre": "TecnoTV Android 1", "url": "https://tecnotv.club/tusw/android1.m3u", "categoria": "OTROS", "confianza": "media"},
    {"nombre": "TecnoTV Android 2", "url": "https://tecnotv.club/tusw/android2.m3u", "categoria": "OTROS", "confianza": "media"},
    {"nombre": "TecnoTV Android 3", "url": "https://tecnotv.club/tusw/android3.m3u", "categoria": "OTROS", "confianza": "media"},
    {"nombre": "TecnoTV GeoMex", "url": "https://tecnotv.club/tusw/geomex.m3u", "categoria": "OTROS", "confianza": "media"},
    #{"nombre": "TecnoTV Películas", "url": "https://tecnotv.club/tusw/peliculas.m3u", "categoria": "CINE", "confianza": "media"},
  
    #{"nombre": "GitHub Melendez Raw Bridge", "url": "https://raw.githubusercontent.com/dmelendez11/lista-canales-m3u/main/lista_especial_con_respaldos.m3u", "categoria": "DEPORTES", "confianza": "baja"},
  
  

  
]

FUENTES_SIN_FILTRO = []

# ══════════════════════════════════════════════════════════════════════════
#  PROCESAMIENTO Y AGRUPACIÓN DE FUENTES M3U/M3U8
# ══════════════════════════════════════════════════════════════════════════
def buscar_canales_m3u(max_por_fuente: int = 10000, max_total: int = 20000) -> list[dict]:
    """
    Descarga, parsea y agrupa los canales provenientes de listas M3U y M3U8
    evitando duplicados y categorizando dinámicamente.
    """
    encontrados = []
    urls_vistas = set()
    nombres_existentes = set()

    # Pre-poblar nombres existentes con los canales fijos para no duplicarlos
    for c in CANALES_FIJOS:
        nombres_existentes.add(c["nombre"].upper().strip())

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Diccionario de mapeo algorítmico rápido para categorización
    PATRONES_CATEGORIAS = {
        "DEPORTES": ["SPORT", "DEPORT", "FUTBOL", "FOOTBALL", "LIGA", "COPA", "MOTOR", "ESPN", "FOX S", "TYC", "TNT SPORT", "DSPORTS", "WIN"],
        "CINE": ["MOVIE", "CINE", "PELICULA", "HBO", "STAR", "CINEMAX", "WARNER", "TNT SERIES", "HOLLYWOOD"],
        "NOTICIAS": ["NEWS", "NOTICIAS", "INFO", "24H", "PRENSA", "CNN", "TN", "C5N", "LN+"],
        "MUSICA": ["MUSIC", "MUSICA", "HITS", "MTV", "VH1", "QUIERO", "TMF"],
        "DOCUMENTALES": ["DOCU", "WILD", "HISTORY", "NAT GEO", "DISCOVERY", "ANIMAL", "DISC."],
        "INFANTIL": ["KIDS", "INFANTIL", "CHILDREN", "CARTOON", "DISNEY", "NICK", "BOOMERANG", "DISCOVERY KIDS"],
        "ADULTOS": ["XXX", "ADULT", "PLAYBOY", "PENTHOUSE", "VENUS", "SEX", "LIVECAMS", "MILF", "BIGTITS"]
    }

    for fuente_info in FUENTES_M3U:
        if len(encontrados) >= max_total:
            break

        fuente_url = fuente_info["url"]
        fuente_nombre = fuente_info["nombre"]

        try:
            print(f" 📥 Procesando lista M3U/M3U8: {fuente_nombre}...")
            r = requests.get(fuente_url, timeout=25, headers=headers)
            if r.status_code != 200:
                print(f" ❌ Error HTTP {r.status_code} en fuente {fuente_nombre}")
                continue

            # Soporte nativo de codificación utf-8 con fallback automático
            contenido = r.content.decode('utf-8', errors='ignore')
            lineas = [linea.strip() for linea in contenido.split("\n") if linea.strip()]
            
            agregados_fuente = 0
            
            for i in range(len(lineas) - 1):
                linea = lineas[i]
                if not linea.startswith("#EXTINF"):
                    continue

                url_linea = lineas[i+1].strip()
                if not url_linea.startswith("http"):
                    continue

                # Evitar procesamiento de la misma URL exacta
                if url_linea in urls_vistas:
                    continue

                # Parsear Metadatos mediante expresiones regulares exactas
                logo_m = re.search(r'tvg-logo="([^"]*)"', linea, re.IGNORECASE)
                logo = logo_m.group(1).strip() if logo_m else ""

                grp_m = re.search(r'group-title="([^"]*)"', linea, re.IGNORECASE)
                grp = grp_m.group(1).upper().strip() if grp_m else ""

                nombre = linea.split(",")[-1].strip() if "," in linea else "Canal Desconocido"
                n_upper = nombre.upper().strip()

                # Control estricto de duplicidad por nombre
                if not nombre or n_upper in nombres_existentes:
                    continue

                # Evaluación y Categorización Inteligente
                cat = "INTERNACIONAL"
                target_string = f"{grp} {n_upper}"
                
                for categoria_id, patrones in PATRONES_CATEGORIAS.items():
                    if any(patron in target_string for patron in patrones):
                        cat = categoria_id
                        break

                encontrados.append({
                    "nombre": nombre,
                    "url": url_linea,
                    "logo": logo or "https://cdn-icons-png.flaticon.com/512/716/716429.png",
                    "categoria": cat,
                    "origen": fuente_nombre
                })

                urls_vistas.add(url_linea)
                nombres_existentes.add(n_upper)
                agregados_fuente += 1

                if agregados_fuente >= max_por_fuente or len(encontrados) >= max_total:
                    break

            print(f" ✅ {agregados_fuente} canales nuevos indexados de esta fuente.")
            
        except Exception as e:
            print(f" ❌ Error crítico procesando fuente {fuente_nombre}: {str(e)[:60]}")

    print(f" 📊 Total M3U/M3U8 extraído con éxito: {len(encontrados)} canales")
    return encontrados


# ══════════════════════════════════════════════════════════════════════════
#  MÓDULO DE ACTUALIZACIÓN (PRESERVA TUS CANALES FIJOS EXACTAMENTE IGUAL)
# ══════════════════════════════════════════════════════════════════════════
def actualizar_canales(ref):
    print("\n📡 Iniciando sincronización de base de datos en Firebase...")
    ahora = datetime.utcnow().isoformat()
    data = {}

    # 1. Canales fijos - Sin cambios
    for c in CANALES_FIJOS:
        data[c["id"]] = {
            "nombre": c["nombre"],
            "url": c["url"],
            "logo": c["logo"],
            "categoria": c.get("categoria", "DEPORTES").upper(),
            "fallbacks": c.get("fallbacks", []),
            "fijo": True,
            "actualizado": ahora
        }

    # 2. Inyección de Canales dinámicos M3U agrupados
    extra = buscar_canales_m3u()
    for i, c in enumerate(extra):
        canal_id = f"ext_{i+1:05d}"  # Genera IDs ordenados y limpios como ext_00001
        data[canal_id] = {
            "nombre": c["nombre"],
            "url": c["url"],
            "logo": c["logo"],
            "categoria": c["categoria"],
            "fallbacks": [],
            "fijo": False,
            "actualizado": ahora
        }

    # 3. Mapeo y persistencia del flag 'activo' desde Firebase
    try:
        existentes = ref.child("canales").get()
        for cid, canal in data.items():
            if existentes and cid in existentes and "activo" in existentes[cid]:
                canal["activo"] = existentes[cid]["activo"]
            else:
                canal["activo"] = True
    except Exception as e:
        print(f" ⚠️ Alerta al sincronizar estados activos: {e}")
        for canal in data.values():
            canal["activo"] = True

    # 4. Escritura atómica final
    ref.child("canales").set(data)
    print(f" 💾 Transacción finalizada. {len(data)} canales totales desplegados en Firebase.")
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
#  EVENTOS DEPORTIVOS DEL DÍA
# ══════════════════════════════════════════════════════════════════════════
def scrapear_eventos(ref):
    """
    Scrapea https://streamtpday1.xyz/eventos.html
    y guarda los eventos en Firebase bajo /eventos_dia
    """
    print("\n⚽ Scrapeando eventos deportivos...")
    URL = "https://streamtpday1.xyz/eventos.html"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-AR,es;q=0.9",
        "Referer": "https://streamtpday1.xyz/",
    }

    try:
        r = requests.get(URL, headers=headers, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(f"  ❌ No se pudo conectar a eventos.html: {e}")
        return

    soup = BeautifulSoup(r.text, "html.parser")
    eventos = []

    # Buscar todos los .event divs
    event_divs = soup.select(".event")

    for div in event_divs:
        # Hora + título en .event-name
        name_el = div.select_one(".event-name")
        if not name_el:
            continue

        # Solo el texto directo (sin hijos como el span de idioma)
        full_text = name_el.get_text(separator=" ", strip=True)

        # Separar hora del título: "HH:MM - Título del partido"
        import re as _re
        match = _re.match(r"^(\d{1,2}:\d{2})\s*[-–]\s*(.+)$", full_text)
        hora   = match.group(1).strip() if match else ""
        titulo = match.group(2).strip() if match else full_text

        # Link del stream
        link_el = div.select_one(".iframe-link")
        link = link_el.get("value", "").strip() if link_el else ""

        # Estado en vivo
        status_el = div.select_one(".status-button")
        en_vivo = "status-live" in (status_el.get("class", []) if status_el else [])

        # Idioma (bandera img alt)
        idioma_el = name_el.select_one("img")
        idioma = idioma_el.get("alt", "").strip() if idioma_el else ""

        # Categoría inferida del título
        t = titulo.lower()
        if any(x in t for x in ["libertadores"]):
            categoria = "Libertadores"
        elif any(x in t for x in ["sudamericana"]):
            categoria = "Sudamericana"
        elif any(x in t for x in ["mundial", "fifa", "selección", "seleccion"]):
            categoria = "Mundial"
        elif any(x in t for x in ["nba", "basquet", "basket"]):
            categoria = "Basquet"
        elif any(x in t for x in ["tenis", "atp", "wta"]):
            categoria = "Tenis"
        elif any(x in t for x in ["f1", "formula", "nascar", "moto"]):
            categoria = "Motor"
        elif any(x in t for x in ["boxeo", "ufc", "mma", "pelea"]):
            categoria = "Boxeo"
        elif any(x in t for x in ["rugby", "nfl"]):
            categoria = "Rugby"
        elif any(x in t for x in ["liga", "premier", "bundesliga", "serie a", "laliga"]):
            categoria = "Fútbol"
        else:
            categoria = "Otros"

        if titulo:
            eventos.append({
                "hora": hora,
                "titulo": titulo,
                "link": link,
                "idioma": idioma,
                "enVivo": en_vivo,
                "categoria": categoria,
            })

    # Guardar en Firebase
    ahora = datetime.utcnow().isoformat()
    data = {
        "actualizadoEn": ahora,
        "total": len(eventos),
        "eventos": eventos,
    }

    try:
        ref.child("eventos_dia").set(data)
        print(f"  💾 {len(eventos)} eventos guardados en Firebase")
    except Exception as e:
        print(f"  ❌ Error guardando eventos: {e}")


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
    scrapear_eventos(ref)

    print("\n" + "=" * 55)
    print("  ✅ TODO ACTUALIZADO EN FIREBASE")
    print("=" * 55)

if __name__ == "__main__":
    main()
