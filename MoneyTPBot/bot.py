from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

TOKEN = "7539618847:AAFBAaEzJVaNYkBB2sKgmqddfPwsnbfcUUE"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("cred.json", scope)
client = gspread.authorize(creds)

# PAKAI SATU SHEET SAJA
sheet = client.open("duit_tracker").sheet1

def get_kategori(t):
    t=t.lower()
    if any(x in t for x in ["nasi","ayam","ikan","mie","beras","sayur"]): return "Makanan Pokok"
    if any(x in t for x in ["kopi","teh","es","snack","bakso"]): return "Jajan"
    if any(x in t for x in ["bensin","ojek","angkot","grab"]): return "Transport"
    return "Lainnya"

# /saldoawal 100000
async def saldoawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        saldo = int(context.args[0])
        sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), "SALDO", "-", "Saldo Awal", saldo])
        await update.message.reply_text("✅ Saldo awal disimpan")
    except:
        await update.message.reply_text("Pakai: /saldoawal 100000")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        # PEMASUKAN pakai +
        if text.startswith("+"):
            ket, nom = text[1:].rsplit(" ",1)
            sheet.append_row([tanggal,"IN","-",ket,int(nom)])
            await update.message.reply_text("✅ Pemasukan tercatat")
            return

        # PENGELUARAN
        ket, nom = text.rsplit(" ",1)
        kat = get_kategori(ket)
        sheet.append_row([tanggal,"OUT",kat,ket,int(nom)])
        await update.message.reply_text(f"✅ Tercatat ({kat})")

    except:
        await update.message.reply_text("Contoh:\nkopi 12000\n+ gaji 500000")

async def rekap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = sheet.get_all_records()

    saldo_awal = 0
    masuk = 0
    keluar = 0
    kategori = {}

    for r in data:
        if r["Tipe"] == "SALDO":
            saldo_awal = int(r["Nominal"])
        elif r["Tipe"] == "IN":
            masuk += int(r["Nominal"])
        elif r["Tipe"] == "OUT":
            n = int(r["Nominal"])
            keluar += n
            kategori[r["Kategori"]] = kategori.get(r["Kategori"],0) + n

    saldo_akhir = saldo_awal + masuk - keluar

    msg = f"📊 REKAP\n\nSaldo Awal: {saldo_awal}\nPemasukan: {masuk}\n\nPengeluaran:\n"
    for k,v in kategori.items():
        msg += f"{k}: {v}\n"
    msg += f"\nTotal Keluar: {keluar}\nSaldo Akhir: {saldo_akhir}"

    await update.message.reply_text(msg)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("saldoawal", saldoawal))
app.add_handler(CommandHandler("rekap", rekap))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("Bot jalan...")
app.run_polling()
