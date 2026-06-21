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

function ajustarHoraArgentina(horaTexto) {
    if (!horaTexto || !horaTexto.includes(':')) return '';
    try {
        const [horas, minutos] = horaTexto.split(':').map(Number);
        const fecha = new Date();
        fecha.setHours(horas + 2); // Diferencia horaria (+2 horas)
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
        
        await page.goto(FUENTE_URL, { waitUntil: 'networkidle2', timeout: 30000 });
        
        console.log('⏳ Esperando renderizado de la página...');
        await page.waitForSelector('body', { timeout: 10000 });
        await new Promise(resolve => setTimeout(resolve, 4000));
        
        const eventosNuevos = await page.evaluate(() => {
            const results = [];
            // Selectores adaptados para buscar las opciones/filas
            document.querySelectorAll('table tr, div.row-event, .evento-bloque, .event').forEach(row => {
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

                if (tituloOriginal && link) {
                    results.push({
                        titulo: tituloOriginal,
                        horaOriginal: horaOriginal,
                        link: link
                    });
                }
            });
            return results;
        });

        await browser.close();

        // 🚨 CAMBIO CRÍTICO: Si la página no devolvió nada, cancelamos para no vaciar la BD
        if (eventosNuevos.length === 0) {
            console.log('⚠️ La web devolvió 0 eventos (posible recarga o caída). Manteniendo datos anteriores de Firebase para evitar pantalla vacía.');
            process.exit(0);
        }

        console.log(`✅ Web exitosa: Se encontraron ${eventosNuevos.length} enlaces activos.`);

        if (admin.apps.length) {
            const token = await admin.app().options.credential.getAccessToken();
            const timestampActual = new Date().toISOString();

            // Formatear los nuevos eventos con la hora local de Argentina
            const eventosProcesados = eventosNuevos.map(ev => {
                const horaArg = ajustarHoraArgentina(ev.horaOriginal);
                return {
                    titulo: ev.horaOriginal ? `[${horaArg}] ${ev.titulo}` : ev.titulo,
                    link: ev.link,
                    lastSeen: timestampActual
                };
            });

            // ==========================================================
            // LOGICA MEJORADA: Obtener y fusionar manteniendo el historial
            // ==========================================================
            const dbUrlEventos = `https://mundialenvivo-ar-default-rtdb.firebaseio.com/eventos_dia.json?access_token=${token.access_token}`;
            const response = await httpRequest(dbUrlEventos, 'GET');
            let listaAnterior = (response.data && response.data.eventos) ? response.data.eventos : [];

            // Combinar: Si ya existe por título y link, actualiza su 'lastSeen'. Si es nuevo, lo agrega.
            eventosProcesados.forEach(nuevo => {
                const index = listaAnterior.findIndex(prev => prev.titulo === nuevo.titulo && prev.link === nuevo.link);
                if (index !== -1) {
                    listaAnterior[index].lastSeen = timestampActual; // Sigue vivo
                } else {
                    listaAnterior.unshift(nuevo); // Es un evento nuevo detectado
                }
            });

            // Limpieza por tiempo: Solo borrar eventos que lleven más de 5 horas sin ser vistos en la web
            const HORAS_PERSISTENCIA = 5;
            const limiteTiempo = new Date(Date.now() - HORAS_PERSISTENCIA * 60 * 60 * 1000);
            
            let listaFiltrada = listaAnterior.filter(e => {
                // Si por alguna razón no tiene lastSeen, le ponemos la actual para que no se borre
                const ultimaVezVisto = e.lastSeen ? new Date(e.lastSeen) : new Date();
                return ultimaVezVisto > limiteTiempo;
            });

            // Guardar lista limpia en eventos_dia
            await httpRequest(dbUrlEventos, 'PUT', JSON.stringify({ actualizadoEn: timestampActual, eventos: listaFiltrada }));
            console.log('🔥 Firebase: eventos_dia actualizado de forma segura.');

            // ==========================================================
            // LOGICA MEJORADA: Canales Dinámicos (cheventoXX)
            // ==========================================================
            const dbUrlCanales = `https://mundialenvivo-ar-default-rtdb.firebaseio.com/canales.json?access_token=${token.access_token}`;
            const mapeoCanales = {};

            // Mapeamos los canales usando la lista filtrada activa (máximo 80 canales para no saturar)
            listaFiltrada.slice(0, 80).forEach((evento, idx) => {
                const idCanal = `chevento${String(idx + 1).padStart(2, '0')}`;
                mapeoCanales[idCanal] = {
                    activo: true,
                    actualizado: timestampActual,
                    categoria: "DEPORTES",
                    fijo: false,
                    logo: "https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png",
                    nombre: evento.titulo,
                    url: evento.link
                };
            });

            // Enviamos el bloque usando PATCH (no borra canales manuales estables de tu app)
            await httpRequest(dbUrlCanales, 'PATCH', JSON.stringify(mapeoCanales));
            console.log('🔥 Firebase: Nodos /canales actualizados con persistencia.');
        }
    } catch (err) {
        console.error('❌ Error general en la ejecución:', err.message);
        if (browser) await browser.close().catch(() => {});
    }
}

scrapearEventos().then(() => { process.exit(0); }).catch(() => { process.exit(1); });
