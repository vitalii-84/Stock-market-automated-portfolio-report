# ===============================
# Автоматизація звітності портфеля з Telegram
# ===============================

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px
import requests
import os

# ===============================
# Налаштування портфеля
# ===============================
holdings = {
    'AAPL': 16,
    'TSLA': 15,
    'TEAM': 7,
}

tickers = list(holdings.keys())

# ===============================
# Налаштування Telegram бота через GitHub Secrets
# ===============================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("Telegram credentials are not set in environment variables")

def send_telegram_message(message: str):
    """
    Надсилає повідомлення в Telegram
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

# ===============================
# Завантаження даних
# ===============================
end_date = datetime.today()
start_date = end_date - timedelta(days=7)  # останні 7 днів

data = yf.download(
    tickers,
    start=start_date.strftime('%Y-%m-%d'),
    end=end_date.strftime('%Y-%m-%d'),
    auto_adjust=True  # отримуємо скориговані ціни
)

if data.empty or 'Close' not in data.columns:
    raise ValueError("Дані не були завантажені. Перевірте тикери або діапазон дат.")

# ===============================
# Обробка даних
# ===============================
close_prices = data['Close'].reset_index()

# Перетворюємо у long формат для графіка
close_long = pd.melt(
    close_prices,
    id_vars='Date',
    value_vars=tickers,
    var_name='Ticker',
    value_name='Close'
)

# Додаємо вартість кожної позиції
close_long['Position_Value'] = close_long['Close'] * close_long['Ticker'].map(holdings)

# Загальна вартість портфеля по датах
total_value = close_long.groupby('Date')['Position_Value'].sum().reset_index()
total_value.rename(columns={'Position_Value': 'Total_Value'}, inplace=True)

# Додаємо Total Value у long DataFrame для графіка
total_long = total_value.copy()
total_long['Ticker'] = 'Total Value'
total_long.rename(columns={'Total_Value': 'Close'}, inplace=True)

plot_df = pd.concat([close_long[['Date','Ticker','Close']], total_long], ignore_index=True)

# ===============================
# Побудова графіка
# ===============================
fig = px.line(
    plot_df,
    x='Date',
    y='Close',
    color='Ticker',
    title="Динаміка вартості портфеля та акцій"
)
fig.update_layout(
    yaxis_title="Вартість ($)",
    xaxis_title="Дата"
)
fig.write_html("portfolio_plot.html")  # зберігаємо графік у файл

# ===============================
# Розрахунок відсоткової зміни Total Value
# ===============================
if len(total_value) >= 2:
    today_val = total_value['Close'].iloc[-1]
    prev_val = total_value['Close'].iloc[-2]
    change_pct = (today_val - prev_val) / prev_val * 100
else:
    today_val = total_value['Close'].iloc[-1]
    change_pct = 0

# ===============================
# Надсилаємо повідомлення у Telegram
# ===============================
message = f"📊 Total Value: ${today_val:,.2f} ({change_pct:+.3f}%)"
send_telegram_message(message)

# ===============================
# Зберігаємо CSV звіт
# ===============================
total_value.to_csv("portfolio_report.csv", index=False)
