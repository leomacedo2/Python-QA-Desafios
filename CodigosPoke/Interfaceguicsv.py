import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import pandas as pd
import os
import json
import copy

class PokemonEditor:
    def __init__(self, root):
        self.root = root
        self.df_original = None
        self.caminho_arquivo = None
        self.arquivo_progresso = None
        self.pokemon_atual = None
        self.move_copia_atual = None 
        self.completed_set = set()
        self.favorites_set = set()
        self.arquivo_favoritos = None 
        self.historico_undo = []
        self.historico_redo = []
        
        self.root.title("PokeMove Editor")
        self.root.geometry("1150x750")

        # --- BARRA DE FERRAMENTAS SUPERIOR (CABEÇALHO) ---
        self.toolbar_frame = ttk.Frame(root)
        self.toolbar_frame.pack(side="top", fill="x", padx=10, pady=5)

        self.btn_undo = ttk.Button(self.toolbar_frame, text="↩️ Desfazer", state=tk.DISABLED, command=self.executar_ctrl_z)
        self.btn_undo.pack(side="left", padx=2)

        self.btn_redo = ttk.Button(self.toolbar_frame, text="↪️ Refazer", state=tk.DISABLED, command=self.executar_ctrl_y)
        self.btn_redo.pack(side="left", padx=2)

        # --- ATALHOS DE TECLADO ---
        self.root.bind('<Control-s>', lambda e: self.exportar_final())
        self.root.bind('<Control-w>', lambda e: self.add_blank_move())
        self.root.bind('<Control-d>', lambda e: self.organizar_visual())
        self.root.bind('<Control-f>', lambda e: self.ent_search.focus_set())
        self.root.bind('<Control-a>', self.toggle_completed_atalho)
        self.root.bind('<Control-q>', self.toggle_favorite_atalho)

        # --- SISTEMA UNDO / REDO ---
        self.root.bind('<Control-z>', self.executar_ctrl_z)
        self.root.bind('<Control-y>', self.executar_ctrl_y)

        # --- ATALHOS DO TECLADO NUMÉRICO (NUMPAD) ---
        # self.root.bind('<Control-Up>', lambda e: self.organizar_visual())
        #self.root.bind('<Control-Up>', lambda e: self.organizar_visual()) 
        #self.root.bind('<Control-Down>', lambda e: self.lb_pkmn.focus_set())
        self.root.bind('<Control-Up>', lambda e: self.navegar_leveis(-1)) 
        self.root.bind('<Control-Down>', lambda e: self.navegar_leveis(1))
        self.root.bind('<Control-Left>', lambda e: self.lb_pkmn.focus_set())
        self.root.bind('<Control-Right>', lambda e: self.organizar_visual())
        #self.root.bind('<Control-Left>', lambda e: self.navegar_leveis(-1))
        #self.root.bind('<Control-Right>', lambda e: self.navegar_leveis(1))
        # self.root.bind('<Control-Right>', self.navegar_campos_edicao)
        self.root.bind('<Control-Key-1>', self.toggle_favorite_atalho)           # Ctrl + Numpad 1 (Favoritar)
        self.root.bind('<Control-Key-2>', self.toggle_completed_atalho)          # Ctrl + Numpad 2 (Concluir)
        self.root.bind('<Control-Key-3>', lambda e: self.ent_search.focus_set()) # Ctrl + Numpad 3 (Buscar)
        self.root.bind('<Control-Key-5>', lambda e: self.iniciar_copia_todos())  # Ctrl + Numpad 5 (Copiar Todos)
        self.root.bind('<Control-Key-0>', lambda e: self.exportar_final())       # Ctrl + Numpad 0 (Salvar Tudo)


        # --- MENU SUPERIOR ---
        self.menu_bar = tk.Menu(root)
        self.root.config(menu=self.menu_bar)
        
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Arquivo", menu=self.file_menu)
        self.file_menu.add_command(label="Abrir CSV (Original ou Editado)", command=self.selecionar_arquivo)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Sair", command=root.quit)

        # Layout Principal
        self.main_frame = ttk.Frame(root)
        
        # --- FRAME 1: LISTA PRINCIPAL (Esquerda) ---
        self.frame_lista = ttk.Frame(self.main_frame)
        self.frame_lista.pack(side="left", fill="y", padx=10, pady=10)
        
        # Filtro de Status
        ttk.Label(self.frame_lista, text="Filtro de Status:").pack()
        self.filter_status_var = tk.StringVar(value="Mostrar todos")
        self.combo_filter = ttk.Combobox(self.frame_lista, textvariable=self.filter_status_var, 
                                         values=["Mostrar todos", "Mostrar completos", "Mostrar incompletos", "Favoritos"], state="readonly")
        self.combo_filter.pack(fill="x", pady=(0, 5))
        self.combo_filter.bind("<<ComboboxSelected>>", self.filtrar_lista)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filtrar_lista)
        ttk.Label(self.frame_lista, text="Buscar Pokémon:").pack()
        self.ent_search = ttk.Entry(self.frame_lista, textvariable=self.search_var)
        self.ent_search.pack(fill="x", pady=5)

        self.lb_pkmn = tk.Listbox(self.frame_lista, width=25, font=("Arial", 10), exportselection=False)
        self.lb_pkmn.pack(expand=True, fill="both")
        self.lb_pkmn.bind('<<ListboxSelect>>', self.trocar_pokemon)

        # --- TRAVA PARA A LISTBOX NÃO PULAR POKÉMON COM O CTRL ---
        self.lb_pkmn.bind('<Control-Up>', lambda e: self.navegar_leveis(-1))
        self.lb_pkmn.bind('<Control-Down>', lambda e: self.navegar_leveis(1))

        # --- FRAME 3: LISTA ALVO PARA COPIAR (Direita) ---
        self.frame_alvo = ttk.Frame(self.main_frame)
        
        self.lbl_alvo_titulo = ttk.Label(self.frame_alvo, text="Selecione o Destino:", font=("Arial", 10, "bold"), foreground="purple")
        self.lbl_alvo_titulo.pack(pady=5)
        
        # ---> CÓDIGO NOVO: Filtro de Status para a coluna alvo <---
        ttk.Label(self.frame_alvo, text="Filtro de Status:").pack()
        self.filter_alvo_status_var = tk.StringVar(value="Mostrar todos")
        self.combo_filter_alvo = ttk.Combobox(self.frame_alvo, textvariable=self.filter_alvo_status_var, values=["Mostrar todos", "Mostrar completos", "Mostrar incompletos", "Favoritos"], state="readonly")
        self.combo_filter_alvo.pack(fill="x", pady=(0, 5))
        self.combo_filter_alvo.bind("<<ComboboxSelected>>", self.filtrar_lista_alvo)
        # ----------------------------------------------------------

        self.search_alvo_var = tk.StringVar()
        self.search_alvo_var.trace("w", self.filtrar_lista_alvo)
        ttk.Label(self.frame_alvo, text="Buscar Destino:").pack()
        self.ent_search_alvo = ttk.Entry(self.frame_alvo, textvariable=self.search_alvo_var)
        self.ent_search_alvo.pack(fill="x", pady=5)

        self.lb_alvo = tk.Listbox(self.frame_alvo, width=25, font=("Arial", 10), exportselection=False)
        self.lb_alvo.pack(expand=True, fill="both")
        self.lb_alvo.bind('<<ListboxSelect>>', self.confirmar_copia_lista)

        ttk.Button(self.frame_alvo, text="❌ Cancelar Cópia", command=self.esconder_painel_copia).pack(pady=5, fill="x")

        # --- FRAME 2: EDIÇÃO (Meio) ---
        self.frame_edit = ttk.Frame(self.main_frame)
        self.frame_edit.pack(side="left", expand=True, fill="both", padx=10, pady=10)

        self.lbl_nome = ttk.Label(self.frame_edit, text="Aguardando arquivo...", font=("Arial", 14, "bold"))
        self.lbl_nome.pack(pady=(10, 0))

        # Checkbutton para marcar como Concluído
        self.is_completed_var = tk.BooleanVar()
        self.chk_completed = tk.Checkbutton(self.frame_edit, text="✅ Marcar como Concluído", 
                                            variable=self.is_completed_var, command=self.toggle_completed,
                                            font=("Arial", 10, "bold"), fg="green")
        self.is_favorite_var = tk.BooleanVar()
        self.chk_favorite = tk.Checkbutton(self.frame_edit, text="⭐ Favoritar", 
                                            variable=self.is_favorite_var, command=self.toggle_favorite,
                                            font=("Arial", 10, "bold"), fg="#FF8C00") # Laranja escuro
        self.canvas = tk.Canvas(self.frame_edit)
        self.scrollbar = ttk.Scrollbar(self.frame_edit, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas)
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="top", fill="both", expand=True, pady=5)
        self.scrollbar.pack(side="right", fill="y")

        # --- BARRA INFERIOR DA LISTA DE EDIÇÃO ---
        self.bottom_edit_frame = ttk.Frame(self.frame_edit)
        self.bottom_edit_frame.pack(fill="x", pady=5, side="bottom")
        
        self.lbl_aviso_limite = ttk.Label(self.bottom_edit_frame, text="", font=("Arial", 11, "bold"))
        self.lbl_aviso_limite.pack(side="left", padx=5)

        ttk.Button(self.bottom_edit_frame, text="📑 Copiar TODOS os Golpes", 
                   command=self.iniciar_copia_todos).pack(side="left", padx=5)

        # --- BOTÕES INFERIORES GERAIS ---
        self.btn_frame = ttk.Frame(root)
        ttk.Button(self.btn_frame, text="➕ Add Golpe (Ctrl+Q)", command=self.add_blank_move).pack(side="left", padx=10)
        ttk.Button(self.btn_frame, text="⚡ Ordenar (Ctrl+D)", command=self.organizar_visual).pack(side="left", padx=10)
        ttk.Button(self.btn_frame, text="💾 SALVAR TUDO (Ctrl+S)", command=self.exportar_final).pack(side="left", padx=10)

        self.lbl_status = ttk.Label(root, text="Atalhos: Ctrl+S (Salvar) | Ctrl+Q (Add Golpe) | Ctrl+A (Concluir) | Ctrl+D (Ordenar)", foreground="blue")
        self.lbl_status.pack(side="bottom", pady=5)

    def atualizar_estado_botoes_historico(self):
        # Se tem algo no passado, acende o botão Desfazer
        if len(self.historico_undo) > 0:
            self.btn_undo.config(state=tk.NORMAL)
        else:
            self.btn_undo.config(state=tk.DISABLED)
            
        # Se tem algo no futuro, acende o botão Refazer
        if len(self.historico_redo) > 0:
            self.btn_redo.config(state=tk.NORMAL)
        else:
            self.btn_redo.config(state=tk.DISABLED)

    def selecionar_arquivo(self):
        caminho = filedialog.askopenfilename(filetypes=[("Arquivos CSV", "*.csv")])
        if caminho:
            try:
                self.df_original = pd.read_csv(caminho, sep=',', encoding='utf-8', dtype=str)
                self.df_original = self.df_original.fillna("0")
                
                self.caminho_arquivo = caminho
                self.arquivo_progresso = self.caminho_arquivo.replace('.csv', '_progresso.json')
                self.completed_set = set()
                
                if os.path.exists(self.arquivo_progresso):
                    try:
                        with open(self.arquivo_progresso, 'r', encoding='utf-8') as f:
                            self.completed_set = set(json.load(f))
                    except:
                        pass
                
                self.arquivo_favoritos = self.caminho_arquivo.replace('.csv', '_favoritos.json')
                self.favorites_set = set()
                if os.path.exists(self.arquivo_favoritos):
                    try:
                        with open(self.arquivo_favoritos, 'r', encoding='utf-8') as f:
                            self.favorites_set = set(json.load(f))
                    except: pass

                self.main_frame.pack(fill="both", expand=True)
                self.btn_frame.pack(fill="x", side="bottom", pady=10)
                self.carregar_lista_nomes()
                self.lbl_status.config(text=f"Editando: {os.path.basename(caminho)}", foreground="green")
                messagebox.showinfo("Sucesso", "Arquivo carregado!")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível ler o arquivo:\n{e}")

                self.historico_undo.clear()
                self.historico_redo.clear()
                self.atualizar_estado_botoes_historico()

    def carregar_lista_nomes(self):
        self.lista_formatada = []
        for idx, row in self.df_original.iterrows():
            pid = str(row['ID']).replace('.0', '')
            pname = str(row['Name'])
            self.lista_formatada.append(f"{pid} - {pname}")
            
        self.filtrar_lista()
        self.filtrar_lista_alvo()

    def filtrar_lista(self, *args):
        if self.df_original is None: return
        search = self.search_var.get().upper()
        status_filtro = self.filter_status_var.get()
        
        self.lb_pkmn.delete(0, tk.END)
        for item in self.lista_formatada:
            pname = item.split(" - ", 1)[1]
            is_completed = pname in self.completed_set
            is_favorite = pname in self.favorites_set
            
            if status_filtro == "Mostrar completos" and not is_completed: continue
            if status_filtro == "Mostrar incompletos" and is_completed: continue
            if status_filtro == "Favoritos" and not is_favorite: continue
                
            # Monta os ícones do lado do nome
            prefix = ""
            if is_favorite: prefix += "⭐ "
            if is_completed: prefix += "✅ "
            
            if search in item.upper():
                self.lb_pkmn.insert(tk.END, prefix + item)

    def filtrar_lista_alvo(self, *args):
        if self.df_original is None: return
        search = self.search_alvo_var.get().upper()
        status_filtro = self.filter_alvo_status_var.get() # Lê a opção escolhida no novo filtro
        
        self.lb_alvo.delete(0, tk.END)
        for item in self.lista_formatada:
            pname = item.split(" - ", 1)[1]
            is_completed = pname in self.completed_set
            is_favorite = pname in self.favorites_set

            if status_filtro == "Mostrar completos" and not is_completed: continue
            if status_filtro == "Mostrar incompletos" and is_completed: continue
            if status_filtro == "Favoritos" and not is_favorite: continue
            
            # Monta os ícones do lado do nome
            prefix = ""
            if is_favorite: prefix += "⭐ "
            if is_completed: prefix += "✅ "
            
            if search in item.upper():
                self.lb_alvo.insert(tk.END, prefix + item)

    def restaurar_selecao_lista(self):
        if not self.pokemon_atual: return
        itens = self.lb_pkmn.get(0, tk.END)
        for i, item in enumerate(itens):
            nome = item.replace("✅ ", "").replace("⭐ ", "").split(" - ", 1)[1]
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
        
        if self.is_completed_var.get():
            self.completed_set.add(self.pokemon_atual)
        else:
            self.completed_set.discard(self.pokemon_atual)
            
        if self.arquivo_progresso:
            with open(self.arquivo_progresso, 'w', encoding='utf-8') as f:
                json.dump(list(self.completed_set), f)
                
        self.filtrar_lista()
        self.filtrar_lista_alvo()
        self.restaurar_selecao_lista()
        self.lb_pkmn.focus_set()

    def toggle_favorite_atalho(self, event=None):
        if not self.pokemon_atual: return
        self.is_favorite_var.set(not self.is_favorite_var.get())
        self.toggle_favorite()

    def toggle_favorite(self):
        if not self.pokemon_atual: return
        
        if self.is_favorite_var.get():
            self.favorites_set.add(self.pokemon_atual)
        else:
            self.favorites_set.discard(self.pokemon_atual)
            
        if self.arquivo_favoritos:
            with open(self.arquivo_favoritos, 'w', encoding='utf-8') as f:
                json.dump(list(self.favorites_set), f)
                
        self.filtrar_lista()
        if hasattr(self, 'filtrar_lista_alvo'): # Para a lista do alvo, se houver
            self.filtrar_lista_alvo()
        self.restaurar_selecao_lista()
        self.lb_pkmn.focus_set()
    
    def obter_campos_edicao(self, container):
        campos = []
        for child in container.winfo_children():
            # Adicionei tk.Spinbox e ttk.Spinbox caso seus levels usem isso
            if isinstance(child, (tk.Entry, ttk.Entry, ttk.Combobox, tk.Spinbox, ttk.Spinbox)):
                try:
                    if str(child.cget('state')) != 'disabled':
                        campos.append(child)
                except:
                    campos.append(child)
            campos.extend(self.obter_campos_edicao(child))
        return campos
    
    def focar_primeiro_campo(self, event=None):
        campos = self.obter_campos_edicao(self.frame_edit)
        if campos:
            # O "Pulo do Gato": Ordena fisicamente pela posição na tela (Y: cima pra baixo, X: esq pra dir)
            campos.sort(key=lambda w: (w.winfo_rooty(), w.winfo_rootx()))
            
            campos[0].focus_set()
            try:
                campos[0].select_range(0, tk.END)
            except: pass
        return "break"

    def obter_spinboxes_leveis(self, container):
        campos = []
        for child in container.winfo_children():
            # Filtra APENAS Spinbox (ignorando os Combobox e Entry dos ataques)
            if isinstance(child, (tk.Spinbox, ttk.Spinbox)):
                try:
                    if str(child.cget('state')) != 'disabled':
                        campos.append(child)
                except:
                    campos.append(child)
            campos.extend(self.obter_spinboxes_leveis(child))
        return campos

    def navegar_leveis(self, direcao, event=None):
        # "direcao" será 1 (para baixo) ou -1 (para cima)
        campos = self.obter_spinboxes_leveis(self.frame_edit)
        if not campos: return "break"

        # Ordena geometricamente para respeitar a tela (cima pra baixo)
        campos.sort(key=lambda w: (w.winfo_rooty(), w.winfo_rootx()))

        foco_atual = self.root.focus_get()

        if foco_atual in campos:
            indice_atual = campos.index(foco_atual)
            # A mágica da matemática: se for -1 e estiver no topo, ele vai pro final da lista!
            proximo_indice = (indice_atual + direcao) % len(campos)
            campos[proximo_indice].focus_set()
            
            try:
                campos[proximo_indice].select_range(0, tk.END)
            except: pass
        else:
            # O "Else" que você pediu de volta: Se não estiver num Level, pula pro 1º Level!
            campos[0].focus_set()
            try:
                campos[0].select_range(0, tk.END)
            except: pass
            
        return "break"

    def salvar_em_memoria(self):
        if self.df_original is None or self.pokemon_atual is None:
            return

        golpes_tela = []
        for w in self.scroll_frame.winfo_children():
            ents = [e for e in w.winfo_children() if isinstance(e, (tk.Entry, tk.Spinbox))]
            if len(ents) >= 2:
                m = str(ents[0].get()).strip()
                l = str(ents[1].get()).strip()
                if m != "":
                    golpes_tela.append((m, l))
        
        golpes_tela.sort(key=lambda x: int(x[1]) if x[1].isdigit() else 0)

        idx = self.df_original.index[self.df_original['Name'] == self.pokemon_atual][0]
        nova_row = [str(self.df_original.at[idx, 'ID']), str(self.df_original.at[idx, 'Name'])]
        
        for m, l in golpes_tela:
            nova_row.extend([m, l])
            
        while len(nova_row) < len(self.df_original.columns):
            nova_row.extend(["0", "0"])
        
        self.df_original.iloc[idx] = nova_row[:len(self.df_original.columns)]

    def atualizar_contador_golpes(self):
        if not self.pokemon_atual: return
        
        count = 0
        for w in self.scroll_frame.winfo_children():
            if w.winfo_exists():
                ents = [e for e in w.winfo_children() if isinstance(e, (tk.Entry, tk.Spinbox))]
                if len(ents) >= 2 and ents[0].get().strip() != "":
                    count += 1
                    
        if count > 20:
            self.lbl_aviso_limite.config(text=f"⚠️ AVISO: {count} golpes! (Limite de 20 ultrapassado)", foreground="red")
        else:
            self.lbl_aviso_limite.config(text=f"Total de golpes: {count}/20", foreground="blue")

    def trocar_pokemon(self, event):
        if not self.lb_pkmn.curselection(): return
        
        if self.pokemon_atual:
            self.salvar_em_memoria()
            
        selecionado = self.lb_pkmn.get(self.lb_pkmn.curselection())
        selecionado = selecionado.replace("✅ ", "").replace("⭐ ", "") 
        nome = selecionado.split(" - ", 1)[1]
        
        self.pokemon_atual = nome
        self.lbl_nome.config(text=f"Editando: {nome}")
        
        self.chk_completed.pack(pady=(0, 10))
        self.is_completed_var.set(nome in self.completed_set)

        self.chk_favorite.pack(pady=(0, 10))
        self.is_favorite_var.set(nome in self.favorites_set)
        
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        linha = self.df_original[self.df_original['Name'] == nome].iloc[0]
        for i in range(2, len(self.df_original.columns), 2):
            move = linha.iloc[i]
            lvl = linha.iloc[i+1]
            if move != '0' and move != 0 and pd.notna(move):
                self.criar_linha_ui(move, lvl)
                
        self.esconder_painel_copia()
        self.atualizar_contador_golpes()

    def recarregar_ui_atual(self):
        # Se não tiver nenhum Pokémon selecionado, não faz nada
        if not self.pokemon_atual: return
        
        # Limpa todos os golpes da tela
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Puxa os dados da "máquina do tempo" (do DataFrame) e recria as linhas
        linha = self.df_original[self.df_original['Name'] == self.pokemon_atual].iloc[0]
        for i in range(2, len(self.df_original.columns), 2):
            move = linha.iloc[i]
            lvl = linha.iloc[i+1]
            if move != '0' and move != 0 and pd.notna(move):
                self.criar_linha_ui(move, lvl)
                
        # Atualiza os visuais
        self.atualizar_contador_golpes()
        self.destacar_duplicatas()

    def destacar_duplicatas(self, *args):
        level_entries = []
        move_entries = []
        level_counts = {}
        move_counts = {}
        
        for w in self.scroll_frame.winfo_children():
            if not w.winfo_exists(): continue
            ents = [e for e in w.winfo_children() if isinstance(e, (tk.Entry, tk.Spinbox))]
            if len(ents) >= 2:
                m_entry = ents[0]
                l_entry = ents[1]
                
                m_val = m_entry.get().strip()
                l_val = l_entry.get().strip()
                
                move_entries.append((m_entry, m_val))
                level_entries.append((l_entry, l_val))
                
                if l_val != "":
                    level_counts[l_val] = level_counts.get(l_val, 0) + 1
                    
                if m_val not in ["", "0", "NOVO_GOLPE"]:
                    move_counts[m_val] = move_counts.get(m_val, 0) + 1

        for i in range(len(level_entries)):
            l_entry, l_val = level_entries[i]
            m_entry, m_val = move_entries[i]
            
            if l_val == "1" and level_counts.get("1", 0) >= 5:
                l_entry.config(bg="cyan")
            elif l_val not in ["1", "0", ""] and level_counts.get(l_val, 0) > 1:
                l_entry.config(bg="#ffb3b3")
            else:
                l_entry.config(bg="white")
                
            if m_val not in ["", "0", "NOVO_GOLPE"] and move_counts.get(m_val, 0) > 1:
                m_entry.config(bg="yellow")
            else:
                m_entry.config(bg="white")

    def deletar_golpe(self, frame):
        self.salvar_estado_para_desfazer()
        frame.destroy()
        self.root.after(10, self.destacar_duplicatas)
        self.root.after(10, self.atualizar_contador_golpes)
        self.lb_pkmn.focus_set()

    def alterar_valor_spinbox(self, widget, incremento, event=None):
        self.salvar_estado_para_desfazer()
        try:
            # Pega o texto atual e transforma em número
            valor_atual = int(widget.get())
            novo_valor = valor_atual + incremento
            
            # Trava nos limites lógicos (0 a 100)
            if novo_valor > 100: novo_valor = 100
            if novo_valor < 0: novo_valor = 0
            
            # Apaga o antigo e insere o novo
            widget.delete(0, tk.END)
            widget.insert(0, str(novo_valor))
            
            # Atualiza o visual de duplicatas, já que o número mudou
            self.destacar_duplicatas()
            
        except ValueError:
            pass # Se por acaso a caixa estiver vazia, não faz nada e não dá erro
            
        return "break" # Impede que o evento se espalhe


    def criar_linha_ui(self, move, lvl):
        f = ttk.Frame(self.scroll_frame)
        f.pack(fill="x", pady=2)
        
        m_entry = tk.Entry(f, width=25)
        m_entry.insert(0, move)
        m_entry.pack(side="left", padx=2)
        
        # Aqui está a mágica do Spinbox!
        l_entry = tk.Spinbox(f, from_=0, to=100, width=5, 
                             command=lambda: self.root.after(10, self.destacar_duplicatas))
        l_entry.delete(0, tk.END)
        l_entry.insert(0, lvl)
        l_entry.pack(side="left", padx=2)
        
        # ✨ A MÁGICA DA INVERSÃO ✨
        
        # 1. Setas SOZINHAS agora navegam! (e retornam 'break' para não mudar o valor)
        l_entry.bind('<Up>', lambda e: self.navegar_leveis(-1))
        l_entry.bind('<Down>', lambda e: self.navegar_leveis(1))
        
        # 2. Ctrl + Setas agora mudam o valor da caixa (chamando a nossa nova função)
        # Atenção ao "w=l_entry" no lambda: isso garante que ele altere a caixa certa!
        l_entry.bind('<Control-Up>', lambda e, w=l_entry: self.alterar_valor_spinbox(w, 1))
        l_entry.bind('<Control-Down>', lambda e, w=l_entry: self.alterar_valor_spinbox(w, -1))
        m_entry.bind('<KeyRelease>', self.destacar_duplicatas)
        l_entry.bind('<KeyRelease>', self.destacar_duplicatas)

        # Atalho para deletar a linha inteira ao apertar a tecla Delete na Spinbox
        l_entry.bind('<Delete>', lambda e, f=f: self.confirmar_delecao_atalho(f))

        # ---> CÓDIGO NOVO: Volta o foco para a lista principal ao apertar Enter <---
        m_entry.bind('<Return>', lambda e: self.lb_pkmn.focus_set())
        l_entry.bind('<Return>', lambda e: self.lb_pkmn.focus_set())
        # -------------------------------------------------------------------------
        
        btn_container = ttk.Frame(f)
        btn_container.pack(side="right")

        ttk.Button(btn_container, text="📋 Copiar", width=9, 
                   command=lambda m=m_entry, l=l_entry: self.iniciar_copia(m.get(), l.get())).pack(side="left", padx=2)
        
        ttk.Button(btn_container, text="🗑️", width=3, 
                   command=lambda: self.deletar_golpe(f)).pack(side="left")
        
        self.destacar_duplicatas()
    
    def confirmar_delecao_atalho(self, frame_da_linha, event=None):
        resposta = messagebox.askyesno("Confirmar Exclusão", "Deseja realmente deletar este golpe?")
        
        if resposta:
            self.deletar_golpe(frame_da_linha)
            # Espera 50 milissegundos para o Frame ser destruído, depois foca no próximo level disponível
            self.root.after(50, lambda: self.navegar_leveis(1)) 
            
        return "break"

    def iniciar_copia(self, move, lvl):
        move = move.strip()
        lvl = lvl.strip()
        
        if not move or move == "NOVO_GOLPE" or move == "0":
            messagebox.showwarning("Aviso", "Edite o nome do golpe para algo válido antes de copiar.")
            return
            
        self.salvar_em_memoria()
        self.move_copia_atual = ("COPIAR_UM", move, lvl)
        
        self.lbl_alvo_titulo.config(text=f"Copiando:\n'{move}' (Lvl {lvl})\n⬇️ Clique no Destino ⬇️")
        self.frame_alvo.pack(side="right", fill="y", padx=10, pady=10)
        self.search_alvo_var.set("")
        self.ent_search_alvo.focus_set()

    def iniciar_copia_todos(self):
        if not self.pokemon_atual: return
        self.salvar_em_memoria()
        
        golpes_para_copiar = []
        for w in self.scroll_frame.winfo_children():
            ents = [e for e in w.winfo_children() if isinstance(e, (tk.Entry, tk.Spinbox))]
            if len(ents) >= 2:
                m = ents[0].get().strip()
                l = ents[1].get().strip()
                if m != "" and m != "0" and m != "NOVO_GOLPE":
                    golpes_para_copiar.append((m, l))
                    
        if not golpes_para_copiar:
            messagebox.showwarning("Aviso", "Não há golpes válidos para copiar.")
            return
            
        self.move_copia_atual = ("COPIAR_TODOS", golpes_para_copiar)
        
        self.lbl_alvo_titulo.config(text=f"Copiando TODOS ({len(golpes_para_copiar)} golpes)\n⬇️ Clique no Destino ⬇️")
        self.frame_alvo.pack(side="right", fill="y", padx=10, pady=10)
        self.search_alvo_var.set("")
        self.ent_search_alvo.focus_set()

    def esconder_painel_copia(self):
        self.frame_alvo.pack_forget()
        self.move_copia_atual = None
        self.lb_alvo.selection_clear(0, tk.END)
        self.lb_pkmn.focus_set()

    def confirmar_copia_lista(self, event):
        if not self.lb_alvo.curselection() or not self.move_copia_atual:
            return
            
        selecionado = self.lb_alvo.get(self.lb_alvo.curselection())
        selecionado = selecionado.replace("✅ ", "").replace("⭐ ", "") 
        target_name = selecionado.split(" - ", 1)[1]
        
        tipo_copia = self.move_copia_atual[0]
        
        if tipo_copia == "COPIAR_TODOS":
            lista_golpes = self.move_copia_atual[1]
            self.executar_copia_todos(lista_golpes, target_name)
        elif tipo_copia == "COPIAR_UM":
            move = self.move_copia_atual[1]
            lvl = self.move_copia_atual[2]
            self.executar_copia(move, lvl, target_name)
            
        self.esconder_painel_copia()

    def executar_copia(self, move, lvl, target_pokemon):
        self.salvar_estado_para_desfazer()
        try:
            idx = self.df_original.index[self.df_original['Name'] == target_pokemon][0]
            linha = self.df_original.iloc[idx]
            
            golpes_alvo = []
            for i in range(2, len(self.df_original.columns), 2):
                m = str(linha.iloc[i]).strip()
                l = str(linha.iloc[i+1]).strip()
                if m != '0' and m != '' and pd.notna(m):
                    golpes_alvo.append((m, l))

            if (move, lvl) in golpes_alvo:
                messagebox.showinfo("Aviso", f"O {target_pokemon} já possui o golpe '{move}' exatamente no level {lvl}! A cópia foi cancelada para evitar duplicação.")
                self.lb_pkmn.focus_set()
                return
                    
            max_moves = (len(self.df_original.columns) - 2) // 2
            if len(golpes_alvo) >= max_moves:
                messagebox.showwarning("Limite Atingido", f"O {target_pokemon} já atingiu o limite de colunas da tabela!")
                self.lb_pkmn.focus_set()
                return

            niveis_existentes = [l for _, l in golpes_alvo if l not in ["1", "0"]]
            novo_lvl = lvl
            
            if novo_lvl in niveis_existentes:
                resposta = simpledialog.askstring(
                    "Conflito de Level", 
                    f"Aviso: {target_pokemon} já possui um golpe no level {novo_lvl}!\n\nDigite um NOVO LEVEL para o golpe '{move}'\n(ou clique em Cancelar):"
                )
                
                if resposta is not None and resposta.strip() != "":
                    novo_lvl = resposta.strip()
                    if (move, novo_lvl) in golpes_alvo:
                        messagebox.showinfo("Aviso", f"A cópia foi abortada. {target_pokemon} já possui '{move}' no level {novo_lvl}.")
                        self.lb_pkmn.focus_set()
                        return
                elif resposta is None:
                    self.lb_pkmn.focus_set()
                    return

            golpes_alvo.append((move, novo_lvl))
            golpes_alvo.sort(key=lambda x: int(x[1]) if x[1].isdigit() else 0)
            
            nova_row = [str(self.df_original.at[idx, 'ID']), str(self.df_original.at[idx, 'Name'])]
            for m, l in golpes_alvo:
                nova_row.extend([m, l])
                
            while len(nova_row) < len(self.df_original.columns):
                nova_row.extend(["0", "0"])
                
            self.df_original.iloc[idx] = nova_row[:len(self.df_original.columns)]
            
            if target_pokemon == self.pokemon_atual:
                for widget in self.scroll_frame.winfo_children():
                    widget.destroy()
                for m, l in golpes_alvo:
                    self.criar_linha_ui(m, l)
                self.atualizar_contador_golpes()
                    
            self.lbl_status.config(text=f"✅ '{move}' adicionado a {target_pokemon} no Lvl {novo_lvl}!", foreground="green")
            self.lb_pkmn.focus_set() 
            
        except Exception as e:
            messagebox.showerror("Erro na Cópia", f"Algo deu errado:\n{e}")
            self.lb_pkmn.focus_set()

    def executar_copia_todos(self, golpes_para_copiar, target_pokemon):
        self.salvar_estado_para_desfazer()
        try:
            idx = self.df_original.index[self.df_original['Name'] == target_pokemon][0]
            linha = self.df_original.iloc[idx]
            
            golpes_alvo = []
            nomes_alvo_existentes = []
            
            for i in range(2, len(self.df_original.columns), 2):
                m = str(linha.iloc[i]).strip()
                l = str(linha.iloc[i+1]).strip()
                if m != '0' and m != '' and pd.notna(m):
                    golpes_alvo.append((m, l))
                    nomes_alvo_existentes.append(m)
                    
            max_moves = (len(self.df_original.columns) - 2) // 2
            
            golpes_adicionados = 0
            for move, lvl in golpes_para_copiar:
                if move in nomes_alvo_existentes:
                    continue 

                if len(golpes_alvo) < max_moves:
                    golpes_alvo.append((move, lvl))
                    nomes_alvo_existentes.append(move)
                    golpes_adicionados += 1
                else:
                    messagebox.showwarning("Aviso de Limite", "O Pokémon de destino atingiu o limite máximo de colunas do CSV. Alguns golpes não couberam.")
                    break
                    
            golpes_alvo.sort(key=lambda x: int(x[1]) if x[1].isdigit() else 0)
            
            nova_row = [str(self.df_original.at[idx, 'ID']), str(self.df_original.at[idx, 'Name'])]
            for m, l in golpes_alvo:
                nova_row.extend([m, l])
                
            while len(nova_row) < len(self.df_original.columns):
                nova_row.extend(["0", "0"])
                
            self.df_original.iloc[idx] = nova_row[:len(self.df_original.columns)]
            
            if target_pokemon == self.pokemon_atual:
                for widget in self.scroll_frame.winfo_children():
                    widget.destroy()
                for m, l in golpes_alvo:
                    self.criar_linha_ui(m, l)
                self.atualizar_contador_golpes()
                    
            if golpes_adicionados > 0:
                self.lbl_status.config(text=f"✅ {golpes_adicionados} novos golpes foram colados no {target_pokemon}!", foreground="green")
            else:
                self.lbl_status.config(text=f"Nenhum golpe colado. Todos os golpes já existiam em {target_pokemon}.", foreground="blue")
            
            self.lb_pkmn.focus_set() 
            
        except Exception as e:
            messagebox.showerror("Erro na Cópia", f"Algo deu errado:\n{e}")
            self.lb_pkmn.focus_set()

    def organizar_visual(self):
        if self.df_original is None: return
        self.salvar_estado_para_desfazer() # <--- FOTO ANTES DE REORGANIZAR        
        dados = []
        for w in self.scroll_frame.winfo_children():
            ents = [e for e in w.winfo_children() if isinstance(e, (tk.Entry, tk.Spinbox))]
            if len(ents) >= 2:
                try:
                    dados.append((ents[0].get(), int(ents[1].get())))
                except: continue
        dados.sort(key=lambda x: x[1])
        for w in self.scroll_frame.winfo_children(): w.destroy()
        for m, l in dados: self.criar_linha_ui(m, str(l))
        self.root.after(10, self.atualizar_contador_golpes)

    def add_blank_move(self):
        if self.df_original is not None:
            self.salvar_estado_para_desfazer()
            self.criar_linha_ui("NOVO_GOLPE", "1")
            self.canvas.yview_moveto(1.0)
            self.root.after(10, self.atualizar_contador_golpes)

    def salvar_estado_para_desfazer(self):
        if self.df_original is None: return
        
        # 1. Salva o que está na tela agora no DataFrame
        self.salvar_em_memoria() 
        
        # 2. Limita o histórico para não pesar a RAM
        if len(self.historico_undo) > 20:
            self.historico_undo.pop(0)
            
        # 3. Tira a foto usando a função nativa do Pandas e guarda na gaveta
        self.historico_undo.append(self.df_original.copy())
        
        # 4. Apaga o futuro (se você fez uma ação nova, não dá pra refazer a antiga)
        self.historico_redo.clear()

        # ---> ATUALIZA OS BOTÕES AQUI <---
        self.atualizar_estado_botoes_historico()

    def executar_ctrl_z(self, event=None):
        if not self.historico_undo: return "break"
        
        # Salva o estado atual (erro) no Redo
        self.salvar_em_memoria()
        self.historico_redo.append(self.df_original.copy())
        
        # Puxa o passado e substitui o cérebro do programa
        estado_anterior = self.historico_undo.pop()
        self.df_original = estado_anterior.copy()
        
        # Redesenha a tela mágica!
        self.recarregar_ui_atual()


        self.atualizar_estado_botoes_historico()
        return "break"

    def executar_ctrl_y(self, event=None):
        if not self.historico_redo: return "break"
        
        # Salva o estado atual no Undo
        self.salvar_em_memoria()
        self.historico_undo.append(self.df_original.copy())
        
        # Puxa o futuro e substitui
        estado_futuro = self.historico_redo.pop()
        self.df_original = estado_futuro.copy()
        
        self.recarregar_ui_atual()

        self.atualizar_estado_botoes_historico()
        return "break"

    def exportar_final(self):
        if self.df_original is None: return
        self.salvar_em_memoria()
        try:
            self.df_original.to_csv(self.caminho_arquivo, index=False)
            agora = pd.Timestamp.now().strftime('%H:%M:%S')
            self.lbl_status.config(text=f"✅ Salvo no arquivo com sucesso às {agora}!", foreground="green")
        except Exception as e:
            messagebox.showerror("Erro ao gravar", f"Erro: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PokemonEditor(root)
    root.mainloop()