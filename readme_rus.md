![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Pip](https://img.shields.io/badge/pip-v23+-3775A9?style=for-the-badge&logo=pypi&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-Server-FCC624?style=for-the-badge&logo=linux&logoColor=black)

Телеграм-бот для управления Fail2Ban и получения уведомлений о блокировках.

## Возможности
*   **Ручное управление:** Бан и Разбан IP через Telegram.
*   **Глобальный Бан:** Возможность забанить IP во всех джейлах одной командой (`all`).
*   **Статус:** Просмотр состояния джейлов через кнопки.
*   **Авто-уведомления:** Бот сам присылает сообщение, когда Fail2Ban кого-то банит.
*   **Безопасность:** Бот отвечает только владельцу (Admin ID).

## Требования
*   Linux Сервер (Ubuntu/Debian/CentOS)
*   Установленный Fail2Ban
*   Python 3 и `pip`
*   Права Root (нужны для выполнения команд `fail2ban-client`)

## Установка

### 1. Подготовка окружения
Замените `YOURUSER` на вашего пользователя Linux.

```bash
mkdir -p /home/YOURUSER/fail2banBOT
cd /home/YOURUSER/fail2banBOT
python3 -m venv venv
/home/YOURUSER/fail2banBOT/venv/bin/pip install pyTelegramBotAPI
```

### 2. Создание скрипта
Создайте файл `bot.py` и вставьте код из основного `README.md` (или скопируйте файл).
**Важно:** Не забудьте указать в коде свой `TOKEN` и `ADMIN_ID`.

### 3. Автозапуск (Systemd)
Создайте файл службы, чтобы бот работал 24/7.

```bash
sudo nano /etc/systemd/system/f2b-bot.service
```

Вставьте конфиг (замените `YOURUSER`):

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

Запустите:
```bash
sudo systemctl daemon-reload
sudo systemctl enable f2b-bot
sudo systemctl start f2b-bot
```

### 4. Настройка Уведомлений
Чтобы Fail2Ban сам писал вам при атаках.

**A. Создайте Action:**
```bash
sudo nano /etc/fail2ban/action.d/telegram.conf
```
(Код конфига возьмите из основного `README.md` в разделе Step 4).

**B. Включите в джейлах:**
В файле `/etc/fail2ban/jail.local`:

```ini
[sshd]
enabled = true
action = iptables-multiport[name=sshd, port="ssh"]
         telegram
```

**C. Перезагрузите:**
```bash
sudo systemctl restart fail2ban
```

## Использование

*   `/start` - Приветствие.
*   `/status` - Показать кнопки с джейлами.
*   `/ban 1.2.3.4 all` - Забанить IP везде.
*   `/ban 1.2.3.4 sshd` - Забанить только в SSH.
*   `/unban 1.2.3.4` - Разбанить.
```
