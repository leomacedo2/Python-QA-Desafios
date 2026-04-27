import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import customtkinter as ctk
import pandas as pd
import os
import json
import copy
import requests
import threading
from io import BytesIO
from PIL import Image

# Configuração do Tema Moderno
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

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
        self.frame_controle_copia_visivel = False
        
        # Caches para não gastar internet à toa
        self.cache_sprites = {} 
        self.cache_familias = {}
        
        self.root.title("PokeMove Editor Pro")
        self.root.geometry("1200x800")
        self.root.state('zoomed')

        # --- BARRA DE FERRAMENTAS SUPERIOR (CABEÇALHO) ---
        self.toolbar_frame = ctk.CTkFrame(root, corner_radius=0, fg_color="transparent")
        self.toolbar_frame.pack(side="top", fill="x", padx=10, pady=5)

        self.btn_undo = ctk.CTkButton(self.toolbar_frame, text="↩️ Desfazer", state="disabled", command=self.executar_ctrl_z, width=100)
        self.btn_undo.pack(side="left", padx=5)

        self.btn_redo = ctk.CTkButton(self.toolbar_frame, text="↪️ Refazer", state="disabled", command=self.executar_ctrl_y, width=100)
        self.btn_redo.pack(side="left", padx=5)

        # --- ATALHOS DE TECLADO --
        self.root.bind('<Control-s>', lambda e: self.exportar_final())
        self.root.bind('<Control-w>', lambda e: self.add_blank_move())
        self.root.bind('<Control-d>', lambda e: self.organizar_visual())
        self.root.bind('<Control-f>', lambda e: self.ent_search.focus_set())
        self.root.bind('<Control-a>', self.toggle_completed_atalho)
        self.root.bind('<Control-q>', self.toggle_favorite_atalho)
        self.root.bind('<Control-z>', self.executar_ctrl_z)
        self.root.bind('<Control-y>', self.executar_ctrl_y)
        self.root.bind('<Alt-Right>', lambda e: self.navegar_familia(1))
        self.root.bind('<Alt-Left>', lambda e: self.navegar_familia(-1))
        self.root.bind('<Control-Up>', lambda e: self.navegar_leveis(-1)) 
        self.root.bind('<Control-Down>', lambda e: self.navegar_leveis(1))
        self.root.bind('<Control-Left>', lambda e: self.navegar_familia(-1))
        self.root.bind('<Control-Right>', lambda e: self.navegar_familia(1))
        self.root.bind('<Control-Key-0>', lambda e: self.organizar_visual())
        self.root.bind('<Control-Key-1>', lambda e: self.lb_pkmn.focus_set())
        self.root.bind('<Control-Key-2>', self.toggle_completed_atalho)
        self.root.bind('<Control-Key-3>', lambda e: self.ent_search.focus_set())
        self.root.bind('<Control-Key-4>', lambda e: self.iniciar_copia_todos())
        self.root.bind('<Control-Key-5>', lambda e: self.exportar_final())
        self.root.bind('<Control-Key-8>', self.toggle_favorite_atalho)

        # --- MENU SUPERIOR ---
        self.menu_bar = tk.Menu(root, bg="#2b2b2b", fg="white")
        self.root.config(menu=self.menu_bar)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0, bg="#2b2b2b", fg="white")
        self.menu_bar.add_cascade(label="Arquivo", menu=self.file_menu)
        self.file_menu.add_command(label="Abrir CSV (Original ou Editado)", command=self.selecionar_arquivo)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Sair", command=root.quit)

        self.main_frame = ctk.CTkFrame(root, fg_color="transparent")
        
        # --- FRAME 1: LISTA PRINCIPAL (Esquerda) ---
        self.frame_lista = ctk.CTkFrame(self.main_frame, width=250)
        self.frame_lista.pack(side="left", fill="y", padx=10, pady=10)
        
        ctk.CTkLabel(self.frame_lista, text="Filtro de Status:", font=("Roboto", 12, "bold")).pack(pady=(10,0))
        self.filter_status_var = tk.StringVar(value="Mostrar todos")
        self.combo_filter = ctk.CTkComboBox(self.frame_lista, variable=self.filter_status_var, 
                                            values=["Mostrar todos", "Mostrar completos", "Mostrar incompletos", "Favoritos"],
                                            command=self.filtrar_lista, state="readonly")
        self.combo_filter.pack(fill="x", padx=10, pady=5)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filtrar_lista)
        ctk.CTkLabel(self.frame_lista, text="Buscar Pokémon:", font=("Roboto", 12, "bold")).pack()
        self.ent_search = ctk.CTkEntry(self.frame_lista, textvariable=self.search_var, placeholder_text="Digite o nome...")
        self.ent_search.pack(fill="x", padx=10, pady=5)

        self.frame_lista_scroll = ctk.CTkFrame(self.frame_lista, fg_color="transparent")
        self.frame_lista_scroll.pack(expand=True, fill="both", padx=10, pady=10)

        self.scroll_pkmn = ctk.CTkScrollbar(self.frame_lista_scroll)
        self.scroll_pkmn.pack(side="right", fill="y")

        self.lb_pkmn = tk.Listbox(self.frame_lista_scroll, width=25, font=("Roboto", 11), 
                                  bg="#2b2b2b", fg="#e1e1e1", selectbackground="#1f538d", 
                                  selectforeground="white", borderwidth=0, highlightthickness=0,
                                  yscrollcommand=self.scroll_pkmn.set)
        self.lb_pkmn.pack(side="left", expand=True, fill="both")
        self.scroll_pkmn.configure(command=self.lb_pkmn.yview)
        self.lb_pkmn.bind('<<ListboxSelect>>', self.trocar_pokemon)
        self.lb_pkmn.bind('<Control-Up>', lambda e: self.navegar_leveis(-1))
        self.lb_pkmn.bind('<Control-Down>', lambda e: self.navegar_leveis(1))

        # --- FRAME 3: LISTA ALVO PARA COPIAR (Direita) ---
        self.frame_alvo = ctk.CTkFrame(self.main_frame, width=250)
        self.lbl_alvo_titulo = ctk.CTkLabel(self.frame_alvo, text="Selecione o Destino:", font=("Roboto", 12, "bold"), text_color="#A984E5")
        self.lbl_alvo_titulo.pack(pady=(10,5))
        
        ctk.CTkLabel(self.frame_alvo, text="Filtro de Status:", font=("Roboto", 12, "bold")).pack()
        self.filter_alvo_status_var = tk.StringVar(value="Mostrar todos")
        self.combo_filter_alvo = ctk.CTkComboBox(self.frame_alvo, variable=self.filter_alvo_status_var, 
                                                 values=["Mostrar todos", "Mostrar completos", "Mostrar incompletos", "Favoritos"], 
                                                 command=self.filtrar_lista_alvo, state="readonly")
        self.combo_filter_alvo.pack(fill="x", padx=10, pady=5)

        self.search_alvo_var = tk.StringVar()
        self.search_alvo_var.trace("w", self.filtrar_lista_alvo)
        ctk.CTkLabel(self.frame_alvo, text="Buscar Destino:", font=("Roboto", 12, "bold")).pack()
        self.ent_search_alvo = ctk.CTkEntry(self.frame_alvo, textvariable=self.search_alvo_var, placeholder_text="Digite o destino...")
        self.ent_search_alvo.pack(fill="x", padx=10, pady=5)

        self.frame_alvo_scroll = ctk.CTkFrame(self.frame_alvo, fg_color="transparent")
        self.frame_alvo_scroll.pack(expand=True, fill="both", padx=10, pady=10)

        self.scroll_alvo = ctk.CTkScrollbar(self.frame_alvo_scroll)
        self.scroll_alvo.pack(side="right", fill="y")

        self.lb_alvo = tk.Listbox(self.frame_alvo_scroll, width=25, font=("Roboto", 11), 
                                  bg="#2b2b2b", fg="#e1e1e1", selectbackground="#1f538d", 
                                  selectforeground="white", borderwidth=0, highlightthickness=0,
                                  yscrollcommand=self.scroll_alvo.set)
        self.lb_alvo.pack(side="left", expand=True, fill="both")
        self.scroll_alvo.configure(command=self.lb_alvo.yview)
        self.lb_alvo.bind('<<ListboxSelect>>', self.confirmar_copia_lista)

        ctk.CTkButton(self.frame_alvo, text="❌ Cancelar Cópia", command=self.esconder_painel_copia, fg_color="#C8504B", hover_color="#8A3632").pack(pady=10, padx=10, fill="x")

        # --- FRAME 2: EDIÇÃO (Meio) ---
        self.frame_edit = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.frame_edit.pack(side="left", expand=True, fill="both", padx=15, pady=10)

        self.header_edit_frame = ctk.CTkFrame(self.frame_edit, fg_color="transparent")
        self.header_edit_frame.pack(fill="x", pady=(0, 5))

        self.title_row = ctk.CTkFrame(self.header_edit_frame, fg_color="transparent")
        self.title_row.pack(fill="x", pady=5)
        self.lbl_nome = ctk.CTkLabel(self.title_row, text="Nenhum arquivo carregado", font=("Roboto", 24, "bold"))
        self.lbl_nome.pack(side="left")
        
        # Botão de Próxima Família Corrigido
        self.btn_prox_pkmn = ctk.CTkButton(self.title_row, text="Próxima Família ⏭️", command=self.proxima_familia, fg_color="#b8860b", hover_color="#8b6508", width=120)
        self.btn_prox_pkmn.pack(side="right", padx=5)

        self.btn_prev_pkmn = ctk.CTkButton(self.title_row, text="⏮️ Anterior", command=self.familia_anterior, fg_color="#b8860b", hover_color="#8b6508", width=100)
        self.btn_prev_pkmn.pack(side="right", padx=5)
        
        # Frame para os controles de cópia (será preenchido quando necessário)
        self.frame_controle_copia = ctk.CTkFrame(self.header_edit_frame, fg_color="transparent")
        # Não é feito pack aqui, será feito quando necessário

        self.switches_frame = ctk.CTkFrame(self.header_edit_frame, fg_color="transparent")
        self.switches_frame.pack(anchor="w", pady=(0, 10))

        self.is_completed_var = tk.BooleanVar()
        self.chk_completed = ctk.CTkSwitch(self.switches_frame, text="✅ Marcar como Concluído", variable=self.is_completed_var, command=self.toggle_completed, font=("Roboto", 12, "bold"), progress_color="#2E8B57")
        self.chk_completed.pack(side="left", padx=(0, 15))
        
        self.is_favorite_var = tk.BooleanVar()
        self.chk_favorite = ctk.CTkSwitch(self.switches_frame, text="⭐ Favoritar", variable=self.is_favorite_var, command=self.toggle_favorite, font=("Roboto", 12, "bold"), progress_color="#FF8C00")
        self.chk_favorite.pack(side="left")

        # NOVA FITA ROLÁVEL DE FAMÍLIA (RIBBON)
        self.scroll_fita_imagens = ctk.CTkScrollableFrame(self.frame_edit, orientation="horizontal", height=130)
        self.scroll_fita_imagens.pack(fill="x", pady=5)

        # --- FRAME DE 3 COLUNAS ---
        self.moves_container = ctk.CTkFrame(self.frame_edit, fg_color="transparent")
        self.moves_container.pack(side="top", fill="both", expand=True, pady=5)

        self.col1 = ctk.CTkFrame(self.moves_container, fg_color="transparent")
        self.col1.pack(side="left", fill="both", expand=True, padx=2)
        self.col2 = ctk.CTkFrame(self.moves_container, fg_color="transparent")
        self.col2.pack(side="left", fill="both", expand=True, padx=2)
        self.col3 = ctk.CTkFrame(self.moves_container, fg_color="transparent")
        self.col3.pack(side="left", fill="both", expand=True, padx=2)

        # --- BARRA INFERIOR ---
        self.bottom_edit_frame = ctk.CTkFrame(self.frame_edit, fg_color="transparent")
        self.bottom_edit_frame.pack(fill="x", pady=10, side="bottom")
        
        self.lbl_aviso_limite = ctk.CTkLabel(self.bottom_edit_frame, text="", font=("Roboto", 12, "bold"))
        self.lbl_aviso_limite.pack(side="left", padx=5)

        self.btn_frame = ctk.CTkFrame(root, fg_color="transparent")
        ctk.CTkButton(self.btn_frame, text="➕ Add Golpe (Ctrl+W)", command=self.add_blank_move, fg_color="#4B0082", hover_color="#300054").pack(side="left", padx=10)
        ctk.CTkButton(self.btn_frame, text="⚡ Ordenar (Ctrl+D)", command=self.organizar_visual, fg_color="#0056b3", hover_color="#004494").pack(side="left", padx=10)
        ctk.CTkButton(self.btn_frame, text="📑 Copiar TODOS", command=self.iniciar_copia_todos, fg_color="#1f538d", hover_color="#14375e").pack(side="left", padx=10)
        ctk.CTkButton(self.btn_frame, text="💾 SALVAR TUDO (Ctrl+S)", command=self.exportar_final, fg_color="#2E8B57", hover_color="#1d5c39").pack(side="left", padx=10)

        self.lbl_status = ctk.CTkLabel(root, text="Aguardando arquivo CSV...", text_color="#1f538d", font=("Roboto", 12, "bold"))
        self.lbl_status.pack(side="bottom", pady=10)

        self.root.after(200, self.tentar_abrir_ultimo_arquivo)
        self.root.after(250, lambda: self.root.state('zoomed'))
        
        # Handler para salvar estado ao fechar
        self.root.protocol("WM_DELETE_WINDOW", self.ao_fechar_programa)

    # =============== MOTOR DA POKÉAPI (FAMÍLIA) ===============
    def traduzir_nome_para_api(self, nome_csv):
        nome_original = str(nome_csv).strip().upper() 

        # --- A OPÇÃO NUCLEAR PARA OS PASSARINHOS TEIMOSOS ---
        if "FARFETCH" in nome_original:
            return "farfetchd"
        
        excecoes = {
            "NIDORANâ™€": "nidoran-f", "NIDORANâ™": "nidoran-m", "NIDORAN♀": "nidoran-f", "NIDORAN♂": "nidoran-m",
            "MR. MIME": "mr-mime", "MIME JR.": "mime-jr",  "FLABÉBÉ": "flabebe",
            "TYPE: NULL": "type-null", "PORYGON-Z": "porygon-z", "HO-OH": "ho-oh",
            "WORMADAM": "wormadam-plant", "SHAYMIN": "shaymin-land", "GIRATINA": "giratina-altered", "DEOXYS": "deoxys-normal",
        }
        if nome_original in excecoes: return excecoes[nome_original]
        return str(nome_csv).lower().strip().replace(" ", "-").replace(".", "").replace("'", "")

    def buscar_familia_api(self, nome_csv):
        nome_api = self.traduzir_nome_para_api(nome_csv)
        familia = [nome_api] 
        
        if nome_api in self.cache_familias:
            familia = self.cache_familias[nome_api]
        else:
            try:
                url_species = f"https://pokeapi.co/api/v2/pokemon-species/{nome_api}"
                resp_species = requests.get(url_species, timeout=3)
                if resp_species.status_code == 200:
                    evo_chain_url = resp_species.json()['evolution_chain']['url']
                    resp_chain = requests.get(evo_chain_url, timeout=3)
                    if resp_chain.status_code == 200:
                        chain_data = resp_chain.json()['chain']
                        familia = self.extrair_nomes_cadeia(chain_data)
                        self.cache_familias[nome_api] = familia
            except: pass
                
        # >>> ADICIONE ESTA LINHA PARA O ATALHO SABER QUEM É A FAMÍLIA <<<
        self.familia_atual_api_nomes = familia
        
        self.root.after(0, lambda: self.desenhar_fita_da_familia(familia, nome_csv))

    def extrair_nomes_cadeia(self, node):
        nomes = []
        try:
            # Trava o ID máximo para 493 (Até a 4ª Geração / Sinnoh)
            url = node['species']['url']
            pkmn_id = int(url.strip('/').split('/')[-1])
            if pkmn_id <= 493:
                nomes.append(node['species']['name'])
        except:
            nomes.append(node['species']['name']) # Fallback de segurança

        for evolucao in node['evolves_to']:
            nomes.extend(self.extrair_nomes_cadeia(evolucao))
        return nomes

    def desenhar_fita_da_familia(self, familia, nome_original_csv):
        # Desliga a cópia de família caso esteja ativa e recria os widgets
        if hasattr(self, 'cancelar_copia_familia'):
            self.cancelar_copia_familia()
        for widget in self.scroll_fita_imagens.winfo_children(): widget.destroy()
            
        for membro_api in familia:
            is_atual = (membro_api == self.traduzir_nome_para_api(nome_original_csv))
            cor_fundo = "#1f538d" if is_atual else "#1f232a"
            
            card = ctk.CTkFrame(self.scroll_fita_imagens, fg_color=cor_fundo, corner_radius=10)
            card.pack(side="left", padx=10, pady=5)
            card.membro_nome = membro_api  # Armazena o nome do membro
            
            lbl_img = ctk.CTkLabel(card, text="...", cursor="hand2")
            lbl_img.pack(padx=10, pady=(10,0))
            lbl_img.bind("<Button-1>", lambda e, m=membro_api: self.clicar_parente(m))
            
            lbl_nome = ctk.CTkLabel(card, text=membro_api.capitalize(), font=("Roboto", 12, "bold"), cursor="hand2")
            lbl_nome.pack(padx=10, pady=(0,5))
            lbl_nome.bind("<Button-1>", lambda e, m=membro_api: self.clicar_parente(m))
            
            threading.Thread(target=self.carregar_sprite_api_card, args=(membro_api, lbl_img), daemon=True).start()

    def carregar_sprite_api_card(self, nome_buscado, label_widget):
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
                    img_tk = ctk.CTkImage(light_image=img_dados, dark_image=img_dados, size=(72, 72))
                    self.cache_sprites[nome_buscado] = img_tk
                    self.root.after(0, lambda: self.atualizar_imagem_label(label_widget, img_tk))
                else: self.root.after(0, lambda: self.atualizar_imagem_label(label_widget, None, "Sem img")) 
            else: self.root.after(0, lambda: self.atualizar_imagem_label(label_widget, None, "Erro API")) 
        except: self.root.after(0, lambda: self.atualizar_imagem_label(label_widget, None, "Sem net"))

    def atualizar_imagem_label(self, label_widget, img_tk, texto=""):
        if not label_widget.winfo_exists(): return
        if img_tk: label_widget.configure(image=img_tk, text="")
        else: label_widget.configure(image=None, text=texto)

    def clicar_parente(self, nome_api):
        nomes = self.lb_pkmn.get(0, tk.END)
        for item in nomes:
            nome_limpo = item.replace("✅ ", "").replace("⭐ ", "").split(" - ", 1)[1]
            if self.traduzir_nome_para_api(nome_limpo) == nome_api:
                self.selecionar_pokemon_automatico(nome_limpo)
                return
        messagebox.showinfo("Aviso", f"O Pokémon '{nome_api.capitalize()}' não foi encontrado na sua lista do CSV.")

    # =============== FUNÇÕES DE HISTÓRICO ===============
    def atualizar_estado_botoes_historico(self):
        self.btn_undo.configure(state="normal" if len(self.historico_undo) > 0 else "disabled")
        self.btn_redo.configure(state="normal" if len(self.historico_redo) > 0 else "disabled")

    def salvar_estado_para_desfazer(self):
        if self.df_original is None: return
        self.salvar_em_memoria() 
        novo_estado = self.df_original.copy()
        if self.historico_undo and self.historico_undo[-1].equals(novo_estado): return 
        if len(self.historico_undo) > 20: self.historico_undo.pop(0)
        self.historico_undo.append(novo_estado)
        self.historico_redo.clear()
        self.atualizar_estado_botoes_historico()

    def executar_ctrl_z(self, event=None):
        if not self.historico_undo: return "break"
        self.salvar_em_memoria()
        self.historico_redo.append(self.df_original.copy())
        self.df_original = self.historico_undo.pop().copy()
        self.recarregar_ui_atual()
        self.atualizar_estado_botoes_historico()
        return "break"

    def executar_ctrl_y(self, event=None):
        if not self.historico_redo: return "break"
        self.salvar_em_memoria()
        self.historico_undo.append(self.df_original.copy())
        self.df_original = self.historico_redo.pop().copy()
        self.recarregar_ui_atual()
        self.atualizar_estado_botoes_historico()
        return "break"

    # =============== ARQUIVOS E LISTAS ===============
    def selecionar_arquivo(self, caminho_direto=None):
        if caminho_direto: caminho = caminho_direto
        else: caminho = filedialog.askopenfilename(filetypes=[("Arquivos CSV", "*.csv")])
            
        if caminho:
            try:
                self.df_original = pd.read_csv(caminho, sep=',', encoding='utf-8', dtype=str).fillna("0")
                self.caminho_arquivo = caminho
                self.arquivo_progresso = self.caminho_arquivo.replace('.csv', '_progresso.json')
                
                self.completed_set, self.favorites_set = set(), set()
                if os.path.exists(self.arquivo_progresso):
                    try:
                        with open(self.arquivo_progresso, 'r', encoding='utf-8') as f: self.completed_set = set(json.load(f))
                    except: pass
                
                self.arquivo_favoritos = self.caminho_arquivo.replace('.csv', '_favoritos.json')
                if os.path.exists(self.arquivo_favoritos):
                    try:
                        with open(self.arquivo_favoritos, 'r', encoding='utf-8') as f: self.favorites_set = set(json.load(f))
                    except: pass

                self.main_frame.pack(fill="both", expand=True)
                self.btn_frame.pack(fill="x", side="bottom", pady=10)
                self.carregar_lista_nomes()
                self.lbl_status.configure(text=f"Editando: {os.path.basename(caminho)}", text_color="#2E8B57")
                
                self.historico_undo.clear()
                self.historico_redo.clear()
                self.atualizar_estado_botoes_historico()
                self.salvar_config()
                
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível ler:\n{e}")

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
                
            prefix = "⭐ " if is_favorite else ""
            prefix += "✅ " if is_completed else ""
            if search in item.upper(): self.lb_pkmn.insert(tk.END, prefix + item)

    def filtrar_lista_alvo(self, *args):
        if self.df_original is None: return
        search = self.search_alvo_var.get().upper()
        status_filtro = self.filter_alvo_status_var.get()
        
        self.lb_alvo.delete(0, tk.END)
        for item in self.lista_formatada:
            pname = item.split(" - ", 1)[1]
            is_completed = pname in self.completed_set
            is_favorite = pname in self.favorites_set

            if status_filtro == "Mostrar completos" and not is_completed: continue
            if status_filtro == "Mostrar incompletos" and is_completed: continue
            if status_filtro == "Favoritos" and not is_favorite: continue
            
            prefix = "⭐ " if is_favorite else ""
            prefix += "✅ " if is_completed else ""
            if search in item.upper(): self.lb_alvo.insert(tk.END, prefix + item)

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

    # =============== NAVEGAÇÃO ===============
    def proxima_familia(self):
        if not self.pokemon_atual: return
        
        # Pega a família da API que baixamos
        nome_api_atual = self.traduzir_nome_para_api(self.pokemon_atual)
        familia_api = [nome_api_atual]
        for cache_fam in self.cache_familias.values():
            if nome_api_atual in cache_fam:
                familia_api = cache_fam
                break

        nomes_lb = self.lb_pkmn.get(0, tk.END)
        idx_atual = -1
        for i, item in enumerate(nomes_lb):
            nome = item.replace("✅ ", "").replace("⭐ ", "").split(" - ", 1)[1] if " - " in item else item
            if nome == self.pokemon_atual:
                idx_atual = i
                break
        
        if idx_atual == -1: return
        
        # Procura o próximo da lista que não seja da família atual
        for i in range(idx_atual + 1, len(nomes_lb)):
            nome_prox = nomes_lb[i].replace("✅ ", "").replace("⭐ ", "").split(" - ", 1)[1] if " - " in nomes_lb[i] else nomes_lb[i]
            if self.traduzir_nome_para_api(nome_prox) not in familia_api:
                self.selecionar_pokemon_automatico(nome_prox)
                return
                
        messagebox.showinfo("Fim da Linha", "Última família desta lista!")

    def familia_anterior(self):
        if not self.pokemon_atual: return
        
        # 1. Pega a família da API
        nome_api_atual = self.traduzir_nome_para_api(self.pokemon_atual)
        familia_api = [nome_api_atual]
        for cache_fam in self.cache_familias.values():
            if nome_api_atual in cache_fam:
                familia_api = cache_fam
                break

        # 2. Descobre onde estamos na lista
        nomes_lb = self.lb_pkmn.get(0, tk.END)
        idx_atual = -1
        for i, item in enumerate(nomes_lb):
            nome = item.replace("✅ ", "").replace("⭐ ", "").split(" - ", 1)[1] if " - " in item else item
            if nome == self.pokemon_atual:
                idx_atual = i
                break
        
        if idx_atual == -1: return
        
        # 3. Sobe na lista (de baixo pra cima) até achar alguém de OUTRA família
        for i in range(idx_atual - 1, -1, -1):
            nome_prev = nomes_lb[i].replace("✅ ", "").replace("⭐ ", "").split(" - ", 1)[1] if " - " in nomes_lb[i] else nomes_lb[i]
            if self.traduzir_nome_para_api(nome_prev) not in familia_api:
                self.selecionar_pokemon_automatico(nome_prev)
                return
                
        messagebox.showinfo("Início da Linha", "Você já está na primeira família desta lista!")

    def obter_frames_linhas(self):
        linhas = []
        if hasattr(self, 'col1'):
            linhas.extend([w for w in self.col1.winfo_children() if w.winfo_exists()])
            linhas.extend([w for w in self.col2.winfo_children() if w.winfo_exists()])
            linhas.extend([w for w in self.col3.winfo_children() if w.winfo_exists()])
        return linhas

    def obter_spinboxes_leveis(self):
        campos = []
        for w in self.obter_frames_linhas():
            ents = [e for e in w.winfo_children() if isinstance(e, ctk.CTkEntry)]
            if len(ents) >= 2:
                try:
                    if str(ents[1].cget('state')) != 'disabled': campos.append(ents[1])
                except: pass
        return campos

    def navegar_leveis(self, direcao, event=None):
        campos = self.obter_spinboxes_leveis()
        if not campos: return "break"
        
        foco_atual = self.root.focus_get()
        indice_atual = next((i for i, c in enumerate(campos) if c._entry == foco_atual or c == foco_atual), -1)

        if indice_atual != -1:
            proximo_indice = (indice_atual + direcao) % len(campos)
            campos[proximo_indice].focus_set()
            try: campos[proximo_indice].select_range(0, tk.END)
            except: pass
        else:
            campos[0].focus_set()
            try: campos[0].select_range(0, tk.END)
            except: pass
        return "break"
    
    def navegar_familia(self, direcao):
        # Só navega se a família já foi carregada e tem mais de 1 membro
        if not hasattr(self, 'familia_atual_api_nomes') or len(self.familia_atual_api_nomes) <= 1:
            return
            
        try:
            # Pega o nome do Pokémon atual no formato da API
            nome_api_atual = self.traduzir_nome_para_api(self.pokemon_atual)
            
            # Acha a posição dele na família
            idx_atual = self.familia_atual_api_nomes.index(nome_api_atual)
            
            # Calcula o próximo (se chegar no final, o '%' faz voltar pro começo)
            novo_idx = (idx_atual + direcao) % len(self.familia_atual_api_nomes)
            novo_membro_api = self.familia_atual_api_nomes[novo_idx]
            
            # Traduz de volta da API para o nome exato da sua planilha CSV
            novo_nome_csv = novo_membro_api
            nomes_csv_disponiveis = self.df_original['Name'].astype(str).tolist()
            
            if novo_membro_api in nomes_csv_disponiveis:
                novo_nome_csv = novo_membro_api
            else:
                for nome in nomes_csv_disponiveis:
                    if self.traduzir_nome_para_api(nome) == novo_membro_api:
                        novo_nome_csv = nome
                        break
                        
            # Troca de pokémon instantaneamente!
            self.selecionar_pokemon_automatico(novo_nome_csv)

            # Aguarda 50ms (tempo pro Tkinter desenhar os novos golpes) e foca na primeira caixa!
            self.root.after(50, self.focar_primeiro_golpe)
            
        except ValueError:
            pass # Se por acaso a família ainda estiver carregando, ignora o atalho
    
    def focar_primeiro_golpe(self):
        frames = self.obter_frames_linhas()
        if frames:
            # Pega as caixas de texto da primeira linha (o primeiro frame)
            ents = [e for e in frames[0].winfo_children() if isinstance(e, ctk.CTkEntry)]
            # Garante que existem as duas caixas na linha
            if len(ents) >= 2: 
                ents[1].focus_set() # O índice 1 é a caixa do Level!
                ents[1].select_range(0, tk.END) # Deixa o número já selecionado

    # =============== STATUS (FAVORITOS / CONCLUÍDOS) ===============
    def toggle_completed_atalho(self, event=None):
        if not self.pokemon_atual: return
        self.is_completed_var.set(not self.is_completed_var.get())
        self.toggle_completed()

    def toggle_completed(self):
        if not self.pokemon_atual: return
        if self.is_completed_var.get(): self.completed_set.add(self.pokemon_atual)
        else: self.completed_set.discard(self.pokemon_atual)
            
        if self.arquivo_progresso:
            with open(self.arquivo_progresso, 'w', encoding='utf-8') as f: json.dump(list(self.completed_set), f)
                
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
        if self.is_favorite_var.get(): self.favorites_set.add(self.pokemon_atual)
        else: self.favorites_set.discard(self.pokemon_atual)
            
        if self.arquivo_favoritos:
            with open(self.arquivo_favoritos, 'w', encoding='utf-8') as f: json.dump(list(self.favorites_set), f)
                
        self.filtrar_lista()
        if hasattr(self, 'filtrar_lista_alvo'): self.filtrar_lista_alvo()
        self.restaurar_selecao_lista()
        self.lb_pkmn.focus_set()

    # =============== GERENCIAMENTO DE DADOS ===============
    def salvar_em_memoria(self):
        if self.df_original is None or self.pokemon_atual is None: return

        golpes_tela = []
        for w in self.obter_frames_linhas():
            ents = [e for e in w.winfo_children() if isinstance(e, ctk.CTkEntry)]
            if len(ents) >= 2:
                m, l = str(ents[0].get()).strip(), str(ents[1].get()).strip()
                if m not in ["", "0", "NOVO_GOLPE"]: golpes_tela.append((m, l))
        
        golpes_tela.sort(key=lambda x: int(x[1]) if x[1].isdigit() else 0)

        idx = self.df_original.index[self.df_original['Name'] == self.pokemon_atual][0]
        nova_row = [str(self.df_original.at[idx, 'ID']), str(self.df_original.at[idx, 'Name'])]
        
        for m, l in golpes_tela: nova_row.extend([m, l])
            
        while len(nova_row) > len(self.df_original.columns):
            novo_num = (len(self.df_original.columns) // 2)
            self.df_original[f"Move{novo_num}"] = "0"
            self.df_original[f"Level{novo_num}"] = "0"
            
        while len(nova_row) < len(self.df_original.columns): nova_row.extend(["0", "0"])
        self.df_original.iloc[idx] = nova_row

    def atualizar_contador_golpes(self):
        if not self.pokemon_atual: return
        count = sum(1 for w in self.obter_frames_linhas() if len([e for e in w.winfo_children() if isinstance(e, ctk.CTkEntry)]) >= 2 and [e for e in w.winfo_children() if isinstance(e, ctk.CTkEntry)][0].get().strip() not in ["", "0", "NOVO_GOLPE"])
                    
        if count > 20: self.lbl_aviso_limite.configure(text=f"Total de golpes: {count}/20 ⚠️ EXCESSO", text_color="#FF4040", font=("Roboto", 14, "bold"))
        else: self.lbl_aviso_limite.configure(text=f"Total de golpes: {count}/20", text_color="#569CD6", font=("Roboto", 12, "bold"))
            
    def teletransportar_para(self, target_pokemon):
        itens = self.lb_pkmn.get(0, tk.END)
        for i, item in enumerate(itens):
            nome = item.replace("✅ ", "").replace("⭐ ", "").split(" - ", 1)[1]
            if nome == target_pokemon:
                self.lb_pkmn.selection_clear(0, tk.END)
                self.lb_pkmn.selection_set(i)
                self.lb_pkmn.activate(i)
                self.lb_pkmn.see(i)
                self.trocar_pokemon(None)
                break

    def trocar_pokemon(self, event):
        if not self.lb_pkmn.curselection(): return
        if self.pokemon_atual: self.salvar_em_memoria()
            
        selecionado = self.lb_pkmn.get(self.lb_pkmn.curselection())
        nome = selecionado.replace("✅ ", "").replace("⭐ ", "").split(" - ", 1)[1]
        
        self.pokemon_atual = nome
        self.lbl_nome.configure(text=nome)
        self.salvar_config()
        
        self.is_completed_var.set(nome in self.completed_set)
        self.is_favorite_var.set(nome in self.favorites_set)
        
        # Inicia a busca da família na PokéAPI
        for widget in self.scroll_fita_imagens.winfo_children(): widget.destroy()
        lbl_loading = ctk.CTkLabel(self.scroll_fita_imagens, text="Buscando família na API...", text_color="gray")
        lbl_loading.pack(padx=10, pady=10)
        threading.Thread(target=self.buscar_familia_api, args=(nome,), daemon=True).start()
        
        self.recarregar_ui_atual()
        self.esconder_painel_copia()

    def recarregar_ui_atual(self):
        if not self.pokemon_atual: return
        linha = self.df_original[self.df_original['Name'] == self.pokemon_atual].iloc[0]
        
        golpes = []
        for i in range(2, len(self.df_original.columns), 2):
            move, lvl = linha.iloc[i], linha.iloc[i+1]
            if move != '0' and move != 0 and pd.notna(move): golpes.append((move, lvl))
                
        frames_existentes = self.obter_frames_linhas()
        qtd_existente = len(frames_existentes)
        
        # O SEU CÓDIGO ORIGINAL RÁPIDO (Recicla os itens da tela)
        for i, (m, l) in enumerate(golpes):
            if i < qtd_existente:
                ents = [e for e in frames_existentes[i].winfo_children() if isinstance(e, ctk.CTkEntry)]
                ents[0].delete(0, tk.END); ents[0].insert(0, str(m))
                ents[1].delete(0, tk.END); ents[1].insert(0, str(l))
            else: 
                self.criar_linha_ui(m, str(l))
                
        # Destrói apenas os frames dos golpes que sobraram (se você deletou algo)
        for i in range(len(golpes), qtd_existente): 
            frames_existentes[i].destroy()
                
        # --- A MÁGICA DA PERFORMANCE ---
        self.root.update_idletasks() # Dá tempo para o sistema processar o que foi destruído
        
        # Olha para as 3 colunas. Se alguma estiver vazia, esconde. Se tiver itens, mostra!
        for col in [self.col1, self.col2, self.col3]:
            # Verifica se sobrou algum golpe vivo dentro da coluna
            if len([w for w in col.winfo_children() if w.winfo_exists()]) > 0:
                col.pack(side="left", fill="both", expand=True, padx=10) # Garante que está visível
            else:
                col.pack_forget() # Esconde a coluna fantasma sem destruir o layout!
        # -------------------------------

        self.atualizar_contador_golpes()
        self.destacar_duplicatas()

    # =============== UI DE LINHAS E DUPLICATAS ===============
    def destacar_duplicatas(self, *args):
        level_entries, move_entries = [], []
        level_counts, move_counts = {}, {}
        
        for w in self.obter_frames_linhas():
            if not w.winfo_exists(): continue
            ents = [e for e in w.winfo_children() if isinstance(e, ctk.CTkEntry)]
            if len(ents) >= 2:
                m_entry, l_entry = ents[0], ents[1]
                m_val, l_val = m_entry.get().strip(), l_entry.get().strip()
                
                move_entries.append((m_entry, m_val))
                level_entries.append((l_entry, l_val))
                
                if l_val != "": level_counts[l_val] = level_counts.get(l_val, 0) + 1
                if m_val not in ["", "0", "NOVO_GOLPE"]: move_counts[m_val] = move_counts.get(m_val, 0) + 1

        for i in range(len(level_entries)):
            l_entry, l_val = level_entries[i]
            m_entry, m_val = move_entries[i]
            
            if l_val == "1" and level_counts.get("1", 0) >= 5: l_entry.configure(fg_color="#006666") 
            elif l_val not in ["1", "0", ""] and level_counts.get(l_val, 0) > 1: l_entry.configure(fg_color="#8B0000") 
            else: l_entry.configure(fg_color=["#F9F9FA", "#343638"]) 
                
            if m_val not in ["", "0", "NOVO_GOLPE"] and move_counts.get(m_val, 0) > 1: m_entry.configure(fg_color="#B8860B") 
            else: m_entry.configure(fg_color=["#F9F9FA", "#343638"])

    def criar_linha_ui(self, move, lvl):
        count1 = len([w for w in self.col1.winfo_children() if w.winfo_exists()])
        count2 = len([w for w in self.col2.winfo_children() if w.winfo_exists()])
        parent_col = self.col1 if count1 < 10 else (self.col2 if count2 < 10 else self.col3)
        
        f = ctk.CTkFrame(parent_col, fg_color="transparent")
        f.pack(fill="x", pady=2)
        
        m_entry = ctk.CTkEntry(f, width=170, font=("Roboto", 12)) 
        m_entry.insert(0, move)
        m_entry.pack(side="left", padx=2)
        
        l_entry = ctk.CTkEntry(f, width=50, font=("Roboto", 12))
        l_entry.insert(0, lvl)
        l_entry.pack(side="left", padx=2)
        
        l_entry.bind('<Up>', lambda e: self.navegar_leveis(-1))
        l_entry.bind('<Down>', lambda e: self.navegar_leveis(1))
        l_entry.bind('<Control-Up>', lambda e, w=l_entry: self.alterar_valor_spinbox(w, 1))
        l_entry.bind('<Control-Down>', lambda e, w=l_entry: self.alterar_valor_spinbox(w, -1))
        m_entry.bind('<KeyRelease>', self.destacar_duplicatas)
        l_entry.bind('<KeyRelease>', self.destacar_duplicatas)
        l_entry.bind('<Delete>', lambda e, f=f: self.confirmar_delecao_atalho(f))
        
        m_entry.bind("<FocusIn>", lambda e: self.salvar_estado_para_desfazer())
        l_entry.bind("<FocusIn>", lambda e: self.salvar_estado_para_desfazer())
        m_entry.bind("<FocusOut>", lambda e: self.salvar_em_memoria())
        l_entry.bind("<FocusOut>", lambda e: self.salvar_em_memoria())
        
        m_entry.bind('<Return>', lambda e: (self.salvar_em_memoria(), self.lb_pkmn.focus_set()))
        l_entry.bind('<Return>', lambda e: (self.salvar_em_memoria(), self.lb_pkmn.focus_set()))
        
        btn_container = ctk.CTkFrame(f, fg_color="transparent")
        btn_container.pack(side="left", padx=15) 

        ctk.CTkButton(btn_container, text="📋", width=30, command=lambda m=m_entry, l=l_entry: self.iniciar_copia(m.get(), l.get())).pack(side="left", padx=2)
        ctk.CTkButton(btn_container, text="🗑️", width=30, fg_color="#C8504B", hover_color="#8A3632", command=lambda: self.deletar_golpe(f)).pack(side="left")

    def deletar_golpe(self, frame):
        self.salvar_estado_para_desfazer()
        
        frames = self.obter_frames_linhas()
        if frame not in frames: return
        
        idx = frames.index(frame)
        
        # 1. Puxa os textos de baixo para cima perfeitamente (cobrindo o buraco)
        for i in range(idx, len(frames) - 1):
            ents_atual = [e for e in frames[i].winfo_children() if isinstance(e, ctk.CTkEntry)]
            ents_prox = [e for e in frames[i+1].winfo_children() if isinstance(e, ctk.CTkEntry)]
            
            if ents_atual and ents_prox:
                ents_atual[0].delete(0, tk.END)
                ents_atual[0].insert(0, ents_prox[0].get())
                
                ents_atual[1].delete(0, tk.END)
                ents_atual[1].insert(0, ents_prox[1].get())
                
        # 2. O ANTI-CLONE: Esvaziamos a última caixa à força para não duplicar!
        ents_ultimo = [e for e in frames[-1].winfo_children() if isinstance(e, ctk.CTkEntry)]
        if ents_ultimo:
            ents_ultimo[0].delete(0, tk.END)
            ents_ultimo[1].delete(0, tk.END)
            
        self.root.update_idletasks()
        
        # 3. Salva no Dataframe (agora sem o clone no final)
        self.salvar_em_memoria() 
        
        # 4. O recarregamento rápido agora VAI destruir a última caixa e implodir a coluna!
        self.recarregar_ui_atual()
        
        self.lb_pkmn.focus_set()

    def confirmar_delecao_atalho(self, frame_da_linha, event=None):
        resposta = messagebox.askyesno("Confirmar Exclusão", "Deseja realmente deletar este golpe?")
        if resposta:
            self.deletar_golpe(frame_da_linha)
            self.root.after(50, lambda: self.navegar_leveis(1)) 
        return "break"

    def alterar_valor_spinbox(self, widget, incremento, event=None):
        self.salvar_estado_para_desfazer()
        try:
            novo_valor = min(100, max(0, int(widget.get()) + incremento))
            widget.delete(0, tk.END)
            widget.insert(0, str(novo_valor))
            self.destacar_duplicatas()
        except ValueError: pass
        return "break" 

    # =============== FUNÇÕES DE CÓPIA ===============
    def iniciar_copia(self, move, lvl):
        move, lvl = move.strip(), lvl.strip()
        if not move or move in ["NOVO_GOLPE", "0"]:
            messagebox.showwarning("Aviso", "Edite o nome do golpe para algo válido antes de copiar.")
            return
            
        self.salvar_em_memoria()
        self.move_copia_atual = ("COPIAR_UM", move, lvl)
        self.lbl_alvo_titulo.configure(text=f"Copiando:\n'{move}' (Lvl {lvl})\n⬇️ Clique no Destino ⬇️")
        
        # Garante que as opções de cópia de família saiam da tela
        if hasattr(self, 'cancelar_copia_multifamilia'):
            self.cancelar_copia_multifamilia()
            
        self.frame_alvo.pack(side="right", fill="y", padx=10, pady=10)
        self.search_alvo_var.set("")
        self.ent_search_alvo.focus_set()

    def iniciar_copia_todos(self):
        if not self.pokemon_atual: return
        self.salvar_em_memoria()
        
        golpes_para_copiar = []
        for w in self.obter_frames_linhas():
            ents = [e for e in w.winfo_children() if isinstance(e, ctk.CTkEntry)]
            if len(ents) >= 2:
                m, l = ents[0].get().strip(), ents[1].get().strip()
                if m not in ["", "0", "NOVO_GOLPE"]: golpes_para_copiar.append((m, l))
                    
        if not golpes_para_copiar:
            messagebox.showwarning("Aviso", "Não há golpes válidos para copiar.")
            return
            
        # Oculta o painel lateral direito de cópia individual
        if hasattr(self, 'frame_alvo'):
            self.frame_alvo.pack_forget()
            
        self.move_copia_atual = ("COPIAR_TODOS", golpes_para_copiar)
        self.adicionar_checkboxes_familia()

    def esconder_painel_copia(self):
        if hasattr(self, 'frame_alvo'):
            self.frame_alvo.pack_forget()
            
        # Essa é a mágica que resolve o cancelamento automático ao trocar de Pokémon!
        if hasattr(self, 'cancelar_copia_multifamilia'):
            self.cancelar_copia_multifamilia()
            
        self.move_copia_atual = None
        self.lb_alvo.selection_clear(0, tk.END)
        self.lb_pkmn.focus_set()

    def adicionar_checkboxes_familia(self):
        """Adiciona checkboxes flutuantes nos cards para selecionar quem receber cópia"""
        # Remove qualquer checkbox anterior para não bugar
        for card in self.scroll_fita_imagens.winfo_children():
            if hasattr(card, 'checkbox_widget') and card.checkbox_widget:
                card.checkbox_widget.destroy()
                card.checkbox_widget = None
            
            if hasattr(card, 'membro_nome'):
                chk = ctk.CTkCheckBox(card, text="", width=24, height=24, fg_color="#2E8B57")
                chk.place(x=5, y=5)
                chk.lift() 
                
                chk.membro_nome = card.membro_nome
                card.checkbox_widget = chk
        
        # Cria ou reutiliza o painel de botões no header
        if not hasattr(self, 'frame_controle_copia') or not self.frame_controle_copia.winfo_exists():
            self.frame_controle_copia = ctk.CTkFrame(self.header_edit_frame, fg_color="transparent")
        else:
            for widget in self.frame_controle_copia.winfo_children(): widget.destroy()
        
        self.frame_controle_copia.pack(side="left", padx=20, pady=5)
        
        lbl_info = ctk.CTkLabel(self.frame_controle_copia, text="✓ Selecione as evoluções nos cards abaixo:", font=("Roboto", 12, "bold"), text_color="#ffcc00")
        lbl_info.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(self.frame_controle_copia, text="✅ Confirmar", command=self.confirmar_copia_multifamilia, fg_color="#2E8B57", hover_color="#1d5c39", width=100).pack(side="left", padx=5)
        ctk.CTkButton(self.frame_controle_copia, text="❌ Cancelar", command=self.cancelar_copia_multifamilia, fg_color="#C8504B", hover_color="#8A3632", width=90).pack(side="left", padx=5)

    def confirmar_copia_multifamilia(self):
        if not self.move_copia_atual or self.move_copia_atual[0] != "COPIAR_TODOS": 
            return
        
        golpes_para_copiar = self.move_copia_atual[1]
        selecionados = []
        
        for card in self.scroll_fita_imagens.winfo_children():
            # A Solução: CTkCheckBox.get() nativo retorna '1' quando marcado! Não buga nunca.
            if hasattr(card, 'checkbox_widget') and card.checkbox_widget and card.checkbox_widget.get() == 1:
                selecionados.append(card.membro_nome)
        
        if not selecionados:
            messagebox.showwarning("Aviso", "Nenhum membro foi selecionado nas imagens!")
            return
            
        self.salvar_estado_para_desfazer()
        self.salvar_em_memoria()
        
        selecionados_csv = []
        nomes_csv_disponiveis = self.df_original['Name'].astype(str).tolist()
        
        for membro_api in selecionados:
            encontrado = False
            if membro_api in nomes_csv_disponiveis:
                selecionados_csv.append(membro_api)
                encontrado = True
            else:
                for nome in nomes_csv_disponiveis:
                    if self.traduzir_nome_para_api(nome) == membro_api:
                        selecionados_csv.append(nome)
                        encontrado = True
                        break
            if not encontrado:
                selecionados_csv.append(membro_api)
        
        copias_feitas = 0
        for target_pokemon in selecionados_csv:
            if target_pokemon != self.pokemon_atual:
                self.executar_copia_todos(golpes_para_copiar, target_pokemon)
                copias_feitas += 1
        
        self.cancelar_copia_multifamilia()
        messagebox.showinfo("Sucesso", f"Todos os golpes foram colados em {copias_feitas} evolução(ões)!")

    def cancelar_copia_multifamilia(self):
        for card in self.scroll_fita_imagens.winfo_children():
            if hasattr(card, 'checkbox_widget') and card.checkbox_widget:
                card.checkbox_widget.destroy()
                card.checkbox_widget = None
        
        if hasattr(self, 'frame_controle_copia') and self.frame_controle_copia.winfo_exists():
            self.frame_controle_copia.pack_forget()
            
        if self.move_copia_atual and self.move_copia_atual[0] == "COPIAR_TODOS":
            self.move_copia_atual = None
            
        self.lb_pkmn.focus_set()

    def confirmar_copia_lista(self, event):
        if not self.lb_alvo.curselection() or not self.move_copia_atual: return
        selecionado = self.lb_alvo.get(self.lb_alvo.curselection())
        target_name = selecionado.replace("✅ ", "").replace("⭐ ", "").split(" - ", 1)[1]
        
        if self.move_copia_atual[0] == "COPIAR_TODOS": self.executar_copia_todos(self.move_copia_atual[1], target_name)
        elif self.move_copia_atual[0] == "COPIAR_UM": self.executar_copia(self.move_copia_atual[1], self.move_copia_atual[2], target_name)
        self.esconder_painel_copia()

    def executar_copia(self, move, lvl, target_pokemon):
        self.salvar_estado_para_desfazer()
        try:
            idx_alvo = self.df_original.index[self.df_original['Name'] == target_pokemon].tolist()[0]
            dados_basicos = self.df_original.iloc[idx_alvo, :2].tolist() 
            
            golpes_alvo = []
            num_colunas = len(self.df_original.columns)
            for i in range(2, num_colunas, 2):
                if i + 1 < num_colunas:
                    m, l = str(self.df_original.iloc[idx_alvo, i]).strip(), str(self.df_original.iloc[idx_alvo, i+1]).strip()
                    if m not in ["", "0", "nan"]: golpes_alvo.append((m, l))

            if (move, lvl) in golpes_alvo:
                messagebox.showinfo("Aviso", f"O {target_pokemon} já possui o golpe '{move}' no level {lvl}!")
                self.lb_pkmn.focus_set()
                return

            niveis_existentes = [l for _, l in golpes_alvo if l not in ["1", "0"]]
            novo_lvl = lvl
            if novo_lvl in niveis_existentes:
                resposta = simpledialog.askstring("Conflito de Level", f"{target_pokemon} já possui golpe no level {novo_lvl}!\nDigite um NOVO LEVEL para '{move}':")
                if resposta and resposta.strip() != "":
                    novo_lvl = resposta.strip()
                    if (move, novo_lvl) in golpes_alvo: return
                else: return

            golpes_alvo.append((move, novo_lvl))
            golpes_alvo.sort(key=lambda x: int(x[1]) if str(x[1]).isdigit() else 0)
            
            nova_row = dados_basicos.copy()
            for m, l in golpes_alvo: nova_row.extend([m, l])
            while len(nova_row) > len(self.df_original.columns):
                self.df_original[f"Move{len(self.df_original.columns)//2}"] = "0"
                self.df_original[f"Level{len(self.df_original.columns)//2}"] = "0"
            while len(nova_row) < len(self.df_original.columns): nova_row.extend(["0", "0"])
            self.df_original.iloc[idx_alvo] = nova_row
            
            if target_pokemon == self.pokemon_atual: self.recarregar_ui_atual()
            if len(golpes_alvo) > 20:
                messagebox.showwarning("Excesso", f"O {target_pokemon} ficou com {len(golpes_alvo)} golpes.")
                self.teletransportar_para(target_pokemon)
            else: self.lbl_status.configure(text=f"✅ '{move}' adicionado a {target_pokemon}!", text_color="#2E8B57")
            self.lb_pkmn.focus_set() 
        except Exception as e: messagebox.showerror("Erro na Cópia", f"Erro: {e}")

    def executar_copia_todos(self, golpes_para_copiar, target_pokemon):
        self.salvar_estado_para_desfazer()
        try:
            idx_alvo = self.df_original.index[self.df_original['Name'] == target_pokemon].tolist()[0]
            dados_basicos = self.df_original.iloc[idx_alvo, :2].tolist()
            
            golpes_alvo, nomes_alvo = [], []
            for i in range(2, len(self.df_original.columns), 2):
                if i + 1 < len(self.df_original.columns):
                    m, l = str(self.df_original.iloc[idx_alvo, i]).strip(), str(self.df_original.iloc[idx_alvo, i+1]).strip()
                    if m not in ["", "0", "nan"]:
                        golpes_alvo.append((m, l))
                        nomes_alvo.append(m)
            
            golpes_adicionados = 0
            for move, lvl in golpes_para_copiar:
                if move not in nomes_alvo: 
                    golpes_alvo.append((move, lvl))
                    nomes_alvo.append(move)
                    golpes_adicionados += 1
                    
            golpes_alvo.sort(key=lambda x: int(x[1]) if str(x[1]).isdigit() else 0)
            nova_row = dados_basicos.copy()
            for m, l in golpes_alvo: nova_row.extend([m, l])
            while len(nova_row) > len(self.df_original.columns):
                self.df_original[f"Move{len(self.df_original.columns)//2}"] = "0"
                self.df_original[f"Level{len(self.df_original.columns)//2}"] = "0"
            while len(nova_row) < len(self.df_original.columns): nova_row.extend(["0", "0"])
            self.df_original.iloc[idx_alvo] = nova_row

            if target_pokemon == self.pokemon_atual: self.recarregar_ui_atual()
            if golpes_adicionados > 0: 
                if len(golpes_alvo) > 20: self.teletransportar_para(target_pokemon)
                else: self.lbl_status.configure(text=f"✅ {golpes_adicionados} novos golpes colados em {target_pokemon}!", text_color="#2E8B57")
            self.lb_pkmn.focus_set() 
        except Exception as e: messagebox.showerror("Erro na Cópia", f"Erro: {e}")

    # =============== OUTROS ATALHOS ===============
    def organizar_visual(self):
        if self.df_original is None: return
        self.salvar_estado_para_desfazer()       
        dados = []
        for w in self.obter_frames_linhas():
            ents = [e for e in w.winfo_children() if isinstance(e, ctk.CTkEntry)]
            if len(ents) >= 2:
                try: dados.append((ents[0].get(), int(ents[1].get())))
                except: continue
                
        dados.sort(key=lambda x: x[1])
        frames_existentes = self.obter_frames_linhas()
        for i, (m, l) in enumerate(dados):
            ents = [e for e in frames_existentes[i].winfo_children() if isinstance(e, ctk.CTkEntry)]
            ents[0].delete(0, tk.END); ents[0].insert(0, str(m))
            ents[1].delete(0, tk.END); ents[1].insert(0, str(l))
            
        self.root.after(10, self.atualizar_contador_golpes)
        self.root.after(10, self.destacar_duplicatas)

    def add_blank_move(self):
        if self.df_original is not None:
            self.salvar_estado_para_desfazer()
            self.criar_linha_ui("NOVO_GOLPE", "1")
            self.root.after(10, self.atualizar_contador_golpes)
            self.root.after(10, self.destacar_duplicatas) 

    def salvar_config(self):
        try:
            dados = {
                "ultimo_csv": getattr(self, 'caminho_arquivo', None),
                "ultimo_pokemon": getattr(self, 'pokemon_atual', None),
                # Puxa o texto atual das variáveis do filtro!
                "filtro_lista_esq": self.filter_status_var.get() if hasattr(self, 'filter_status_var') else "Todos",
                "filtro_lista_dir": self.filter_alvo_status_var.get() if hasattr(self, 'filter_alvo_status_var') else "Todos"
            }
            with open("config_pokemove.json", 'w', encoding='utf-8') as f:
                json.dump(dados, f)
        except Exception: pass

    def ao_fechar_programa(self):
        """Salva o estado completo antes de fechar"""
        if self.df_original is not None:
            self.salvar_em_memoria()
        self.salvar_config()
        self.root.destroy()

    def tentar_abrir_ultimo_arquivo(self):
        if os.path.exists("config_pokemove.json"):
            try:
                with open("config_pokemove.json", 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    
                    # 1. Carrega os filtros salvos (se existirem no JSON)
                    if "filtro_lista_esq" in dados and hasattr(self, 'filter_status_var'):
                        self.filter_status_var.set(dados["filtro_lista_esq"])
                    if "filtro_lista_dir" in dados and hasattr(self, 'filter_alvo_status_var'):
                        self.filter_alvo_status_var.set(dados["filtro_lista_dir"])

                    # 2. Abre o CSV
                    if dados.get("ultimo_csv") and os.path.exists(dados.get("ultimo_csv")):
                        self.selecionar_arquivo(caminho_direto=dados.get("ultimo_csv"))
                        
                        # Limpa o campo de busca
                        self.search_var.set("")
                        
                        # >>> FORÇA A APLICAÇÃO DOS FILTROS NAS DUAS LISTAS LOGO APÓS ABRIR <<<
                        self.filtrar_lista()
                        self.filtrar_lista_alvo()
                        
                        if dados.get("ultimo_pokemon"):
                            self.root.after(200, lambda: self.selecionar_pokemon_automatico(dados.get("ultimo_pokemon")))
            except: pass

    def selecionar_pokemon_automatico(self, nome_pkmn):
        nomes = self.lb_pkmn.get(0, tk.END)
        for i, item in enumerate(nomes):
            nome_limpo = item.replace("✅ ", "").replace("⭐ ", "").split(" - ", 1)[1] if " - " in item else item
            if nome_limpo == nome_pkmn:
                self.lb_pkmn.selection_clear(0, tk.END)
                self.lb_pkmn.selection_set(i)
                self.lb_pkmn.activate(i)
                self.lb_pkmn.see(i)
                self.lb_pkmn.event_generate("<<ListboxSelect>>")
                break

    def exportar_final(self):
        if self.df_original is None: return
        self.salvar_em_memoria()
        try:
            self.df_original.to_csv(self.caminho_arquivo, index=False)
            self.lbl_status.configure(text=f"✅ Salvo no arquivo com sucesso às {pd.Timestamp.now().strftime('%H:%M:%S')}!", text_color="#2E8B57")
        except Exception as e: messagebox.showerror("Erro ao gravar", f"Erro: {e}")

if __name__ == "__main__":
    root = ctk.CTk()
    app = PokemonEditor(root)
    root.mainloop()