const puppeteer = require('puppeteer');
const admin     = require('firebase-admin');
const fs        = require('fs');
const https     = require('https');

const FUENTE_URL = 'https://streamtpnew.com/eventos.html';

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

function httpRequest(url, method, body = null) {
    return new Promise((resolve, reject) => {
        const urlObj = new URL(url);
        const options = {
            hostname: urlObj.hostname,
            path: urlObj.pathname + urlObj.search,
            method: method,
            headers: { 'Content-Type': 'application/json' }
        };
        if (body) options.headers['Content-Length'] = Buffer.byteLength(body);
        const req = https.request(options, res => {
            let data = '';
            res.on('data', chunk => { data += chunk; });
            res.on('end', () => {
                try { resolve({ status: res.statusCode, data: data ? JSON.parse(data) : null }); }
                catch (e) { resolve({ status: res.statusCode, data: null }); }
            });
        });
        req.on('error', reject);
        if (body) req.write(body);
        req.end();
    });
}

async function scrapearEventos() {
    let browser;
    try {
        console.log('🚀 Iniciando...');
        browser = await puppeteer.launch({
            headless: 'new',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
        });
        const page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        await page.goto(FUENTE_URL, { waitUntil: 'networkidle2', timeout: 30000 });
        await page.waitForSelector('.event', { timeout: 10000 }).catch(() => {});
        
        const eventosNuevos = await page.evaluate(() => {
            const results = [];
            document.querySelectorAll('.event').forEach(div => {
                const nameEl = div.querySelector('.event-name');
                const linkEl = div.querySelector('.iframe-link');
                if (!nameEl) return;
                const titulo = nameEl.textContent.trim();
                const link = linkEl ? (linkEl.value || '').trim() : '';
                results.push({ titulo, link, lastSeen: new Date().toISOString() });
            });
            return results;
        });

        await browser.close();
        console.log(`✅ Web: ${eventosNuevos.length} eventos.`);

        if (admin.apps.length && eventosNuevos.length > 0) {
            const token = await admin.app().options.credential.getAccessToken();
            const dbUrl = `https://mundialenvivo-ar-default-rtdb.firebaseio.com/eventos_dia.json?access_token=${token.access_token}`;
            const response = await httpRequest(dbUrl, 'GET');
            let lista = (response.data && response.data.eventos) ? response.data.eventos : [];

            eventosNuevos.forEach(n => {
                const i = lista.findIndex(e => e.titulo === n.titulo);
                if (i !== -1) { lista[i] = { ...lista[i], ...n }; }
                else { lista.unshift(n); }
            });

            const limite = new Date(Date.now() - 24 * 60 * 60 * 1000);
            lista = lista.filter(e => new Date(e.lastSeen) > limite);

            await httpRequest(dbUrl, 'PUT', JSON.stringify({ actualizadoEn: new Date().toISOString(), eventos: lista }));
            console.log('🔥 Firebase actualizado.');
        }
    } catch (err) {
        console.error('❌ Error:', err.message);
        if (browser) await browser.close().catch(() => {});
    }
}

scrapearEventos().then(() => { process.exit(0); }).catch(() => { process.exit(1); });
