import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import os
import json

class PokeEvoEditor:
    def __init__(self, root):
        self.root = root
        self.df_original = None
        self.caminho_arquivo = None
        self.arquivo_progresso = None
        self.pokemon_atual = None
        self.completed_set = set()
        self.familia_em_edicao = []  # Armazena todos os Pokémon da família em edição
        
        # Lista para o dropdown de "Evolve To" (ex: "2: IVYSAUR")
        self.lista_evos_possiveis = []
        
        self.root.title("PokeEvo Editor - Edição de Evoluções")
        self.root.geometry("1000x650")

        # --- ATALHOS DE TECLADO ---
        self.root.bind('<Control-s>', lambda e: self.exportar_final())
        self.root.bind('<Control-q>', lambda e: self.add_blank_evo())
        self.root.bind('<Control-a>', self.toggle_completed_atalho)

        # --- MENU SUPERIOR ---
        self.menu_bar = tk.Menu(root)
        self.root.config(menu=self.menu_bar)
        
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Arquivo", menu=self.file_menu)
        self.file_menu.add_command(label="Abrir CSV de Evoluções", command=self.selecionar_arquivo)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Sair", command=root.quit)

        # Layout Principal
        self.main_frame = ttk.Frame(root)
        
        # --- FRAME 1: LISTA PRINCIPAL (Esquerda) ---
        self.frame_lista = ttk.Frame(self.main_frame)
        self.frame_lista.pack(side="left", fill="y", padx=10, pady=10)
        
        ttk.Label(self.frame_lista, text="Filtro de Status:").pack()
        self.filter_status_var = tk.StringVar(value="Mostrar todos")
        self.combo_filter = ttk.Combobox(self.frame_lista, textvariable=self.filter_status_var, 
                                         values=["Mostrar todos", "Mostrar completos", "Mostrar incompletos"], state="readonly")
        self.combo_filter.pack(fill="x", pady=(0, 5))
        self.combo_filter.bind("<<ComboboxSelected>>", self.filtrar_lista)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filtrar_lista)
        ttk.Label(self.frame_lista, text="Buscar Pokémon:").pack()
        self.ent_search = ttk.Entry(self.frame_lista, textvariable=self.search_var)
        self.ent_search.pack(fill="x", pady=5)

        self.lb_pkmn = tk.Listbox(self.frame_lista, width=28, font=("Arial", 10), exportselection=False)
        self.lb_pkmn.pack(expand=True, fill="both")
        self.lb_pkmn.bind('<<ListboxSelect>>', self.trocar_pokemon)

        # --- FRAME 2: EDIÇÃO (Direita) ---
        self.frame_edit = ttk.Frame(self.main_frame)
        self.frame_edit.pack(side="left", expand=True, fill="both", padx=10, pady=10)

        self.lbl_nome = ttk.Label(self.frame_edit, text="Aguardando arquivo...", font=("Arial", 16, "bold"), foreground="#4B0082")
        self.lbl_nome.pack(pady=(10, 5))

        self.is_completed_var = tk.BooleanVar()
        self.chk_completed = tk.Checkbutton(self.frame_edit, text="✅ Família Concluída (Ctrl+A)", 
                                            variable=self.is_completed_var, command=self.toggle_completed,
                                            font=("Arial", 10, "bold"), fg="green")

        # Container rolável para as evoluções
        self.canvas = tk.Canvas(self.frame_edit)
        self.scrollbar = ttk.Scrollbar(self.frame_edit, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas)
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="top", fill="both", expand=True, pady=10)
        self.scrollbar.pack(side="right", fill="y")

        # --- BOTÕES INFERIORES GERAIS ---
        self.btn_frame = ttk.Frame(root)
        ttk.Button(self.btn_frame, text="➕ Add Evolução (Ctrl+Q)", command=self.add_blank_evo).pack(side="left", padx=10)
        ttk.Button(self.btn_frame, text="💾 SALVAR TUDO (Ctrl+S)", command=self.exportar_final).pack(side="right", padx=10)

        self.lbl_status = ttk.Label(root, text="Atalhos: Ctrl+S (Salvar) | Ctrl+Q (Add Evolução) | Ctrl+A (Concluir)", foreground="blue")
        self.lbl_status.pack(side="bottom", pady=5)

    def selecionar_arquivo(self):
        caminho = filedialog.askopenfilename(filetypes=[("Arquivos CSV", "*.csv")])
        if caminho:
            try:
                # Na tabela de evoluções, preenchemos com vazio "" invés de "0"
                self.df_original = pd.read_csv(caminho, sep=',', encoding='utf-8', dtype=str).fillna("")
                
                self.caminho_arquivo = caminho
                self.arquivo_progresso = self.caminho_arquivo.replace('.csv', '_progresso.json')
                self.completed_set = set()
                
                if os.path.exists(self.arquivo_progresso):
                    try:
                        with open(self.arquivo_progresso, 'r', encoding='utf-8') as f:
                            self.completed_set = set(json.load(f))
                    except: pass

                # Gera a lista de evoluções possíveis para o dropdown
                self.lista_evos_possiveis = []
                for idx, row in self.df_original.iterrows():
                    pid = str(row['ID']).replace('.0', '')
                    self.lista_evos_possiveis.append(f"{pid}: {str(row['Name'])}")

                self.main_frame.pack(fill="both", expand=True)
                self.btn_frame.pack(fill="x", side="bottom", pady=10)
                self.carregar_lista_nomes()
                self.lbl_status.config(text=f"Editando: {os.path.basename(caminho)}", foreground="green")
                messagebox.showinfo("Sucesso", "Tabela de Evoluções carregada!")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível ler o arquivo:\n{e}")

    def carregar_lista_nomes(self):
        self.lista_formatada = []
        for idx, row in self.df_original.iterrows():
            pid = str(row['ID']).replace('.0', '')
            pname = str(row['Name'])
            self.lista_formatada.append(f"{pid} - {pname}")
            
        self.filtrar_lista()

    def filtrar_lista(self, *args):
        if self.df_original is None: return
        search = self.search_var.get().upper()
        status_filtro = self.filter_status_var.get()
        
        self.lb_pkmn.delete(0, tk.END)
        for item in self.lista_formatada:
            pname = item.split(" - ", 1)[1]
            is_completed = pname in self.completed_set
            
            if status_filtro == "Mostrar completos" and not is_completed: continue
            if status_filtro == "Mostrar incompletos" and is_completed: continue
                
            prefix = "✅ " if is_completed else ""
            if search in item.upper():
                self.lb_pkmn.insert(tk.END, prefix + item)

    def restaurar_selecao_lista(self):
        if not self.pokemon_atual: return
        itens = self.lb_pkmn.get(0, tk.END)
        for i, item in enumerate(itens):
            nome = item.replace("✅ ", "").split(" - ", 1)[1]
            if nome == self.pokemon_atual:
                self.lb_pkmn.selection_clear(0, tk.END)
                self.lb_pkmn.selection_set(i)
                self.lb_pkmn.activate(i)
                self.lb_pkmn.see(i)
                break

    def encontrar_familia_evolutiva(self, pokemon_nome):
        """Encontra todos os Pokémon que fazem parte da mesma família evolutiva."""
        familia = set()
        visitados = set()
        
        def adicionar_com_conexoes(nome):
            if nome in visitados:
                return
            visitados.add(nome)
            familia.add(nome)
            
            # Encontra sucessores (Pokémon para os quais este evolui)
            linha = self.df_original[self.df_original['Name'] == nome]
            if not linha.empty:
                for i in range(1, 7):
                    col_evo = f'Evolves To {i}'
                    if col_evo in self.df_original.columns:
                        evo_to = str(linha.iloc[0].get(col_evo, "")).strip()
                        if evo_to and evo_to.lower() != 'nan' and evo_to != "":
                            # Extrai nome do formato "2: IVYSAUR"
                            nome_evo = evo_to.split(": ")[-1].strip() if ": " in evo_to else evo_to
                            if nome_evo in self.df_original['Name'].values:
                                adicionar_com_conexoes(nome_evo)
            
            # Encontra predecessores (Pokémon que evoluem para este)
            for idx, row in self.df_original.iterrows():
                for i in range(1, 7):
                    col_evo = f'Evolves To {i}'
                    if col_evo in self.df_original.columns:
                        evo_to = str(row.get(col_evo, "")).strip()
                        if evo_to and evo_to.lower() != 'nan' and evo_to != "":
                            nome_evo = evo_to.split(": ")[-1].strip() if ": " in evo_to else evo_to
                            if nome_evo == nome:
                                nome_pred = str(row['Name']).strip()
                                if nome_pred and nome_pred.lower() != 'nan':
                                    adicionar_com_conexoes(nome_pred)
        
        adicionar_com_conexoes(pokemon_nome)
        return sorted(list(familia))

    def toggle_completed_atalho(self, event=None):
        if not self.pokemon_atual: return
        self.is_completed_var.set(not self.is_completed_var.get())
        self.toggle_completed()

    def toggle_completed(self):
        if not self.pokemon_atual: return
        
        if self.is_completed_var.get():
            self.completed_set.add(self.pokemon_atual)
        else:
            self.completed_set.discard(self.pokemon_atual)
            
        if self.arquivo_progresso:
            with open(self.arquivo_progresso, 'w', encoding='utf-8') as f:
                json.dump(list(self.completed_set), f)
                
        self.filtrar_lista()
        self.restaurar_selecao_lista()
        self.lb_pkmn.focus_set()

    def salvar_em_memoria(self):
        if self.df_original is None or not self.familia_em_edicao:
            return

        # Salva as evoluções de cada membro da família
        for pokemon_nome in self.familia_em_edicao:
            evos_tela = []
            # Encontra todos os frames de evolução deste Pokémon
            for w in self.scroll_frame.winfo_children():
                if not w.winfo_exists():
                    continue
                
                # Verifica se este frame pertence ao pokemon_nome
                if hasattr(w, 'pokemon_dono') and w.pokemon_dono == pokemon_nome:
                    filhos = w.winfo_children()
                    if len(filhos) >= 6:
                        evo_to = str(filhos[1].get()).strip()
                        method = str(filhos[3].get()).strip()
                        param = str(filhos[5].get()).strip()
                        
                        if evo_to != "":
                            evos_tela.append((evo_to, method, param))
            
            # Encontra o índice do Pokémon no dataframe
            idx_list = self.df_original.index[self.df_original['Name'] == pokemon_nome]
            if len(idx_list) == 0:
                continue
            
            idx = idx_list[0]
            evos_tela = evos_tela[:6]
            
            nova_row = [str(self.df_original.at[idx, 'ID']), str(self.df_original.at[idx, 'Name'])]
            
            for et, m, p in evos_tela:
                nova_row.extend([et, m, p])
            
            # O CSV de evoluções tem 2 colunas base + 6*3 colunas de evoluções = 20 colunas
            while len(nova_row) < 20:
                nova_row.extend(["", "", ""])
            
            self.df_original.iloc[idx] = nova_row[:20]

    def trocar_pokemon(self, event):
        if not self.lb_pkmn.curselection(): return
        
        if self.pokemon_atual:
            self.salvar_em_memoria()
            
        selecionado = self.lb_pkmn.get(self.lb_pkmn.curselection())
        selecionado = selecionado.replace("✅ ", "") 
        nome = selecionado.split(" - ", 1)[1]
        
        self.pokemon_atual = nome
        
        # Encontra a família evolutiva
        self.familia_em_edicao = self.encontrar_familia_evolutiva(nome)
        
        self.lbl_nome.config(text=f"Família: {' → '.join(self.familia_em_edicao)}")
        
        self.chk_completed.pack(pady=(0, 10))
        self.is_completed_var.set(nome in self.completed_set)
        
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Carrega evoluções de cada membro da família
        for pokemon_nome in self.familia_em_edicao:
            # Adiciona header para este Pokémon
            f_header = ttk.Frame(self.scroll_frame)
            f_header.pack(fill="x", pady=(15, 5), padx=5)
            ttk.Label(f_header, text=f"📌 {pokemon_nome}", font=("Arial", 11, "bold"), foreground="#0066CC").pack(anchor="w")
            
            linha = self.df_original[self.df_original['Name'] == pokemon_nome].iloc[0]
            
            # Loop nas 6 possíveis colunas de evolução
            for i in range(1, 7):
                col_evo = f'Evolves To {i}'
                col_met = f'Method {i}'
                col_par = f'Parameter {i}'
                
                if col_evo in self.df_original.columns:
                    evo_to = str(linha.get(col_evo, "")).strip()
                    method = str(linha.get(col_met, "")).strip()
                    param = str(linha.get(col_par, "")).strip()
                    
                    # Ignora valores NaN
                    if evo_to and evo_to.lower() != 'nan':
                        self.criar_linha_ui(evo_to, method, param, pokemon_nome)

    def deletar_evo(self, frame):
        frame.destroy()
        self.lb_pkmn.focus_set()

    def criar_linha_ui(self, evo_to="", method="", param="", pokemon_dono=""):
        f = ttk.Frame(self.scroll_frame)
        f.pack(fill="x", pady=5, padx=10)
        
        # Armazena qual Pokémon é dono desta evolução
        f.pokemon_dono = pokemon_dono
        
        # 1. Evolves To (Dropdown com a lista de todos os Pokémon)
        ttk.Label(f, text="Evolui para:", font=("Arial", 9, "bold")).pack(side="left", padx=(5,2))
        c_to = ttk.Combobox(f, values=self.lista_evos_possiveis, width=22)
        c_to.insert(0, evo_to)
        c_to.pack(side="left", padx=2)
        
        # 2. Method (Dropdown com os métodos padrões)
        ttk.Label(f, text="Método:", font=("Arial", 9, "bold")).pack(side="left", padx=(15,2))
        metodos_padrao = ["Reach Level", "Reach Level (Male)", "Reach Level (Female)"]
        c_met = ttk.Combobox(f, values=metodos_padrao, width=20)
        c_met.insert(0, method)
        c_met.pack(side="left", padx=2)
        
        # 3. Parameter (Entry livre para "Level 16", etc)
        ttk.Label(f, text="Parâmetro:", font=("Arial", 9, "bold")).pack(side="left", padx=(15,2))
        e_par = tk.Entry(f, width=15)
        e_par.insert(0, param)
        e_par.pack(side="left", padx=2)
        
        ttk.Button(f, text="🗑️", width=3, command=lambda: self.deletar_evo(f)).pack(side="right", padx=10)

    def add_blank_evo(self):
        if self.df_original is not None:
            # Conta quantas evoluções já tem na tela para o Pokémon atual
            count = sum(1 for w in self.scroll_frame.winfo_children() 
                       if hasattr(w, 'pokemon_dono') and w.pokemon_dono == self.pokemon_atual and w.winfo_exists())
            if count >= 6:
                messagebox.showwarning("Limite Máximo", "O arquivo permite no máximo 6 evoluções por Pokémon.")
                return
                
            self.criar_linha_ui("", "Reach Level", "Level ", self.pokemon_atual)
            self.canvas.yview_moveto(1.0)
        else:
            messagebox.showwarning("Aviso", "Abra a Tabela de Evoluções primeiro!")

    def exportar_final(self):
        if self.df_original is None: return
        self.salvar_em_memoria()
        try:
            self.df_original.to_csv(self.caminho_arquivo, index=False)
            agora = pd.Timestamp.now().strftime('%H:%M:%S')
            self.lbl_status.config(text=f"✅ Evoluções salvas com sucesso às {agora}!", foreground="green")
        except Exception as e:
            messagebox.showerror("Erro ao gravar", f"Erro: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PokeEvoEditor(root)
    root.mainloop()