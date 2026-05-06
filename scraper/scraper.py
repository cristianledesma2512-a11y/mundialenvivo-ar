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
    {"id":"stp01","nombre":"Disney","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=disney","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp02","nombre":"Disney 1","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=disney1","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp03","nombre":"Disney 2","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=disney2","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp04","nombre":"Disney 3","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=disney3","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp05","nombre":"Disney 4","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=disney4","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp06","nombre":"Disney 5","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=disney5","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp07","nombre":"Disney 6","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=disney6","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp08","nombre":"Disney 7","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=disney7","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp09","nombre":"Disney 8","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=disney8","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp10","nombre":"Disney 9","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=disney9","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp11","nombre":"Disney 10","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=disney10","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp12","nombre":"Disney 11","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=disney11","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp13","nombre":"Disney 12","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=disney12","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp14","nombre":"Disney 13","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=disney13","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp15","nombre":"Disney 14","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=disney14","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},
    {"id":"stp16","nombre":"Disney 15","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=disney15","logo":"https://images.seeklogo.com/logo-png/4/1/disney-logo-png_seeklogo-41972.png","fallbacks":[]},

    # ── FANATIZ 
    {"id":"stp17","nombre":"Fanatiz","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fanatiz","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp18","nombre":"Fanatiz 1","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fanatiz1","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp19","nombre":"Fanatiz 2","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fanatiz2","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp20","nombre":"Fanatiz 3","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fanatiz3","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp21","nombre":"Fanatiz 4","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fanatiz4","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp22","nombre":"Fanatiz 5","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fanatiz5","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp23","nombre":"Fanatiz 6","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fanatiz6","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp24","nombre":"Fanatiz 7","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fanatiz7","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp25","nombre":"Fanatiz 8","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fanatiz8","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp26","nombre":"Fanatiz 9","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fanatiz9","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp27","nombre":"Fanatiz 10","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fanatiz10","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp28","nombre":"Fanatiz 11","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fanatiz11","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp29","nombre":"Fanatiz 12","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fanatiz12","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp30","nombre":"Fanatiz 13","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fanatiz13","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp31","nombre":"Fanatiz 14","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fanatiz14","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},
    {"id":"stp32","nombre":"Fanatiz 15","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fanatiz15","logo":"https://nextjs.fanatiz.com/fanatiz/strapi/production/Fanatiz_new_92171dc64b.png","fallbacks":[]},


    #  ESPN  
    {"id":"stp33","nombre":"ESPN","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp34","nombre":"ESPN 1","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn1","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp35","nombre":"ESPN 2","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn2","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp36","nombre":"ESPN 3","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn3","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp37","nombre":"ESPN 4","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn4","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp38","nombre":"ESPN 5","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn5","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp39","nombre":"ESPN 6","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn6","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp40","nombre":"ESPN 7","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn7","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp41","nombre":"ESPN 8","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn8","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp42","nombre":"ESPN 9","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn9","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp43","nombre":"ESPN 10","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn10","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp44","nombre":"ESPN 11","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn11","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp45","nombre":"ESPN 12","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn12","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp46","nombre":"ESPN 13","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn13","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp47","nombre":"ESPN 14","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn14","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},
    {"id":"stp48","nombre":"ESPN 15","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn15","logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png","fallbacks":[]},


    #  DSPORTS 
    {"id":"stp49","nombre":"DSports","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=dsports","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp50","nombre":"DSports 1","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=dsports1","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp51","nombre":"DSports 2","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=dsports2","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp52","nombre":"DSports 3","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=dsports3","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp53","nombre":"DSports 4","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=dsports4","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp54","nombre":"DSports 5","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=dsports5","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp55","nombre":"DSports 6","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=dsports6","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp56","nombre":"DSports 7","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=dsports7","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp57","nombre":"DSports 8","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=dsports8","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp58","nombre":"DSports 9","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=dsports9","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp59","nombre":"DSports 10","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=dsports10","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp60","nombre":"DSports 11","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=dsports11","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp61","nombre":"DSports 12","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=dsports12","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp62","nombre":"DSports 13","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=dsports13","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp63","nombre":"DSports 14","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=dsports14","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},
    {"id":"stp64","nombre":"DSports 15","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=dsports15","logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png","fallbacks":[]},

    #  TUDN USA 
    {"id":"stp65","nombre":"TUDN USA","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tudn_usa","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp66","nombre":"TUDN USA 1","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tudn_usa1","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp67","nombre":"TUDN USA 2","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tudn_usa2","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp68","nombre":"TUDN USA 3","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tudn_usa3","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp69","nombre":"TUDN USA 4","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tudn_usa4","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp70","nombre":"TUDN USA 5","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tudn_usa5","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp71","nombre":"TUDN USA 6","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tudn_usa6","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp72","nombre":"TUDN USA 7","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tudn_usa7","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp73","nombre":"TUDN USA 8","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tudn_usa8","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp74","nombre":"TUDN USA 9","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tudn_usa9","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp75","nombre":"TUDN USA 10","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tudn_usa10","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp76","nombre":"TUDN USA 11","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tudn_usa11","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp77","nombre":"TUDN USA 12","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tudn_usa12","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp78","nombre":"TUDN USA 13","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tudn_usa13","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp79","nombre":"TUDN USA 14","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tudn_usa14","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},
    {"id":"stp80","nombre":"TUDN USA 15","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tudn_usa15","logo":"https://images.seeklogo.com/logo-png/38/1/tudn-positivo-logo-png_seeklogo-387423.png","fallbacks":[]},

    #  MAX 
    {"id":"stp81","nombre":"Max","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=max","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp82","nombre":"Max 1","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=max1","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp83","nombre":"Max 2","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=max2","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp84","nombre":"Max 3","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=max3","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp85","nombre":"Max 4","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=max4","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp86","nombre":"Max 5","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=max5","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp87","nombre":"Max 6","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=max6","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp88","nombre":"Max 7","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=max7","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp89","nombre":"Max 8","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=max8","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp90","nombre":"Max 9","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=max9","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp91","nombre":"Max 10","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=max10","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp92","nombre":"Max 11","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=max11","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp93","nombre":"Max 12","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=max12","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp94","nombre":"Max 13","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=max13","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp85","nombre":"Max 14","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=max14","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},
    {"id":"stp96","nombre":"Max 15","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=max15","logo":"https://images.seeklogo.com/logo-png/2/1/canal-logo-png_seeklogo-25587.png","fallbacks":[]},

    
    
    #   TyC sport
    {"id":"stp97","nombre":"TyC Sports","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tycsports","logo":"https://images.seeklogo.com/logo-png/34/1/tyc-sports-logo-png_seeklogo-340604.png","fallbacks":[]},
    {"id":"stp125","nombre":"TyC Sports Inter","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tycinternacional","logo":"https://images.seeklogo.com/logo-png/34/1/tyc-sports-logo-png_seeklogo-340604.png","fallbacks":[]},


    


    #  paramount
    {"id":"stp98","nombre":"paramount1","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=paramount1","logo":"https://images.seeklogo.com/logo-png/10/1/paramount-logo-png_seeklogo-106080.png","fallbacks":[]},
    {"id":"stp99","nombre":"paramount2","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=paramount2","logo":"https://images.seeklogo.com/logo-png/10/1/paramount-logo-png_seeklogo-106080.png","fallbacks":[]},
    {"id":"stp100","nombre":"paramount3","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=paramount3","logo":"https://images.seeklogo.com/logo-png/10/1/paramount-logo-png_seeklogo-106080.png","fallbacks":[]},
    {"id":"stp101","nombre":"paramount4","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=paramount4","logo":"https://images.seeklogo.com/logo-png/10/1/paramount-logo-png_seeklogo-106080.png","fallbacks":[]},
    {"id":"stp102","nombre":"paramount5","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=paramount5","logo":"https://images.seeklogo.com/logo-png/10/1/paramount-logo-png_seeklogo-106080.png","fallbacks":[]},
    {"id":"stp103","nombre":"paramount6","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=paramount6","logo":"https://images.seeklogo.com/logo-png/10/1/paramount-logo-png_seeklogo-106080.png","fallbacks":[]},
    {"id":"stp104","nombre":"paramount7","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=paramount7","logo":"https://images.seeklogo.com/logo-png/10/1/paramount-logo-png_seeklogo-106080.png","fallbacks":[]},
    {"id":"stp105","nombre":"paramount8","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=paramount8","logo":"https://images.seeklogo.com/logo-png/10/1/paramount-logo-png_seeklogo-106080.png","fallbacks":[]},

    {"id":"stp106","nombre":"paramount9","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=paramount9","logo":"https://images.seeklogo.com/logo-png/10/1/paramount-logo-png_seeklogo-106080.png","fallbacks":[]},

    {"id":"stp107","nombre":"paramount10","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=paramount10","logo":"https://images.seeklogo.com/logo-png/10/1/paramount-logo-png_seeklogo-106080.png","fallbacks":[]},

    
    

    #  espn mx
    {"id":"stp108","nombre":"espn mx","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espnmx","logo":"https://1000logos.net/wp-content/uploads/2017/01/espn-symbol.jpg","fallbacks":[]},     
    {"id":"stp109","nombre":"espn 2mx","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn2mx","logo":"https://1000logos.net/wp-content/uploads/2017/01/espn-symbol.jpg","fallbacks":[]}, 	
    {"id":"stp110","nombre":"espn 3mx","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espn3mx","logo":"https://1000logos.net/wp-content/uploads/2017/01/espn-symbol.jpg","fallbacks":[]},


    #  fox sport
    {"id":"stp111","nombre":"Fox Sports 1","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fox1ar","logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png","fallbacks":[]},
    {"id":"stp112","nombre":"Fox Sports 2","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fox2ar","logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png","fallbacks":[]},
    {"id":"stp113","nombre":"Fox Sports 3","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=fox3ar","logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png","fallbacks":[]},
    

    #   TNT GB
    {"id":"stp114","nombre":"TNT 1 gb","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tnt_1_gb","logo":"https://www.freepnglogos.com/uploads/tnt-logo-png-9.jpg","fallbacks":[]},

    {"id":"stp115","nombre":"TNT 2 gb","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tnt_2_gb","logo":"https://www.freepnglogos.com/uploads/tnt-logo-png-9.jpg","fallbacks":[]},

    {"id":"stp116","nombre":"TNT 3 gb","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tnt_3_gb","logo":"https://www.freepnglogos.com/uploads/tnt-logo-png-9.jpg","fallbacks":[]},

    {"id":"stp117","nombre":"TNT 4 gb","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tnt_4_gb","logo":"https://www.freepnglogos.com/uploads/tnt-logo-png-9.jpg","fallbacks":[]},

    #   Aire
    {"id":"stp118","nombre":"Telefe F","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=telefe","logo":"https://images.seeklogo.com/logo-png/45/1/telefe-tv-logo-png_seeklogo-451860.png","fallbacks":[]},

    {"id":"stp119","nombre":"Telefe EN VIVO","categoria":"NOTICIAS","url":"http://201.217.246.42:44310/Live/3fcb6e26785fd8d415571b26dc3cf5d3/telefe.playlist.m3u8","logo":"https://images.seeklogo.com/logo-png/45/1/telefe-tv-logo-png_seeklogo-451860.png","fallbacks":[]},

    
    {"id":"stp120","nombre":"TN noticias","categoria":"NOTICIAS","url":"https://www.youtube.com/watch?v=cb12KmMMDJA","logo":"https://images.seeklogo.com/logo-png/46/1/todo-noticias-logo-png_seeklogo-462511.png","fallbacks":[]},
    

    #   ESPN Premium
    {"id":"stp121","nombre":"ESPN Premium","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espnpremium","logo":"https://librefutbol.com.ar/wp-content/uploads/2025/03/espn-premium-logo.png","fallbacks":[]},

    #   ESPN deportes
    {"id":"stp122","nombre":"ESPN deportes","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=espndeportes","logo":"https://2.bp.blogspot.com/-RG0tX1-q0VM/UZ5RRl910eI/AAAAAAAAAKg/RasxwojGhHo/s1600/espndeportes.jpg","fallbacks":[]},

    #   DSPORT PLUS
    {"id":"stp123","nombre":"DSPORT Plus","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=dsportsplus","logo":"https://i0.wp.com/trucosonline.com/wp-content/uploads/2022/11/613.png","fallbacks":[]},


    #   TNT sport
    {"id":"stp124","nombre":"TNT Sports","categoria":"NOTICIAS","url":"https://streamtpnew.com/global2.php?stream=tntsports","logo":"https://images.seeklogo.com/logo-png/51/1/tnt-sports-logo-png_seeklogo-519540.png","fallbacks":[]},
  
  
    # ── Bolaloca via proxy Railway ────────────────────────────────────

    {"id":"bol01",
        "nombre":"TYC SPORT",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/77",
        "logo":"https://images.seeklogo.com/logo-png/34/1/tyc-sports-logo-png_seeklogo-340604.png",
        "fallbacks":[]},
    {"id":"bol02",
        "nombre":"ESPN PREMIUM",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/76",
        "logo":"https://images.seeklogo.com/logo-png/4/1/espn-logo-png_seeklogo-49194.png",
        "fallbacks":[]},
    {"id":"bol03",
        "nombre":"TNT SPORT",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/75",
        "logo":"https://images.seeklogo.com/logo-png/51/1/tnt-sports-logo-png_seeklogo-519540.png",
        "fallbacks":[]},
    {"id":"bol04",
        "nombre":"DSPORT",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/94",
        "logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png",
        "fallbacks":[]},
    {"id":"bol05",
        "nombre":"DSPORT2",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/95",
        "logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png",
        "fallbacks":[]},
    {"id":"bol06",
        "nombre":"DSPORT+",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/96",
        "logo":"https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png",
        "fallbacks":[]},
    {"id":"bol07",
        "nombre":"+FOOT",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/12",
        "logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks":[]},
    {"id":"bol08",
        "nombre":"+SPORT",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/13",
        "logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks":[]},
    {"id":"bol09",
        "nombre":"+SPORT360",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/14",
        "logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks":[]},
    {"id":"bol10",
        "nombre":"EUROSPORT1",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/15",
        "logo":"https://images.seeklogo.com/logo-png/27/1/eurosport-logo-png_seeklogo-270286.png",
        "fallbacks":[]},
    {"id":"bol11",
        "nombre":"EUROSPORT",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/16",
        "logo":"https://images.seeklogo.com/logo-png/27/1/eurosport-logo-png_seeklogo-270286.png",
        "fallbacks":[]},
    {"id":"bol12",
        "nombre":"RMC SPORT1",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/17",
        "logo":"https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks":[]},
    {"id":"bol13",
        "nombre":"ligue 1+",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/18",
        "logo":"https://logos-world.net/wp-content/uploads/2024/06/Ligue-1-Logo-New.png",
        "fallbacks":[]},
    {"id":"bol14",
        "nombre":"TUDN",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/68",
        "logo":"https://tvlatina.tv/tvhispana/wp-content/uploads/sites/12/2015/11/TUDN_logo.jpg",
        "fallbacks":[]},
    {"id":"bol15",
        "nombre":"FOX DEPORTES",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/70",
        "logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png",
        "fallbacks":[]},
    {"id":"bol16",
        "nombre":"LAS",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/74",
        "logo":"https://i0.wp.com/laligatoronto.ca/wp-content/uploads/2022/11/Logo_La-Liga-Sports-Complex_verde.png",
        "fallbacks":[]},
    {"id":"bol17",
        "nombre":"FOXSPORT",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/78",
        "logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png",
        "fallbacks":[]},
    {"id":"bol18",
        "nombre":"FOXSPORT2",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/79",
        "logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png",
        "fallbacks":[]},
    {"id":"bol19",
        "nombre":"FOXSPORT3",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/80",
        "logo":"https://images.seeklogo.com/logo-png/31/1/fox-sports-logo-png_seeklogo-315883.png",
        "fallbacks":[]},
    {"id":"bol20",
        "nombre":"WINSPORT",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/81",
        "logo":"https://images.seeklogo.com/logo-png/64/1/win-sports-logo-png_seeklogo-644046.png",
        "fallbacks":[]},
    {"id":"bol21",
        "nombre":"TNTSPORT PREMIUM",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/83",
        "logo":"https://images.seeklogo.com/logo-png/37/1/tnt-sports-logo-png_seeklogo-373020.png",
        "fallbacks":[]},
    {"id":"bol22",
        "nombre":"ESPN",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/87",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"bol23",
        "nombre":"ESPN2",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/88",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"bol24",
        "nombre":"ESPN3",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/89",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"bol25",
        "nombre":"ESPN4",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/90",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"bol26",
        "nombre":"ESPN5",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/91",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},
    {"id":"bol27",
        "nombre":"ESPN6",
        "categoria":"INTERNACIONAL",
        "url":"https://bolaloca.my/player/2/92",
        "logo":"https://images.seeklogo.com/logo-png/28/1/espn-logo-png_seeklogo-283139.png",
        "fallbacks":[]},

      # canales capoplay──────────────────

      {
        "id": "cap01",
        "nombre": "canal1",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal1.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap02",
        "nombre": "canal2",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal2.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap03",
        "nombre": "canal3",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal3.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap04",
        "nombre": "canal4",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal4.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap05",
        "nombre": "canal5",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal5.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap06",
        "nombre": "canal6",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal6.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap07",
        "nombre": "canal7",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal7.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap08",
        "nombre": "canal8",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal8.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap09",
        "nombre": "canal9",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal9.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap10",
        "nombre": "canal10",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal10.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap11",
        "nombre": "canal11",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal11.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap12",
        "nombre": "canal12",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal12.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap13",
        "nombre": "canal13",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal13.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap14",
        "nombre": "canal14",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal14.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap15",
        "nombre": "canal15",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal15.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap16",
        "nombre": "canal16",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal16.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap17",
        "nombre": "canal17",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal17.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap18",
        "nombre": "canal18",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal18.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap19",
        "nombre": "canal19",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal19.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap20",
        "nombre": "canal20",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal20.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap21",
        "nombre": "canal21",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal21.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap22",
        "nombre": "canal22",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal22.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap23",
        "nombre": "canal23",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal23.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap24",
        "nombre": "canal24",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal24.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap25",
        "nombre": "canal25",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal25.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap26",
        "nombre": "canal26",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal26.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap27",
        "nombre": "canal27",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal27.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap28",
        "nombre": "canal28",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal28.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap29",
        "nombre": "canal29",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal29.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap30",
        "nombre": "canal30",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal30.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap31",
        "nombre": "canal31",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal31.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap32",
        "nombre": "canal32",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal32.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap33",
        "nombre": "canal33",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal33.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap34",
        "nombre": "canal34",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal34.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap35",
        "nombre": "canal35",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal35.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap36",
        "nombre": "canal36",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal36.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap37",
        "nombre": "canal37",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal37.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap38",
        "nombre": "canal38",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal38.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap39",
        "nombre": "canal39",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal39.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap40",
        "nombre": "canal40",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal40.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap41",
        "nombre": "canal41",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal41.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap42",
        "nombre": "canal42",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal42.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap43",
        "nombre": "canal43",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal43.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap44",
        "nombre": "canal44",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal44.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap45",
        "nombre": "canal45",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal45.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap46",
        "nombre": "canal46",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal46.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap47",
        "nombre": "canal47",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal47.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap48",
        "nombre": "canal48",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal48.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap49",
        "nombre": "canal49",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal49.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      },
      {
        "id": "cap50",
        "nombre": "canal50",
        "categoria": "MUSICA",
        "url": "https://www.capoplay.net/canal50.php",
        "logo": "https://cdn-icons-png.flaticon.com/512/53/53283.png",
        "fallbacks": []
      }

          
]
TDT_CANALES = [
    
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
#  EVENTOS DEPORTIVOS DEL DÍA
# ══════════════════════════════════════════════════════════════════════════
def scrapear_eventos(ref):
    """
    Scrapea https://streamtpnew.com/eventos.html
    y guarda los eventos en Firebase bajo /eventos_dia
    """
    print("\n⚽ Scrapeando eventos deportivos...")
    URL = "https://streamtpnew.com/eventos.html"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-AR,es;q=0.9",
        "Referer": "https://streamtpnew.com/",
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
