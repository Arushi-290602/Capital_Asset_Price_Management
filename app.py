import datetime
import streamlit as st
import pandas as pd
import yfinance as yf
import capm_functions

st.set_page_config(page_title="CAPM", page_icon="chart_with_upwards_trend", layout='wide')
st.title("Capital Asset Pricing Model")

# Getting input from the user
col1, col2 = st.columns([1, 1])
with col1:
    stocks_list = st.multiselect(
        "Choose 4 stocks",
        ('TSLA', 'AAPL', 'NFLX', 'MSFT', 'MGM', 'AMZN', 'NVDA', 'GOOGL'),
        ['TSLA', 'AAPL', 'AMZN', 'GOOGL']
    )
with col2:
    year = st.number_input("Number of years", 1, 10)

# Downloading data for S&P 500 and selected stocks
try:
    end = datetime.date.today()
    start = datetime.date(end.year - year, end.month, end.day)

    # Downloading S&P 500 data using yfinance
    sp500 = yf.download('^GSPC', start=start, end=end)['Close'].copy()
    sp500 = sp500.rename('sp500').reset_index()

    # Downloading stock data
    stocks_df = pd.DataFrame()
    for stock in stocks_list:
        data = yf.download(stock, start=start, end=end)
        if 'Close' in data:
            stocks_df[stock] = data['Close'].copy()
        else:
            st.warning(f"No data available for {stock} over the selected period.")

    # Checking if data is available before proceeding
    if not sp500.empty and not stocks_df.empty:
        stocks_df.reset_index(inplace=True)
        sp500.columns = ['Date', 'sp500']
        stocks_df['Date'] = pd.to_datetime(stocks_df['Date'])
        stocks_df = pd.merge(stocks_df, sp500, on='Date', how='inner')

        # Displaying data head and tail in Streamlit
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("### Dataframe Head")
            st.dataframe(stocks_df.head(), use_container_width=True)
        with col2:
            st.markdown("### Dataframe Tail")
            st.dataframe(stocks_df.tail(), use_container_width=True)

        # Price of all stocks plot
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("### Price of all the stocks")
            st.plotly_chart(capm_functions.interactive_plot(stocks_df))

        # Normalized price plot
        with col2:
            st.markdown("### Price of all the stocks (After Normalization)")
            normalized_df = capm_functions.normalize(stocks_df)
            st.plotly_chart(capm_functions.interactive_plot(normalized_df))

        # Calculating daily returns
        stocks_daily_return = capm_functions.daily_return(stocks_df)

        # Calculating Beta and Alpha for each stock
        beta = {}
        alpha = {}
        for stock in stocks_daily_return.columns:
            if stock != 'Date' and stock != 'sp500':
                b, a = capm_functions.calculate_beta(stocks_daily_return, stock)
                beta[stock] = b
                alpha[stock] = a

        # Displaying Beta values
        beta_df = pd.DataFrame({'Stock': list(beta.keys()), 'Beta Value': [round(val, 2) for val in beta.values()]})
        with col1:
            st.markdown("### Calculated Beta Value")
            st.dataframe(beta_df, use_container_width=True)

        # Calculating Expected Returns using CAPM
        rf = 0  # Risk-free rate
        rm = stocks_daily_return['sp500'].mean() * 252  # Annualized market return
        return_value = []

        for stock in stocks_list:
            if stock in beta:
                expected_return = rf + (beta[stock] * (rm - rf))
                return_value.append(str(round(expected_return, 2)))
            else:
                return_value.append("N/A")  # Handle stocks with no beta value

        # Create return_df DataFrame
        return_df = pd.DataFrame({
            'Stock': stocks_list,
            'Return Value': return_value
        })

        # Displaying Expected Returns
        with col2:
            st.markdown('### Calculated Return using CAPM')
            st.dataframe(return_df, use_container_width=True)

    else:
        st.error("Data could not be retrieved for the selected period. Try a shorter timeframe.")

except Exception as e:
    st.error(f"An error occurred: {e}")
