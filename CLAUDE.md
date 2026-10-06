# Diario peso – contesto per Claude Code

## Scopo
Web app personale, mobile-first, per registrare il peso ogni mattina e seguire un piano nutrizionale stagionale (cut finale, lean bulk, cut di fine stagione). Usata solo da telefono (iPhone, aggiunta alla schermata Home come PWA). Interfaccia in **italiano informale**, numeri con virgola decimale.

## Stack e regole
- Un solo file `index.html` con HTML, CSS e JS vanilla. **Niente framework, niente build, niente dipendenze.**
- Nessuna chiamata di rete verso API. Unica risorsa esterna: Google Fonts (Barlow, Barlow Condensed) con fallback di sistema.
- Dati salvati in `localStorage` (solo sul dispositivo):
  - `diario_peso` -> oggetto `{ "YYYY-MM-DD": { date, kg } }`
  - `diario_vita`  -> oggetto `{ "YYYY-MM-DD": { date, cm } }`
  - `diario_meta`  -> oggetto `{ lastBackup: "YYYY-MM-DD", chartWaist: bool }` (impostazioni e promemoria, non dati di misura)
- **Non cambiare mai il formato di queste chiavi senza scrivere una migrazione**: l'utente ha dati reali. Backup/ripristino in JSON: `{ v, exported, weights, waists }`.
- PWA: `manifest.webmanifest`, `sw.js` (network-first, fallback cache), icone `icon-192.png`, `icon-512.png`, `apple-touch-icon.png`. Tutti i percorsi sono **relativi** (`./`) perche' il sito sta in una sottocartella di GitHub Pages.
- Su iOS la PWA aggiunta alla Home ha uno storage separato da Safari: i dati inseriti in Safari non compaiono nell'icona. Usare solo l'icona, oppure passare i dati col backup.

## Struttura di index.html
Tre tab: **Diario** (in cima `#todo`: card della pesata spostata li' se manca quella di oggi + avviso backup oltre 30 giorni; poi peso, grafico con vita attivabile, verdetto, vita nascosta in un `<details>`, ultime pesate, incolla pesate, backup), **Piano** (timeline colorata delle fasi, dettaglio kcal/macro), **Goals** (barre di avanzamento, vita, costanza, traguardi).
Nel JS: `PLAN` (punti di traiettoria peso), `PH` (fasi con kcal e macro), `GOALS`, `PLANLAB`, funzioni `verdict`, `render*`, `save/remove` (+`saveW/removeW` per la vita).

## Il piano (fonte di verita' in `PH` e `PLAN`)
| Fase | Periodo | Kcal | P / C / G (g) |
|---|---|---|---|
| Cut finale | 5 ott – 17 ott 2026 | 1900 | 162 / 212 / 42 |
| (pre-partita 16-17 ott) | | ~2400 | 160 / 340 / 45 |
| Transizione | 18 – 24 ott | 2300 | 160 / 290 / 55 |
| Lean bulk | 25 ott – 4 apr 2027 | 2500 | 160 / 340 / 55 |
| Cut soft | 5 – 25 apr | 2250 | 170 / 270 / 55 |
| Cut pieno | 26 apr – 14 giu | 2100 | 170 / 245 / 50 |
| Uscita | 15 – 28 giu | 2300 poi 2500 | 160 / 290 / 55 |

Traiettoria peso attesa (`PLAN`): 5 ott 78,5 – 17 ott 77,8 – 5 nov 79,2 – 5 dic 79,9 – 5 gen 80,6 – 5 feb 81,3 – 5 mar 81,9 – 5 apr 82,5 – 25 apr 81,6 – 14 giu 78,5 (kg, media settimanale).

Regole del verdetto (calcolate su media 7 giorni vs 7 giorni prima, servono almeno 3 pesate per finestra):
- Bulk: ritmo <0,1 kg/sett -> +150 kcal; >0,4 -> -150; vita +1,5 cm in 10+ giorni con peso in salita -> -150; altrimenti ok (obiettivo +0,15/+0,25).
- Transizione: scende piu' di 0,3 kg/sett -> +150; altrimenti ok.
- Cut: scende piu' di 0,7 kg/sett -> +150; peso fermo (> -0,1) -> -100/150; altrimenti ok.
- Soglie per anticipare il cut: vita >= 87 cm, peso medio >= 83 kg.
Se si cambia il piano, aggiornare **sia** `PH`/`PLAN`/`GOALS` **sia** questa tabella.

## Design
Palette vivace con token CSS su `:root` (chiaro) e override scuro in `@media (prefers-color-scheme: dark)` e `[data-theme="dark"]`. Ogni fase ha un colore (`--c-cut`, `--c-trans`, `--c-bulk`, `--c-cutsoft`, `--c-cutfull`, `--c-out`) e il testo relativo (`--on-*`): la card del peso prende il colore della fase corrente. Tab colorate (viola, verde, arancione). Font: Barlow Condensed per i numeri grandi, Barlow per il testo. Rispettare `env(safe-area-inset-*)` e `viewport-fit=cover`. Mantenere contrasto leggibile e target touch >= 44 px.

## Come lavorare
1. Modifica solo cio' che serve, mantenendo il file unico e l'impostazione delle tre tab.
2. Prova in locale: `python3 -m http.server 8000` e apri `http://localhost:8000` (il service worker richiede http/https, non `file://`). Controlla la console senza errori e prova viewport 390x844, tema chiaro e scuro.
3. **Ad ogni modifica a index.html o agli asset**: incrementa la versione in `sw.js` (`CACHE`) e nel footer `v1.x` di `index.html`, cosi' il telefono scarica l'aggiornamento.
4. Commit chiari in italiano, poi `git push` su `main`. GitHub Pages pubblica da `main` / root.
5. Mai committare dati personali dell'utente (esportazioni CSV/JSON). Il repo e' pubblico: nessun segreto e nessun dato di peso reale.

## Idee future (solo su richiesta)
Note giornaliere, widget con la media a 7 giorni, pasti tipo per fase con tabella degli scambi (servono i cibi abituali, il numero di pasti e gli orari di allenamento dell'utente).
Scartate dall'utente: import da Apple Salute (preferisce scrivere il peso), notifiche push (usa un promemoria del calendario alle 7:30), log di forza, carico, infortuni (li gestisce la squadra).
