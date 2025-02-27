import pandas as pd
import pandas_datareader.data as web
from datetime import datetime
import streamlit as st
import plotly.express as px
import capm_functions as capm  # Import CAPM functions

st.set_page_config(page_title="CAPM Analysis", page_icon="📈", layout='wide')
st.title("📊 Capital Asset Pricing Model (CAPM)")

API_KEY = "1IU1JG05HK0NPBP8"  # Replace with your API Key

# UI Components
col1, col2 = st.columns([1, 1])
with col1:
    stocks_list = st.multiselect(
        "Choose 4 stocks",
        ('TSLA', 'AAPL', 'NFLX', 'MSFT', 'MGM', 'AMZN', 'NVDA', 'GOOGL'),
        ['TSLA', 'AAPL', 'AMZN', 'GOOGL']
    )
with col2:
    year = st.number_input("Number of years", 1, 10, 5)

# Define date range
end = datetime.today()
start = datetime(end.year - year, end.month, end.day)

# Fetch S&P 500 data
try:
    sp500 = web.DataReader("SPY", "av-daily", start, end, api_key=API_KEY)[["close"]]
    sp500 = sp500.rename(columns={"close": "sp500"}).reset_index()
    sp500.rename(columns={"index": "Date"}, inplace=True)
    sp500["Date"] = pd.to_datetime(sp500["Date"])
except Exception as e:
    st.error(f"⚠️ Failed to retrieve S&P 500 data: {e}")
    sp500 = pd.DataFrame()

# Fetch stock data
stocks_df = pd.DataFrame()
for stock in stocks_list:
    try:
        data = web.DataReader(stock, "av-daily", start, end, api_key=API_KEY)[["close"]]
        data = data.rename(columns={"close": f"{stock}_close"}).reset_index()
        data.rename(columns={"index": "Date"}, inplace=True)
        data["Date"] = pd.to_datetime(data["Date"])
        stocks_df = pd.concat([stocks_df, data.set_index("Date")], axis=1)
    except Exception as e:
        st.warning(f"No data available for {stock}. Skipping...")

if not stocks_df.empty:
    stocks_df.reset_index(inplace=True)
    stocks_df["Date"] = pd.to_datetime(stocks_df["Date"])

if not sp500.empty and not stocks_df.empty:
    stocks_df = pd.merge(stocks_df, sp500, on="Date", how="inner")

    # Display DataFrames
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("### 📄 Dataframe Head")
        st.dataframe(stocks_df.head(), use_container_width=True)
    with col2:
        st.markdown("### 📄 Dataframe Tail")
        st.dataframe(stocks_df.tail(), use_container_width=True)

    # Price of stocks over time
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("### 📈 Stock Prices Over Time")
        fig = capm.interactive_plot(stocks_df)
        st.plotly_chart(fig)

    # Normalized Price of Stocks
    with col2:
        st.markdown("### 📊 Normalized Stock Prices")
        normalized_df = capm.normalize(stocks_df)
        fig = capm.interactive_plot(normalized_df)
        st.plotly_chart(fig)

    # Calculate Daily Returns
    daily_returns_df = capm.daily_return(stocks_df)

    # Beta & Alpha Calculation
    st.subheader("📉 Stock Risk & Performance Metrics")

    results = []
    for stock in stocks_list:
        beta, alpha = capm.calculate_beta(daily_returns_df, f"{stock}_close")
        results.append((stock, beta, alpha))

    # UI for Stock Interpretation
    st.markdown("### 📊 Stock Performance Summary")

    col1, col2 = st.columns([1, 1])  # Two-column layout

    with col1:
        st.write("#### 🔍 Risk & Market Volatility")
        for stock, beta, alpha in results:
            risk = "⚠️ High Risk" if beta > 1.5 else "📉 Moderate Risk" if beta > 1 else "🟢 Low Risk"
            st.markdown(f"**{stock}** - **Beta: {beta:.2f}** | {risk}")

    with col2:
        st.write("#### 📈 Performance Against Market")
        for stock, beta, alpha in results:
            performance = "📈 Outperforming" if alpha > 0 else "🔴 Underperforming"
            st.markdown(f"**{stock}** - **Alpha: {alpha:.2f}** | {performance}")

    # Summary Table
    st.markdown("### 📊 Summary Table")
    table_data = pd.DataFrame(results, columns=["Stock", "Beta (β)", "Alpha (α)"])
    st.dataframe(table_data.style.highlight_max(axis=0, subset=["Beta (β)"], color="yellow"))

    # Overall Insights
    st.markdown("### 📢 Key Takeaways")
    for stock, beta, alpha in results:
        interpretation = ""
        if beta > 1.5:
            interpretation = f"🚀 **{stock} is highly volatile**, meaning it reacts strongly to market changes."
        elif beta > 1:
            interpretation = f"📊 **{stock} has moderate risk**, moving slightly more than the S&P 500."
        else:
            interpretation = f"🛡️ **{stock} is stable**, moving less than the market."

        if alpha > 0:
            interpretation += f" ✅ **Positive Alpha** suggests that {stock} is **outperforming** market expectations."
        else:
            interpretation += f" 🔴 **Negative Alpha** means that {stock} is **underperforming** relative to expectations."

        st.info(interpretation)

else:
    st.error("⚠️ Data could not be retrieved. Try a different time frame or API.")
