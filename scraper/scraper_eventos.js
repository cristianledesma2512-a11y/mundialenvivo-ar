const puppeteer = require('puppeteer');
const admin     = require('firebase-admin');
const fs        = require('fs');
const https     = require('https');

const FUENTE_URL = 'https://streamtpnew.com/eventos.html';

// ── Firebase Configuration ────────────────────────────────────────────────
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

// Función auxiliar para peticiones HTTPS (GET/PUT)
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
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    resolve({ status: res.statusCode, data: data ? JSON.parse(data) : null });
                } catch (e) {
                    resolve({ status: res.statusCode, data: null });
                }
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
        console.log('🚀 Iniciando scraper persistente...');
        browser = await puppeteer.launch({
            headless: 'new',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
        });

        const page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');

        console.log(`📡 Scrapeando: ${FUENTE_URL}`);
        await page.goto(FUENTE_URL, { waitUntil: 'networkidle2', timeout: 30000 });
        await page.waitForSelector('.event', { timeout: 15000 }).catch(() => {});
        
        const eventosNuevos = await page.evaluate(() => {
            const results = [];
            document.querySelectorAll('.event').forEach(div => {
                const nameEl   = div.querySelector('.event-name');
                const linkEl   = div.querySelector('.iframe-link');
                const statusEl = div.querySelector('.status-button');
                if (!nameEl) return;

                const fullText = nameEl.firstChild?.textContent?.trim() || nameEl.textContent.trim();
                const match   = fullText.match(/^(\d{1,2}:\d{2})\s*[-–]\s*(.+)$/);
                const hora    = match ? match[1] : '';
                const titulo = match ? match[2].trim() : fullText;
                const link    = linkEl ? (linkEl.value || '').trim() : '';
                const enVivo = statusEl ? statusEl.className.includes('live') : false;

                const t = titulo.toLowerCase();
                let categoria = 'Fútbol';
                if (/libertadores/.test(t)) categoria = 'Libertadores';
                else if (/sudamericana/.test(t)) categoria = 'Sudamericana';
                else if (/mundial|fifa|selección|seleccion/.test(t)) categoria = 'Mundial';
                else if (/nba|basquet|basket/.test(t)) categoria = 'Basquet';
                else if (/tenis|atp|wta/.test(t)) categoria = 'Tenis';
                else if (/f1|formula|moto/.test(t)) categoria = 'Motor';
                else if (/boxeo|ufc|mma/.test(t)) categoria = 'Boxeo';
                else if (/rugby|nfl/.test(t)) categoria = 'Rugby';

                if (titulo) results.push({ hora, titulo, link, enVivo, categoria, lastSeen: new Date().toISOString() });
            });
            return results;
        });

        await browser.close();
        console.log(`✅ ${eventosNuevos.length} eventos detectados en la web.`);

        if (admin.apps.length) {
            const token = await admin.app().options.credential.getAccessToken();
            const dbUrl = `https://mundialenvivo-ar-default-rtdb.firebaseio.com/eventos_dia.json?access_token=${token.access_token}`;

            console.log('📥 Obteniendo datos actuales de Firebase...');
            const response = await httpRequest(dbUrl, 'GET');
            let listaPersistente = (response.data && response.data.eventos) ? response.data.eventos : [];

            if (eventosNuevos.length > 0) {
                eventosNuevos.forEach(nuevo => {
                    const idx = listaPersistente.findIndex(e => e.titulo === nuevo.titulo);
                    if (idx !== -1) {
                        listaPersistente[idx] = { ...listaPersistente[idx], ...nuevo };
                    } else {
                        listaPersistente.unshift(nuevo);
                    }
                });

                const unDiaAtras = new Date(Date.now() - 24 * 60 * 60 * 1000);
                listaPersistente = listaPersistente.filter(e => new Date(e.lastSeen) > unDiaAtras);

                const datosFinales = {
