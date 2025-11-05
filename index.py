import customtkinter as ctk
from datetime import datetime
import tkinter.messagebox
import sys # Para fechar o programa em caso de erro grave, se necessário

# --- Simulação do Módulo de Tema (theme.py) ---
class Theme:
    COR_PRIMARIA_ESCURA = "#E65100"
    COR_SEGUNDARIA = "#C62828"
    COR_SEGUNDARIA_HOVER = "#A81C1C"
    
    # Fontes
    FONTE_LABEL_MAQUINA = ("Arial", 14, "bold")
    FONTE_LABEL_CAMPO = ("Arial", 12)
    FONTE_BOTAO = ("Arial", 16, "bold")
    FONTE_MENU = ("Arial", 18, "bold") # Novo
    
    # Dimensões
    LARGURA_ENTRY = 280
    ALTURA_BOTAO = 40
    LARGURA_SAIDA = 350
    LARGURA_BOTAO_MENU = 450 # Botões grandes para o menu


# #######################################################################
# --- OPÇÃO 1: CADASTRO DE ENTRADA (MÁQUINAS) ---
# #######################################################################

def open_cadastro_entrada_window():
    """Cria a janela Toplevel para o cadastro de Entradas de Máquinas."""
    
    if hasattr(app, "entrada_window") and app.entrada_window is not None:
         app.entrada_window.focus()
         return

    entrada_window = ctk.CTkToplevel(app)
    entrada_window.title("Cadastrar Entrada de Frota")
    entrada_window.geometry("1000x480")
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
        text='REGISTRAR ENTRADAS DA FROTA (R$/HORA e R$/DIÁRIA)', 
        font=ctk.CTkFont(family="Arial", size=18, weight="bold"), 
        text_color=Theme.COR_PRIMARIA_ESCURA
    )
    label_secao_entrada.grid(row=0, column=0, columnspan=3, padx=20, pady=(20, 15))


    # Função auxiliar para criar campos e armazenar referências
    entries_map = {}
    
    def criar_entradas_maquina(app_ref, nome_maquina, coluna_index):
        """Cria e posiciona as Labels e Entries de Hora e Diária no grid."""
        
        label_maquina = ctk.CTkLabel(
            app_ref, 
            text=nome_maquina, 
            font=ctk.CTkFont(*Theme.FONTE_LABEL_MAQUINA), 
            text_color=Theme.COR_PRIMARIA_ESCURA
        )
        label_maquina.grid(row=1, column=coluna_index, padx=20, pady=(5, 5))

        # Hora
        ctk.CTkLabel(app_ref, text='Valor por hora:', anchor="w", font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO)).grid(row=2, column=coluna_index, padx=20, pady=(5, 0), sticky='w')
        entry_hora = ctk.CTkEntry(app_ref, placeholder_text='R$ / hora', width=Theme.LARGURA_ENTRY)
        entry_hora.grid(row=3, column=coluna_index, padx=20, pady=(0, 15))
        
        # Diária
        ctk.CTkLabel(app_ref, text='Valor diária:', anchor="w", font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO)).grid(row=4, column=coluna_index, padx=20, pady=(5, 0), sticky='w')
        entry_diaria = ctk.CTkEntry(app_ref, placeholder_text='R$ / diária', width=Theme.LARGURA_ENTRY)
        entry_diaria.grid(row=5, column=coluna_index, padx=20, pady=(0, 15))
        
        # Armazena as referências para a validação
        entries_map[nome_maquina] = {'hora': entry_hora, 'diaria': entry_diaria}


    def cadastrar_entrada():
        """Valida e processa as entradas de máquinas."""
        
        dados_entrada = {}
        for maquina, entries in entries_map.items():
            for tipo, entry in entries.items():
                valor_str = entry.get().strip().replace(',', '.')
                
                # 1. Validação de Vazio
                if not valor_str:
                    # Permite vazio, assumindo que o valor é 0.00 se o campo for ignorado.
                    # Se fosse obrigatório, usaríamos messagebox aqui.
                    dados_entrada[f'{maquina}_{tipo}'] = 0.0
                    continue

                # 2. Validação Numérica
                try:
                    valor = float(valor_str)
                    if valor < 0:
                        raise ValueError
                    dados_entrada[f'{maquina}_{tipo}'] = valor
                except ValueError:
                    tkinter.messagebox.showerror("Erro de Validação", f"O campo '{tipo.capitalize()} da {maquina}' deve ser um número positivo válido.")
                    entry.focus()
                    return

        # --- Se todas as validações passarem, a lógica de negócio é executada ---
        print("\n" + "=" * 40)
        print("✅ Entradas de Máquina Cadastradas com Sucesso!")
        for k, v in dados_entrada.items():
            print(f"{k}: R$ {v:.2f}")
        print("=" * 40 + "\n")
        
        tkinter.messagebox.showinfo("Sucesso", "Entradas de frota registradas!")
        on_close()


    # Criação dos campos no Toplevel
    criar_entradas_maquina(entrada_window, 'Escavadeira', 0)
    criar_entradas_maquina(entrada_window, 'Caminhão', 1)
    criar_entradas_maquina(entrada_window, 'Retro-Escavadeira', 2)

    # Botão de Cadastro
    btn_cadastrar = ctk.CTkButton(
        entrada_window, 
        text='Registrar Entradas', 
        command=cadastrar_entrada,
        fg_color=Theme.COR_PRIMARIA_ESCURA, 
        hover_color=Theme.COR_PRIMARIA_ESCURA, 
        font=ctk.CTkFont(*Theme.FONTE_BOTAO),
        height=Theme.ALTURA_BOTAO
    )
    btn_cadastrar.grid(row=6, column=0, columnspan=3, padx=20, pady=(20, 20), sticky="ew")

    entrada_window.focus()


# #######################################################################
# --- OPÇÃO 2: CADASTRO DE SAÍDA (DESPESAS) ---
# #######################################################################

def open_cadastro_saida_window():
    """Cria e exibe a janela separada para o cadastro de Saídas (Despesas) com validação."""
    
    # Garante que apenas uma janela de saída seja aberta por vez
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
    label_titulo_saida = ctk.CTkLabel(saida_window, text='Título/Descrição:', font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO), anchor='w')
    label_titulo_saida.grid(row=1, column=0, padx=20, pady=(10, 0), sticky='w')
    entry_titulo_saida = ctk.CTkEntry(saida_window, placeholder_text='Ex: Aluguel do Galpão', width=Theme.LARGURA_SAIDA)
    entry_titulo_saida.grid(row=2, column=0, padx=20, pady=(0, 10))

    # Valor da Saída
    label_valor_saida = ctk.CTkLabel(saida_window, text='Valor da Saída (R$):', font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO), anchor='w')
    label_valor_saida.grid(row=3, column=0, padx=20, pady=(10, 0), sticky='w')
    entry_valor_saida = ctk.CTkEntry(saida_window, placeholder_text='R$ 0.00', width=Theme.LARGURA_SAIDA)
    entry_valor_saida.grid(row=4, column=0, padx=20, pady=(0, 10))

    # Data da Primeira Saída
    label_data_saida = ctk.CTkLabel(saida_window, text='Data da Primeira Saída (DD/MM/AAAA):', font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO), anchor='w')
    label_data_saida.grid(row=5, column=0, padx=20, pady=(10, 0), sticky='w')
    entry_data_saida = ctk.CTkEntry(saida_window, placeholder_text='Ex: 25/11/2025', width=Theme.LARGURA_SAIDA)
    entry_data_saida.grid(row=6, column=0, padx=20, pady=(0, 10))
    
    # --- Configuração de Recorrência ---
    recorrente_var = ctk.StringVar(value="nao_recorrente") 

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

    frequencias = ["Mensal", "Trimestral", "Semestral", "Anual"]
    combobox_frequencia = ctk.CTkComboBox(
        saida_window, 
        values=frequencias,
        state="disabled",
        width=Theme.LARGURA_SAIDA
    )
    combobox_frequencia.set("Selecione a frequência")
    combobox_frequencia.grid(row=8, column=0, padx=20, pady=(0, 20))
    
    # --- FUNÇÃO DE VALIDAÇÃO E CADASTRO ---
    def cadastrar_saida():
        titulo = entry_titulo_saida.get().strip()
        valor_str = entry_valor_saida.get().strip().replace(',', '.')
        data_str = entry_data_saida.get().strip()
        recorrente = recorrente_var.get() == "recorrente"
        frequencia = combobox_frequencia.get() if recorrente else "N/A"
        
        # 2. VALIDAÇÃO DE TÍTULO
        if not titulo:
            tkinter.messagebox.showerror("Erro de Validação", "O campo 'Título/Descrição' não pode estar vazio.")
            entry_titulo_saida.focus()
            return
            
        # 3. VALIDAÇÃO DE VALOR
        try:
            valor = float(valor_str)
            if valor <= 0:
                 raise ValueError
        except ValueError:
            tkinter.messagebox.showerror("Erro de Validação", "O 'Valor da Saída' deve ser um número positivo válido.")
            entry_valor_saida.focus()
            return
            
        # 4. VALIDAÇÃO DE DATA
        try:
            data_obj = datetime.strptime(data_str, '%d/%m/%Y')
        except ValueError:
            tkinter.messagebox.showerror("Erro de Validação", "O formato da 'Data' é inválido. Use DD/MM/AAAA.")
            entry_data_saida.focus()
            return
            
        # 5. VALIDAÇÃO DE RECORRÊNCIA
        if recorrente and frequencia == "Selecione a frequência":
            tkinter.messagebox.showerror("Erro de Validação", "Se a despesa é recorrente, você deve selecionar a Frequência.")
            combobox_frequencia.focus()
            return
            
        # --- Se todas as validações passarem, a lógica de negócio é executada ---
        print("\n" + "=" * 40)
        print("✅ Dados Válidos. Saída Cadastrada com Sucesso!")
        print(f"DESCRIÇÃO: {titulo}")
        print(f"VALOR: R$ {valor:.2f}")
        print(f"DATA INICIAL: {data_obj.strftime('%Y-%m-%d')}")
        print(f"RECORRÊNCIA: {'SIM' if recorrente else 'NÃO'} | CICLO: {frequencia}")
        print("=" * 40 + "\n")
        
        tkinter.messagebox.showinfo("Sucesso", "Saída cadastrada!")
        on_close()

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
# --- OPÇÃO 3: VISUALIZAR E PROPHET ---
# #######################################################################

def visualizar_prophet_action():
    """Função placeholder para a tela de visualização e geração do modelo Prophet."""
    
    if hasattr(app, "prophet_window") and app.prophet_window is not None:
         app.prophet_window.focus()
         return

    prophet_window = ctk.CTkToplevel(app)
    prophet_window.title("Visualizar Dados e Modelo Prophet")
    prophet_window.geometry("600x400")
    prophet_window.resizable(False, False)
    
    app.prophet_window = prophet_window
    prophet_window.grid_columnconfigure(0, weight=1)
    
    def on_close():
        app.prophet_window = None
        prophet_window.destroy()
        
    prophet_window.protocol("WM_DELETE_WINDOW", on_close)

    # Conteúdo Placeholder
    ctk.CTkLabel(
        prophet_window, 
        text='VISUALIZAÇÃO E MODELO PROPHET', 
        font=ctk.CTkFont(family="Arial", size=20, weight="bold"), 
        text_color=Theme.COR_PRIMARIA_ESCURA
    ).grid(row=0, column=0, padx=20, pady=(30, 10))

    ctk.CTkLabel(
        prophet_window, 
        text='Esta janela será dedicada à:\n1. Carregamento e exibição dos dados (Entradas/Saídas).\n2. Geração do modelo Prophet.\n3. Apresentação dos resultados e gráficos de previsão.', 
        font=ctk.CTkFont(*Theme.FONTE_LABEL_CAMPO),
        justify="center"
    ).grid(row=1, column=0, padx=20, pady=20)
    
    ctk.CTkButton(
        prophet_window, 
        text='Rodar Simulação Prophet', 
        command=lambda: tkinter.messagebox.showinfo("Ação", "Simulação do Prophet iniciada!"),
        fg_color=Theme.COR_SEGUNDARIA, 
        font=ctk.CTkFont(*Theme.FONTE_BOTAO),
        height=Theme.ALTURA_BOTAO,
        width=300
    ).grid(row=2, column=0, padx=20, pady=30)
    
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
    text='3. Visualizar Dados e Gerar Modelo', 
    command=visualizar_prophet_action,
    fg_color="#00695C", # Nova cor para destaque
    hover_color="#00897B",
    font=ctk.CTkFont(*Theme.FONTE_MENU),
    height=Theme.ALTURA_BOTAO,
    width=Theme.LARGURA_BOTAO_MENU
)
btn_prophet.grid(row=3, column=0, padx=20, pady=10)


# --- 4. Loop Principal ---
app.mainloop()