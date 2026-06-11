/**
 * @file scraper.js
 * @description Scraper de alta disponibilidad para Mundial en Vivo - TECNOCOM
 * @version 1.0.2
 */

const puppeteer = require('puppeteer');
const admin = require('firebase-admin');
const fs = require('fs');

const FUENTE_URL = process.env.FUENTE_URL || 'https://streamtpday1.xyz/eventos.html';
const DB_URL = process.env.FIREBASE_DATABASE_URL || 'https://mundialenvivo-ar-default-rtdb.firebaseio.com';

// Inicialización del SDK de Firebase
if (!admin.apps.length) {
    let serviceAccount = null;
    if (process.env.FIREBASE_SERVICE_ACCOUNT) {
        try {
            serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
        } catch (e) {
            console.error('❌ Error al parsear FIREBASE_SERVICE_ACCOUNT:', e.message);
        }
    } else if (fs.existsSync('./firebase-adminsdk.json')) {
        serviceAccount = require('./firebase-adminsdk.json');
    }

    if (serviceAccount) {
        admin.initializeApp({
            credential: admin.credential.cert(serviceAccount),
            databaseURL: DB_URL
        });
        console.log('🚀 Firebase Admin SDK conectado.');
    } else {
        console.error('❌ Error crítico: No se encontraron credenciales de Firebase.');
        process.exit(1);
    }
}

const db = admin.database();

/**
 * Sanitiza cadenas de texto para evitar caracteres de control.
 * @param {string} text 
 * @returns {string}
 */
function sanitizeString(text) {
    if (!text) return '';
    return text.replace(/[\r\n\t]+/g, ' ').trim();
}

async function ejecutarScraper() {
    let browser = null;
    try {
        console.log(`⏱️ Inicio de ciclo: ${new Date().toISOString()}`);
        
        browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox', 
                '--disable-setuid-sandbox', 
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ],
        });

        const page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36');
        await page.setDefaultNavigationTimeout(45000);

        console.log(`🔗 Navegando a: ${FUENTE_URL}`);
        await page.goto(FUENTE_URL, { waitUntil: 'networkidle2' });

        console.log('⏳ Esperando renderizado de la estructura .event...');
        await page.waitForSelector('.event', { timeout: 20000 });

        // Forzar delay de 3.5 segundos para garantizar la carga completa de elementos asíncronos en el DOM
        await new Promise(resolve => setTimeout(resolve, 3500));

        // Extracción directa utilizando selectores específicos validados por DevTools
        const eventosExtraidos = await page.evaluate(() => {
            const resultados = [];
            const bloques = document.querySelectorAll('.event');
            
            bloques.forEach(div => {
                const nameEl = div.querySelector('.event-name');
                const inputEl = div.querySelector('input.iframe-link');
                
                if (nameEl && inputEl) {
                    const titulo = nameEl.textContent.trim();
                    const url = inputEl.value.trim();
                    if (url) {
                        resultados.push({ titulo, url });
                    }
                }
            });
            return resultados;
        });

        await browser.close();
        console.log(`📊 Total de eventos capturados: ${eventosExtraidos.length}`);

        if (eventosExtraidos.length === 0) {
            console.log('⚠️ No se encontraron eventos válidos en este ciclo.');
            return;
        }

        const canalesRef = db.ref('canales');
        const timestampActual = new Date().toISOString();
        const actualizaciones = {};

        // Mapeo secuencial estricto a claves cheventoXX
        eventosExtraidos.forEach((evento, idx) => {
            const idCanal = `chevento${String(idx + 1).padStart(2, '0')}`;
            
            actualizaciones[idCanal] = {
                activo: true,
                actualizado: timestampActual,
                categoria: "DEPORTES",
                fijo: false,
                logo: "https://streamtpday1.xyz/stp.png",
                nombre: sanitizeString(evento.titulo),
                url: sanitizeString(evento.url)
            };
        });

        console.log(`🔄 Sincronizando actualizaciones en /canales...`);
        await canalesRef.update(actualizaciones);
        console.log('🔥 Firebase Realtime Database actualizada exitosamente.');

    } catch (error) {
        console.error('❌ Error en ejecución del scraper:', error.stack);
        if (browser) await browser.close().catch(() => {});
    }
}

ejecutarScraper().then(() => {
    process.exit(0);
}).catch(err => {
    console.error('💥 Fallo catastrófico:', err);
    process.exit(1);
});
