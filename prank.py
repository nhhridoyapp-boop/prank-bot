
```python
import os
import logging
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters,
)

TOKEN = os.environ.get("BOT_TOKEN", "").strip()
if not TOKEN:
    raise SystemExit("❌ BOT_TOKEN missing")

CALL_API = "https://darktoolshubs.qzz.io/prank/call.php"
RECORD_API = "https://darktoolshubs.qzz.io/prank/Api.php"

JOKES = [
    ("8803", "পিজ্জা ডেলিভারি"),
    ("8804", "ট্যাক্সি অপেক্ষা করছে"),
    ("8805", "গাজার মতো দুর্গন্ধ!"),
    ("8806", "কামরার হৈচৈ আওয়াজ"),
    ("8807", "কুকুরটি ক্লান্তিকর!"),
    ("8808", "ওয়াই-ফাই চুরি!"),
    ("8809", "আমাকে কেন কল করেন?"),
    ("8810", "গার্লফ্রেন্ডকে কল কেন?"),
]

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("prank")

pending = {}
waiting_uid = set()


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    kb = [[InlineKeyboardButton(t, callback_data=f"j:{jid}")] for jid, t in JOKES]
    kb.append([InlineKeyboardButton("🎙️ কল রেকর্ড দেখুন", callback_data="record")])
    await update.message.reply_text(
        "🎭 কোন প্র্যাঙ্ক টপিক দিয়ে কল করবেন?",
        reply_markup=InlineKeyboardMarkup(kb),
    )


async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "record":
        waiting_uid.add(uid)
        pending.pop(uid, None)
        await q.edit_message_text("🎙️ আপনার Prank UID পাঠান:\n(যেমন: 3e3f72e020e98299@jokesphone)")
        return

    joke_id = q.data.split(":", 1)[1]
    pending[uid] = joke_id
    waiting_uid.discard(uid)
    await q.edit_message_text("📞 টার্গেটের ১০/১১ ডিজিটের নম্বর পাঠান:")


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    text = update.message.text.strip()

    if uid in waiting_uid:
        waiting_uid.discard(uid)
        await update.message.reply_text("🔍 রেকর্ড খোঁজা হচ্ছে...")
        try:
            async with httpx.AsyncClient(timeout=20) as c:
                r = await c.get(RECORD_API, params={"uid": text})
                rec = r.json()
        except Exception as e:
            log.warning("record api: %s", e)
            rec = []
        if isinstance(rec, list) and rec and isinstance(rec[0], str):
            try:
                await update.message.reply_audio(audio=rec[0], caption="🎙️ Prank Call Record")
            except Exception:
                await update.message.reply_text(f"🎙️ রেকর্ড লিংক: {rec[0]}")
        else:
            await update.message.reply_text("❌ রেকর্ড পাওয়া যায়নি বা কল এখনো শেষ হয়নি।")
        return

    if uid not in pending:
        await update.message.reply_text("শুরু করতে /start চাপুন।")
        return

    if not text.isdigit() or len(text) < 10:
        await update.message.reply_text("❌ সঠিক ১০/১১ ডিজিটের নম্বর দিন।")
        return

    joke_id = pending.pop(uid)
    await update.message.reply_text("🔄 কল যাচ্ছে...")
    try:
        async with httpx.AsyncClient(timeout=25) as c:
            r = await c.get(
                CALL_API,
                params={"send": text, "jokeid": joke_id},
                headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
            )
            res = r.json()
    except Exception as e:
        log.warning("call api: %s", e)
        res = {}

    ok = (
        isinstance(res, dict)
        and res.get("status") == "success"
        and isinstance(res.get("server_response"), dict)
        and res["server_response"].get("res") == "OK"
    )

    if ok:
        await update.message.reply_text(
            "✅ কল গেছে!\n\n"
            f"🎯 Target: {text}\n"
            f"🆔 Joke: {joke_id}\n"
            f"🔑 UID: {res.get('generated_account', 'N/A')}\n\n"
            "💡 রেকর্ড শুনতে UID দিয়ে 'কল রেকর্ড' অপশন ব্যবহার করুন।"
        )
    else:
        await update.message.reply_text(
            "❌ কল যায়নি। নম্বরটি বার বার কল করার কারণে ব্লকড হতে পারে, "
            "অথবা সার্ভার সমস্যা। অন্য নম্বরে চেষ্টা করুন।"
        )


def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    log.info("Bot running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
```
