import customtkinter as ctk
from datetime import datetime
import tkinter.messagebox
import sys 
import pandas as pd 
from database import DatabaseManager 
from prophet_model import run_prophet_forecast 

import plotly.graph_objects as go
import plotly.offline as pyo
import webbrowser
import os


class Theme:
    COR_PRIMARIA_ESCURA = "#E65100" 
    COR_SEGUNDARIA = "#C62828"
    COR_SEGUNDARIA_HOVER = "#A81C1C"
    
    # Fontes
    FONTE_LABEL_MAQUINA = ("Arial", 14, "bold")
    FONTE_LABEL_CAMPO = ("Arial", 12)
    FONTE_BOTAO = ("Arial", 16, "bold")
    FONTE_MENU = ("Arial", 18, "bold") 
    
    # Dimensões
    LARGURA_ENTRY = 280
    ALTURA_BOTAO = 40
    LARGURA_SAIDA = 350
    LARGURA_BOTAO_MENU = 450 

# Inicializa o gerenciador de banco de dados
try:
    db_manager = DatabaseManager()
except Exception as e:
    tkinter.messagebox.showerror("Erro de Inicialização", f"Falha ao conectar ou configurar o banco de dados: {e}. O programa será encerrado.")
    sys.exit(1)


# #######################################################################
# --- OPÇÃO 1: CADASTRO DE ENTRADA (MÁQUINAS) ---
# #######################################################################

def open_cadastro_entrada_window():
    """Cria a janela Toplevel para o cadastro de Entradas de Máquinas."""
    
    if hasattr(app, "entrada_window") and app.entrada_window is not None:
        app.entrada_window.focus()
        return

    entrada_window = ctk.CTkToplevel(app)
    entrada_window.title("Cadastrar Entrada de Frota - Horas Trabalhadas")
    entrada_window.geometry("1000x550") 
    entrada_window.resizable(False, False)
    
    app.entrada_window = entrada_window
    
    def on_close():
        app.entrada_window = None
        entrada_window.destroy()
        
    entrada_window.protocol("WM_DELETE_WINDOW", on_close)

    # Configurar 3 colunas para as máquinas
    entrada_window.grid_columnconfigure((0, 1, 2), weight=1)

    # Título da Seção
    label_secao_entrada = ctk.CTkLabel(
        entrada_window, 
        text='REGISTRAR RECEITA POR HORAS TRABALHADAS', 
        font=ctk.CTkFont(family="Arial", size=18, weight="bold"), 
        text_color=Theme.COR_PRIMARIA_ESCURA
    )
    label_secao_entrada.grid(row=0, column=0, columnspan=3, padx=20, pady=(20, 15))

    
    # --- NOVO CAMPO: DATA DO TRABALHO ---
    ctk.CTkLabel(entrada_window, text='Data do Trabalho (DD/MM/AAAA):', anchor="w", font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO, weight="bold")).grid(row=1, column=0, columnspan=3, padx=20, pady=(10, 0), sticky='w')
    entry_data_trabalho = ctk.CTkEntry(entrada_window, placeholder_text='Ex: 31/12/2025', width=Theme.LARGURA_ENTRY)
    entry_data_trabalho.insert(0, datetime.now().strftime('%d/%m/%Y'))
    entry_data_trabalho.grid(row=2, column=0, columnspan=3, padx=20, pady=(0, 20), sticky='w')
    
    # Mapa para armazenar referências das Entries
    entries_map = {}
    
    def criar_entradas_maquina(app_ref, nome_maquina, coluna_index):
        """Cria e posiciona as Labels e Entries de Hora e Horas Trabalhadas no grid."""
        
        # Linha inicial deslocada devido ao novo campo de data
        start_row = 3
        
        label_maquina = ctk.CTkLabel(
            app_ref, 
            text=nome_maquina, 
            font=ctk.CTkFont(*Theme.FONTE_LABEL_MAQUINA), 
            text_color=Theme.COR_PRIMARIA_ESCURA
        )
        label_maquina.grid(row=start_row, column=coluna_index, padx=20, pady=(5, 5))

        # Valor por Hora
        ctk.CTkLabel(app_ref, text='Valor por hora (R$):', anchor="w", font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO)).grid(row=start_row + 1, column=coluna_index, padx=20, pady=(5, 0), sticky='w')
        entry_hora = ctk.CTkEntry(app_ref, placeholder_text='R$ / hora', width=Theme.LARGURA_ENTRY)
        entry_hora.grid(row=start_row + 2, column=coluna_index, padx=20, pady=(0, 15))
        
        # Horas Trabalhadas
        ctk.CTkLabel(app_ref, text='Horas trabalhadas:', anchor="w", font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO)).grid(row=start_row + 3, column=coluna_index, padx=20, pady=(5, 0), sticky='w')
        entry_horas_trabalhadas = ctk.CTkEntry(app_ref, placeholder_text='Ex: 8.5', width=Theme.LARGURA_ENTRY)
        entry_horas_trabalhadas.grid(row=start_row + 4, column=coluna_index, padx=20, pady=(0, 15))
        
        # Armazena as referências
        entries_map[nome_maquina] = {'valor_hora': entry_hora, 'horas_trabalhadas': entry_horas_trabalhadas}


    def cadastrar_entrada():
        """Valida e processa as entradas de máquinas, calculando e salvando a receita total no DB."""
        
        data_str = entry_data_trabalho.get().strip()
        
        # 1. Validação de Data
        try:
            # Tenta converter a data para garantir o formato DD/MM/AAAA
            datetime.strptime(data_str, '%d/%m/%Y')
        except ValueError:
            tkinter.messagebox.showerror("Erro de Validação", "O formato da 'Data do Trabalho' é inválido. Use DD/MM/AAAA.")
            entry_data_trabalho.focus()
            return
        
        dados_salvos = 0
        
        for maquina, entries in entries_map.items():
            valor_hora_str = entries['valor_hora'].get().strip().replace(',', '.')
            horas_trabalhadas_str = entries['horas_trabalhadas'].get().strip().replace(',', '.')
            
            # Se a linha de entrada da máquina estiver vazia, ignora
            if not valor_hora_str and not horas_trabalhadas_str:
                continue
                
            # 2. Validação Numérica e Cálculo
            try:
                # Se um campo está preenchido, o outro é obrigatório para o cálculo.
                if not valor_hora_str or not horas_trabalhadas_str:
                     tkinter.messagebox.showerror("Erro de Validação", f"Para a '{maquina}', os campos 'Valor por hora' e 'Horas trabalhadas' são obrigatórios.")
                     (entries['valor_hora'] if not valor_hora_str else entries['horas_trabalhadas']).focus()
                     return
                     
                valor_hora = float(valor_hora_str)
                horas_trabalhadas = float(horas_trabalhadas_str)
                
                if valor_hora < 0 or horas_trabalhadas < 0:
                    raise ValueError # Garante que os valores sejam positivos

                valor_total = valor_hora * horas_trabalhadas

            except ValueError:
                tkinter.messagebox.showerror("Erro de Validação", f"Os valores de 'Valor por hora' e 'Horas trabalhadas' da '{maquina}' devem ser números positivos válidos.")
                entries['valor_hora'].focus()
                return

            # --- Lógica de Negócio: Salvar no Banco de Dados ---
            if db_manager.insert_entrada(maquina, valor_total, data_str):
                dados_salvos += 1

        if dados_salvos > 0:
            tkinter.messagebox.showinfo("Sucesso", f"{dados_salvos} novos registros de receita por horas trabalhadas foram salvos para a data {data_str}!")
            on_close()
        else:
            tkinter.messagebox.showwarning("Aviso", "Nenhum novo registro de receita foi inserido. Preencha pelo menos uma entrada de máquina completa.")


    # Criação dos campos no Toplevel
    criar_entradas_maquina(entrada_window, 'Escavadeira', 0)
    criar_entradas_maquina(entrada_window, 'Caminhão', 1)
    criar_entradas_maquina(entrada_window, 'Retro-Escavadeira', 2)

    # Botão de Cadastro
    btn_cadastrar = ctk.CTkButton(
        entrada_window, 
        text='Calcular e Registrar Receitas', 
        command=cadastrar_entrada,
        fg_color=Theme.COR_PRIMARIA_ESCURA, 
        hover_color=Theme.COR_SEGUNDARIA, 
        font=ctk.CTkFont(*Theme.FONTE_BOTAO),
        height=Theme.ALTURA_BOTAO
    )
    # Aumentei a linha do grid para acomodar os novos campos
    btn_cadastrar.grid(row=8, column=0, columnspan=3, padx=20, pady=(20, 20), sticky="ew")

    entrada_window.focus()


# #######################################################################
# --- OPÇÃO 2: CADASTRO DE SAÍDA (DESPESAS) ---
# #######################################################################

def open_cadastro_saida_window():
    """Cria e exibe a janela separada para o cadastro de Saídas (Despesas) com validação."""
    
    if hasattr(app, "saida_window") and app.saida_window is not None:
        app.saida_window.focus()
        return

    saida_window = ctk.CTkToplevel(app)
    saida_window.title("Cadastrar Nova Saída (Despesa)")
    saida_window.geometry("500x550")
    saida_window.resizable(False, False)
    
    app.saida_window = saida_window
    
    def on_close():
        app.saida_window = None
        saida_window.destroy()
        
    saida_window.protocol("WM_DELETE_WINDOW", on_close)

    saida_window.grid_columnconfigure(0, weight=1)
    
    # Título da Seção
    label_secao_saida = ctk.CTkLabel(
        saida_window, 
        text='REGISTRAR NOVA SAÍDA', 
        font=ctk.CTkFont(family="Arial", size=18, weight="bold"), 
        text_color=Theme.COR_SEGUNDARIA
    )
    label_secao_saida.grid(row=0, column=0, padx=20, pady=(20, 10))

    # --- CAMPOS DE ENTRADA ---
    
    # Título da Saída
    ctk.CTkLabel(saida_window, text='Título/Descrição:', font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO), anchor='w').grid(row=1, column=0, padx=20, pady=(10, 0), sticky='w')
    entry_titulo_saida = ctk.CTkEntry(saida_window, placeholder_text='Ex: Aluguel do Galpão', width=Theme.LARGURA_SAIDA)
    entry_titulo_saida.grid(row=2, column=0, padx=20, pady=(0, 10))

    # Valor da Saída
    ctk.CTkLabel(saida_window, text='Valor da Saída (R$):', font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO), anchor='w').grid(row=3, column=0, padx=20, pady=(10, 0), sticky='w')
    entry_valor_saida = ctk.CTkEntry(saida_window, placeholder_text='R$ 0.00', width=Theme.LARGURA_SAIDA)
    entry_valor_saida.grid(row=4, column=0, padx=20, pady=(0, 10))

    # Data da Primeira Saída
    ctk.CTkLabel(saida_window, text='Data da Primeira Saída (DD/MM/AAAA):', font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO), anchor='w').grid(row=5, column=0, padx=20, pady=(10, 0), sticky='w')
    entry_data_saida = ctk.CTkEntry(saida_window, placeholder_text='Ex: 25/11/2025', width=Theme.LARGURA_SAIDA)
    # Define a data atual como placeholder
    entry_data_saida.insert(0, datetime.now().strftime('%d/%m/%Y')) 
    entry_data_saida.grid(row=6, column=0, padx=20, pady=(0, 10))
    
    # --- Configuração de Recorrência ---
    recorrente_var = ctk.StringVar(value="nao_recorrente") 
    frequencias = ["Mensal", "Trimestral", "Semestral", "Anual"]

    combobox_frequencia = ctk.CTkComboBox(
        saida_window, 
        values=frequencias,
        state="disabled",
        width=Theme.LARGURA_SAIDA
    )
    combobox_frequencia.set("Selecione a frequência")
    
    def toggle_frequencia():
        if recorrente_var.get() == "recorrente":
            combobox_frequencia.configure(state="normal")
            combobox_frequencia.set("Mensal")
        else:
            combobox_frequencia.configure(state="disabled")
            combobox_frequencia.set("Selecione a frequência")

    checkbox_recorrente = ctk.CTkCheckBox(
        saida_window, 
        text="Despesa Recorrente?", 
        command=toggle_frequencia, 
        variable=recorrente_var, 
        onvalue="recorrente", 
        offvalue="nao_recorrente",
        fg_color=Theme.COR_SEGUNDARIA,
        hover_color=Theme.COR_SEGUNDARIA_HOVER,
        font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO, weight="bold")
    )
    checkbox_recorrente.grid(row=7, column=0, padx=20, pady=(10, 5), sticky='w')

    combobox_frequencia.grid(row=8, column=0, padx=20, pady=(0, 20))
    
    # --- FUNÇÃO DE VALIDAÇÃO E CADASTRO ---
    def cadastrar_saida():
        titulo = entry_titulo_saida.get().strip()
        valor_str = entry_valor_saida.get().strip().replace(',', '.')
        data_str = entry_data_saida.get().strip()
        recorrente = recorrente_var.get() == "recorrente"
        frequencia = combobox_frequencia.get() if recorrente else "N/A"
        
        # 1. VALIDAÇÃO DE TÍTULO
        if not titulo:
            tkinter.messagebox.showerror("Erro de Validação", "O campo 'Título/Descrição' não pode estar vazio.")
            entry_titulo_saida.focus()
            return
            
        # 2. VALIDAÇÃO DE VALOR
        try:
            valor = float(valor_str)
            if valor <= 0:
                raise ValueError
        except ValueError:
            tkinter.messagebox.showerror("Erro de Validação", "O 'Valor da Saída' deve ser um número positivo válido.")
            entry_valor_saida.focus()
            return
            
        # 3. VALIDAÇÃO DE DATA
        try:
            datetime.strptime(data_str, '%d/%m/%Y')
        except ValueError:
            tkinter.messagebox.showerror("Erro de Validação", "O formato da 'Data' é inválido. Use DD/MM/AAAA.")
            entry_data_saida.focus()
            return
            
        # 4. VALIDAÇÃO DE RECORRÊNCIA
        if recorrente and frequencia == "Selecione a frequência":
            tkinter.messagebox.showerror("Erro de Validação", "Se a despesa é recorrente, você deve selecionar a Frequência.")
            combobox_frequencia.focus()
            return
            
        # --- Lógica de Negócio: Salvar no Banco de Dados ---
        if db_manager.insert_saida(titulo, valor, data_str, recorrente, frequencia):
            tkinter.messagebox.showinfo("Sucesso", "Saída cadastrada e salva no banco de dados!")
            on_close()
        else:
            tkinter.messagebox.showerror("Erro", "Falha ao salvar a saída no banco de dados.")

    btn_cadastrar_saida = ctk.CTkButton(
        saida_window, 
        text='Cadastrar Saída', 
        command=cadastrar_saida,
        fg_color=Theme.COR_SEGUNDARIA, 
        hover_color=Theme.COR_SEGUNDARIA_HOVER, 
        font=ctk.CTkFont(*Theme.FONTE_BOTAO),
        height=Theme.ALTURA_BOTAO,
        width=Theme.LARGURA_SAIDA
    )
    btn_cadastrar_saida.grid(row=9, column=0, padx=20, pady=20)
    
    saida_window.focus()


# #######################################################################
# --- FUNÇÃO PARA CRIAR O GRÁFICO (NOVA) ---
# #######################################################################
def create_forecast_plot(df_forecast_plot: pd.DataFrame):
    """
    Cria um gráfico de barras AGRUPADAS interativo comparando Receitas e Despesas.
    Recebe o DataFrame com 'ds', 'y_receita', 'y_despesa'.
    """
    
    # Filtra apenas os próximos 180 dias a partir de hoje
    today = pd.to_datetime(datetime.now().date())
    df_plot_future = df_forecast_plot[df_forecast_plot['ds'] >= today].copy()
    
    # NÃO precisamos de valores negativos aqui, apenas os valores absolutos para barras agrupadas
    
    fig = go.Figure(
        data=[
            go.Bar(
                name='Receitas Previstas',
                x=df_plot_future['ds'],
                y=df_plot_future['y_receita'],
                marker_color=Theme.COR_PRIMARIA_ESCURA # Laranja
            ),
            go.Bar(
                name='Despesas Previstas',
                x=df_plot_future['ds'],
                y=df_plot_future['y_despesa'],
                marker_color=Theme.COR_SEGUNDARIA # Vermelho
            )
        ]
    )

    fig.update_layout(
        barmode='group', # MODO AGRUPADO: barras lado a lado
        title_text='Comparação de Receitas vs. Despesas Previstas (Próximos 180 Dias)',
        xaxis_title="Data",
        yaxis_title="Valor (R$)",
        hovermode="x unified",
        xaxis=dict(tickformat="%d/%m/%y"), # Formato de data no eixo X
        yaxis=dict(rangemode='tozero') # Garante que o eixo Y comece em zero
    )
    
    # Salva o gráfico em um arquivo HTML temporário e o abre
    plot_file = "forecast_comparison_plot.html"
    try:
        pyo.plot(fig, filename=plot_file, auto_open=False)
        
        # Abre o arquivo no navegador padrão
        webbrowser.open_new_tab(os.path.abspath(plot_file))
        print(f"Gráfico comparativo salvo e aberto em: {os.path.abspath(plot_file)}")
        tkinter.messagebox.showinfo("Gráfico Gerado", "O gráfico de previsão comparativo foi gerado e aberto em seu navegador padrão.")
        
    except Exception as e:
        tkinter.messagebox.showerror("Erro no Gráfico", f"Não foi possível gerar ou abrir o gráfico (Plotly). Erro: {e}\n\nVerifique se a biblioteca 'plotly' está instalada (pip install plotly).")
        print(f"Erro ao gerar/abrir gráfico: {e}")


# #######################################################################
# --- OPÇÃO 3: VISUALIZAR E PROPHET ---
# #######################################################################

def visualizar_prophet_action():
    """Busca dados, roda o modelo Prophet e exibe a previsão, e gera o gráfico."""
    
    if hasattr(app, "prophet_window") and app.prophet_window is not None:
        app.prophet_window.focus()
        return

    prophet_window = ctk.CTkToplevel(app)
    prophet_window.title("Previsão Orçamentária - Modelo Prophet")
    prophet_window.geometry("800x600")
    
    app.prophet_window = prophet_window
    prophet_window.grid_columnconfigure(0, weight=1)
    
    def on_close():
        app.prophet_window = None
        prophet_window.destroy()
        
    prophet_window.protocol("WM_DELETE_WINDOW", on_close)

    # Título
    ctk.CTkLabel(
        prophet_window, 
        text='PREVISÃO DE FLUXO DE CAIXA FUTURO', 
        font=ctk.CTkFont(family="Arial", size=20, weight="bold"), 
        text_color=Theme.COR_PRIMARIA_ESCURA
    ).grid(row=0, column=0, padx=20, pady=(15, 5))
    
    # Label de Status
    status_label = ctk.CTkLabel(
        prophet_window, 
        text='Aguardando execução do modelo...', 
        font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO, weight="bold"),
        text_color="gray"
    )
    status_label.grid(row=1, column=0, padx=20, pady=(5, 10))
    
    # Frame para exibir os resultados (Tabela/Texto)
    results_frame = ctk.CTkScrollableFrame(prophet_window, label_text="Previsão (Próximos 180 Dias)", width=750, height=400)
    results_frame.grid(row=3, column=0, padx=20, pady=(10, 5), sticky="nsew")
    results_frame.grid_columnconfigure(0, weight=1)
    
    # Variável para armazenar o DataFrame completo para o gráfico
    # Inicializa como um DataFrame vazio do Pandas
    df_data_for_plot = pd.DataFrame() 

    # Botão para gerar o gráfico
    btn_plot = ctk.CTkButton(
        prophet_window,
        text="Gerar Gráfico Comparativo",
        # A função lambda chama create_forecast_plot com o DF armazenado
        command=lambda: create_forecast_plot(df_data_for_plot), 
        fg_color="#00695C", 
        hover_color="#00897B",
        state="disabled" # Desabilitado até que a previsão seja feita
    )
    btn_plot.grid(row=4, column=0, padx=20, pady=(5, 15))


    def rodar_prophet_e_exibir():
        nonlocal df_data_for_plot # Permite modificar a variável externa df_data_for_plot
        
        status_label.configure(text='Buscando e formatando dados no SQLite...', text_color="#00695C")
        btn_plot.configure(state="disabled")
        prophet_window.update()
        
        try:
            # 1. Obter dados no formato Prophet (ds, y, y_receita, y_despesa)
            df_prophet_data = db_manager.get_prophet_data(horizonte_dias=180)
            
            # Conta quantos dias no passado têm dados
            historico_count = (df_prophet_data['ds'].dt.date < datetime.now().date()).sum()
            
            if df_prophet_data.empty or historico_count < 2:
                status_label.configure(text="AVISO: Insira mais dados de Entradas e Saídas antes de rodar a previsão.", text_color=Theme.COR_SEGUNDARIA)
                tkinter.messagebox.showwarning("Dados Insuficientes", "O modelo Prophet precisa de dados históricos (mínimo 2 datas) para gerar uma previsão confiável.")
                return

            status_label.configure(text='Treinando o modelo Prophet e gerando previsão...', text_color="#00695C")
            prophet_window.update()
            
            # 2. Rodar o Prophet
            df_forecast_y = df_prophet_data[['ds', 'y']].copy()
            df_forecast = run_prophet_forecast(df_forecast_y, periods=180)
            
            if df_forecast.empty:
                status_label.configure(text="ERRO: Falha ao rodar o modelo Prophet. Verifique o console.", text_color=Theme.COR_SEGUNDARIA)
                return

            # 3. Combinar previsão do Prophet (yhat) com as receitas e despesas (y_receita, y_despesa)
            # Pegamos as receitas e despesas que calculamos no DB
            df_base_future = df_prophet_data[['ds', 'y_receita', 'y_despesa']].copy()
            df_result = pd.merge(df_forecast, df_base_future, on='ds', how='left')
            
            # Armazena o resultado combinado para o botão de gráfico
            df_data_for_plot = df_result.copy()
            
            status_label.configure(text='Previsão concluída! Exibindo resultados.', text_color=Theme.COR_PRIMARIA_ESCURA)

            # 4. Exibir Resultados na Tabela
            for widget in results_frame.winfo_children():
                widget.destroy()

            # Configurar cabeçalho da tabela
            headers = ["Data", "Previsão (yhat)", "Min (90%)", "Max (90%)"]
            
            for i, header in enumerate(headers):
                label = ctk.CTkLabel(results_frame, text=header, font=ctk.CTkFont(*Theme.FONTE_LABEL_MAQUINA))
                label.grid(row=0, column=i, padx=10, pady=5, sticky="ew")
                results_frame.grid_columnconfigure(i, weight=1)

            # Popula as linhas
            for i, row in df_result.iterrows():
                row_index = i - df_result.index[0] + 1
                
                # Formatar Data
                data_str = row['ds'].strftime('%d/%m/%Y')
                
                # Formatar Valores (R$)
                yhat_str = f"R$ {row['yhat']:.2f}"
                y_lower_str = f"R$ {row['yhat_lower']:.2f}"
                y_upper_str = f"R$ {row['yhat_upper']:.2f}"

                ctk.CTkLabel(results_frame, text=data_str, font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO)).grid(row=row_index, column=0, padx=10, pady=2, sticky="w")
                
                # Destaque para Fluxo de Caixa Negativo (Previsão)
                yhat_label = ctk.CTkLabel(results_frame, text=yhat_str, font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO, weight="bold"))
                yhat_label.grid(row=row_index, column=1, padx=10, pady=2, sticky="e")
                if row['yhat'] < 0:
                     yhat_label.configure(text_color="red") # Cor para previsão negativa
                
                ctk.CTkLabel(results_frame, text=y_lower_str, font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO)).grid(row=row_index, column=2, padx=10, pady=2, sticky="e")
                ctk.CTkLabel(results_frame, text=y_upper_str, font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO)).grid(row=row_index, column=3, padx=10, pady=2, sticky="e")
                
            # Habilita o botão de gráfico
            btn_plot.configure(state="normal")


        except Exception as e:
            status_label.configure(text=f"ERRO CRÍTICO na execução: {e}", text_color=Theme.COR_SEGUNDARIA)
            print(f"Erro Crítico: {e}")
            tkinter.messagebox.showerror("Erro Crítico", f"Ocorreu um erro crítico ao processar o modelo: {e}")


    ctk.CTkButton(
        prophet_window, 
        text='Rodar Previsão Prophet (180 Dias)', 
        command=rodar_prophet_e_exibir,
        fg_color="#00695C", 
        hover_color="#00897B",
        font=ctk.CTkFont(*Theme.FONTE_BOTAO),
        height=Theme.ALTURA_BOTAO,
        width=350
    ).grid(row=2, column=0, padx=20, pady=15)
    
    prophet_window.focus()


# #######################################################################
# --- CÓDIGO DA JANELA PRINCIPAL (MENU) ---
# #######################################################################

# --- 1. Configuração Básica ---
ctk.set_appearance_mode('light') 
app = ctk.CTk()
app.title('Sistema de Gestão - Menu Principal')
app.geometry('550x450') 
app.resizable(False, False)

# Configurar o grid: 1 coluna expansível para centralizar
app.grid_columnconfigure(0, weight=1)

# Título do Menu
ctk.CTkLabel(
    app, 
    text='MENU PRINCIPAL', 
    font=ctk.CTkFont(family="Arial", size=24, weight="bold"), 
    text_color=Theme.COR_PRIMARIA_ESCURA
).grid(row=0, column=0, padx=20, pady=(40, 30))

# --- 2. Botões do Menu ---

# Opção 1: Registrar Entrada
btn_entrada = ctk.CTkButton(
    app, 
    text='1. Registrar Entrada de Frota', 
    command=open_cadastro_entrada_window,
    fg_color=Theme.COR_PRIMARIA_ESCURA, 
    hover_color=Theme.COR_SEGUNDARIA, 
    font=ctk.CTkFont(*Theme.FONTE_MENU),
    height=Theme.ALTURA_BOTAO,
    width=Theme.LARGURA_BOTAO_MENU
)
btn_entrada.grid(row=1, column=0, padx=20, pady=10)

# Opção 2: Registrar Saída
btn_saida = ctk.CTkButton(
    app, 
    text='2. Registrar Saída (Despesa)', 
    command=open_cadastro_saida_window,
    fg_color=Theme.COR_SEGUNDARIA, 
    hover_color=Theme.COR_PRIMARIA_ESCURA,
    font=ctk.CTkFont(*Theme.FONTE_MENU),
    height=Theme.ALTURA_BOTAO,
    width=Theme.LARGURA_BOTAO_MENU
)
btn_saida.grid(row=2, column=0, padx=20, pady=10)

# Opção 3: Visualizar e Gerar Prophet
btn_prophet = ctk.CTkButton(
    app, 
    text='3. Previsão Orçamentária (Prophet)', 
    command=visualizar_prophet_action,
    fg_color="#00695C", # Verde Escuro
    hover_color="#00897B",
    font=ctk.CTkFont(*Theme.FONTE_MENU),
    height=Theme.ALTURA_BOTAO,
    width=Theme.LARGURA_BOTAO_MENU
)
btn_prophet.grid(row=3, column=0, padx=20, pady=10)

# --- 4. Loop Principal e Limpeza ---

def on_app_close():
    """Fecha a conexão com o DB antes de encerrar a aplicação."""
    print("Fechando conexão com o banco de dados...")
    db_manager.close()
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_app_close)
app.mainloop()