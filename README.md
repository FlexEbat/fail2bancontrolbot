![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pip](https://img.shields.io/badge/pip-v23+-3775A9?style=for-the-badge&logo=pypi&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-Server-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![Fail2Ban](https://img.shields.io/badge/Fail2Ban-Protected-red?style=for-the-badge&logo=guard&logoColor=white)

### 🇷🇺 [ИНСТРУКЦИЯ НА РУССКОМ (Russian Manual)](./readme_rus.md)

A Python-based Telegram bot to control Fail2Ban and receive automatic notifications about banned IPs.

## Features
*   **Manual Control:** Ban and Unban IPs via Telegram commands.
*   **Global Ban:** Ability to ban an IP across **all** active jails simultaneously.
*   **Status Check:** View the status of specific jails via interactive buttons.
*   **Auto-Notifications:** Receive instant alerts when Fail2Ban automatically bans an IP.
*   **Security:** Responds only to the specified Admin ID.

## Prerequisites
*   Linux Server (Ubuntu/Debian/CentOS)
*   Fail2Ban installed and running
*   Python 3 & `pip`
*   Root access (required to control `fail2ban-client`)

## Installation

### 1. Setup Environment
Replace `YOURUSER` with your actual Linux username.

```bash
mkdir -p /home/YOURUSER/fail2banBOT
cd /home/YOURUSER/fail2banBOT
python3 -m venv venv
/home/YOURUSER/fail2banBOT/venv/bin/pip install pyTelegramBotAPI
```

### 2. Create Bot Script
Create a file named `bot.py`:

```bash
nano bot.py
```

Paste the following code (replace `YOUR_BOT_TOKEN` and `YOUR_ADMIN_ID`):


### 3. Setup Systemd Service
Create a service file to keep the bot running 24/7. Replace `YOURUSER` with your username.

```bash
sudo nano /etc/systemd/system/f2b-bot.service
```

```ini
[Unit]
Description=Fail2Ban Telegram Bot Control
After=network.target fail2ban.service

[Service]
Type=simple
User=root
WorkingDirectory=/home/YOURUSER/fail2banBOT
ExecStart=/home/YOURUSER/fail2banBOT/venv/bin/python3 /home/YOURUSER/fail2banBOT/bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable f2b-bot
sudo systemctl start f2b-bot
```

### 4. Setup Automatic Notifications
Configure Fail2Ban to send alerts when it bans an IP automatically.

**A. Create Action File:**
```bash
sudo nano /etc/fail2ban/action.d/telegram.conf
```
Paste (replace `YOUR_BOT_TOKEN` and `YOUR_CHAT_ID`):

```ini
[Definition]
actionstart = curl -s -X POST "https://api.telegram.org/bot%(token)s/sendMessage" -d chat_id=%(chat_id)s -d parse_mode="Markdown" -d text="🟢 *Fail2Ban Started*"
actionstop = curl -s -X POST "https://api.telegram.org/bot%(token)s/sendMessage" -d chat_id=%(chat_id)s -d parse_mode="Markdown" -d text="🔴 *Fail2Ban Stopped*"
actionban = curl -s -X POST "https://api.telegram.org/bot%(token)s/sendMessage" -d chat_id=%(chat_id)s -d parse_mode="Markdown" -d text="🛡 *AUTO-BAN*%%0AIP: `<ip>`%%0AJail: *<name>*"
actionunban = curl -s -X POST "https://api.telegram.org/bot%(token)s/sendMessage" -d chat_id=%(chat_id)s -d parse_mode="Markdown" -d text="🕊 *AUTO-UNBAN*%%0AIP: `<ip>`"

[Init]
token = YOUR_BOT_TOKEN
chat_id = YOUR_CHAT_ID
```

**B. Enable in Jail Config:**
Edit `/etc/fail2ban/jail.local`:

```ini
[sshd]
enabled = true
action = iptables-multiport[name=sshd, port="ssh"]
         telegram
```

**C. Restart Fail2Ban:**
```bash
sudo systemctl restart fail2ban
```

## Usage

Send commands to your bot:

*   `/start` - Welcome message.
*   `/status` - Show interactive buttons for jails.
*   `/ban 1.2.3.4 all` - Ban IP in **all** jails.
*   `/ban 1.2.3.4 sshd` - Ban IP in `sshd` only.
*   `/unban 1.2.3.4` - Unban IP.
