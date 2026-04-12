const puppeteer = require('puppeteer');
const admin     = require('firebase-admin');
const fs        = require('fs');

const FUENTE_URL = 'https://streamtpnew.com/eventos.html';

// ── Firebase ──────────────────────────────────────────────────────────────
if (!admin.apps.length) {
    let serviceAccount;
    if (process.env.FIREBASE_SERVICE_ACCOUNT) {
        serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
    } else if (fs.existsSync('./firebase-adminsdk.json')) {
        serviceAccount = require('./firebase-adminsdk.json');
    }
    if (serviceAccount) {
        admin.initializeApp({
            credential: admin.credential.cert(serviceAccount),
            databaseURL: 'https://mundialenvivo-ar-default-rtdb.firebaseio.com'
        });
    }
}

async function scrapearEventos() {
    let browser;
    try {
        console.log('🚀 Iniciando scraper de eventos...');
        browser = await puppeteer.launch({
            headless: 'new',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
        });

        const page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');

        console.log(`📡 Cargando ${FUENTE_URL}...`);
        await page.goto(FUENTE_URL, { waitUntil: 'networkidle2', timeout: 30000 });
        await page.waitForSelector('.event', { timeout: 15000 }).catch(() => {});
        await new Promise(r => setTimeout(r, 2000));

        const eventos = await page.evaluate(() => {
            const results = [];
            document.querySelectorAll('.event').forEach(div => {
                const nameEl   = div.querySelector('.event-name');
                const linkEl   = div.querySelector('.iframe-link');
                const statusEl = div.querySelector('.status-button');
                if (!nameEl) return;

                const fullText = nameEl.firstChild?.textContent?.trim() || nameEl.textContent.trim();
                const match  = fullText.match(/^(\d{1,2}:\d{2})\s*[-–]\s*(.+)$/);
                const hora   = match ? match[1] : '';
                const titulo = match ? match[2].trim() : fullText;
                const link   = linkEl ? (linkEl.value || '').trim() : '';
                const enVivo = statusEl ? statusEl.className.includes('live') : false;

                const t = titulo.toLowerCase();
                let categoria = 'Fútbol';
                if (/libertadores/.test(t))                          categoria = 'Libertadores';
                else if (/sudamericana/.test(t))                     categoria = 'Sudamericana';
                else if (/mundial|fifa|selección|seleccion/.test(t)) categoria = 'Mundial';
                else if (/nba|basquet|basket/.test(t))               categoria = 'Basquet';
                else if (/tenis|atp|wta/.test(t))                    categoria = 'Tenis';
                else if (/f1|formula|moto/.test(t))                  categoria = 'Motor';
                else if (/boxeo|ufc|mma/.test(t))                    categoria = 'Boxeo';
                else if (/rugby|nfl/.test(t))                        categoria = 'Rugby';

                if (titulo) results.push({ hora, titulo, link, enVivo, categoria });
            });
            return results;
        });

        // Cerrar browser inmediatamente
        await browser.close();
        browser = null;
        console.log(`✅ ${eventos.length} eventos scrapeados`);

        if (eventos.length > 0 && admin.apps.length) {
            const datosFinales = {
                actualizadoEn: new Date().toISOString(),
                total: eventos.length,
                eventos,
            };

            // Usar REST API directamente en vez de Firebase SDK para evitar conexiones colgadas
            const dbUrl = 'https://mundialenvivo-ar-default-rtdb.firebaseio.com/eventos_dia.json';
            const token = await admin.app().options.credential.getAccessToken();

            const https = require('https');
            const body  = JSON.stringify(datosFinales);

            await new Promise((resolve, reject) => {
                const url = new URL(dbUrl + '?access_token=' + token.access_token);
                const req = https.request({
                    hostname: url.hostname,
                    path: url.pathname + url.search,
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Content-Length': Buffer.byteLength(body),
                    },
                }, res => {
                    let data = '';
                    res.on('data', chunk => data += chunk);
                    res.on('end', () => {
                        if (res.statusCode === 200) {
                            console.log(`🔥 Firebase: ${eventos.length} eventos guardados en /eventos_dia`);
                            resolve();
                        } else {
                            reject(new Error(`HTTP ${res.statusCode}: ${data}`));
                        }
                    });
                });
                req.on('error', reject);
                req.write(body);
                req.end();
            });
        }

    } catch (err) {
        console.error('❌ Error scraper:', err.message);
        if (browser) await browser.close().catch(() => {});
    }
}

scrapearEventos()
    .then(() => {
        console.log('✅ Scraper finalizado');
        // Forzar salida — destruye todas las conexiones pendientes
        setTimeout(() => process.exit(0), 500);
    })
    .catch(err => {
        console.error('❌ Error fatal:', err.message);
        setTimeout(() => process.exit(1), 500);
    });
