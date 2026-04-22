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
        
        # Dicionários para lógica de família e UI
        self.grafo_familia = {}
        self.lista_evos_possiveis = []
        self.frames_membros = {} # Guarda os frames onde ficam as evos de cada membro
        
        self.root.title("PokeEvo Editor - Edição por Família")
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

        # Container rolável para as evoluções da família
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
        ttk.Button(self.btn_frame, text="➕ Add Evo para Alvo (Ctrl+Q)", command=self.add_blank_evo).pack(side="left", padx=10)
        ttk.Button(self.btn_frame, text="💾 SALVAR TUDO (Ctrl+S)", command=self.exportar_final).pack(side="right", padx=10)

        self.lbl_status = ttk.Label(root, text="Atalhos: Ctrl+S (Salvar) | Ctrl+Q (Add Evo pro Selecionado) | Ctrl+A (Concluir)", foreground="blue")
        self.lbl_status.pack(side="bottom", pady=5)

    def construir_arvore_familia(self):
        """Lê o CSV inteiro para encontrar as conexões entre os Pokémon"""
        self.grafo_familia = {}
        
        # Garante que todo Pokémon exista no grafo
        for idx, row in self.df_original.iterrows():
            nome = str(row['Name']).strip()
            if nome: self.grafo_familia[nome] = set()
            
        # Conecta as evoluções (Ida e Volta para poder puxar a família inteira)
        for idx, row in self.df_original.iterrows():
            nome = str(row['Name']).strip()
            if not nome: continue
            
            for i in range(1, 7):
                col_evo = f'Evolves To {i}'
                if col_evo in self.df_original.columns:
                    val = str(row.get(col_evo, "")).strip()
                    if val and val.lower() != 'nan':
                        # Separa o ID do Nome (ex: "2: IVYSAUR" -> "IVYSAUR")
                        alvo = val.split(": ", 1)[1].strip() if ": " in val else val
                        
                        if alvo not in self.grafo_familia:
                            self.grafo_familia[alvo] = set()
                            
                        self.grafo_familia[nome].add(alvo)
                        self.grafo_familia[alvo].add(nome) # Liga de volta pra formar a família

    def get_familia(self, nome_inicial):
        """Retorna uma lista com a família inteira conectada ao Pokémon, ordenado por ID"""
        visitados = set()
        fila = [nome_inicial]
        
        while fila:
            atual = fila.pop(0)
            if atual not in visitados:
                visitados.add(atual)
                if atual in self.grafo_familia:
                    for vizinho in self.grafo_familia[atual]:
                        if vizinho not in visitados:
                            fila.append(vizinho)
                            
        # Ordena a família pela ordem da Pokédex (ID)
        name_to_id = {str(row['Name']).strip(): int(str(row['ID']).replace('.0', '')) for idx, row in self.df_original.iterrows()}
        familia_ordenada = sorted(list(visitados), key=lambda x: name_to_id.get(x, 9999))
        return familia_ordenada

    def selecionar_arquivo(self):
        caminho = filedialog.askopenfilename(filetypes=[("Arquivos CSV", "*.csv")])
        if caminho:
            try:
                self.df_original = pd.read_csv(caminho, sep=',', encoding='utf-8', dtype=str).fillna("")
                self.caminho_arquivo = caminho
                self.arquivo_progresso = self.caminho_arquivo.replace('.csv', '_progresso.json')
                self.completed_set = set()
                
                if os.path.exists(self.arquivo_progresso):
                    try:
                        with open(self.arquivo_progresso, 'r', encoding='utf-8') as f:
                            self.completed_set = set(json.load(f))
                    except: pass

                # Gera Dropdown e Grafo de Família
                self.lista_evos_possiveis = []
                for idx, row in self.df_original.iterrows():
                    pid = str(row['ID']).replace('.0', '')
                    self.lista_evos_possiveis.append(f"{pid}: {str(row['Name'])}")
                
                self.construir_arvore_familia()

                self.main_frame.pack(fill="both", expand=True)
                self.btn_frame.pack(fill="x", side="bottom", pady=10)
                self.carregar_lista_nomes()
                self.lbl_status.config(text=f"Editando: {os.path.basename(caminho)}", foreground="green")
                messagebox.showinfo("Sucesso", "Tabela de Evoluções e Árvores Familiares carregadas!")
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

    def toggle_completed_atalho(self, event=None):
        if not self.pokemon_atual: return
        self.is_completed_var.set(not self.is_completed_var.get())
        self.toggle_completed()

    def toggle_completed(self):
        if not self.pokemon_atual: return
        
        familia = self.get_familia(self.pokemon_atual)
        
        if self.is_completed_var.get():
            for m in familia: self.completed_set.add(m)
        else:
            for m in familia: self.completed_set.discard(m)
            
        if self.arquivo_progresso:
            with open(self.arquivo_progresso, 'w', encoding='utf-8') as f:
                json.dump(list(self.completed_set), f)
                
        self.filtrar_lista()
        self.restaurar_selecao_lista()
        self.lb_pkmn.focus_set()

    def salvar_em_memoria(self):
        if self.df_original is None or not hasattr(self, 'frames_membros'): return

        # Salva as alterações de TODOS os membros da família que estão na tela
        for membro, container in self.frames_membros.items():
            evos_tela = []
            for w in container.winfo_children():
                if not w.winfo_exists(): continue
                
                filhos = w.winfo_children()
                if len(filhos) >= 6:
                    evo_to = str(filhos[1].get()).strip()
                    method = str(filhos[3].get()).strip()
                    param = str(filhos[5].get()).strip()
                    if evo_to != "": evos_tela.append((evo_to, method, param))
            
            evos_tela = evos_tela[:6] # Limite do CSV

            idxs = self.df_original.index[self.df_original['Name'] == membro].tolist()
            if not idxs: continue
            idx = idxs[0]
            
            nova_row = [str(self.df_original.at[idx, 'ID']), str(self.df_original.at[idx, 'Name'])]
            for et, m, p in evos_tela: nova_row.extend([et, m, p])
            while len(nova_row) < 20: nova_row.extend(["", "", ""])
            
            self.df_original.iloc[idx] = nova_row[:20]

        # Reconstrói as conexões do grafo caso você tenha mudado quem evolui pra quem!
        self.construir_arvore_familia()

    def trocar_pokemon(self, event):
        if not self.lb_pkmn.curselection(): return
        
        if self.pokemon_atual:
            self.salvar_em_memoria()
            
        selecionado = self.lb_pkmn.get(self.lb_pkmn.curselection())
        selecionado = selecionado.replace("✅ ", "") 
        nome = selecionado.split(" - ", 1)[1]
        
        self.pokemon_atual = nome
        familia = self.get_familia(nome)
        
        # Atualiza Titulo da Família
        nomes_familia = " ➔ ".join(familia) if len(familia) > 1 else nome
        self.lbl_nome.config(text=f"Editando Família:\n{nomes_familia}")
        
        # Se todos da familia estão completos, a caixa fica marcada
        all_completed = all(m in self.completed_set for m in familia)
        self.chk_completed.pack(pady=(0, 10))
        self.is_completed_var.set(all_completed)
        
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        self.frames_membros = {}

        # Carrega a UI para cada membro da família
        for membro in familia:
            frame_membro = ttk.LabelFrame(self.scroll_frame, text=f"🐾 {membro}", padding=10)
            frame_membro.pack(fill="x", padx=10, pady=5)
            
            # Container interno pros inputs de evolucao
            container_evos = ttk.Frame(frame_membro)
            container_evos.pack(fill="x")
            
            self.frames_membros[membro] = container_evos
            
            btn_add = ttk.Button(frame_membro, text=f"➕ Add Evo para {membro}", 
                                 command=lambda m=membro: self.add_blank_evo_membro(m))
            btn_add.pack(pady=5, anchor="w")

            # Puxa os dados atuais do CSV pra preencher
            idxs = self.df_original.index[self.df_original['Name'] == membro].tolist()
            if not idxs: continue
            linha = self.df_original.iloc[idxs[0]]
            
            for i in range(1, 7):
                col_evo = f'Evolves To {i}'
                col_met = f'Method {i}'
                col_par = f'Parameter {i}'
                if col_evo in self.df_original.columns:
                    evo_to = str(linha.get(col_evo, "")).strip()
                    method = str(linha.get(col_met, "")).strip()
                    param = str(linha.get(col_par, "")).strip()
                    if evo_to and evo_to.lower() != 'nan':
                        self.criar_linha_ui(container_evos, evo_to, method, param)

    def deletar_evo(self, frame):
        frame.destroy()
        self.lb_pkmn.focus_set()

    def criar_linha_ui(self, parent_container, evo_to="", method="", param=""):
        f = ttk.Frame(parent_container)
        f.pack(fill="x", pady=5)
        
        # 1. Evolves To
        ttk.Label(f, text="Evolui para:", font=("Arial", 9, "bold")).pack(side="left", padx=(5,2))
        c_to = ttk.Combobox(f, values=self.lista_evos_possiveis, width=22)
        c_to.insert(0, evo_to)
        c_to.pack(side="left", padx=2)
        
        # 2. Method
        ttk.Label(f, text="Método:", font=("Arial", 9, "bold")).pack(side="left", padx=(15,2))
        metodos_padrao = ["Reach Level", "Reach Level (Male)", "Reach Level (Female)"]
        c_met = ttk.Combobox(f, values=metodos_padrao, width=20)
        c_met.insert(0, method)
        c_met.pack(side="left", padx=2)
        
        # 3. Parameter 
        ttk.Label(f, text="Parâmetro:", font=("Arial", 9, "bold")).pack(side="left", padx=(15,2))
        e_par = tk.Entry(f, width=15)
        e_par.insert(0, param)
        e_par.pack(side="left", padx=2)
        
        ttk.Button(f, text="🗑️", width=3, command=lambda: self.deletar_evo(f)).pack(side="right", padx=10)

    def add_blank_evo_membro(self, membro):
        """Adiciona uma linha vazia no Frame específico de um Pokémon da família"""
        if membro in self.frames_membros:
            container = self.frames_membros[membro]
            count = sum(1 for w in container.winfo_children() if w.winfo_exists())
            if count >= 6:
                messagebox.showwarning("Limite Máximo", f"O arquivo permite no máximo 6 evoluções por Pokémon. {membro} já atingiu o limite.")
                return
                
            self.criar_linha_ui(container, "", "Reach Level", "Level ")
            self.canvas.yview_moveto(1.0)
            
    def add_blank_evo(self):
        """Atalho de teclado adiciona para o Pokémon principal focado"""
        if self.pokemon_atual:
            self.add_blank_evo_membro(self.pokemon_atual)
        else:
            messagebox.showwarning("Aviso", "Selecione um Pokémon primeiro!")

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