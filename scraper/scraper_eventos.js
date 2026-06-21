const puppeteer = require('puppeteer');
const admin      = require('firebase-admin');
const fs         = require('fs');
const https      = require('https');

const FUENTE_URL = 'https://streamtpday1.xyz/eventos.html';

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

// Función auxiliar para formatear la hora sumando 2 horas (Convertir a Hora de Argentina)
function ajustarHoraArgentina(horaTexto) {
    if (!horaTexto || !horaTexto.includes(':')) return '';
    try {
        const [horas, minutos] = horaTexto.split(':').map(Number);
        const fecha = new Date();
        fecha.setHours(horas + 2); // Sumamos las 2 horas de diferencia
        fecha.setMinutes(minutos);
        
        return fecha.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', hour12: false });
    } catch (e) {
        return horaTexto;
    }
}

async function scrapearEventos() {
    let browser;
    try {
        console.log('🚀 Iniciando Puppeteer...');
        browser = await puppeteer.launch({
            headless: 'new',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
        });
        const page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        await page.setViewport({ width: 1280, height: 800 });
        
        await page.goto(FUENTE_URL, { waitUntil: 'networkidle2', timeout: 30000 });
        
        console.log('⏳ Esperando renderizado de la totalidad de los eventos...');
        // Esperamos un selector genérico de contenedor de eventos o filas
        await page.waitForSelector('body', { timeout: 10000 });
        await new Promise(resolve => setTimeout(resolve, 4000));
        
        const eventosNuevos = await page.evaluate(() => {
            const results = [];
            
            // Adaptar estos selectores según los nombres de clase reales de la web inspeccionada
            // Asumimos una estructura común de listas o tablas para este clon de agendas deportivas
            const bloquesEventos = document.querySelectorAll('.event, tr.evento, div.item-evento'); 
            
            // Si la estructura usa filas globales, recorremos las filas que contienen los partidos y opciones
            document.querySelectorAll('table tr, div.row-event, .evento-bloque').forEach(row => {
                // Cambia estos selectores tras inspeccionar el código fuente exacto (F12) de la web
                const nameEl = row.querySelector('.event-name, td strong, .titulo-evento');
                const timeEl = row.querySelector('.event-time, .hora, td:first-child');
                const linkEl = row.querySelector('input.iframe-link, .link-stream, a.btn-opcion');
                
                if (!nameEl) return;
                
                const tituloOriginal = nameEl.textContent.trim();
                const horaOriginal = timeEl ? timeEl.textContent.trim() : '';
                
                let link = '';
                if (linkEl) {
                    link = linkEl.tagName === 'INPUT' ? linkEl.value : (linkEl.getAttribute('href') || linkEl.textContent);
                }
                link = link.trim();

                if (tituloOriginal) {
                    results.push({
                        titulo: tituloOriginal,
                        horaOriginal: horaOriginal,
                        link: link,
                        lastSeen: new Date().toISOString()
                    });
                }
            });
            
            return results;
        });

        await browser.close();
        console.log(`✅ Web: Procesados ${eventosNuevos.length} enlaces de opciones.`);

        if (admin.apps.length && eventosNuevos.length > 0) {
            const token = await admin.app().options.credential.getAccessToken();
            const timestampActual = new Date().toISOString();

            // Mapeamos los eventos y corregimos los horarios antes de enviarlos a Firebase
            const eventosProcesados = eventosNuevos.map(ev => {
                const horaArg = ajustarHoraArgentina(ev.horaOriginal);
                return {
                    titulo: ev.horaOriginal ? `[${horaArg}] ${ev.titulo}` : ev.titulo,
                    link: ev.link,
                    lastSeen: ev.lastSeen
                };
            });

            // ==========================================
            // LOGICA: Actualizar eventos_dia
            // ==========================================
            const dbUrlEventos = `https://mundialenvivo-ar-default-rtdb.firebaseio.com/eventos_dia.json?access_token=${token.access_token}`;
            const response = await httpRequest(dbUrlEventos, 'GET');
            let lista = (response.data && response.data.eventos) ? response.data.eventos : [];

            eventosProcesados.forEach(n => {
                const i = lista.findIndex(e => e.titulo === n.titulo && e.link === n.link);
                if (i !== -1) { lista[i] = { ...lista[i], ...n }; }
                else { lista.unshift(n); }
            });

            const limite = new Date(Date.now() - 24 * 60 * 60 * 1000);
            lista = lista.filter(e => new Date(e.lastSeen) > limite);

            await httpRequest(dbUrlEventos, 'PUT', JSON.stringify({ actualizadoEn: timestampActual, eventos: lista }));
            console.log('🔥 Firebase: eventos_dia actualizado con horario de Argentina.');

            // ==========================================
            // LOGICA: Actualizar /canales/cheventoXX
            // ==========================================
            const dbUrlCanales = `https://mundialenvivo-ar-default-rtdb.firebaseio.com/canales.json?access_token=${token.access_token}`;
            const mapeoCanales = {};

            eventosProcesados.slice(0, 80).forEach((evento, idx) => {
                const idCanal = `chevento${String(idx + 1).padStart(2, '0')}`;
                mapeoCanales[idCanal] = {
                    activo: true,
                    actualizado: timestampActual,
                    categoria: "DEPORTES",
                    fijo: false,
                    logo: "https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png",
                    nombre: evento.titulo,
                    url: evento.url || evento.link
                };
            });

            await httpRequest(dbUrlCanales, 'PATCH', JSON.stringify(mapeoCanales));
            console.log('🔥 Firebase: Nodos /canales actualizados.');
        }
    } catch (err) {
        console.error('❌ Error:', err.message);
        if (browser) await browser.close().catch(() => {});
    }
}

scrapearEventos().then(() => { process.exit(0); }).catch(() => { process.exit(1); });
