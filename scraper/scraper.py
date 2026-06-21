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
    {"id":"stp02","nombre":"Disney 1","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=disney1","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp03","nombre":"Disney 2","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=disney2","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp04","nombre":"Disney 3","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=disney3","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp05","nombre":"Disney 4","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=disney4","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp06","nombre":"Disney 5","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=disney5","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    
    # ── FANATIZ 
    {"id":"stp17","nombre":"Fanatiz","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=fanatiz","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp18","nombre":"Fanatiz 1","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=fanatiz1","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp19","nombre":"Fanatiz 2","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=fanatiz2","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp20","nombre":"Fanatiz 3","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=fanatiz3","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp21","nombre":"Fanatiz 4","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=fanatiz4","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp22","nombre":"Fanatiz 5","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=fanatiz5","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    

    #  ESPN  
    {"id":"stp33","nombre":"ESPN","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global1.php?stream=espn","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp34","nombre":"ESPN 1","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=espn1","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp35","nombre":"ESPN 2","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=espn2","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp36","nombre":"ESPN 3","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=espn3","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp37","nombre":"ESPN 4","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=espn4","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp38","nombre":"ESPN 5","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=espn5","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    

    #  DSPORTS 
    {"id":"stp49","nombre":"DSports","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=dsports","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp50","nombre":"DSports 1","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=dsports1","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp51","nombre":"DSports 2","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=dsports2","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp52","nombre":"DSports 3","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=dsports3","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp53","nombre":"DSports 4","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=dsports4","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp54","nombre":"DSports 5","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=dsports5","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
        #  TUDN USA 
    {"id":"stp65","nombre":"TUDN USA","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=tudn_usa","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp66","nombre":"TUDN USA 1","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=tudn_usa1","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp67","nombre":"TUDN USA 2","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=tudn_usa2","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp68","nombre":"TUDN USA 3","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=tudn_usa3","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp69","nombre":"TUDN USA 4","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=tudn_usa4","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp70","nombre":"TUDN USA 5","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=tudn_usa5","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    
    #  MAX 
    {"id":"stp81","nombre":"Max","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=max","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp82","nombre":"Max 1","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=max1","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp83","nombre":"Max 2","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=max2","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp84","nombre":"Max 3","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=max3","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp85","nombre":"Max 4","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=max4","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp86","nombre":"Max 5","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=max5","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    
    
    
    #   TyC sport
    {"id":"stp97","nombre":"TyC Sports","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=tycsports","logo":"https://images.seeklogo.com/logo-png/34/1/tyc-sports-logo-png_seeklogo-340604.png","fallbacks":[]},
    {"id":"stp125","nombre":"TyC Sports Inter","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=tycinternacional","logo":"https://images.seeklogo.com/logo-png/34/1/tyc-sports-logo-png_seeklogo-340604.png","fallbacks":[]},


    


    #  paramount
    {"id":"stp98","nombre":"paramount1","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=paramount1","logo":"https://images.seeklogo.com/logo-png/10/1/paramount-logo-png_seeklogo-106080.png","fallbacks":[]},
    {"id":"stp99","nombre":"paramount2","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=paramount2","logo":"https://images.seeklogo.com/logo-png/10/1/paramount-logo-png_seeklogo-106080.png","fallbacks":[]},
    {"id":"stp100","nombre":"paramount3","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=paramount3","logo":"https://images.seeklogo.com/logo-png/10/1/paramount-logo-png_seeklogo-106080.png","fallbacks":[]},
      
    

    #  espn mx
    {"id":"stp108","nombre":"espn mx","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=espnmx","logo":"https://1000logos.net/wp-content/uploads/2017/01/espn-symbol.jpg","fallbacks":[]},     
    {"id":"stp109","nombre":"espn 2mx","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=espn2mx","logo":"https://1000logos.net/wp-content/uploads/2017/01/espn-symbol.jpg","fallbacks":[]}, 	
    {"id":"stp110","nombre":"espn 3mx","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=espn3mx","logo":"https://1000logos.net/wp-content/uploads/2017/01/espn-symbol.jpg","fallbacks":[]},


    #  fox sport
    {"id":"stp111","nombre":"Fox Sports 1","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=fox1ar","logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png","fallbacks":[]},
    {"id":"stp112","nombre":"Fox Sports 2","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=fox2ar","logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png","fallbacks":[]},
    {"id":"stp113","nombre":"Fox Sports 3","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=fox3ar","logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png","fallbacks":[]},
    

    #   TNT GB
    {"id":"stp114","nombre":"TNT 1 gb","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=tnt_1_gb","logo":"https://www.freepnglogos.com/uploads/tnt-logo-png-9.jpg","fallbacks":[]},

    {"id":"stp115","nombre":"TNT 2 gb","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=tnt_2_gb","logo":"https://www.freepnglogos.com/uploads/tnt-logo-png-9.jpg","fallbacks":[]},

   
    #   Aire
    {"id":"stp118","nombre":"Telefe opc1","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=telefe","logo":"https://images.seeklogo.com/logo-png/45/1/telefe-tv-logo-png_seeklogo-451860.png","fallbacks":[]},

    
    #   ESPN Premium
    {"id":"stp121","nombre":"ESPN Premium","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=espnpremium","logo":"https://librefutbol.com.ar/wp-content/uploads/2025/03/espn-premium-logo.png","fallbacks":[]},

    #   ESPN deportes
    {"id":"stp122","nombre":"ESPN deportes","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=espndeportes","logo":"https://2.bp.blogspot.com/-RG0tX1-q0VM/UZ5RRl910eI/AAAAAAAAAKg/RasxwojGhHo/s1600/espndeportes.jpg","fallbacks":[]},

    #   DSPORT PLUS
    {"id":"stp123","nombre":"DSPORT Plus","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=dsportsplus","logo":"https://i0.wp.com/trucosonline.com/wp-content/uploads/2022/11/613.png","fallbacks":[]},


    #   TNT sport
    {"id":"stp124","nombre":"TNT Sports","categoria":"DEPORTES","url":"https://streamtpday1.xyz/global2.php?stream=tntsports","logo":"https://images.seeklogo.com/logo-png/51/1/tnt-sports-logo-png_seeklogo-519540.png","fallbacks":[]},
  
  
    # ── Bolaloca via proxy Railway ────────────────────────────────────

    {
    "id": "bol01",
    "nombre": "BEIN SPORT 1 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/01",
    "logo": "https://images.seeklogo.com/logo-png/48/1/bein-sports-1-logo-png_seeklogo-481583.png",
    "fallbacks": []
  },
  {
    "id": "bol02",
    "nombre": "BEIN SPORT 2 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/02",
    "logo": "https://images.seeklogo.com/logo-png/48/1/bein-sports-2-logo-png_seeklogo-481584.png",
    "fallbacks": []
  },
  {
    "id": "bol03",
    "nombre": "BEIN SPORT 3 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/03",
    "logo": "https://images.seeklogo.com/logo-png/48/1/bein-sports-3-logo-png_seeklogo-481585.png",
    "fallbacks": []
  },
  {
    "id": "bol04",
    "nombre": "BEIN SPORT 4 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/04",
    "logo": "https://images.seeklogo.com/logo-png/36/1/bein-sports-logo-png_seeklogo-367812.png",
    "fallbacks": []
  },
  {
    "id": "bol12",
    "nombre": "canal 12 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/12",
    "logo": "https://thumb.canalplus.pro/bran/unsafe/%7BresolutionXY%7D/image/630c886aa7ce0/uploads/media/LOGO-CANAL-FOOT-TALL.png",
    "fallbacks": []
  },
  {
    "id": "bol13",
    "nombre": "canal 13 (B)",
    "categoria": "CINE",
    "url": "https://bolaloca.my/player/2/13",
    "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
    "fallbacks": []
  },
  {
    "id": "bol14",
    "nombre": "FOOT (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/14",
    "logo": "https://thumb.canalplus.pro/bran/unsafe/%7BresolutionXY%7D/image/630c886aa7ce0/uploads/media/LOGO-CANAL-FOOT-TALL.png",
    "fallbacks": []
  },
  {
    "id": "bol15",
    "nombre": "EUROSPORT 1 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/15",
    "logo": "https://images.seeklogo.com/logo-png/40/1/eurosport-logo-png_seeklogo-407861.png",
    "fallbacks": []
  },
  {
    "id": "bol16",
    "nombre": "EUROSPORT 2 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/16",
    "logo": "https://images.seeklogo.com/logo-png/27/1/eurosport-2-logo-png_seeklogo-270285.png",
    "fallbacks": []
  },
  {
    "id": "bol19",
    "nombre": "LEQUIPE (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/19",
    "logo": "https://images.seeklogo.com/logo-png/24/1/lequipe-logo-png_seeklogo-245702.png",
    "fallbacks": []
  },
  
  {
    "id": "bol24",
    "nombre": "TF1 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/24",
    "logo": "https://images.seeklogo.com/logo-png/16/1/tf1-logo-png_seeklogo-169793.png",
    "fallbacks": []
  },
  {
    "id": "bol25",
    "nombre": "TCM (B)",
    "categoria": "CINE",
    "url": "https://bolaloca.my/player/2/25",
    "logo": "https://images.seeklogo.com/logo-png/13/1/tcm-logo-png_seeklogo-136143.png",
    "fallbacks": []
  },
  
  {
    "id": "bol27",
    "nombre": "W9 (B)",
    "categoria": "CINE",
    "url": "https://bolaloca.my/player/2/27",
    "logo": "https://images.seeklogo.com/logo-png/25/1/w9-logo-png_seeklogo-252476.png",
    "fallbacks": []
  },
  {
    "id": "bol28",
    "nombre": "FRANCE TV (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/28",
    "logo": "https://images.seeklogo.com/logo-png/52/1/france-tv-2022-logo-png_seeklogo-521449.png",
    "fallbacks": []
  },
  
  {
    "id": "bol30",
    "nombre": "canal 30 (B)",
    "categoria": "INFANTIL",
    "url": "https://bolaloca.my/player/2/30",
    "logo": "https://images.seeklogo.com/logo-png/39/1/okoo-logo-png_seeklogo-399478.png",
    "fallbacks": []
  },
  {
    "id": "bol53",
    "nombre": "LA LIGA (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/53",
    "logo": "https://images.seeklogo.com/logo-png/61/1/la-liga-logo-png_seeklogo-614181.png",
    "fallbacks": []
  },
  {
    "id": "bol68",
    "nombre": "TUDN (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/68",
    "logo": "https://images.seeklogo.com/logo-png/36/1/tudn-logo-png_seeklogo-367833.png",
    "fallbacks": []
  },
  {
    "id": "bol69",
    "nombre": "canal 69 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/69",
    "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
    "fallbacks": []
  },
  {
    "id": "bol70",
    "nombre": "FOX SPORT ES (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/70",
    "logo": "https://images.seeklogo.com/logo-png/30/1/fox-sports-en-espanol-logo-png_seeklogo-301754.png",
    "fallbacks": []
  },
  
  {
    "id": "bol72",
    "nombre": "NBC (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/72",
    "logo": "https://images.seeklogo.com/logo-png/26/1/nbc-universo-logo-png_seeklogo-261153.png",
    "fallbacks": []
  },
  {
    "id": "bol73",
    "nombre": "TELEMUNDO (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/73",
    "logo": "https://images.seeklogo.com/logo-png/45/1/telemundo-logo-png_seeklogo-454415.png",
    "fallbacks": []
  },
  
  {
    "id": "bol75",
    "nombre": "TNT SPORTS (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/75",
    "logo": "https://images.seeklogo.com/logo-png/51/1/tnt-sports-logo-png_seeklogo-519540.png",
    "fallbacks": []
  },
  {
    "id": "bol76",
    "nombre": "ESPN (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/76",
    "logo": "https://images.seeklogo.com/logo-png/4/1/espn-logo-png_seeklogo-49195.png",
    "fallbacks": []
  },
  {
    "id": "bol77",
    "nombre": "TYC SPORT (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/77",
    "logo": "https://images.seeklogo.com/logo-png/34/1/tyc-sports-logo-png_seeklogo-340604.png",
    "fallbacks": []
  },
  {
    "id": "bol78",
    "nombre": "FOX SPORT (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/78",
    "logo": "https://images.seeklogo.com/logo-png/27/1/fox-sports-logo-png_seeklogo-270420.png",
    "fallbacks": []
  },
  {
    "id": "bol79",
    "nombre": "FOX SPORT 2 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/79",
    "logo": "https://images.seeklogo.com/logo-png/47/1/fox-sports-2-argentina-2023-logo-png_seeklogo-471070.png",
    "fallbacks": []
  },
  {
    "id": "bol80",
    "nombre": "FOX SPORT 3 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/80",
    "logo": "https://images.seeklogo.com/logo-png/47/1/fox-sports-3-argentina-2023-logo-png_seeklogo-471071.png",
    "fallbacks": []
  },
  {
    "id": "bol81",
    "nombre": "WIN SPORT (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/81",
    "logo": "https://images.seeklogo.com/logo-png/37/1/win-sport-logo-png_seeklogo-371670.png",
    "fallbacks": []
  },
  {
    "id": "bol82",
    "nombre": "WIN SPORT 2 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/82",
    "logo": "https://images.seeklogo.com/logo-png/25/1/win-sports-logo-png_seeklogo-259337.png",
    "fallbacks": []
  },
  {
    "id": "bol83",
    "nombre": "TNT SPORT 3 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/83",
    "logo": "https://images.seeklogo.com/logo-png/51/1/tnt-sports-logo-png_seeklogo-519540.png",
    "fallbacks": []
  },
  {
    "id": "bol84",
    "nombre": "L1 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/84",
    "logo": "https://images.seeklogo.com/logo-png/51/1/l1-logo-png_seeklogo-519696.png",
    "fallbacks": []
  },
  {
    "id": "bol85",
    "nombre": "CHILEVISION (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/85",
    "logo": "https://images.seeklogo.com/logo-png/32/1/chilevision-2018-present-logo-png_seeklogo-326993.png",
    "fallbacks": []
  },
  {
    "id": "bol86",
    "nombre": "canal 86 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/86",
    "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
    "fallbacks": []
  },
  {
    "id": "bol87",
    "nombre": "ESPN (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/87",
    "logo": "https://images.seeklogo.com/logo-png/4/1/espn-logo-png_seeklogo-49196.png",
    "fallbacks": []
  },
  {
    "id": "bol88",
    "nombre": "ESPN 2 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/88",
    "logo": "https://images.seeklogo.com/logo-png/26/1/espn2-logo-png_seeklogo-261969.png",
    "fallbacks": []
  },
  {
    "id": "bol89",
    "nombre": "ESPN 3 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/89",
    "logo": "https://images.seeklogo.com/logo-png/53/1/espn-logo-png_seeklogo-537115.png",
    "fallbacks": []
  },
  {
    "id": "bol90",
    "nombre": "ESPN 4 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/90",
    "logo": "https://images.seeklogo.com/logo-png/53/1/espn-logo-png_seeklogo-537115.png",
    "fallbacks": []
  },
  {
    "id": "bol91",
    "nombre": "ESPN 5 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/91",
    "logo": "https://images.seeklogo.com/logo-png/52/1/espn-5-logo-png_seeklogo-522715.png",
    "fallbacks": []
  },
  {
    "id": "bol92",
    "nombre": "ESPN 6 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/92",
    "logo": "https://images.seeklogo.com/logo-png/52/1/espn-6-logo-png_seeklogo-522717.png",
    "fallbacks": []
  },
  {
    "id": "bol93",
    "nombre": "ESPN 7 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/93",
    "logo": "https://images.seeklogo.com/logo-png/52/1/espn-7-logo-png_seeklogo-522718.png",
    "fallbacks": []
  },
  {
    "id": "bol94",
    "nombre": "DSPORTS (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/94",
    "logo": "https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png",
    "fallbacks": []
  },
  {
    "id": "bol95",
    "nombre": "DSPORTS 2 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/95",
    "logo": "https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png",
    "fallbacks": []
  },
  {
    "id": "bol96",
    "nombre": "canal 96",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/96",
    "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
    "fallbacks": []
  },
  {
    "id": "bol97",
    "nombre": "ESPN 8 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/97",
    "logo": "https://images.seeklogo.com/logo-png/4/1/espn-logo-png_seeklogo-49195.png",
    "fallbacks": []
  },
  {
    "id": "bol98",
    "nombre": "ESPN 2 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/98",
    "logo": "https://images.seeklogo.com/logo-png/4/1/espn-2-logo-png_seeklogo-49202.png",
    "fallbacks": []
  },
  {
    "id": "bol99",
    "nombre": "ESPN 3 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/99",
    "logo": "https://images.seeklogo.com/logo-png/26/1/espn-deportes-logo-png_seeklogo-261968.png",
    "fallbacks": []
  },
  {
    "id": "bol100",
    "nombre": "ESPN 4 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/100",
    "logo": "https://images.seeklogo.com/logo-png/4/1/espn-logo-png_seeklogo-49194.png",
    "fallbacks": []
  },
  {
    "id": "bol101",
    "nombre": "FOX SPORT HD (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/101",
    "logo": "https://images.seeklogo.com/logo-png/28/1/fox-sports-hd-logo-png_seeklogo-284627.png",
    "fallbacks": []
  },
  {
    "id": "bol102",
    "nombre": "FOX SPORT 2 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/102",
    "logo": "https://images.seeklogo.com/logo-png/36/1/fox-sports-2-logo-png_seeklogo-369602.png",
    "fallbacks": []
  },
  {
    "id": "bol103",
    "nombre": "FOX SPORT 3 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/103",
    "logo": "https://images.seeklogo.com/logo-png/51/1/fox-sports-3-logo-png_seeklogo-510012.png",
    "fallbacks": []
  },
  {
    "id": "bol104",
    "nombre": "FOX SPORT 4 (B)",
    "categoria": "DEPORTES",
    "url": "https://bolaloca.my/player/2/104",
    "logo": "https://images.seeklogo.com/logo-png/32/1/fox-sports-logo-png_seeklogo-326645.png",
    "fallbacks": []
  },
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
        "nombre":"LATINAS",
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
  {"nombre": "Gist Canales Personalizados", "url": "https://gist.githubusercontent.com/frantdse/f6989518c73826ade6734c63c367af4c/raw/"},
{"nombre": "IPTV global 2", "url": "https://raw.githubusercontent.com/dzh0ni/iPTV-FREE-LIST/master/iPTV-Free-List_TV.m3u"},
   
]

FUENTES_SIN_FILTRO = []


def buscar_canales_m3u(max_por_fuente=5000, max_total=10800):
    print("\n🔍 Escaneando fuentes M3U...")
    # Fix prevent TypeError: asegura que c sea dict y tenga "nombre"
    nombres_existentes = {
        c["nombre"].upper() for c in CANALES_FIJOS + TDT_CANALES 
        if isinstance(c, dict) and "nombre" in c
    }
    
    encontrados = []
    ids_vistos = set()
    headers = {"User-Agent": "Mozilla/5.0 (compatible; StreamX-Scraper/2.0)"}

    for fuente_info in FUENTES_M3U:
        if len(encontrados) >= max_total:
            break
            
        # Extraer URL y Nombre del diccionario de la fuente
        fuente_url = fuente_info["url"]
        fuente_nombre = fuente_info["nombre"]
        
        try:
            print(f"  📥 Procesando: {fuente_nombre}...")
            r = requests.get(fuente_url, timeout=25, headers=headers)
            if r.status_code != 200:
                print(f"      ❌ HTTP {r.status_code}")
                continue
                
            lineas = r.text.split("\n")
            agregados_fuente = 0
            
            for i in range(len(lineas) - 1):
                linea = lineas[i].strip()
                if not linea.startswith("#EXTINF"):
                    continue
                
                url_linea = lineas[i+1].strip()
                if not url_linea.startswith("http"):
                    continue

                # Parsear Metadatos
                logo_m = re.search(r'tvg-logo="([^"]*)"', linea)
                logo = logo_m.group(1) if logo_m else ""
                
                grp_m = re.search(r'group-title="([^"]*)"', linea)
                grp = grp_m.group(1).upper() if grp_m else ""
                
                nombre = linea.split(",")[-1].strip() if "," in linea else "Canal Desconocido"
                n = nombre.upper()
                key = n # Usamos el nombre como clave de duplicidad

                if not nombre or key in nombres_existentes or key in ids_vistos:
                    continue

                # Lógica de Categorización Mejorada
                if any(x in (grp + n) for x in ["SPORT", "DEPORT", "FUTBOL", "FOOTBALL", "LIGA", "COPA", "MOTOR", "ESPN", "FOX S"]):
                    cat = "DEPORTES"
                elif any(x in (grp + n) for x in ["MOVIE", "CINE", "PELICULA", "HBO", "STAR", "CINEMAX", "WARNER"]):
                    cat = "CINE"
                elif any(x in (grp + n) for x in ["NEWS", "NOTICIAS", "INFO", "24H", "PRENSA"]):
                    cat = "NOTICIAS"
                elif any(x in (grp + n) for x in ["MUSIC", "MUSICA", "HITS", "MTV", "VH1"]):
                    cat = "MUSICA"
                elif any(x in (grp + n) for x in ["DOCU", "WILD", "HISTORY", "NAT GEO", "DISCOVERY", "ANIMAL", "DISC."]):
                    cat = "DOCUMENTALES"
                elif any(x in (grp + n) for x in ["KIDS", "INFANTIL", "CHILDREN", "CARTOON", "DISNEY", "NICK", "BOOMERANG"]):
                    cat = "INFANTIL"
                elif any(x in (grp + n) for x in ["XXX", "ADULT", "PLAYBOY", "PENTHOUSE", "VENUS", "SEX"]):
                    cat = "ADULTOS"
                else:
                    cat = "INTERNACIONAL"

                encontrados.append({
                    "nombre": nombre, 
                    "url": url_linea,
                    "logo": logo or "https://cdn-icons-png.flaticon.com/512/716/716429.png",
                    "categoria": cat,
                    "origen": fuente_nombre
                })
                
                ids_vistos.add(key)
                agregados_fuente += 1
                
                if agregados_fuente >= max_por_fuente or len(encontrados) >= max_total:
                    break
                    
            print(f"      ✅ {agregados_fuente} canales nuevos")
            
        except Exception as e:
            print(f"      ❌ Error en fuente: {str(e)[:50]}")

    print(f"  📊 Total M3U extraído: {len(encontrados)}")
    return encontrados


def actualizar_canales(ref):
    print("\n📡 Iniciando actualización en Firebase...")
    ahora = datetime.utcnow().isoformat()
    data = {}

    # 1. Canales fijos (Estructura AR)
    for c in CANALES_FIJOS:
        data[c["id"]] = {
            "nombre": c["nombre"],
            "url": c["url"],
            "logo": c["logo"],
            "categoria": c.get("categoria", "AIRE").upper(),
            "fallbacks": c.get("fallbacks", []),
            "fijo": True,
            "actualizado": ahora
        }

    # 2. Canales TDT (Estructura Internacional/España)
    for c in TDT_CANALES:
        data[c["id"]] = {
            "nombre": c["nombre"],
            "url": c["url"],
            "logo": c["logo"],
            "categoria": c.get("categoria", "AIRE").upper(),
            "fallbacks": [],
            "fijo": False,
            "actualizado": ahora
        }

    # 3. Canales extra de fuentes M3U (Generación de IDs tdt_ext_...)
    extra = buscar_canales_m3u()
    for i, c in enumerate(extra):
        # Generamos un ID único para Firebase basado en el índice
        canal_id = f"ext_{i+1:05d}"
        data[canal_id] = {
            "nombre": c["nombre"],
            "url": c["url"],
            "logo": c["logo"],
            "categoria": c["categoria"],
            "fallbacks": [],
            "fijo": False,
            "actualizado": ahora
        }

    # 4. Preservar estado "activo" desde Firebase
    try:
        existentes = ref.child("canales").get()
        for cid, canal in data.items():
            if existentes and cid in existentes and "activo" in existentes[cid]:
                canal["activo"] = existentes[cid]["activo"]
            else:
                canal["activo"] = True 
    except Exception as e:
        print(f"  ⚠️ Error sincronizando estado activo: {e}")
        for canal in data.values(): canal["activo"] = True

    # 5. Guardado final
    ref.child("canales").set(data)
    print(f"  💾 Guardado exitoso: {len(data)} canales totales en Firebase.")

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
