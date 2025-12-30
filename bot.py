import telebot
from telebot import types
import subprocess
import re
import time

TOKEN = 'YOUR_BOT_TOKEN'
ADMIN_ID = 123456789

bot = telebot.TeleBot(TOKEN)

def run_command(cmd):
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return result.decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        return e.output.decode('utf-8').strip()

def get_active_jails():
    output = run_command("fail2ban-client status")
    match = re.search(r"Jail list:\s+(.*)", output)
    if match:
        jails = [j.strip() for j in match.group(1).split(',')]
        return [j for j in jails if j]
    return []

@bot.message_handler(func=lambda message: message.chat.id != ADMIN_ID)
def ignore_strangers(message):
    return

@bot.message_handler(commands=['start'])
def send_welcome(message):
    msg = (
        "👮‍♂️ **Fail2Ban Admin Bot**\n\n"
        "Control panel for server firewall.\n"
        "⚡ **Features:**\n"
        "— Ban IP everywhere (`all`)\n"
        "— Status via buttons\n"
        "— Manual Unban\n\n"
        "Connection: `fail2ban-client`\n"
        "👉 Type /help for commands."
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def send_help(message):
    msg = (
        "🛠 **Commands:**\n\n"
        "1️⃣ **BAN:**\n"
        "`/ban IP [jail]`\n"
        "`/ban IP all`\n\n"
        "2️⃣ **UNBAN:**\n"
        "`/unban IP [jail]`\n"
        "`/unban IP all`\n\n"
        "3️⃣ **STATUS:**\n"
        "`/status`\n"
        "`/status all`"
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(commands=['ban'])
def ban_ip(message):
    args = message.text.split()[1:]
    if not args:
        bot.reply_to(message, "⚠ Enter IP. Example: `/ban 1.2.3.4 all`", parse_mode="Markdown")
        return
    ip = args[0]
    target_jail = args[1] if len(args) > 1 else 'sshd'
    if not re.match(r"^[0-9a-fA-F\.:]+$", ip):
        bot.reply_to(message, "⛔ Invalid IP.")
        return

    jails_to_ban = get_active_jails() if target_jail == 'all' else [target_jail]
    if not jails_to_ban:
        bot.reply_to(message, "⚠ No active jails found.")
        return

    report = []
    if target_jail == 'all':
        bot.reply_to(message, f"⏳ Banning `{ip}` everywhere...", parse_mode="Markdown")

    for jail in jails_to_ban:
        out = run_command(f"fail2ban-client set {jail} banip {ip}")
        if out == "0": report.append(f"🔹 **{jail}**: Already banned")
        elif "does not exist" in out: report.append(f"❌ **{jail}**: Jail not found")
        else: report.append(f"🔨 **{jail}**: BANNED")
    bot.send_message(message.chat.id, "\n".join(report), parse_mode="Markdown")

@bot.message_handler(commands=['unban'])
def unban_ip(message):
    args = message.text.split()[1:]
    if not args:
        bot.reply_to(message, "⚠ Enter IP.", parse_mode="Markdown")
        return
    ip = args[0]
    target_jail = args[1] if len(args) > 1 else 'sshd'
    jails_to_unban = get_active_jails() if target_jail == 'all' else [target_jail]
    
    report = []
    for jail in jails_to_unban:
        out = run_command(f"fail2ban-client set {jail} unbanip {ip}")
        if out != "0" and "does not exist" not in out:
            report.append(f"🕊 **{jail}**: Unbanned")
    
    if report: bot.send_message(message.chat.id, "\n".join(report), parse_mode="Markdown")
    else: bot.reply_to(message, f"🤷‍♂️ IP `{ip}` not found in banlist.", parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def status_handler(message):
    args = message.text.split()[1:]
    if args and args[0] == 'all':
        jails = get_active_jails()
        full_report = ""
        for jail in jails:
            full_report += f"📊 **{jail}**\n```\n{run_command(f'fail2ban-client status {jail}')}\n```\n"
        bot.send_message(message.chat.id, full_report if full_report else "No jails found.", parse_mode="Markdown")
        return

    jails = get_active_jails()
    if not jails:
        bot.reply_to(message, "⚠ No active jails or no root rights.")
        return
    markup = types.InlineKeyboardMarkup()
    for jail in jails:
        markup.add(types.InlineKeyboardButton(text=f"📊 {jail}", callback_data=f"st_{jail}"))
    bot.send_message(message.chat.id, "Select jail:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('st_'))
def callback_status(call):
    if call.message.chat.id != ADMIN_ID: return
    jail_name = call.data.split('_')[1]
    out = run_command(f"fail2ban-client status {jail_name}")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="🔙 Back", callback_data="back_to_list"))
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                              text=f"📊 Status **{jail_name}**:\n```\n{out}\n```", 
                              parse_mode="Markdown", reply_markup=markup)
    except: pass

@bot.callback_query_handler(func=lambda call: call.data == "back_to_list")
def callback_back(call):
    if call.message.chat.id != ADMIN_ID: return
    status_handler(call.message)

if __name__ == '__main__':
    print("Bot started...")
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60)
        except Exception as e:
            time.sleep(5)
