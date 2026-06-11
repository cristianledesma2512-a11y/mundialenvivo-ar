const puppeteer = require('puppeteer');
const admin = require('firebase-admin');
const fs = require('fs');

const FUENTE_URL = 'https://streamtpday1.xyz/eventos.html';
const DB_URL = 'https://mundialenvivo-ar-default-rtdb.firebaseio.com';

// 1. Inicialización limpia y segura de Firebase Admin SDK
if (!admin.apps.length) {
    let serviceAccount = null;
    if (process.env.FIREBASE_SERVICE_ACCOUNT) {
        serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
    } else if (fs.existsSync('./firebase-adminsdk.json')) {
        serviceAccount = require('./firebase-adminsdk.json');
    }

    if (serviceAccount) {
        admin.initializeApp({
            credential: admin.credential.cert(serviceAccount),
            databaseURL: DB_URL
        });
        console.log('🚀 Firebase conectado correctamente utilizando el SDK Oficial.');
    } else {
        console.error('❌ Error: No se encontraron credenciales de Firebase (archivo o variable de entorno).');
        process.exit(1);
    }
}

const db = admin.database();

async function scrapearYActualizarCanales() {
    let browser;
    try {
        console.log('⏳ Iniciando proceso de scraping...');
        
        browser = await puppeteer.launch({
            headless: 'new',
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
        });
        
        const page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        
        // Navegación con tiempo de espera prudencial
        await page.goto(FUENTE_URL, { waitUntil: 'networkidle2', timeout: 45000 });
        
        // Esperamos explícitamente a que aparezca al menos un evento en el DOM
        await page.waitForSelector('.event', { timeout: 15000 });

        // 2. Extracción de datos usando los selectores exactos de tu DevTools
        const eventosScrapeados = await page.evaluate(() => {
            const resultados = [];
            const bloques = document.querySelectorAll('.event');
            
            bloques.forEach(div => {
                const nameEl = div.querySelector('.event-name');
                const inputEl = div.querySelector('input.iframe-link');
                
                if (nameEl && inputEl) {
                    const titulo = nameEl.textContent.replace(/[\r\n\t]+/g, ' ').trim();
                    const url = inputEl.value.trim();
                    
                    if (url) {
                        resultados.push({ titulo, url });
                    }
                }
            });
            return resultados;
        });

        await browser.close();
        console.log(`✅ Se extrajeron exitosamente ${eventosScrapeados.length} enlaces de la web.`);

        if (eventosScrapeados.length === 0) {
            console.log('⚠️ No se encontraron eventos válidos para procesar.');
            return;
        }

        // 3. Preparación de la estructura para el nodo /canales
        const canalesRef = db.ref('canales');
        const timestampActual = new Date().toISOString();
        const nuevasActualizaciones = {};

        eventosScrapeados.forEach((evento, index) => {
            // Genera claves secuenciales: chevento01, chevento02, etc.
            const idCanal = `chevento${String(index + 1).padStart(2, '0')}`;
            
            nuevasActualizaciones[idCanal] = {
                activo: true,
                actualizado: timestampActual,
                categoria: "DEPORTES",
                fijo: false, // Falso porque son eventos dinámicos que rotan
                logo: "https://images.seeklogo.com/logo-png/62/1/dsports-logo-png_seeklogo-626310.png", // Logo genérico o de DSports como pasaste en el ejemplo
                nombre: evento.titulo,
                url: evento.url
            };
        });

        // 4. Actualización Atómica en Firebase (reemplaza o pisa solo los cheventoXX generados)
        console.log('🔄 Sincronizando datos con Realtime Database...');
        await canalesRef.update(nuevasActualizaciones);
        console.log('🔥 ¡Nodo /canales actualizado en Firebase con éxito!');

    } catch (error) {
        console.error('❌ Ocurrió un error en el flujo:', error.message);
        if (browser) await browser.close().catch(() => {});
    }
}

// Ejecución del script
scrapearYActualizarCanales().then(() => {
    process.exit(0);
}).catch(err => {
    console.error('💥 Error catastrófico:', err);
    process.exit(1);
});
