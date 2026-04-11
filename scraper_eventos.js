const puppeteer = require('puppeteer');
const fs        = require('fs');
const path      = require('path');

const FUENTE_URL  = 'https://streamtpnew.com/eventos.html';
const OUTPUT_PATH = path.join(__dirname, 'public', 'eventos_dia.json');

async function scrapearEventos() {
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: 'new',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--no-first-run',
      ],
    });

    const page = await browser.newPage();

    // User agent de Chrome para evitar bloqueos
    await page.setUserAgent(
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    );

    await page.goto(FUENTE_URL, { waitUntil: 'networkidle2', timeout: 30000 });

    // Esperar a que cargue el contenedor de eventos
    await page.waitForSelector('.event', { timeout: 15000 }).catch(() => {});

    // Extraer los eventos del DOM
    const eventos = await page.evaluate(() => {
      const results = [];
      const eventDivs = document.querySelectorAll('.event');

      eventDivs.forEach(div => {
        // Hora + título (viene junto en .event-name como "HH:MM - Título")
        const nameEl   = div.querySelector('.event-name');
        const linkEl   = div.querySelector('.iframe-link');
        const statusEl = div.querySelector('.status-button');

        if (!nameEl) return;

        const fullText = nameEl.firstChild?.textContent?.trim() || nameEl.textContent.trim();

        // Separar hora del título
        const match   = fullText.match(/^(\d{1,2}:\d{2})\s*-\s*(.+)$/);
        const hora    = match ? match[1] : '';
        const titulo  = match ? match[2].trim() : fullText;

        // Idioma / bandera si tiene
        const langEl  = nameEl.querySelector('img');
        const idioma  = langEl ? langEl.alt : '';

        const link    = linkEl ? linkEl.value : '';
        const status  = statusEl ? statusEl.className : '';
        const enVivo  = status.includes('live');

        // Categoría — viene en los botones de filtro activos del evento
        // La sacamos del texto del evento (Copa Lib, Copa Sud, etc.)
        let categoria = 'Otros';
        if (/libertadores/i.test(titulo)) categoria = 'Fútbol_cup';
        else if (/sudamericana/i.test(titulo)) categoria = 'Fútbol_cup';
        else if (/mundial/i.test(titulo)) categoria = 'Fútbol';
        else if (/nba|basquet|basket/i.test(titulo)) categoria = 'Basquet';
        else if (/tenis/i.test(titulo)) categoria = 'Tenis';
        else if (/f1|formula/i.test(titulo)) categoria = 'Motor';
        else if (/boxeo|ufc|mma/i.test(titulo)) categoria = 'Boxeo';

        if (titulo) {
          results.push({ hora, titulo, link, idioma, enVivo, categoria });
        }
      });

      return results;
    });

    // Guardar JSON
    fs.mkdirSync(path.dirname(OUTPUT_PATH), { recursive: true });
    fs.writeFileSync(OUTPUT_PATH, JSON.stringify({
      actualizadoEn: new Date().toISOString(),
      total: eventos.length,
      eventos,
    }, null, 2));

    console.log(`[Eventos] ✅ ${eventos.length} eventos guardados — ${new Date().toLocaleTimeString('es-AR')}`);
    return eventos.length;

  } catch (err) {
    console.error('[Eventos] ❌ Error scraping:', err.message);
    // Si falla, guardar JSON vacío para que el frontend no rompa
    if (!fs.existsSync(OUTPUT_PATH)) {
      fs.writeFileSync(OUTPUT_PATH, JSON.stringify({
        actualizadoEn: new Date().toISOString(),
        total: 0,
        eventos: [],
        error: err.message,
      }, null, 2));
    }
    return 0;
  } finally {
    if (browser) await browser.close();
  }
}

module.exports = scrapearEventos;
