const scrapearEventos = require('./scraper_eventos.js');

(async () => {
    console.log("Iniciando scraper...");
    await scrapearEventos();
    console.log("Proceso terminado.");
})();