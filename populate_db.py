import sys
from datetime import datetime, timedelta
import random
import time

# Tenta importar o DatabaseManager. Certifique-se de que database.py está no mesmo diretório.
try:
    from database import DatabaseManager
except ImportError:
    print("ERRO: Não foi possível importar 'DatabaseManager' do arquivo 'database.py'.")
    print("Certifique-se de que 'database.py' está no mesmo diretório.")
    sys.exit(1)

def generate_historical_entradas(db_manager, days_history=90):
    """Gera dados históricos de Entradas (Receitas) para 90 dias."""
    
    print("\n--- 1. INSERINDO ENTRADAS (RECEITAS) HISTÓRICAS ---")
    
    start_date = datetime.now() - timedelta(days=days_history)
    maquinas = ['Escavadeira', 'Caminhão', 'Retro-Escavadeira']
    total_entries = 0
    
    # Simula 90 dias (cerca de 3 meses)
    for i in range(days_history):
        current_date = start_date + timedelta(days=i)
        
        # Simula dias de trabalho (70% de chance de trabalhar)
        if random.random() < 0.7:
            # Simula valores totais de receita para cada máquina no dia
            for maquina in random.sample(maquinas, k=random.randint(1, len(maquinas))):
                
                # Simula uma variação de receita entre R$ 800 e R$ 2500 por máquina por dia
                valor_total = round(random.uniform(800.00, 2500.00), 2)
                data_str = current_date.strftime('%d/%m/%Y')
                
                if db_manager.insert_entrada(maquina, valor_total, data_str):
                    total_entries += 1
                
    print(f"✅ {total_entries} registros de Receita/Entrada histórica inseridos com sucesso.")


def generate_despesas(db_manager):
    """Insere despesas recorrentes e pontuais."""
    
    print("\n--- 2. INSERINDO DESPESAS (SAÍDAS) ---")
    
    today_str = datetime.now().strftime('%d/%m/%Y')
    
    despesas_a_inserir = [
        # Despesa Recorrente Mensal (Desde 3 meses atrás)
        {
            'titulo': 'Aluguel do Galpão', 
            'valor': 3500.00, 
            'data_saida': (datetime.now() - timedelta(days=90)).strftime('%d/%m/%Y'), 
            'recorrente': True, 
            'frequencia': 'Mensal'
        },
        # Despesa Recorrente Trimestral (Próxima data recente)
        {
            'titulo': 'Seguro Obrigatório da Frota', 
            'valor': 8000.00, 
            'data_saida': (datetime.now() - timedelta(days=30)).strftime('%d/%m/%Y'), 
            'recorrente': True, 
            'frequencia': 'Trimestral'
        },
        # Despesa Recorrente Anual (Exemplo para o próximo ano)
        {
            'titulo': 'Licença de Software de Rastreamento', 
            'valor': 1200.00, 
            'data_saida': (datetime.now() + timedelta(days=60)).strftime('%d/%m/%Y'), 
            'recorrente': True, 
            'frequencia': 'Anual'
        },
        # Despesa Não Recorrente (Manutenção recente)
        {
            'titulo': 'Troca de Pneus Caminhão #02', 
            'valor': 4500.00, 
            'data_saida': (datetime.now() - timedelta(days=15)).strftime('%d/%m/%Y'), 
            'recorrente': False, 
            'frequencia': 'N/A'
        },
        # Despesa Não Recorrente (Fundo de emergência)
        {
            'titulo': 'Fundo de Reserva de Caixa', 
            'valor': 10000.00, 
            'data_saida': today_str, 
            'recorrente': False, 
            'frequencia': 'N/A'
        },
    ]
    
    total_despesas = 0
    for d in despesas_a_inserir:
        if db_manager.insert_saida(d['titulo'], d['valor'], d['data_saida'], d['recorrente'], d['frequencia']):
            total_despesas += 1
            
    print(f"✅ {total_despesas} registros de Despesa/Saída inseridos com sucesso.")
    print("\n" + "=" * 50)
    print("BANCO DE DADOS POPULADO COM DADOS DE TESTE.")
    print("AGORA VOCÊ PODE EXECUTAR 'main.py' E O MODELO PROPHET.")
    print("=" * 50 + "\n")


if __name__ == '__main__':
    # Inicializa o gerenciador de banco de dados
    try:
        db_manager = DatabaseManager()
    except Exception as e:
        print(f"ERRO: Falha ao conectar ou configurar o banco de dados. {e}")
        sys.exit(1)
        
    generate_historical_entradas(db_manager)
    generate_despesas(db_manager)
    
    db_manager.close()