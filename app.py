import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Escáner Automático de Señales CFDs", layout="wide")

st.title("⚡ Escáner Automático de Señales y Entradas Escalonadas (CFDs)")
st.markdown("""
Este escáner analiza automáticamente una cesta completa de tus activos preferidos en tiempo real. 
Detecta tendencia, calcula la **Entrada principal**, el **Stop Loss**, el **Take Profit** y las **Señales de Entrada Escalonada (Piramidación)** si la operación va ganando.
""")

ACTIVOS_CFD = {
    "EUR/USD (Forex)": "EURUSD=X",
    "Petróleo WTI": "CL=F",
    "Petróleo Brent": "BZ=F",
    "Oro": "GC=F",
    "Plata": "SI=F",
    "S&P 500": "SPY",
    "Nasdaq 100": "QQQ",
    "Dow Jones": "DIA"
}

if st.button("🚀 Escanear Todos los Activos Ahora", type="primary"):
    resultados = []
    progress_bar = st.progress(0)
    total_activos = len(ACTIVOS_CFD)
    
    for i, (nombre, ticker) in enumerate(ACTIVOS_CFD.items()):
        try:
            df = yf.download(ticker, period="5d", interval="1h", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            if len(df) > 25:
                df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
                df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
                
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                df['RSI'] = 100 - (100 / (1 + rs))

                last = df.iloc[-1]
                precio = float(last['Close'])
                ema9 = float(last['EMA9'])
                ema21 = float(last['EMA21'])
                rsi = float(last['RSI'])

                if ema9 > ema21 and 50 <= rsi <= 75:
                    estado = "🟢 COMPRA (LONG)"
                    entrada = precio
                    stop_loss = entrada - (entrada * 0.0035)
                    take_profit = entrada + (entrada * 0.012)
                    escala_1 = entrada + (entrada * 0.003)
                    escala_2 = entrada + (entrada * 0.006)
                elif ema9 < ema21 and 25 <= rsi <= 50:
                    estado = "🔴 VENTA (SHORT)"
                    entrada = precio
                    stop_loss = entrada + (entrada * 0.0035)
                    take_profit = entrada - (entrada * 0.012)
                    escala_1 = entrada - (entrada * 0.003)
                    escala_2 = entrada - (entrada * 0.006)
                else:
                    estado = "⚪ NEUTRAL / ESPERAR"
                    entrada = precio
                    stop_loss = 0
                    take_profit = 0
                    escala_1 = 0
                    escala_2 = 0

                resultados.append({
                    "Activo": nombre,
                    "Símbolo": ticker,
                    "Precio Actual": round(precio, 4),
                    "RSI": round(rsi, 1),
                    "Señal": estado,
                    "Entrada Base": round(entrada, 4),
                    "Stop Loss": round(stop_loss, 4) if stop_loss > 0 else "-",
                    "Take Profit": round(take_profit, 4) if take_profit > 0 else "-",
                    "Escala 1 (Pyramid)": round(escala_1, 4) if escala_1 > 0 else "-",
                    "Escala 2 (Pyramid)": round(escala_2, 4) if escala_2 > 0 else "-"
                })
        except Exception as e:
            pass
            
        progress_bar.progress((i + 1) / total_activos)
        
    progress_bar.empty()
    
    if resultados:
        df_res = pd.DataFrame(resultados)
        st.success("¡Escaneo masivo completado con éxito!")
        st.dataframe(df_res, use_container_width=True)
        st.markdown("---")
        st.subheader("💡 ¿Cómo interpretar las Entradas Escalonadas (Piramidación)?")
        st.markdown("""
        * **Entrada Base:** Punto gatillo inicial detectado por el escáner.
        * **Escala 1 y Escala 2:** Niveles para añadir más contratos si la operación va ganando.
        * **Gestión (50 USD):** Las entradas escalonadas solo deben ejecutarse si la operación principal ya movió su Stop Loss a Break-Even.
        """)
    else:
        st.warning("No se pudieron procesar las señales en este momento.")
else:
    st.info("👈 Haz clic en el botón superior **'Escanear Todos los Activos Ahora'**.")
