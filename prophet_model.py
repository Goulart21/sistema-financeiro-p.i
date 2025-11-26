import pandas as pd
from prophet import Prophet
import numpy as np
from datetime import datetime

def run_prophet_forecast(df: pd.DataFrame, periods: int = 180):
    """
    Roda o modelo Prophet para previsão de fluxo de caixa (coluna 'y').

    Args:
        df (pd.DataFrame): DataFrame com colunas 'ds' (datetime) e 'y' (float).
        periods (int): Número de dias para prever no futuro.

    Returns:
        pd.DataFrame: DataFrame contendo a previsão ('ds', 'yhat', 'yhat_lower', 'yhat_upper').
    """
    
    if df.empty or 'ds' not in df.columns or 'y' not in df.columns:
        print("Erro: DataFrame de entrada inválido ou vazio para o Prophet.")
        return pd.DataFrame()
    
    # CORREÇÃO: Converte a data atual (Python date) para Pandas Timestamp (datetime64[ns])
    # Isso garante que a comparação com a coluna df['ds'] seja válida.
    today_dt = pd.to_datetime(datetime.now().date()) 

    # 1. Ajustar o DataFrame (Prophet precisa de dados históricos)
    # Utiliza today_dt corrigido para a comparação
    df_hist = df[df['ds'] < today_dt].copy()
    
    if df_hist.empty:
        print("Aviso: Dados históricos insuficientes. Gerando previsão fictícia.")
        # Se não houver dados passados, cria uma linha base fictícia para que o Prophet não falhe
        base_date = datetime.now().date() - pd.Timedelta(days=1)
        df_hist = pd.DataFrame({'ds': [pd.to_datetime(base_date)], 'y': [0.0]})


    # 2. Configuração e Treinamento do Modelo
    try:
        # Configuração do Prophet para extrair o máximo: sazonalidade anual, semanal e feriados (para feriados BR)
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            # Configurações extras de modelo para maior precisão (ex: incerteza)
            interval_width=0.90 # Intervalo de confiança de 90%
        )
        
        # Adicionar feriados brasileiros como regressores (opcional, mas recomendado para BR)
        # from prophet.make_holidays import make_holidays_df
        # holidays = make_holidays_df(year_list=list(range(datetime.now().year, datetime.now().year + 2)), country='BR')
        # model.add_country_holidays(country_name='BR')
        
        model.fit(df_hist)

        # 3. Gerar Datas Futuras
        future = model.make_future_dataframe(periods=periods)

        # 4. Previsão
        forecast = model.predict(future)
        
        # Filtra apenas o futuro para visualização
        # Utiliza today_dt corrigido para a comparação
        forecast_future = forecast[forecast['ds'] >= today_dt].copy()
        
        return forecast_future[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    except Exception as e:
        print(f"Erro ao rodar o modelo Prophet: {e}")
        # Retorna um DataFrame vazio em caso de falha
        return pd.DataFrame()