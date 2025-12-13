import pandas as pd
import yfinance as yf
from datetime import datetime

# ==============================
# Налаштування портфеля
# ==============================

# Кількість акцій у портфелі
holdings = {
    "AAPL": 16,
    "TSLA": 15,
    "TEAM": 7
}

tickers = list(holdings.keys())

# Діапазон дат (останні 90 днів)
end_date = datetime.today().strftime("%Y-%m-%d")
start_date = (datetime.today() - pd.Timedelta(days=90)).strftime("%Y-%m-%d")

print("📥 Завантаження даних з Yahoo Finance...")

# ==============================
# Завантаження даних
# ==============================

data = yf.download(
    tickers,
    start=start_date,
    end=end_date,
    group_by="ticker",
    auto_adjust=True,
    progress=False
)

if data.empty:
    raise ValueError("❌ Дані не були завантажені")

# ==============================
# Формування DataFrame
# ==============================

rows = []

for ticker in tickers:
    last_price = data[ticker]["Close"].iloc[-1]
    quantity = holdings[ticker]
    total_value = last_price * quantity

    rows.append({
        "Ticker": ticker,
        "Price": round(last_price, 2),
        "Quantity": quantity,
        "Position Value": round(total_value, 2),
        "Date": end_date
    })

portfolio_df = pd.DataFrame(rows)

# Загальна вартість портфеля
total_portfolio_value = portfolio_df["Position Value"].sum()

print("📊 Поточний портфель:")
print(portfolio_df)
print(f"\n💰 Загальна вартість портфеля: ${total_portfolio_value:,.2f}")

# ==============================
# Збереження результату у CSV
# ==============================

output_file = "portfolio_report.csv"
portfolio_df.to_csv(output_file, index=False)

print(f"💾 Звіт збережено у файл: {output_file}")

import plotly.express as px

# ==============================
# Побудова графіку
# ==============================

fig = px.bar(
    portfolio_df,
    x="Ticker",
    y="Position Value",
    title="Вартість позицій у портфелі",
    text="Position Value"
)

fig.update_layout(
    yaxis_title="USD",
    xaxis_title="Акція"
)

chart_file = "portfolio_chart.html"
fig.write_html(chart_file)

print(f"📈 Графік збережено у файл: {chart_file}")
