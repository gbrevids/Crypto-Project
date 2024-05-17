import pandas as pd
import streamlit as st
import krakenex
from datetime import datetime, timedelta
import plotly.graph_objects as go

def obtener_cotizaciones(crypto, fiat, intervalo='1', horas_atras=6):
    try:
        k = krakenex.API()
        symbol = f"{crypto}/{fiat}"
        now = datetime.utcnow()
        since = int((now - timedelta(hours=horas_atras)).timestamp())
        params = {'pair': symbol, 'interval': intervalo, 'since': since}
        
        response = k.query_public('OHLC', params)
        if response['error']:
            raise Exception(f"Error al obtener cotizaciones: {response['error']}")

        # Verifica que la respuesta contenga datos
        if symbol not in response['result']:
            raise Exception("No se encontraron datos en la respuesta")

        cotizaciones = response['result'][symbol]
        df = pd.DataFrame(cotizaciones, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'count', 'next_open'])
        df = df.drop(columns=['next_open'])

        for column in ['open','high','low','close','volume']:
            df[column] = df[column].astype(float)

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        return df

    except Exception as e:
        print(f"Error: {e}")
        return None

def agrupar_cotizaciones(df):
    try:
        df = df.set_index('timestamp')
        df_agrupado = df.resample('5T').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'})
        return df_agrupado

    except Exception as e:
        print(f"Error al agrupar cotizaciones: {e}")
        return None

def calcular_oscilador_estocastico(df, ventana_k=14, ventana_d=3):
    try:
        df['%K'] = 100 * (df['close'] - df['low'].rolling(window=ventana_k).min()) / (df['high'].rolling(window=ventana_k).max() - df['low'].rolling(window=ventana_k).min())
        df['%D'] = df['%K'].rolling(window=ventana_d).mean()
        return df

    except Exception as e:
        print(f"Error al calcular el oscilador estocástico: {e}")
        return None

# Título de la aplicación
st.title("Analisis de Crypto - UNAV")

# Solicitar al usuario que ingrese la criptomoneda y la moneda fiduciaria
crypto = st.sidebar.selectbox("Crypto", ['ETH', 'BTC', 'USDT', 'XRP', 'SOL'])
fiat = st.sidebar.selectbox("Fiat", ['USD', 'EUR', 'GBP'])

# Ejemplo de uso con intervalo de 1 segundo y las últimas 6 horas
datos_cotizaciones = obtener_cotizaciones(crypto, fiat, intervalo='1', horas_atras=6)

# Verificar si se obtuvieron datos de cotizaciones correctamente
if datos_cotizaciones is not None:
    # Agrupa los datos en intervalos de 5 minutos
    df_agrupado = agrupar_cotizaciones(datos_cotizaciones)

    # Crear un gráfico de velas
    fig = go.Figure(data=[go.Candlestick(x=df_agrupado.index,
                                         open=df_agrupado['open'],
                                         high=df_agrupado['high'],
                                         low=df_agrupado['low'],
                                         close=df_agrupado['close'])])
    fig.update_layout(title=f'{crypto}/{fiat}',
                      xaxis_title='Tiempo',
                      yaxis_title='Precio',
                      template='plotly_dark')
    
    # Mostrar el gráfico de velas en Streamlit
    st.plotly_chart(fig)

    # Añadir botón de control para el oscilador estocástico en la barra lateral
    mostrar_oscilador = st.sidebar.checkbox("Oscilador Estocástico", False)

    # Verificar si se agruparon los datos correctamente
    if df_agrupado is not None and mostrar_oscilador:
        # Calcular el oscilador estocástico
        df_agrupado_con_estocastico = calcular_oscilador_estocastico(df_agrupado)

        # Verificar si se calculó el oscilador estocástico correctamente
        if df_agrupado_con_estocastico is not None:
            # Crear un gráfico para el oscilador estocástico
            fig_oscilador = go.Figure()
            fig_oscilador.add_trace(go.Scatter(x=df_agrupado_con_estocastico.index, y=df_agrupado_con_estocastico['%K'], name='%K', line=dict(color='blue')))
            fig_oscilador.add_trace(go.Scatter(x=df_agrupado_con_estocastico.index, y=df_agrupado_con_estocastico['%D'], name='%D', line=dict(color='red')))
            fig_oscilador.update_layout(title='Oscilador Estocástico',
                                        xaxis_title='Tiempo',
                                        yaxis_title='%K y %D',
                                        template='plotly_dark')

            # Mostrar el gráfico del oscilador estocástico en Streamlit
            st.plotly_chart(fig_oscilador)
        else:
            st.error("Error al calcular el oscilador estocástico. Por favor, inténtelo de nuevo.")
    elif df_agrupado is None:
        st.error("Error al procesar los datos de cotizaciones. Por favor, inténtelo de nuevo.")
else:
    st.error("Error al obtener los datos de cotizaciones. Por favor, inténtelo de nuevo.")