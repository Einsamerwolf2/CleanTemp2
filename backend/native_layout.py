"""Native dashboard composition, separate from cleaning and scheduling actions."""
import tkinter as tk
from tkinter import ttk

from cleaner import targets
from resources import RESOURCE_ROOT
from scheduler import ALLOWED, read_schedule
from settings import VERSION

BG = '#0a1220'
CARD = '#142238'
TEXT = '#edf4ff'
MUTED = '#a5b6ce'
TEAL = '#4dd4bd'


def build(window):
    w = window
    root = w.root
    root.title('CleanTemp')
    root.configure(bg=BG)
    root.geometry(f'{min(1180, root.winfo_screenwidth()-90)}x{min(830, root.winfo_screenheight()-90)}')
    root.minsize(860, 640)
    root.iconbitmap(str(RESOURCE_ROOT / 'assets/cleantemp.ico'))
    root.protocol('WM_DELETE_WINDOW', w.close)
    root.option_add('*Font', ('Segoe UI', 10))
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('TNotebook', background=BG, borderwidth=0, tabmargins=(0, 6, 0, 0))
    style.configure('TNotebook.Tab', background='#17243a', foreground=MUTED, padding=(25, 12), font=('Segoe UI', 11))
    style.map('TNotebook.Tab', background=[('selected', '#233d50')], foreground=[('selected', '#73ead3')])
    style.configure('Treeview', background=CARD, fieldbackground=CARD, foreground=TEXT,
                    rowheight=34, borderwidth=0, font=('Segoe UI', 10))
    style.configure('Treeview.Heading', background='#1c3048', foreground=MUTED, padding=8,
                    font=('Segoe UI', 10, 'bold'), relief='flat')
    style.map('Treeview', background=[('selected', '#204b5b')], foreground=[('selected', 'white')])
    style.configure('TEntry', fieldbackground='#1d3048', foreground=TEXT, padding=7, insertcolor=TEXT)
    style.configure('Horizontal.TProgressbar', background=TEAL, troughcolor='#1c3048', borderwidth=0)
    style.configure('TScrollbar', background='#29415d', troughcolor=BG, borderwidth=0)

    def frame(parent, color=CARD, **kwargs):
        return tk.Frame(parent, bg=color, **kwargs)
    def label(parent, text, size=10, bold=False, color=TEXT, **kwargs):
        return tk.Label(parent, text=text, bg=parent.cget('bg'), fg=color,
                        font=('Segoe UI', size, 'bold' if bold else 'normal'), **kwargs)
    def heading(parent, title, detail):
        label(parent, title, 20, True).pack(anchor='w', pady=(14, 5))
        label(parent, detail, color=MUTED, wraplength=960, justify='left').pack(anchor='w', pady=(0, 15))
    def panel(parent):
        return frame(parent, padx=18, pady=14, highlightbackground='#23364e', highlightthickness=1)

    header = frame(root, BG)
    header.pack(fill='x', padx=24, pady=(18, 8))
    w.logo = tk.PhotoImage(file=str(RESOURCE_ROOT / 'assets/cleantemp.png')).subsample(5)
    tk.Label(header, image=w.logo, bg=BG).pack(side='left', padx=(0, 12))
    identity = frame(header, BG)
    identity.pack(side='left')
    label(identity, 'CleanTemp', 25, True).pack(anchor='w')
    label(identity, 'Mais espaço. Menos complicação.', color=MUTED).pack(anchor='w')
    w.button(header, 'Como usar', w.tour).pack(side='right')
    label(header, '●  Funciona sem internet', color=TEAL).pack(side='right', padx=20)

    footer = frame(root, BG)
    footer.pack(side='bottom', fill='x', padx=24, pady=(8, 12))
    label(footer, 'CleanTemp • Criado por Edilson Enoque', 9, color=MUTED).pack(side='left')
    label(footer, f'Versão {VERSION}', 9, color=MUTED).pack(side='right')
    w.notebook = ttk.Notebook(root)
    w.notebook.pack(fill='both', expand=True, padx=24)
    w.pages, w.contents = {}, {}
    scrollables = []
    for key, title in [('clean', 'Limpeza'), ('schedule', 'Agendamento'), ('history', 'Histórico'), ('help', 'Ajuda')]:
        outer = frame(w.notebook, BG, padx=2)
        w.notebook.add(outer, text=title)
        w.pages[key] = outer
        if key in ('schedule', 'help'):
            canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
            scroll = ttk.Scrollbar(outer, orient='vertical', command=canvas.yview)
            scroll.pack(side='right', fill='y')
            canvas.pack(fill='both', expand=True)
            canvas.configure(yscrollcommand=scroll.set)
            page = frame(canvas, BG)
            item = canvas.create_window((0, 0), window=page, anchor='nw')
            page.bind('<Configure>', lambda event, c=canvas: c.configure(scrollregion=c.bbox('all')))
            canvas.bind('<Configure>', lambda event, c=canvas, i=item: c.itemconfigure(i, width=event.width))
            w.contents[key] = page
            scrollables.append((page, canvas))
        else:
            w.contents[key] = outer
    def wheel(event):
        for inner, canvas in scrollables:
            if str(event.widget).startswith(str(inner)):
                canvas.yview_scroll(-int(event.delta / 120), 'units')
                return 'break'
    root.bind('<MouseWheel>', wheel)
    def wrap_labels():
        def walk(widget):
            for child in widget.winfo_children():
                if isinstance(child, tk.Label) and int(child.cget('wraplength')) > 0:
                    child.configure(wraplength=max(200, child.master.winfo_width() - 40))
                walk(child)
        walk(root)
    def resized(event):
        if event.widget is root:
            if getattr(w, 'layout_timer', None):
                root.after_cancel(w.layout_timer)
            w.layout_timer = root.after(100, wrap_labels)
    root.bind('<Configure>', resized)
    w.notebook.bind('<<NotebookTabChanged>>', w.tab_changed)

    page = w.contents['clean']
    stats = frame(page, BG)
    stats.pack(fill='x', pady=(16, 12))
    stats.grid_columnconfigure((0, 1, 2), weight=1, uniform='metric')
    metrics = []
    for index, (caption, value) in enumerate([('ESPAÇO ENCONTRADO', '—'), ('ARQUIVOS TEMPORÁRIOS', '—'), ('SUA SELEÇÃO', 'Nenhuma opção')]):
        metric = panel(stats)
        metric.grid(row=0, column=index, sticky='nsew', padx=(0 if index == 0 else 7, 0))
        label(metric, caption, 9, color=MUTED).pack(anchor='w')
        number = label(metric, value, 20 if index < 2 else 16, True, TEAL if index == 0 else TEXT)
        number.pack(anchor='w', pady=(6, 0))
        metrics.append(number)
    w.total, w.file_total, w.selection_total = metrics
    actions = frame(page, BG)
    actions.pack(fill='x', pady=(0, 8))
    w.scan_button = w.button(actions, 'Analisar computador', w.scan, '#167f78')
    w.scan_button.pack(side='left')
    w.cancel_scan_button = w.button(actions, 'Parar análise', w.cancel_scan)
    w.clean_button = w.button(actions, 'Limpar selecionados', w.clean, '#167f78')
    w.clean_button.pack(side='right')
    w.clean_button.configure(state='disabled')
    w.progress_text = tk.StringVar(value='Comece com uma análise. Nenhum arquivo será apagado nessa etapa.')
    label(page, '', color=MUTED, textvariable=w.progress_text, anchor='w').pack(fill='x', pady=(0, 5))
    w.progress = ttk.Progressbar(page, mode='determinate', maximum=100)
    w.progress.pack(fill='x', pady=(0, 10))
    filters = frame(page, BG)
    filters.pack(fill='x', pady=(0, 8))
    w.search = tk.StringVar()
    label(filters, 'Buscar opção', color=MUTED).pack(side='left', padx=(0, 8))
    w.search_entry = ttk.Entry(filters, textvariable=w.search, width=22)
    w.search_entry.pack(side='left')
    w.search.trace_add('write', lambda *args: w.render_rows())
    w.select_all_button = w.button(filters, 'Marcar disponíveis', w.select_available)
    w.select_all_button.pack(side='right')
    w.clear_selection_button = w.button(filters, 'Limpar seleção', w.clear_selection)
    w.clear_selection_button.pack(side='right', padx=6)
    result = panel(page)
    result.pack(side='bottom', fill='x', pady=(8, 0))
    line = frame(result)
    line.pack(fill='x')
    w.result_headline = tk.StringVar(value='Pronto para começar')
    label(line, '', 12, True, textvariable=w.result_headline, anchor='w', wraplength=750).pack(side='left', fill='x', expand=True)
    w.button(line, 'Ver resultado', w.show_result).pack(side='right')
    label(result, 'Somente temporários com mais de um dia. Arquivos em uso e pastas são preservados.',
          9, color=MUTED, wraplength=1000, justify='left').pack(anchor='w', pady=(7, 0))
    w.authorize_button = w.button(result, 'Tentar limpar com autorização', w.authorize, '#344f85')
    w.authorize_button.configure(state='disabled')
    w.result = tk.StringVar(value='Tudo pronto para começar.')
    w.result.trace_add('write', lambda *args: w.result_headline.set(w.result.get().splitlines()[0] if w.result.get() else 'Pronto'))
    details = frame(page, BG)
    details.pack(side='bottom', fill='x', pady=(7, 0))
    w.folder_detail = tk.StringVar(value='Marque na primeira coluna ou use Espaço. Selecione uma linha para ver o local.')
    label(details, '', 9, color=MUTED, textvariable=w.folder_detail, anchor='w', wraplength=1020).pack(fill='x')
    table = frame(page)
    table.pack(fill='both', expand=True)
    scrollbar = ttk.Scrollbar(table, orient='vertical')
    scrollbar.pack(side='right', fill='y')
    w.tree = ttk.Treeview(table, columns=('choice', 'name', 'size', 'reason'), show='headings',
                         height=6, selectmode='browse', yscrollcommand=scrollbar.set)
    scrollbar.configure(command=w.tree.yview)
    for col, title, width, minimum in [('choice', 'Marcar', 64, 60), ('name', 'Opção', 250, 170), ('size', 'Espaço', 100, 80), ('reason', 'Situação', 360, 180)]:
        w.tree.heading(col, text=title)
        w.tree.column(col, width=width, minwidth=minimum, stretch=col in ('name', 'reason'))
    w.tree.tag_configure('protected', foreground='#8193ad')
    w.tree.pack(fill='both', expand=True)
    w.tree.bind('<ButtonRelease-1>', w.toggle)
    w.tree.bind('<space>', w.toggle)
    w.tree.bind('<<TreeviewSelect>>', w.folder_details)
    w.tree.bind('<Control-a>', lambda event: w.select_available())
    w.tree.insert('', 'end', iid='empty', values=('', 'Nenhuma análise realizada', '', 'Clique em Analisar computador para começar.'))

    page = w.contents['schedule']
    heading(page, 'Uma rotina mais leve', 'Escolha um horário diário e deixe o Windows cuidar dos temporários pessoais selecionados.')
    config = read_schedule()
    box = panel(page)
    box.pack(fill='x', pady=(0, 12))
    w.schedule_text = tk.StringVar()
    label(box, '', 15, True, TEAL, textvariable=w.schedule_text, anchor='w', wraplength=980).pack(fill='x')
    label(box, 'O computador precisa estar ligado e seu usuário conectado. O aplicativo pode estar fechado.',
          color=MUTED, wraplength=980, justify='left').pack(anchor='w', pady=(8, 0))
    controls = panel(page)
    controls.pack(fill='x')
    time_row = frame(controls)
    time_row.pack(fill='x', pady=(0, 12))
    label(time_row, 'Todos os dias às', 12, True).pack(side='left')
    w.hour = tk.StringVar(value=config.get('hour', '18:00'))
    ttk.Entry(time_row, textvariable=w.hour, width=8, justify='center').pack(side='left', padx=14)
    label(time_row, 'Formato 18:30 • horário do seu Windows', color=MUTED).pack(side='left')
    label(controls, 'O que deseja limpar automaticamente?', 12, True).pack(anchor='w', pady=(0, 8))
    options = frame(controls)
    options.pack(fill='x')
    for index, target in enumerate(t for t in targets() if t['id'] in ALLOWED):
        value = tk.BooleanVar(value=target['id'] in config.get('ids', ['user_temp']))
        w.choices[target['id']] = value
        tk.Checkbutton(options, text=target['name'], variable=value, bg=CARD, fg=TEXT,
                       selectcolor='#1d3048', activebackground=CARD, activeforeground=TEXT,
                       anchor='w', padx=4, pady=6).grid(row=index//2, column=index%2, sticky='w', padx=(0, 30))
    row = frame(controls)
    row.pack(fill='x', pady=(18, 0))
    w.schedule_save_button = w.button(row, 'Ativar / salvar horário', w.save_schedule, '#167f78')
    w.schedule_save_button.pack(side='left')
    w.schedule_disable_button = w.button(row, 'Desativar agendamento', w.disable_schedule)
    w.schedule_disable_button.pack(side='left', padx=10)
    w.button(row, 'Último resultado', w.last_result).pack(side='right')
    label(page, 'A exclusão automática é permanente e não pede nova confirmação. Não acorda o computador, não recupera horários perdidos e nunca solicita administrador.',
          color=MUTED, wraplength=1000, justify='left').pack(anchor='w', pady=15)
    w.refresh_schedule_status()

    page = w.contents['history']
    heading(page, 'Veja o que já foi feito', 'Resumo das últimas limpezas manuais e automáticas. Guardado apenas neste computador.')
    row = frame(page, BG)
    row.pack(fill='x', pady=(0, 10))
    w.history_status = tk.StringVar()
    label(row, '', color=MUTED, textvariable=w.history_status).pack(side='left')
    w.button(row, 'Atualizar histórico', w.refresh_history).pack(side='right')
    w.button(row, 'Abrir detalhes', w.history_details).pack(side='right', padx=8)
    table = frame(page)
    table.pack(fill='both', expand=True)
    scroll = ttk.Scrollbar(table, orient='vertical')
    scroll.pack(side='right', fill='y')
    w.history_tree = ttk.Treeview(table, columns=('at', 'mode', 'deleted', 'size'), show='headings',
                                 yscrollcommand=scroll.set, selectmode='browse')
    scroll.configure(command=w.history_tree.yview)
    for col, title, width in [('at', 'Quando', 260), ('mode', 'Limpeza', 150), ('deleted', 'Arquivos removidos', 180), ('size', 'Espaço liberado', 180)]:
        w.history_tree.heading(col, text=title)
        w.history_tree.column(col, width=width, minwidth=100)
    w.history_tree.pack(fill='both', expand=True)
    w.history_tree.bind('<Double-1>', lambda event: w.history_details())
    label(page, 'O histórico não contém nomes de arquivos pessoais. Resultados da autorização adicional são exibidos na própria janela auxiliar.',
          color=MUTED, wraplength=1000, justify='left').pack(anchor='w', pady=14)
    w.refresh_history()

    page = w.contents['help']
    heading(page, 'Estamos por perto', 'Aprenda a usar o CleanTemp, consulte o guia e encontre os canais de assistência.')
    guide = panel(page)
    guide.pack(fill='x', pady=(0, 12))
    label(guide, 'Primeiros passos', 14, True).pack(anchor='w')
    label(guide, 'Um passeio pela aplicação e um guia em PDF que funciona sem internet.', color=MUTED).pack(anchor='w', pady=8)
    row = frame(guide)
    row.pack(fill='x')
    w.button(row, 'Rever passeio', w.tour, '#167f78').pack(side='left')
    w.button(row, 'Abrir guia em PDF', w.guide).pack(side='left', padx=8)
    w.button(row, 'Termos de uso', w.show_terms).pack(side='right')
    support = frame(page, BG)
    support.pack(fill='x', pady=(0, 12))
    support.grid_columnconfigure((0, 1, 2), weight=1, uniform='support')
    for index, (key, name, color) in enumerate([('discord', 'Discord', '#5865f2'), ('telegram', 'Telegram', '#168ac2'), ('whatsapp', 'WhatsApp', '#138b47')]):
        item = panel(support)
        item.grid(row=0, column=index, sticky='nsew', padx=(0 if index == 0 else 8, 0))
        icon = tk.PhotoImage(file=str(RESOURCE_ROOT / f'assets/support-{key}.png'))
        setattr(w, 'icon_' + key, icon)
        tk.Label(item, image=icon, bg=CARD).pack(anchor='w')
        label(item, name, 13, True).pack(anchor='w', pady=(7, 3))
        label(item, 'Assistência e dúvidas', 9, color=MUTED).pack(anchor='w', pady=(0, 8))
        w.button(item, 'Falar pelo ' + name, lambda channel=key: w.support(channel), color).pack(fill='x')
    update = panel(page)
    update.pack(fill='x')
    label(update, 'Novidades do CleanTemp', 13, True).pack(anchor='w')
    w.update_text = label(update, 'A limpeza continua funcionando sem internet.', color=MUTED, wraplength=950, justify='left')
    w.update_text.pack(anchor='w', pady=7)
    row = frame(update)
    row.pack(fill='x')
    w.check_update_button = w.button(row, 'Verificar agora', w.update)
    w.check_update_button.pack(side='left')
    w.update_url = ''
    w.update_button = w.button(row, 'Ver nova versão', w.open_update, '#167f78')
    w.auto_updates = tk.BooleanVar(value=w.local.preferences()['automatic_updates'])
    tk.Checkbutton(update, text='Verificar novidades automaticamente quando houver conexão', variable=w.auto_updates,
                   command=w.save_update_preference, bg=CARD, fg=TEXT, selectcolor='#1d3048',
                   activebackground=CARD, activeforeground=TEXT).pack(anchor='w', pady=(10, 0))
    label(page, 'Nenhuma mensagem ou relatório é enviado automaticamente. Canais sem link mostram “Em desenvolvimento”.',
          9, color=MUTED, wraplength=1000).pack(anchor='w', pady=12)
