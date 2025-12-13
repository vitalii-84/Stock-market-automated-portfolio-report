# ===============================
# Автоматизація звітності портфеля з Telegram
# ===============================

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px
import requests
import sys

# ===============================
# Налаштування портфеля
# ===============================
holdings = {
    'AAPL': 16,
    'TSLA': 15,
    'TEAM': 7,
}

# ===============================
# Налаштування Telegram бота
# ===============================
bot_token = "8316612047:AAGRPfyKZyjKg_q3rEWavf2RiO9EBhydHmo"
chat_id = 6241484631  # твій chat_id з getUpdates

def send_telegram_message(message: str):
    """
    Надсилає повідомлення в Telegram
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Помилка при відправці Telegram:", e)

# ===============================
# Завантаження даних
# ===============================
tickers = list(holdings.keys())
end_date = datetime.today() - timedelta(days=1)
start_date = end_date - timedelta(days=7)

data = yf.download(
    tickers,
    start=start_date.strftime('%Y-%m-%d'),
    end=end_date.strftime('%Y-%m-%d'),
    auto_adjust=True
)

# Перевірка завантаження
if data.empty:
    send_telegram_message("⚠️ Дані для портфеля не були завантажені. Можливо, сьогодні вихідний на біржі.")
    sys.exit(0)

# ===============================
# Обробка даних
# ===============================
# Для нових версій yfinance
try:
    adj_close = data['Adj Close'].copy()
except KeyError:
    # Якщо MultiIndex, дістаємо всі тикери для 'Adj Close'
    adj_close = data.loc[:, ('Adj Close', slice(None))].copy()
    adj_close.columns = adj_close.columns.droplevel(0)  # залишаємо тільки назви тикерів

adj_close = adj_close.reset_index()

# Перетворюємо у формат long для побудови графіка
adj_close_long = pd.melt(
    adj_close,
    id_vars='Date',
    value_vars=tickers,
    var_name='Ticker',
    value_name='Adj_Close'
)

# Додаємо вартість позицій для кожної акції
adj_close_long['Position_Value'] = adj_close_long['Adj_Close'] * adj_close_long['Ticker'].map(holdings)

# Обчислюємо загальну вартість портфеля по кожній даті
total_value = adj_close_long.groupby('Date')['Position_Value'].sum().reset_index()
total_value.rename(columns={'Position_Value': 'Total_Value'}, inplace=True)

# Додаємо Total Value у long DataFrame для графіка
total_long = total_value.copy()
total_long['Ticker'] = 'Total Value'
total_long.rename(columns={'Total_Value': 'Adj_Close'}, inplace=True)

plot_df = pd.concat([adj_close_long[['Date','Ticker','Adj_Close']], total_long], ignore_index=True)

# ===============================
# Побудова графіка
# ===============================
fig = px.line(plot_df, x='Date', y='Adj_Close', color='Ticker',
              title="Динаміка вартості портфеля та акцій")
fig.update_layout(
    yaxis_title="Вартість ($)",
    xaxis_title="Дата"
)
fig.write_html("portfolio_plot.html")  # зберігаємо графік у файл

# ===============================
# Розрахунок відсоткової зміни Total Value
# ===============================
if len(total_value) >= 2:
    today_val = total_value['Total_Value'].iloc[-1]
    prev_val = total_value['Total_Value'].iloc[-2]
    change_pct = (today_val - prev_val) / prev_val * 100
else:
    today_val = total_value['Total_Value'].iloc[-1]
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
