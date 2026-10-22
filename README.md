# Bot Telegram GUSTAVOEURO

Bot che manda la password del sito dopo un captcha, in 5 lingue.

- /start  -> scelta lingua -> captcha -> password (15 secondi)
- dopo 15 secondi la chat si azzera da sola
- /password -> rimanda la password
- /lingua   -> ricambia lingua

## Variabili d'ambiente (da mettere su Railway)
- BOT_TOKEN      = token dato da @BotFather
- PASSWORD_SITO  = password del sito (default: GUSTAVO!nodo#7K2x)
- SECONDI        = secondi prima di azzerare (default: 15)

## Deploy su Railway
1. Crea il repository su GitHub e carica questi 4 file.
2. Railway -> New Project -> Deploy from GitHub repo -> scegli il repo.
3. Scheda Variables -> aggiungi BOT_TOKEN (e PASSWORD_SITO).
4. Deploy. Nei log deve comparire "bot avviato".
