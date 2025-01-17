import re
import datetime
from collections import Counter
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Функция для отправки уведомления по email
def send_email_alert(subject, body, recipient_email):
    sender_email = "your_email@example.com"  # Ваш email
    sender_password = "your_password"  # Ваш пароль от email

    # Создание сообщения
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Подключение к серверу и отправка письма
    try:
        with smtplib.SMTP_SSL('smtp.example.com', 465) as server:  # Измените на свой SMTP сервер
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print("Email alert sent!")
    except Exception as e:
        print(f"Error sending email: {e}")


# Функция для анализа логов
def analyze_logs(log_file, threshold_failed_logins=10, threshold_ip_activity=5):
    # Паттерны для поиска угроз
    patterns = {
        'failed_login': r'Failed password.*',
        'suspicious_ip': r'(\d+\.\d+\.\d+\.\d+)',
        'user_agent': r'User-Agent: (.*?)\n',
        'http_error_404': r'HTTP/1.1" 404',
        'http_error_500': r'HTTP/1.1" 500',
        'time_pattern': r'(\d{2}:\d{2}:\d{2})',  # Время в формате HH:MM:SS
    }

    # Чтение лога
    with open(log_file, 'r') as file:
        logs = file.readlines()

    failed_logins = []
    ip_addresses = []
    user_agents = []
    http_404_errors = 0
    http_500_errors = 0
    timestamps = []

    # Обработка каждого лога
    for line in logs:
        # Поиск неудачных попыток входа
        if re.search(patterns['failed_login'], line):
            failed_logins.append(line)

        # Поиск IP-адресов
        ip_match = re.search(patterns['suspicious_ip'], line)
        if ip_match:
            ip_addresses.append(ip_match.group(1))

        # Поиск строк с информацией о User-Agent
        user_agent_match = re.search(patterns['user_agent'], line)
        if user_agent_match:
            user_agents.append(user_agent_match.group(1))

        # Поиск ошибок HTTP 404 и 500
        if re.search(patterns['http_error_404'], line):
            http_404_errors += 1
        if re.search(patterns['http_error_500'], line):
            http_500_errors += 1

        # Поиск времени из записей
        time_match = re.search(patterns['time_pattern'], line)
        if time_match:
            timestamps.append(time_match.group(1))

    # Анализ неудачных попыток входа
    print(f"Количество неудачных попыток входа: {len(failed_logins)}")

    if len(failed_logins) > threshold_failed_logins:
        print(f"Внимание! Слишком много неудачных попыток входа: {len(failed_logins)}")
        send_email_alert("Alert: Too many failed login attempts",
                         f"Detected {len(failed_logins)} failed login attempts.", "admin@example.com")

    # Часто встречающиеся IP-адреса
    ip_counter = Counter(ip_addresses)
    print("Подозрительные IP-адреса (частота):")
    for ip, count in ip_counter.most_common():
        print(f"  {ip}: {count} раз")
        if count > threshold_ip_activity:
            send_email_alert("Alert: Suspicious IP activity", f"IP {ip} has made {count} requests.",
                             "admin@example.com")

    # Анализ ошибок HTTP 404 и 500
    print(f"Количество ошибок 404: {http_404_errors}")
    print(f"Количество ошибок 500: {http_500_errors}")

    # Если слишком много ошибок 404, это может быть признаком атаки на веб-приложение
    if http_404_errors > 50:
        send_email_alert("Alert: Too many 404 errors", f"Detected {http_404_errors} 404 errors, possible attack.",
                         "admin@example.com")

    # Если слишком много ошибок 500, это может быть признаком проблем на сервере или попытки DoS-атаки
    if http_500_errors > 10:
        send_email_alert("Alert: Too many 500 errors", f"Detected {http_500_errors} 500 errors, possible DoS attack.",
                         "admin@example.com")

    # Анализ активности по времени (например, попытки входа ночью)
    timestamp_counter = Counter(timestamps)
    print("Анализ времени активности:")
    for timestamp, count in timestamp_counter.most_common():
        print(f"  {timestamp}: {count} запросов")

    # Уведомление о необычной активности по времени
    for timestamp, count in timestamp_counter.items():
        hour = int(timestamp.split(":")[0])
        if hour < 6 and count > 10:
            send_email_alert("Alert: Suspicious late-night activity",
                             f"Detected {count} requests during night hours ({timestamp}).", "admin@example.com")


# Пример использования
log_file = 'log_file.txt'  # Замените на путь к вашему лог-файлу
analyze_logs(log_file)