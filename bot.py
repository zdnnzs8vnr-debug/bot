#!/usr/bin/env python3
"""Bot Telegram GUSTAVOEURO: 5 lingue, captcha, password a tempo, chat che si azzera."""
import asyncio
import os
import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes,
    MessageHandler, filters,
)

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
PASSWORD_SITO = os.environ.get("PASSWORD_SITO", "GUSTAVO!nodo#7K2x").strip()
SECONDI = int(os.environ.get("SECONDI", "15"))

TESTI = {
    "it": {
        "captcha": "\U0001F512 Verifica di sicurezza\n\nQuanto fa {a} + {b}?",
        "ko": "\u274C Sbagliato! Riprova.",
        "benvenuto": "Buongiorno, questa \u00E8 la password per entrare nel sito.\nHai 15 secondi per copiarla \U0001F447",
        "copia": "Tocca la password per copiarla.",
        "pulita": "\U0001F9F9 Chat azzerata.\nPremi /start per rivedere la password.",
    },
    "en": {
        "captcha": "\U0001F512 Security check\n\nHow much is {a} + {b}?",
        "ko": "\u274C Wrong! Try again.",
        "benvenuto": "Good morning, this is the password to enter the site.\nYou have 15 seconds to copy it \U0001F447",
        "copia": "Tap the password to copy it.",
        "pulita": "\U0001F9F9 Chat cleared.\nPress /start to see the password again.",
    },
    "fr": {
        "captcha": "\U0001F512 V\u00E9rification de s\u00E9curit\u00E9\n\nCombien font {a} + {b} ?",
        "ko": "\u274C Faux ! R\u00E9essaie.",
        "benvenuto": "Bonjour, voici le mot de passe pour entrer sur le site.\nVous avez 15 secondes pour le copier \U0001F447",
        "copia": "Touche le mot de passe pour le copier.",
        "pulita": "\U0001F9F9 Chat effac\u00E9e.\nAppuie sur /start pour revoir le mot de passe.",
    },
    "es": {
        "captcha": "\U0001F512 Verificaci\u00F3n de seguridad\n\n\u00BFCu\u00E1nto es {a} + {b}?",
        "ko": "\u274C \u00A1Incorrecto! Int\u00E9ntalo otra vez.",
        "benvenuto": "Buenos d\u00EDas, esta es la contrase\u00F1a para entrar en el sitio.\nTienes 15 segundos para copiarla \U0001F447",
        "copia": "Toca la contrase\u00F1a para copiarla.",
        "pulita": "\U0001F9F9 Chat borrada.\nPulsa /start para ver la contrase\u00F1a otra vez.",
    },
    "de": {
        "captcha": "\U0001F512 Sicherheitspr\u00FCfung\n\nWie viel ist {a} + {b}?",
        "ko": "\u274C Falsch! Versuche es erneut.",
        "benvenuto": "Guten Morgen, das ist das Passwort f\u00FCr die Website.\nDu hast 15 Sekunden, um es zu kopieren \U0001F447",
        "copia": "Tippe auf das Passwort, um es zu kopieren.",
        "pulita": "\U0001F9F9 Chat geleert.\nDr\u00FCcke /start, um das Passwort erneut zu sehen.",
    },
}

SCEGLI = ("\U0001F30D Scegli la lingua / Choose your language\n"
          "Choisissez la langue / Elige el idioma / W\u00E4hle die Sprache")

cronologia = {}
timer = {}
lingua_di = {}


def annota(chat, mid):
    if mid:
        cronologia.setdefault(chat, []).append(mid)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat.id
    if update.effective_message:
        annota(chat, update.effective_message.message_id)
    vecchio = timer.pop(chat, None)
    if vecchio and not vecchio.done():
        vecchio.cancel()
    righe = [
        [InlineKeyboardButton("\U0001F1EE\U0001F1F9 Italiano", callback_data="ling:it"),
         InlineKeyboardButton("\U0001F1EC\U0001F1E7 English", callback_data="ling:en")],
        [InlineKeyboardButton("\U0001F1EB\U0001F1F7 Fran\u00E7ais", callback_data="ling:fr"),
         InlineKeyboardButton("\U0001F1EA\U0001F1F8 Espa\u00F1ol", callback_data="ling:es")],
        [InlineKeyboardButton("\U0001F1E9\U0001F1EA Deutsch", callback_data="ling:de")],
    ]
    m = await ctx.bot.send_message(chat, SCEGLI, reply_markup=InlineKeyboardMarkup(righe))
    annota(chat, m.message_id)


async def manda_captcha(ctx, chat, mid=None):
    a = random.randint(2, 9)
    b = random.randint(2, 9)
    giusta = a + b
    opzioni = {giusta}
    while len(opzioni) < 4:
        v = giusta + random.randint(-3, 3)
        if 0 < v != giusta:
            opzioni.add(v)
    opzioni = list(opzioni)
    random.shuffle(opzioni)
    t = TESTI.get(lingua_di.get(chat, "it"), TESTI["it"])
    bottoni = [InlineKeyboardButton(str(v), callback_data="cap:%d:%d" % (v, giusta)) for v in opzioni]
    markup = InlineKeyboardMarkup([bottoni[:2], bottoni[2:]])
    testo = t["captcha"].format(a=a, b=b)
    if mid:
        await ctx.bot.edit_message_text(testo, chat_id=chat, message_id=mid, reply_markup=markup)
    else:
        m = await ctx.bot.send_message(chat, testo, reply_markup=markup)
        annota(chat, m.message_id)


async def scelta_lingua(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    chat = q.message.chat_id
    annota(chat, q.message.message_id)
    lingua_di[chat] = q.data.split(":", 1)[1]
    await manda_captcha(ctx, chat, q.message.message_id)


async def risposta_captcha(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    chat = q.message.chat_id
    annota(chat, q.message.message_id)
    lingua = lingua_di.get(chat, "it")
    _, scelto, giusta = q.data.split(":")
    if int(scelto) != int(giusta):
        await q.answer(TESTI[lingua]["ko"])
        await manda_captcha(ctx, chat, q.message.message_id)
        return
    await q.answer("\u2705")
    try:
        await ctx.bot.delete_message(chat, q.message.message_id)
        if q.message.message_id in cronologia.get(chat, []):
            cronologia[chat].remove(q.message.message_id)
    except Exception:
        pass
    t = TESTI[lingua]
    testo = "%s\n\n`%s`\n\n%s" % (t["benvenuto"], PASSWORD_SITO, t["copia"])
    m = await ctx.bot.send_message(chat, testo, parse_mode=ParseMode.MARKDOWN)
    annota(chat, m.message_id)
    vecchio = timer.pop(chat, None)
    if vecchio and not vecchio.done():
        vecchio.cancel()
    timer[chat] = asyncio.create_task(azzera(ctx.application, chat, lingua))


async def azzera(app, chat, lingua):
    try:
        await asyncio.sleep(SECONDI)
    except asyncio.CancelledError:
        return
    for mid in list(cronologia.get(chat, [])):
        try:
            await app.bot.delete_message(chat, mid)
        except Exception:
            pass
    cronologia[chat] = []
    try:
        m = await app.bot.send_message(chat, TESTI[lingua]["pulita"])
        cronologia[chat].append(m.message_id)
    except Exception:
        pass


async def password_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat.id
    if update.effective_message:
        annota(chat, update.effective_message.message_id)
    lingua = lingua_di.get(chat, "it")
    t = TESTI[lingua]
    testo = "%s\n\n`%s`\n\n%s" % (t["benvenuto"], PASSWORD_SITO, t["copia"])
    m = await ctx.bot.send_message(chat, testo, parse_mode=ParseMode.MARKDOWN)
    annota(chat, m.message_id)
    vecchio = timer.pop(chat, None)
    if vecchio and not vecchio.done():
        vecchio.cancel()
    timer[chat] = asyncio.create_task(azzera(ctx.application, chat, lingua))


async def testo_libero(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat and update.effective_message:
        annota(update.effective_chat.id, update.effective_message.message_id)


async def errore(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    print("errore:", ctx.error)


def avvia_health():
    porta = int(os.environ.get("PORT", "8080"))

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"GUSTAVOEURO bot attivo")

        def log_message(self, *a):
            pass

    try:
        srv = HTTPServer(("0.0.0.0", porta), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        print("health sulla porta", porta)
    except Exception as e:
        print("health non avviato:", e)


def main():
    if not BOT_TOKEN:
        raise SystemExit("Manca la variabile BOT_TOKEN")
    avvia_health()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("password", password_cmd))
    app.add_handler(CommandHandler("lingua", start))
    app.add_handler(CallbackQueryHandler(scelta_lingua, pattern=r"^ling:"))
    app.add_handler(CallbackQueryHandler(risposta_captcha, pattern=r"^cap:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, testo_libero))
    app.add_error_handler(errore)
    print("bot avviato")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
