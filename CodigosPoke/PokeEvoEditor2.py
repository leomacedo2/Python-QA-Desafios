import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import os
import json
import threading
import requests
from io import BytesIO
from PIL import Image

# Configuração Padrão do Tema Escuro
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PokeEvoEditor:
    def __init__(self, root):
        self.root = root
        self.df_original = None
        self.caminho_arquivo = None
        self.arquivo_progresso = None
        self.pokemon_atual = None
        self.membro_em_edicao = None
        self.completed_set = set()
        self.cache_sprites = {} 
        
        self.grafo_familia = {}
        self.grafo_direcionado = {}
        self.lista_evos_possiveis = []
        self.last_focused_entry = None # Para saber onde carimbar o pokemon
        
        self.root.title("PokeEvo Editor - Edição por Família")
        self.root.geometry("1300x800")

        # Correção dos Atalhos
        self.root.bind('<Control-s>', lambda e: self.exportar_final())
        self.root.bind('<Control-q>', lambda e: self.add_blank_evo())
        self.root.bind('<Control-a>', self.toggle_completed_atalho)
        self.root.bind('<Control-Key-1>', lambda e: self.lb_pkmn.focus_set())

        self.menu_bar = tk.Menu(root)
        self.root.config(menu=self.menu_bar)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Arquivo", menu=self.file_menu)
        self.file_menu.add_command(label="Abrir CSV de Evoluções", command=self.selecionar_arquivo)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Sair", command=root.quit)

        self.main_frame = ctk.CTkFrame(root, fg_color="transparent")
        
        # =============== FRAME 1: LISTA PRINCIPAL (Esquerda) ===============
        self.frame_lista = ctk.CTkFrame(self.main_frame, width=250)
        self.frame_lista.pack(side="left", fill="y", padx=10, pady=10)
        
        ctk.CTkLabel(self.frame_lista, text="Filtro de Status:", font=("Roboto", 12)).pack(pady=(10, 0))
        self.filter_status_var = tk.StringVar(value="Mostrar todos")
        self.combo_filter = ctk.CTkOptionMenu(self.frame_lista, variable=self.filter_status_var, 
                                         values=["Mostrar todos", "Mostrar completos", "Mostrar incompletos"],
                                         command=self.filtrar_lista)
        self.combo_filter.pack(fill="x", padx=10, pady=(0, 10))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filtrar_lista)
        ctk.CTkLabel(self.frame_lista, text="Buscar Pokémon:", font=("Roboto", 12)).pack()
        self.ent_search = ctk.CTkEntry(self.frame_lista, textvariable=self.search_var)
        self.ent_search.pack(fill="x", padx=10, pady=5)

        self.frame_listbox = ctk.CTkFrame(self.frame_lista)
        self.frame_listbox.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.scroll_pkmn = ctk.CTkScrollbar(self.frame_listbox)
        self.scroll_pkmn.pack(side="right", fill="y")
        
        self.lb_pkmn = tk.Listbox(self.frame_listbox, font=("Roboto", 11), bg="#2b2b2b", fg="#e1e1e1",
                                  selectbackground="#1f538d", selectforeground="white", 
                                  borderwidth=0, highlightthickness=0, exportselection=False,
                                  yscrollcommand=self.scroll_pkmn.set)
        self.lb_pkmn.pack(side="left", expand=True, fill="both")
        self.scroll_pkmn.configure(command=self.lb_pkmn.yview)
        self.lb_pkmn.bind('<<ListboxSelect>>', self.trocar_pokemon)

        # =============== FRAME 2: EDIÇÃO (Meio) ===============
        self.frame_edit = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.frame_edit.pack(side="left", expand=True, fill="both", padx=10, pady=10)

        self.header_frame = ctk.CTkFrame(self.frame_edit, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 5))
        
        self.lbl_nome = ctk.CTkLabel(self.header_frame, text="Aguardando arquivo...", font=("Roboto", 20, "bold"), text_color="#1f538d")
        self.lbl_nome.pack(side="left", padx=5)

        self.btn_prox_fam = ctk.CTkButton(self.header_frame, text="Próxima Família ⏭️", command=self.proxima_familia, fg_color="#b8860b", hover_color="#8b6508", width=140)
        self.btn_prox_fam.pack(side="right", padx=5)

        self.btn_prev_fam = ctk.CTkButton(self.header_frame, text="⏮️ Anterior", command=self.familia_anterior, fg_color="#b8860b", hover_color="#8b6508", width=100)
        self.btn_prev_fam.pack(side="right", padx=5)

        self.is_completed_var = tk.BooleanVar()
        self.chk_completed = ctk.CTkCheckBox(self.frame_edit, text="✅ Família Concluída (Ctrl+A)", 
                                            variable=self.is_completed_var, command=self.toggle_completed,
                                            font=("Roboto", 12, "bold"), text_color="#2E8B57", fg_color="#2E8B57")
        self.chk_completed.pack(pady=(0, 10))

        self.scroll_fita_imagens = ctk.CTkScrollableFrame(self.frame_edit, orientation="horizontal", height=150)
        self.scroll_fita_imagens.pack(fill="x", pady=5)

        self.frame_contexto = ctk.CTkFrame(self.frame_edit, fg_color="#2b2b2b")
        self.frame_contexto.pack(fill="x", pady=10)
        self.lbl_contexto = ctk.CTkLabel(self.frame_contexto, text="Selecione um Pokémon para editar.", font=("Roboto", 14))
        self.lbl_contexto.pack(pady=10)

        self.scroll_edicao = ctk.CTkScrollableFrame(self.frame_edit)
        self.scroll_edicao.pack(fill="both", expand=True)

        # =============== FRAME 3: SELEÇÃO RÁPIDA (Direita) ===============
        self.frame_selecao = ctk.CTkFrame(self.main_frame, width=250)
        self.frame_selecao.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(self.frame_selecao, text="Seleção Rápida", font=("Roboto", 14, "bold")).pack(pady=10)
        self.ent_busca_rapida = ctk.CTkEntry(self.frame_selecao, placeholder_text="Filtrar lista...")
        self.ent_busca_rapida.pack(fill="x", padx=10, pady=5)
        self.ent_busca_rapida.bind("<KeyRelease>", self.filtrar_lista_selecao)

        self.lb_selecao = tk.Listbox(self.frame_selecao, font=("Roboto", 10), bg="#1e1e1e", fg="#e1e1e1", 
                                     selectbackground="#b8860b", borderwidth=0, highlightthickness=0)
        self.lb_selecao.pack(expand=True, fill="both", padx=10, pady=10)
        self.lb_selecao.bind("<Double-Button-1>", self.carimbar_pokemon)

        # =============== BOTÕES INFERIORES ===============
        self.btn_frame = ctk.CTkFrame(root, fg_color="transparent")
        
        self.btn_add = ctk.CTkButton(self.btn_frame, text="➕ Add Evo (Ctrl+Q)", command=self.add_blank_evo, fg_color="#1f538d")
        self.btn_add.pack(side="left", padx=10)
        
        self.btn_salvar = ctk.CTkButton(self.btn_frame, text="💾 SALVAR TUDO (Ctrl+S)", command=self.exportar_final, fg_color="#2E8B57")
        self.btn_salvar.pack(side="right", padx=10)

        self.lbl_status = ctk.CTkLabel(root, text="Aguardando arquivo...", text_color="#1f538d")
        self.lbl_status.pack(side="bottom", pady=5)

        self.root.after(200, self.tentar_abrir_ultimo_arquivo)
        self.root.after(250, lambda: self.root.state('zoomed'))
        
        # Handler para salvar estado ao fechar
        self.root.protocol("WM_DELETE_WINDOW", self.ao_fechar_programa)

    # --- FUNÇÕES DA LISTA DE SELEÇÃO DIREITA ---
    def filtrar_lista_selecao(self, event=None):
        busca = self.ent_busca_rapida.get().lower()
        self.lb_selecao.delete(0, tk.END)
        for p in self.lista_evos_possiveis:
            if busca in p.lower():
                self.lb_selecao.insert(tk.END, p)

    def carimbar_pokemon(self, event=None):
        selecao = self.lb_selecao.curselection()
        if selecao and self.last_focused_entry:
            nome_completo = self.lb_selecao.get(selecao[0])
            self.last_focused_entry.delete(0, tk.END)
            self.last_focused_entry.insert(0, nome_completo)

    # =============== MOTOR DE MEMÓRIA ===============
    def salvar_config(self):
        try:
            dados = {"ultimo_csv": self.caminho_arquivo, "ultimo_pokemon": self.pokemon_atual}
            with open("config_pokeevo.json", 'w', encoding='utf-8') as f: json.dump(dados, f)
        except: pass

    def ao_fechar_programa(self):
        """Salva o estado completo antes de fechar"""
        if self.df_original is not None:
            self.salvar_em_memoria()
        self.salvar_config()
        self.root.destroy()

    def tentar_abrir_ultimo_arquivo(self):
        if os.path.exists("config_pokeevo.json"):
            try:
                with open("config_pokeevo.json", 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    path = dados.get("ultimo_csv")
                    if path and os.path.exists(path):
                        self.df_original = pd.read_csv(path, sep=',', encoding='utf-8', dtype=str).fillna("")
                        self.caminho_arquivo = path
                        self.arquivo_progresso = path.replace('.csv', '_progresso.json')
                        self.iniciar_dados_arquivo()
                        # Limpa o campo de busca para garantir que o Pokémon seja encontrado
                        self.search_var.set("")
                        if dados.get("ultimo_pokemon"):
                            self.root.after(200, lambda: self.selecionar_pokemon_automatico(dados.get("ultimo_pokemon")))
            except: pass

    def selecionar_pokemon_automatico(self, nome_pkmn):
        nomes = self.lb_pkmn.get(0, tk.END)
        for i, item in enumerate(nomes):
            nome_limpo = item.replace("✅ ", "").split(" - ", 1)[1] if " - " in item else item
            if nome_limpo == nome_pkmn:
                self.lb_pkmn.selection_clear(0, tk.END)
                self.lb_pkmn.selection_set(i)
                self.lb_pkmn.see(i)
                self.lb_pkmn.event_generate("<<ListboxSelect>>")
                break

    # =============== MOTOR DA API E IMAGENS ===============
    def carregar_sprite_api(self, nome_pokemon, label_widget):
        nome_original = str(nome_pokemon).strip().upper() 

        # --- A OPÇÃO NUCLEAR PARA OS PASSARINHOS TEIMOSOS ---
        if "FARFETCH" in nome_original:
            return "farfetchd"
        
        excecoes = {
            "NIDORANâ™€": "nidoran-f", "NIDORANâ™": "nidoran-m", "NIDORAN♀": "nidoran-f", "NIDORAN♂": "nidoran-m",
            "MR. MIME": "mr-mime", "MIME JR.": "mime-jr",  "FLABÉBÉ": "flabebe",
            "TYPE: NULL": "type-null", "PORYGON-Z": "porygon-z", "HO-OH": "ho-oh",
            "WORMADAM": "wormadam-plant", "SHAYMIN": "shaymin-land", "GIRATINA": "giratina-altered", "DEOXYS": "deoxys-normal",
        }

        if nome_original in excecoes: nome_buscado = excecoes[nome_original]
        else: nome_buscado = str(nome_pokemon).lower().strip().replace(" ", "-").replace(".", "").replace("'", "")

        if nome_buscado in self.cache_sprites:
            self.root.after(0, lambda: self.atualizar_imagem_label(label_widget, self.cache_sprites[nome_buscado]))
            return

        try:
            url_api = f"https://pokeapi.co/api/v2/pokemon/{nome_buscado}"
            resposta = requests.get(url_api, timeout=3)
            if resposta.status_code == 200:
                url_imagem = resposta.json()['sprites']['front_default']
                if url_imagem:
                    resp_img = requests.get(url_imagem)
                    img_dados = Image.open(BytesIO(resp_img.content))
                    img_tk = ctk.CTkImage(light_image=img_dados, dark_image=img_dados, size=(96, 96))
                    self.cache_sprites[nome_buscado] = img_tk
                    self.root.after(0, lambda: self.atualizar_imagem_label(label_widget, img_tk))
                else: self.root.after(0, lambda: self.atualizar_imagem_label(label_widget, None, "Sem img"))
            else: self.root.after(0, lambda: self.atualizar_imagem_label(label_widget, None, "Erro API"))
        except Exception: self.root.after(0, lambda: self.atualizar_imagem_label(label_widget, None, "Sem net"))

    def atualizar_imagem_label(self, label_widget, img_tk, texto=""):
        if not label_widget.winfo_exists(): return
        if img_tk: label_widget.configure(image=img_tk, text="")
        else: label_widget.configure(image=None, text=texto)

    # =============== LÓGICA DE DADOS ===============
    def construir_arvore_familia(self):
        self.grafo_familia = {}
        self.grafo_direcionado = {}
        for idx, row in self.df_original.iterrows():
            nome = str(row['Name']).strip()
            if nome: 
                self.grafo_familia[nome] = set()
                self.grafo_direcionado[nome] = set()
        for idx, row in self.df_original.iterrows():
            nome = str(row['Name']).strip()
            if not nome: continue
            for i in range(1, 7):
                val = str(row.get(f'Evolves To {i}', "")).strip()
                if val and val.lower() != 'nan':
                    alvo = val.split(": ", 1)[1].strip() if ": " in val else val
                    if alvo not in self.grafo_familia: 
                        self.grafo_familia[alvo] = set()
                        self.grafo_direcionado[alvo] = set()
                    self.grafo_familia[nome].add(alvo)
                    self.grafo_familia[alvo].add(nome)
                    self.grafo_direcionado[nome].add(alvo)

    def get_familia(self, nome_inicial):
        visitados = set()
        fila = [nome_inicial]
        while fila:
            at = fila.pop(0)
            if at not in visitados:
                visitados.add(at)
                if at in self.grafo_familia:
                    for v in self.grafo_familia[at]: fila.append(v)
        
        membros = list(visitados)
        tem_pai = {m: False for m in membros}
        for m in membros:
            if m in self.grafo_direcionado:
                for f in self.grafo_direcionado[m]:
                    if f in tem_pai: tem_pai[f] = True
        raizes = [m for m, t in tem_pai.items() if not t]
        
        familia_ord = []
        fila_ord = sorted(raizes)
        visitados_ord = set(fila_ord)
        while fila_ord:
            at = fila_ord.pop(0)
            familia_ord.append(at)
            if at in self.grafo_direcionado:
                filhos = sorted([f for f in self.grafo_direcionado[at] if f in membros and f not in visitados_ord])
                for f in filhos:
                    visitados_ord.add(f)
                    fila_ord.append(f)
        return familia_ord

    def descobrir_quem_evolui_para(self, alvo):
        for idx, row in self.df_original.iterrows():
            for i in range(1, 7):
                val = str(row.get(f'Evolves To {i}', "")).strip()
                if val.endswith(alvo):
                    return str(row['Name']), str(row.get(f'Method {i}', "")), str(row.get(f'Parameter {i}', ""))
        return None, None, None

    # =============== FLUXO DO APP ===============
    def selecionar_arquivo(self):
        caminho = filedialog.askopenfilename(filetypes=[("Arquivos CSV", "*.csv")])
        if caminho:
            try:
                self.df_original = pd.read_csv(caminho, sep=',', encoding='utf-8', dtype=str).fillna("")
                self.caminho_arquivo = caminho
                self.arquivo_progresso = self.caminho_arquivo.replace('.csv', '_progresso.json')
                self.iniciar_dados_arquivo()
                self.salvar_config()
                messagebox.showinfo("Sucesso", "Tabela de Evoluções carregada!")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível ler:\n{e}")

    def iniciar_dados_arquivo(self):
        self.completed_set = set()
        if os.path.exists(self.arquivo_progresso):
            try:
                with open(self.arquivo_progresso, 'r', encoding='utf-8') as f:
                    self.completed_set = set(json.load(f))
            except: pass

        self.lista_evos_possiveis = [""]
        for idx, row in self.df_original.iterrows():
            pid = str(row['ID']).replace('.0', '')
            self.lista_evos_possiveis.append(f"{pid}: {str(row['Name'])}")
        
        # --- ADICIONE ESTAS LINHAS AQUI ---
        self.lb_selecao.delete(0, tk.END)  # Limpa a lista visual
        for p in self.lista_evos_possiveis:
            self.lb_selecao.insert(tk.END, p) # Preenche a lista visual
        # ----------------------------------
        
        self.construir_arvore_familia()
        self.main_frame.pack(fill="both", expand=True)
        self.btn_frame.pack(fill="x", side="bottom", pady=10)
        self.carregar_lista_nomes()
        self.lbl_status.configure(text=f"Editando: {os.path.basename(self.caminho_arquivo)}")

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
            if search in item.upper(): self.lb_pkmn.insert(tk.END, prefix + item)

    def restaurar_selecao_lista(self):
        if not self.pokemon_atual: return
        itens = self.lb_pkmn.get(0, tk.END)
        for i, item in enumerate(itens):
            nome = item.replace("✅ ", "").split(" - ", 1)[1]
            if nome == self.pokemon_atual:
                self.lb_pkmn.selection_clear(0, tk.END)
                self.lb_pkmn.selection_set(i)
                self.lb_pkmn.activate(i)
                return i # Retorna o index encontrado
        return None

    def proxima_familia(self):
        if not self.pokemon_atual: return
        
        familia_atual = set(self.get_familia(self.pokemon_atual))
        nomes_lb = self.lb_pkmn.get(0, tk.END)
        
        idx_atual = -1
        for i, item in enumerate(nomes_lb):
            nome = item.replace("✅ ", "").split(" - ", 1)[1] if " - " in item else item
            if nome == self.pokemon_atual:
                idx_atual = i
                break
                
        if idx_atual == -1: return
        
        # Procura o primeiro Pokémon para baixo que NÃO faz parte da família atual
        for i in range(idx_atual + 1, len(nomes_lb)):
            nome_prox = nomes_lb[i].replace("✅ ", "").split(" - ", 1)[1] if " - " in nomes_lb[i] else nomes_lb[i]
            if nome_prox not in familia_atual:
                self.selecionar_pokemon_automatico(nome_prox)
                return
                
        messagebox.showinfo("Fim da Linha", "Você chegou à última família da lista de visualização atual!")

    def familia_anterior(self):
        if not self.pokemon_atual: return
        
        familia_atual = set(self.get_familia(self.pokemon_atual))
        nomes_lb = self.lb_pkmn.get(0, tk.END)
        
        idx_atual = -1
        for i, item in enumerate(nomes_lb):
            nome = item.replace("✅ ", "").split(" - ", 1)[1] if " - " in item else item
            if nome == self.pokemon_atual:
                idx_atual = i
                break
                
        if idx_atual == -1: return
        
        # Sobe na lista até achar alguém de OUTRA família
        for i in range(idx_atual - 1, -1, -1):
            nome_prev = nomes_lb[i].replace("✅ ", "").split(" - ", 1)[1] if " - " in nomes_lb[i] else nomes_lb[i]
            if nome_prev not in familia_atual:
                # Achamos a família anterior! Vamos procurar a "forma base" dela (o menor ID)
                familia_anterior_set = set(self.get_familia(nome_prev))
                idx_alvo = i
                for j in range(i, -1, -1):
                    nome_j = nomes_lb[j].replace("✅ ", "").split(" - ", 1)[1] if " - " in nomes_lb[j] else nomes_lb[j]
                    if nome_j in familia_anterior_set:
                        idx_alvo = j
                    else:
                        break
                
                nome_final = nomes_lb[idx_alvo].replace("✅ ", "").split(" - ", 1)[1] if " - " in nomes_lb[idx_alvo] else nomes_lb[idx_alvo]
                self.selecionar_pokemon_automatico(nome_final)
                return
                
        messagebox.showinfo("Início da Linha", "Você já está na primeira família da lista!")

    # =============== FUNÇÕES DE EDIÇÃO ===============
    def trocar_pokemon(self, event):
        if not self.lb_pkmn.curselection(): return
        if self.membro_em_edicao: self.salvar_em_memoria()
        selecionado = self.lb_pkmn.get(self.lb_pkmn.curselection())
        nome = selecionado.replace("✅ ", "").split(" - ", 1)[1]
        self.pokemon_atual = nome
        self.salvar_config()
        familia = self.get_familia(nome)
        self.lbl_nome.configure(text=f"Família: {' ➔ '.join(familia)}")
        self.is_completed_var.set(all(m in self.completed_set for m in familia))
        self.desenhar_fita_da_familia(familia)
        self.focar_edicao_no_membro(nome)

    def desenhar_fita_da_familia(self, familia):
        for widget in self.scroll_fita_imagens.winfo_children(): widget.destroy()
            
        for membro in familia:
            card = ctk.CTkFrame(self.scroll_fita_imagens, fg_color="#1f232a", corner_radius=10)
            card.pack(side="left", padx=10, pady=5)
            
            lbl_img = ctk.CTkLabel(card, text="Carregando...", cursor="hand2")
            lbl_img.pack(padx=10, pady=(10,0))
            lbl_img.bind("<Button-1>", lambda e, m=membro: self.focar_edicao_no_membro(m))
            
            lbl_nome = ctk.CTkLabel(card, text=membro, font=("Roboto", 12, "bold"), cursor="hand2")
            lbl_nome.pack(padx=10, pady=(0,10))
            lbl_nome.bind("<Button-1>", lambda e, m=membro: self.focar_edicao_no_membro(m))
            
            threading.Thread(target=self.carregar_sprite_api, args=(membro, lbl_img), daemon=True).start()

    def focar_edicao_no_membro(self, membro):
        if self.membro_em_edicao and self.membro_em_edicao != membro:
            self.salvar_em_memoria() 
            
        self.membro_em_edicao = membro
        
        pai, metodo, param = self.descobrir_quem_evolui_para(membro)
        if pai:
            txt_contexto = f"🧬 {membro} evolui de: {pai} (Método: {metodo} | Parâmetro: {param})"
        else:
            txt_contexto = f"🧬 {membro} é o estágio base (Não evolui de ninguém)."
        self.lbl_contexto.configure(text=txt_contexto, text_color="#e1e1e1")
        
        for widget in self.scroll_edicao.winfo_children(): widget.destroy()
        
        titulo_edicao = ctk.CTkLabel(self.scroll_edicao, text=f"Editando evoluções de: {membro}", font=("Roboto", 16, "bold"), text_color="#ffcc00")
        titulo_edicao.pack(pady=10)
        
        idxs = self.df_original.index[self.df_original['Name'] == membro].tolist()
        if not idxs: return
        linha = self.df_original.iloc[idxs[0]]
        
        for i in range(1, 7):
            col_evo = f'Evolves To {i}'
            if col_evo in self.df_original.columns:
                evo_to = str(linha.get(col_evo, "")).strip()
                method = str(linha.get(f'Method {i}', "")).strip()
                param = str(linha.get(f'Parameter {i}', "")).strip()
                
                if evo_to and evo_to.lower() != 'nan':
                    self.criar_linha_ui(evo_to, method, param)

    def criar_linha_ui(self, evo_to="", method="", param=""):
        f = ctk.CTkFrame(self.scroll_edicao, fg_color="#333333")
        f.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(f, text="Evolui para:").pack(side="left", padx=5)
        e_to = ctk.CTkEntry(f, width=200)
        e_to.insert(0, evo_to)
        e_to.pack(side="left", padx=5)
        e_to.bind("<FocusIn>", lambda e: self.set_last_focus(e_to))
        
        ctk.CTkLabel(f, text="Método:").pack(side="left", padx=5)
        metodos = ["Reach Level", "Use Item", "Trade", "Reach Level (Male)", "Reach Level (Female)", "Happiness"]
        
        def on_method_change(choice):
            if "Reach Level" in choice:
                p = e_par.get().strip()
                if not p.lower().startswith("level"):
                    e_par.delete(0, tk.END)
                    e_par.insert(0, f"Level {p}".strip())

        c_met = ctk.CTkComboBox(f, values=metodos, width=150, command=on_method_change)
        c_met.set(method)
        c_met.pack(side="left", padx=5)
        
        ctk.CTkLabel(f, text="Par:").pack(side="left", padx=5)
        e_par = ctk.CTkEntry(f, width=100)
        e_par.insert(0, param)
        e_par.pack(side="left", padx=5)
        
        ctk.CTkButton(f, text="🗑️", width=30, fg_color="#8b0000", command=f.destroy).pack(side="right", padx=5)

    def set_last_focus(self, widget):
        self.last_focused_entry = widget

    def add_blank_evo(self):
        if not self.membro_em_edicao:
            messagebox.showwarning("Aviso", "Selecione um Pokémon na lista ou na fita de imagens primeiro!")
            return
            
        count = sum(1 for w in self.scroll_edicao.winfo_children() if isinstance(w, ctk.CTkFrame))
        if count >= 6:
            messagebox.showwarning("Limite", "O arquivo permite no máximo 6 evoluções por Pokémon.")
            return
            
        self.criar_linha_ui("", "Reach Level", "Level ")

    def salvar_em_memoria(self):
        if self.df_original is None or not self.membro_em_edicao: return

        evos_tela = []
        for w in self.scroll_edicao.winfo_children():
            if isinstance(w, ctk.CTkFrame) and w.winfo_exists():
                filhos = w.winfo_children()
                if len(filhos) >= 6:
                    evo_to = filhos[1].get().strip()
                    method = filhos[3].get().strip()
                    param = filhos[5].get().strip()
                    if evo_to != "": evos_tela.append((evo_to, method, param))
        
        evos_tela = evos_tela[:6]

        idxs = self.df_original.index[self.df_original['Name'] == self.membro_em_edicao].tolist()
        if not idxs: return
        idx = idxs[0]
        
        nova_row = [str(self.df_original.at[idx, 'ID']), str(self.df_original.at[idx, 'Name'])]
        for et, m, p in evos_tela: nova_row.extend([et, m, p])
        while len(nova_row) < 20: nova_row.extend(["", "", ""])
        
        self.df_original.iloc[idx] = nova_row[:20]
        self.construir_arvore_familia() # Importante para atualizar conexões em tempo real

    def toggle_completed_atalho(self, event=None):
        if not self.pokemon_atual: return
        self.is_completed_var.set(not self.is_completed_var.get())
        self.toggle_completed()

    def toggle_completed(self):
        if not self.pokemon_atual: return
        familia = self.get_familia(self.pokemon_atual)
        
        # NOVO: Salva a posição exata da sua barra de rolagem!
        try:
            y_view = self.lb_pkmn.yview()
        except Exception:
            y_view = (0.0, 1.0)
            
        if self.is_completed_var.get():
            for m in familia: self.completed_set.add(m)
        else:
            for m in familia: self.completed_set.discard(m)
            
        if self.arquivo_progresso:
            with open(self.arquivo_progresso, 'w', encoding='utf-8') as f:
                json.dump(list(self.completed_set), f)
                
        self.filtrar_lista()
        
        # NOVO: Restaura a rolagem depois de atualizar a lista. Adeus pulo pro Bulbasaur!
        try:
            self.lb_pkmn.yview_moveto(y_view[0])
        except Exception: pass
            
        self.restaurar_selecao_lista()
        self.lb_pkmn.focus_set()

    def exportar_final(self):
        if self.df_original is None: return
        self.salvar_em_memoria()
        try:
            self.df_original.to_csv(self.caminho_arquivo, index=False)
            agora = pd.Timestamp.now().strftime('%H:%M:%S')
            self.lbl_status.configure(text=f"✅ Evoluções salvas com sucesso às {agora}!", text_color="#2E8B57")
        except Exception as e:
            messagebox.showerror("Erro ao gravar", f"Erro: {e}")

if __name__ == "__main__":
    root = ctk.CTk()
    app = PokeEvoEditor(root)
    root.mainloop()