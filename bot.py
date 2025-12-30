import telebot
from telebot import types
import subprocess
import re
import time


TOKEN = ''
ADMIN_ID = 


bot = telebot.TeleBot(TOKEN)

def run_command(cmd):
    """Выполняет команду и возвращает вывод"""
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return result.decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        return e.output.decode('utf-8').strip()

def get_active_jails():
    """Парсит список активных джейлов из fail2ban-client status"""
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
        "Этот бот — пульт управления фаерволом вашего сервера.\n"
        "Он позволяет вручную блокировать и разблокировать IP-адреса, "
        "минуя автоматические правила, а также проверять статус защиты.\n\n"
        "⚡ **Новые функции:**\n"
        "— Бан IP сразу во всех джейлах (параметр `all`)\n"
        "— Удобный просмотр статуса через кнопки\n\n"
        "Связь с сервером: `fail2ban-client`\n"
        "Права доступа: **Только владелец**\n\n"
        "👉 Нажмите /help для списка команд."
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def send_help(message):
    msg = (
        "🛠 **Список команд:**\n\n"
        "1️⃣ **БАН IP**:\n"
        "`/ban IP [jail]` - Бан в конкретном джейле\n"
        "`/ban IP all` - 😈 Бан ВО ВСЕХ джейлах сразу\n"
        "Пример: `/ban 192.168.1.5 sshd`\n\n"

        "2️⃣ **РАЗБАН IP**:\n"
        "`/unban IP [jail]`\n"
        "`/unban IP all` - Разбан везде\n\n"

        "3️⃣ **СТАТУС**:\n"
        "`/status` - Меню с кнопками выбора джейла\n"
        "`/status all` - Полный текстовый отчет по всем\n\n"
        "📌 *Если jail не указан, используется 'sshd'.*"
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(commands=['ban'])
def ban_ip(message):
    args = message.text.split()[1:]
    if not args:
        bot.reply_to(message, "⚠ Ошибка: Введите IP.\nПример: `/ban 1.2.3.4 all`", parse_mode="Markdown")
        return

    ip = args[0]
    target_jail = args[1] if len(args) > 1 else 'sshd'

    if not re.match(r"^[0-9a-fA-F\.:]+$", ip):
        bot.reply_to(message, "⛔ Ошибка: Некорректный формат IP.")
        return

    jails_to_ban = []

    if target_jail == 'all':
        jails_to_ban = get_active_jails()
        if not jails_to_ban:
            bot.reply_to(message, "⚠ Нет активных джейлов или нет прав root!")
            return
        bot.reply_to(message, f"⏳ Начинаю бан IP `{ip}` во всех джейлах ({len(jails_to_ban)} шт)...", parse_mode="Markdown")
    else:
        jails_to_ban = [target_jail]

    report = []
    for jail in jails_to_ban:
        cmd = f"fail2ban-client set {jail} banip {ip}"
        out = run_command(cmd)
        if out == "0":
            report.append(f"🔹 **{jail}**: Уже в бане")
        elif "does not exist" in out:
            report.append(f"❌ **{jail}**: Джейл не найден")
        else:
            report.append(f"🔨 **{jail}**: ЗАБАНЕН")

    bot.send_message(message.chat.id, "\n".join(report), parse_mode="Markdown")

@bot.message_handler(commands=['unban'])
def unban_ip(message):
    args = message.text.split()[1:]
    if not args:
        bot.reply_to(message, "⚠ Ошибка: Введите IP.\nПример: `/unban 1.2.3.4`", parse_mode="Markdown")
        return

    ip = args[0]
    target_jail = args[1] if len(args) > 1 else 'sshd'

    jails_to_unban = []
    if target_jail == 'all':
        jails_to_unban = get_active_jails()
    else:
        jails_to_unban = [target_jail]

    report = []
    for jail in jails_to_unban:
        cmd = f"fail2ban-client set {jail} unbanip {ip}"
        out = run_command(cmd)
        if out != "0" and "does not exist" not in out:
            report.append(f"🕊 **{jail}**: Разбанен")

    if report:
        bot.send_message(message.chat.id, "\n".join(report), parse_mode="Markdown")
    else:
        bot.reply_to(message, f"🤷‍♂️ IP `{ip}` не найден в банах.", parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def status_handler(message):
    args = message.text.split()[1:]

    if args and args[0] == 'all':
        jails = get_active_jails()
        if not jails:
            bot.reply_to(message, "⚠ Нет активных джейлов (или запустите бота через sudo).")
            return

        bot.send_message(message.chat.id, "⏳ Собираю статистику...", parse_mode="Markdown")
        full_report = ""
        for jail in jails:
            out = run_command(f"fail2ban-client status {jail}")
            full_report += f"📊 **{jail}**\n```\n{out}\n```\n"

        bot.send_message(message.chat.id, full_report, parse_mode="Markdown")
        return

    jails = get_active_jails()
    if not jails:
        out = run_command("fail2ban-client status")
        bot.reply_to(message, f"⚠ Не могу получить список джейлов.\nОшибка:\n`{out}`\n(Запустите бота через sudo)", parse_mode="Markdown")
        return

    markup = types.InlineKeyboardMarkup()
    for jail in jails:
        btn = types.InlineKeyboardButton(text=f"📊 {jail}", callback_data=f"st_{jail}")
        markup.add(btn)

    bot.send_message(message.chat.id, "Выберите джейл для просмотра:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('st_'))
def callback_status(call):
    if call.message.chat.id != ADMIN_ID: return

    jail_name = call.data.split('_')[1]
    out = run_command(f"fail2ban-client status {jail_name}")

    markup = types.InlineKeyboardMarkup()
    back_btn = types.InlineKeyboardButton(text="🔙 Назад к списку", callback_data="back_to_list")
    markup.add(back_btn)

    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f"📊 Статус **{jail_name}**:\n```\n{out}\n```",
                              parse_mode="Markdown", reply_markup=markup)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: call.data == "back_to_list")
def callback_back(call):
    if call.message.chat.id != ADMIN_ID: return

    jails = get_active_jails()
    markup = types.InlineKeyboardMarkup()
    for jail in jails:
        btn = types.InlineKeyboardButton(text=f"📊 {jail}", callback_data=f"st_{jail}")
        markup.add(btn)

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Выберите джейл для просмотра:", reply_markup=markup)

if __name__ == '__main__':
    print("Бот запущен...")
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60)
        except Exception as e:
            print(f"Ошибка падения: {e}")
            time.sleep(5)
