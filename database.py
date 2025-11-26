import sqlite3
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np

# Nome do arquivo do banco de dados
DB_NAME = 'gestao_frota.db'

class DatabaseManager:
    """Gerencia todas as interações com o banco de dados SQLite."""
    
    def __init__(self):
        """Inicializa a conexão e garante que as tabelas existam."""
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.setup_db()
        print(f"Banco de dados '{DB_NAME}' inicializado.")

    def setup_db(self):
        """Cria as tabelas se não existirem."""
        
        # Tabela para registrar as Entradas (Receitas da frota)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS entradas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                maquina TEXT NOT NULL,
                tipo TEXT NOT NULL, -- Usado para identificar o tipo de registro (ex: 'hora_trabalhada')
                valor REAL NOT NULL, -- Valor total da receita gerada no dia
                data_registro TEXT NOT NULL -- DD/MM/AAAA (data em que o trabalho foi realizado)
            )
        ''')

        # Tabela para registrar as Saídas (Despesas)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS despesas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                valor REAL NOT NULL,
                data_saida TEXT NOT NULL, -- Data da primeira saída (DD/MM/AAAA)
                recorrente INTEGER NOT NULL, -- 0 (Não) ou 1 (Sim)
                frequencia TEXT -- 'Mensal', 'Trimestral', 'Anual', etc.
            )
        ''')
        self.conn.commit()

    def insert_entrada(self, maquina, valor_total, data_trabalho):
        """Insere um novo registro de valor total de frota gerado em um dia."""
        # Usa 'hora_trabalhada' no campo 'tipo' para identificar este novo formato de entrada.
        try:
            self.cursor.execute('''
                INSERT INTO entradas (maquina, tipo, valor, data_registro)
                VALUES (?, ?, ?, ?)
            ''', (maquina, 'hora_trabalhada', valor_total, data_trabalho))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao inserir entrada: {e}")
            return False

    def insert_saida(self, titulo, valor, data_saida, recorrente, frequencia):
        """Insere um novo registro de despesa (Saída)."""
        recorrente_int = 1 if recorrente else 0
        try:
            self.cursor.execute('''
                INSERT INTO despesas (titulo, valor, data_saida, recorrente, frequencia)
                VALUES (?, ?, ?, ?, ?)
            ''', (titulo, valor, data_saida, recorrente_int, frequencia))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao inserir saída: {e}")
            return False

    def get_prophet_data(self, horizonte_dias=365):
        """
        Gera um DataFrame unificado no formato do Prophet (ds, y), 
        agregando todas as receitas e despesas por dia.
        
        y = Receita - Despesa (Fluxo de Caixa)
        """
        
        # --- 1. CONFIGURAÇÃO DE DATAS ---
        # Definir o intervalo de tempo para agregação (ex: 1 ano para trás e 1 ano para frente)
        end_date = datetime.now().date() + relativedelta(days=horizonte_dias)
        start_date = datetime.now().date() - relativedelta(years=1)
        
        # Gerar a série temporal de dates (ds) no formato datetime64[ns]
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        df_prophet = pd.DataFrame({'ds': dates})
        
        # Inicializa dicionários de agregação (date objects as keys)
        despesas_agg = {}
        receitas_agg = {}
        
        # --- 2. PROCESSAR DESPESAS (Saídas) ---
        despesas = self.cursor.execute('SELECT titulo, valor, data_saida, recorrente, frequencia FROM despesas').fetchall()
        
        for titulo, valor, data_str, recorrente, frequencia in despesas:
            try:
                data_inicial = datetime.strptime(data_str, '%d/%m/%Y').date()
            except ValueError:
                print(f"Aviso: Data de despesa inválida '{data_str}'. Ignorando.")
                continue
            
            if not recorrente:
                # Despesa não recorrente
                despesas_agg[data_inicial] = despesas_agg.get(data_inicial, 0.0) + valor
            else:
                # Despesa recorrente: simular ocorrências futuras
                if frequencia == 'Mensal':
                    delta = relativedelta(months=1)
                elif frequencia == 'Trimestral':
                    delta = relativedelta(months=3)
                elif frequencia == 'Semestral':
                    delta = relativedelta(months=6)
                elif frequencia == 'Anual':
                    delta = relativedelta(years=1)
                else:
                    continue # Ignora frequência desconhecida
                    
                data_atual = data_inicial
                while data_atual <= end_date:
                    despesas_agg[data_atual] = despesas_agg.get(data_atual, 0.0) + valor
                    data_atual += delta
                    
        # --- 3. PROCESSAR RECEITAS (Entradas) ---
        # 3.1. Busca receitas históricas (valor total de trabalho registrado)
        receitas_historicas = self.cursor.execute('''
            SELECT data_registro, SUM(valor) 
            FROM entradas 
            WHERE tipo='hora_trabalhada' 
            GROUP BY data_registro
        ''').fetchall()

        # 3.2. Popula o dicionário de receitas e calcula a média histórica
        valores_historicos = []
        for data_str, valor_total in receitas_historicas:
            try:
                data_obj = datetime.strptime(data_str, '%d/%m/%Y').date()
                receitas_agg[data_obj] = valor_total
                valores_historicos.append(valor_total)
            except ValueError:
                print(f"Aviso: Data de receita inválida '{data_str}'. Ignorando.")
                continue

        # 3.3. Calcula a média diária das receitas para a PREVISÃO (futuro)
        if valores_historicos:
            media_receita_diaria = np.mean(valores_historicos)
        else:
            media_receita_diaria = 500.00 # Valor padrão se não houver dados históricos

        # 3.4. Aplica a média diária para os dias FUTUROS
        today = datetime.now().date()
        
        current_date_loop = today
        while current_date_loop <= end_date:
            # Apenas adiciona a média se não for um dia de receita histórica registrada
            if current_date_loop not in receitas_agg:
                 receitas_agg[current_date_loop] = media_receita_diaria
            current_date_loop += timedelta(days=1)
        
        # --- 4. MERGE NO DATAFRAME FINAL ---
        
        # Converte os dicionários para DataFrames temporários
        df_despesas = pd.DataFrame(list(despesas_agg.items()), columns=['ds_date', 'y_despesa'])
        df_receitas = pd.DataFrame(list(receitas_agg.items()), columns=['ds_date', 'y_receita'])
        
        # Garante que a coluna de data esteja em datetime64[ns]
        df_despesas['ds'] = pd.to_datetime(df_despesas['ds_date'])
        df_receitas['ds'] = pd.to_datetime(df_receitas['ds_date'])
        
        # Junta os DataFrames no DataFrame principal
        df_final = df_prophet.merge(df_receitas[['ds', 'y_receita']], on='ds', how='left')
        df_final['y_receita'] = df_final['y_receita'].fillna(0.0).astype(float) 

        df_final = df_final.merge(df_despesas[['ds', 'y_despesa']], on='ds', how='left')
        df_final['y_despesa'] = df_final['y_despesa'].fillna(0.0).astype(float)
        
        # --- 5. CALCULAR O FLUXO DE CAIXA (y) ---
        df_final['y'] = df_final['y_receita'] - df_final['y_despesa']
        
        # Retorna todas as colunas necessárias para o gráfico e o Prophet
        # Incluímos y_receita e y_despesa
        return df_final[['ds', 'y', 'y_receita', 'y_despesa']].set_index('ds').sort_index().reset_index()

    def close(self):
        """Fecha a conexão com o banco de dados."""
        self.conn.close()

# Inicializa o DB ao importar
# db_manager = DatabaseManager()