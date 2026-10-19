"""Native, offline CleanTemp window. No browser and no listening server."""
import json
import os
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog
from local_state import LocalState, count, read_json
from ui_dialogs import confirm_action

from cleaner import inspect, targets, preservation_summary
from elevation import request_authorization
from operation import cleaning_guard
from resources import RESOURCE_ROOT
from scheduler import ALLOWED, configure, data_dir, disable, read_schedule
from settings import VERSION, read_config
from updates import checker

BG = '#0a1220'
CARD = '#142238'
TEXT = '#edf4ff'
MUTED = '#a9b9cd'
TOUR = [
    ('Bem-vindo ao CleanTemp', 'Libere espaço com segurança. Este passeio apenas explica e não apaga arquivos.'),
    ('Analisar primeiro', 'Clique em Analisar. Aguarde a lista de temporários com mais de um dia.'),
    ('Escolher o que limpar', 'Marque na primeira coluna ou use Espaço. Áreas protegidas ficam bloqueadas. Nenhuma pasta será removida.'),
    ('Confirmar a limpeza', 'Clique em Limpar selecionados e confirme. A exclusão é permanente; arquivos abertos e sem acesso serão preservados.'),
    ('Definir um horário', 'Na aba Agendamento, escolha opções pessoais e um horário diário. Ative apenas se concordar com a exclusão sem nova confirmação.'),
    ('Consultar o resultado', 'O resultado aparece em Limpeza e o resumo fica na aba Histórico. Você pode consultar a última limpeza automática e desativar o agendamento a qualquer momento.'),
    ('Ajuda quando precisar', 'Na aba Ajuda, abra o guia em PDF para ler offline. Discord, Telegram e WhatsApp precisam de internet e permanecem em desenvolvimento até seus links estarem disponíveis.')]


def amount(value):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if value < 1024 or unit == 'TB':
            return f'{int(value)} B' if unit == 'B' else f'{value:.1f}'.replace('.', ',') + ' ' + unit
        value /= 1024


class Window:
    def __init__(self, root):
        self.root = root
        self.busy = False
        self.busy_kind = None
        self.events = queue.Queue()
        self.rows = []
        self.marked = set()
        self.authorization_pending = False
        self.choices = {}
        self.tour_window = None
        self.scan_stop = threading.Event()
        self.schedule_busy = False
        self.updating = False
        self.local = LocalState(data_dir())
        from native_layout import build
        build(self)
        self.root.after(100, self.poll)
        self.root.after(500, self.start_updates)
        if not (data_dir() / 'tour-seen').exists():
            self.root.after(600, self.tour)
        self.root.bind('<Escape>', lambda event: self.cancel_scan() if self.busy_kind == 'scan' else None)
        self.controls()

    def label(self, parent, text, size=10, bold=False):
        return tk.Label(parent, text=text, font=('Segoe UI', size, 'bold' if bold else 'normal'), bg=parent.cget('bg'), fg=TEXT, justify='left', wraplength=880)

    def button(self, parent, text, command, color='#26364e'):
        return tk.Button(parent, text=text, command=command, bg=color, fg='white', activebackground=color, activeforeground='white', font=('Segoe UI', 10, 'bold'), relief='flat', padx=12, pady=9, cursor='hand2')

    def card(self, body):
        frame = tk.Frame(body, bg=CARD, padx=16, pady=12)
        frame.pack(fill='x', padx=24, pady=7)
        return frame

    def work(self, function, callback):
        def run():
            try:
                self.events.put((callback, function(), None))
            except Exception as exc:
                self.events.put((callback, None, str(exc)))
        threading.Thread(target=run, daemon=True).start()

    def poll(self):
        while not self.events.empty():
            callback, result, error = self.events.get()
            callback(result, error)
        self.root.after(100, self.poll)

    def controls(self):
        self.scan_button.configure(state='disabled' if self.busy else 'normal')
        self.clean_button.configure(state='normal' if self.marked and not self.busy else 'disabled')
        available = any(r['enabled'] and r['file_count'] for r in self.visible_rows())
        self.select_all_button.configure(state='normal' if available and not self.busy else 'disabled')
        self.clear_selection_button.configure(state='normal' if self.marked and not self.busy else 'disabled')
        self.authorize_button.configure(state='normal' if self.authorization_pending and not self.busy else 'disabled')
        selected = [r for r in self.rows if r['id'] in self.marked]
        self.selection_total.configure(text=(f"{len(selected)} {'opção' if len(selected) == 1 else 'opções'} • {amount(sum(r['size_bytes'] for r in selected))}" if selected else 'Nenhuma opção'))

    def visible_rows(self):
        query = self.search.get().strip().casefold()
        return [r for r in self.rows if not query or query in r['name'].casefold()]

    def render_rows(self):
        if not hasattr(self, 'tree'):
            return
        selected = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for item in self.visible_rows():
            usable = item['enabled'] and item['file_count'] > 0
            status = item.get('reason') or (f"{item['file_count']} arquivos • " +
                ('Há itens sem permissão' if item.get('preserved', {}).get('needs_permission') else f"{item['skipped']} itens preservados"))
            self.tree.insert('', 'end', iid=item['id'], values=(
                ('☑' if item['id'] in self.marked else '☐') if usable else '—',
                item['name'], amount(item['size_bytes']) if item['enabled'] else 'Protegido', status),
                tags=() if usable else ('protected',))
        if not self.tree.get_children():
            self.tree.insert('', 'end', iid='empty', values=('', 'Nenhuma opção encontrada' if self.rows else 'Nenhuma análise realizada', '', 'Ajuste a busca.' if self.rows else 'Clique em Analisar computador para começar.'))
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0])
        self.controls()

    def folder_details(self, event=None):
        selection = self.tree.selection()
        item = next((r for r in self.rows if selection and r['id'] == selection[0]), None)
        if item:
            self.folder_detail.set(item.get('path', '') or item['name'])

    def select_available(self):
        if not self.busy:
            self.marked.update(r['id'] for r in self.visible_rows() if r['enabled'] and r['file_count'])
            self.render_rows()

    def clear_selection(self):
        if not self.busy:
            self.marked.clear()
            self.render_rows()

    def scan(self):
        if self.busy:
            return
        self.busy, self.busy_kind = True, 'scan'
        self.scan_stop.clear()
        self.marked.clear()
        self.rows = []
        self.total.configure(text='Analisando…')
        self.file_total.configure(text='—')
        self.set_authorization([])
        self.result.set('Analisando as opções de limpeza…')
        self.cancel_scan_button.pack(side='left', padx=8)
        self.cancel_scan_button.configure(state='normal')
        self.progress.configure(value=0)
        self.render_rows()
        def analyze():
            catalog, rows = targets(), []
            for index, item in enumerate(catalog):
                if self.scan_stop.is_set():
                    break
                self.events.put((self.operation_progress, (index, len(catalog), 'Analisando ' + item['name']), None))
                rows.append(inspect(item, cancel=self.scan_stop))
            return {'rows': rows, 'cancelled': self.scan_stop.is_set()}
        self.work(analyze, self.scanned)

    def operation_progress(self, value, error=None):
        index, total, description = value
        self.progress.configure(maximum=max(total, 1), value=index)
        if not self.scan_stop.is_set() or self.busy_kind != 'scan':
            self.progress_text.set(f'{description} • {index + 1} de {total} opções')

    def cancel_scan(self):
        if self.busy_kind == 'scan':
            self.scan_stop.set()
            self.cancel_scan_button.configure(state='disabled')
            self.progress_text.set('Interrompendo a análise. Nenhum arquivo foi apagado.')

    def finish_operation(self):
        self.busy, self.busy_kind = False, None
        self.cancel_scan_button.pack_forget()
        self.progress.configure(value=0)
        self.controls()

    def scanned(self, value, error):
        self.finish_operation()
        if error:
            self.total.configure(text='—')
            self.result.set('Não foi possível concluir a análise: ' + error)
            self.progress_text.set('Você pode tentar novamente.')
            return
        if isinstance(value, dict) and value.get('cancelled'):
            self.total.configure(text='—')
            self.file_total.configure(text='—')
            self.rows = []
            self.result.set('Análise interrompida. Nenhum arquivo foi apagado.')
            self.progress_text.set('Clique em Analisar computador para começar novamente.')
            self.render_rows()
            return
        self.rows = value['rows'] if isinstance(value, dict) else value
        self.marked = set()
        self.set_authorization(self.rows)
        self.total.configure(text=amount(sum(r['size_bytes'] for r in self.rows)))
        self.file_total.configure(text=str(sum(r['file_count'] for r in self.rows)))
        self.scan_button.configure(text='Analisar novamente')
        self.result.set('Análise concluída. Marque as opções que deseja limpar.')
        self.progress_text.set('A análise é uma estimativa. A verificação de segurança acontece novamente antes de apagar.')
        self.render_rows()

    def toggle(self, event=None):
        if self.busy or not self.rows:
            return
        if event is not None and getattr(event, 'keysym', '') != 'space':
            if self.tree.identify_column(event.x) != '#1':
                return
            row = self.tree.identify_row(event.y)
            if not row:
                return
            self.tree.selection_set(row)
        selection = self.tree.selection()
        item = next((r for r in self.rows if selection and r['id'] == selection[0]), None)
        if not item or not item['enabled'] or not item['file_count']:
            return
        key = item['id']
        self.marked.symmetric_difference_update({key})
        self.tree.set(key, 'choice', '☑' if key in self.marked else '☐')
        self.controls()
        return 'break'

    def clean(self):
        if self.busy or not self.marked:
            return
        chosen = [r for r in self.rows if r['id'] in self.marked]
        summary = '\n'.join('• ' + r['name'] for r in chosen)
        if not confirm_action(self.root, 'Confirmar limpeza',
                summary + f"\n\nEstimativa: {amount(sum(r['size_bytes'] for r in chosen))}.\n"
                'A exclusão é permanente e não passa pela Lixeira. Arquivos abertos e protegidos serão preservados.'):
            return
        ids = set(self.marked)
        self.busy, self.busy_kind = True, 'clean'
        self.controls()
        self.result.set('Limpando… Aguarde antes de encerrar.')
        def remove():
            with cleaning_guard():
                catalog = [r for r in targets() if r['id'] in ids and r['enabled']]
                results = []
                for index, item in enumerate(catalog):
                    self.events.put((self.operation_progress, (index, len(catalog), 'Limpando ' + item['name']), None))
                    results.append(inspect(item, clean=True))
                warning = ''
                try:
                    self.local.record('manual', results)
                except OSError:
                    warning = '\nA limpeza terminou, mas não foi possível guardar o histórico.'
                return {'results': results, 'warning': warning}
        def done(value, error):
            self.rows, self.marked = [], set()
            self.finish_operation()
            self.total.configure(text='—')
            self.file_total.configure(text='—')
            self.render_rows()
            self.progress_text.set('Analise novamente quando desejar fazer outra limpeza.')
            if error:
                self.result.set('Não foi possível concluir: ' + error)
            else:
                results = value['results']
                self.set_authorization(results)
                self.result.set(f"{sum(r['file_count'] for r in results)} arquivos removidos • "
                                + amount(sum(r['size_bytes'] for r in results)) + ' liberados'
                                + '\n' + preservation_summary(results)
                                + '\nAs contagens podem incluir pastas inacessíveis; não estimamos seu conteúdo.' + value['warning'])
                self.refresh_history()
        self.work(remove, done)

    def set_authorization(self, results):
        self.authorization_pending = any(r['id'] == 'system_temp' and r.get('preserved', {}).get('needs_permission', 0) for r in results)
        if self.authorization_pending:
            self.authorize_button.pack(anchor='w', pady=(9, 0))
        else:
            self.authorize_button.pack_forget()
        self.authorize_button.configure(state='normal' if self.authorization_pending and not self.busy else 'disabled')

    def authorize(self):
        if self.busy or not self.authorization_pending:
            return
        if not confirm_action(self.root, 'Autorização opcional',
                'Tentar limpar somente os temporários do Windows?\n\n'
                'O Windows poderá pedir aprovação ou senha de administrador. '
                'Depois disso, uma janela confirmará a exclusão. '
                'Arquivos em uso e protegidos continuarão preservados.', 'Solicitar autorização'):
            return
        self.busy, self.busy_kind = True, 'authorization'
        self.controls()
        previous = self.result.get()
        self.result.set('Aguardando autorização e conclusão da etapa opcional…')
        def done(state, error):
            self.finish_operation()
            if error:
                self.result.set(previous + '\nNão foi possível concluir a etapa autorizada: ' + error)
            elif state == 'cancelled':
                self.result.set(previous + '\nAutorização cancelada. Nenhuma limpeza adicional foi feita.')
            else:
                self.rows, self.marked = [], set()
                self.set_authorization([])
                self.render_rows()
                self.total.configure(text='—')
                self.file_total.configure(text='—')
                self.result.set(previous + '\nEtapa autorizada encerrada. O resultado foi exibido na janela auxiliar. Analise novamente para atualizar.')
        self.work(request_authorization, done)

    def refresh_schedule_status(self):
        config = read_schedule()
        enabled = config.get('enabled') is True
        self.schedule_text.set('Ativado diariamente às ' + config['hour'] if enabled else 'Desativado • você decide quando limpar')
        if hasattr(self, 'schedule_save_button'):
            self.schedule_save_button.configure(state='disabled' if self.schedule_busy else 'normal')
            self.schedule_disable_button.configure(state='normal' if enabled and not self.schedule_busy else 'disabled')

    def save_schedule(self):
        if self.schedule_busy:
            return
        ids = [key for key, value in self.choices.items() if value.get()]
        hour = self.hour.get().strip()
        import re
        if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', hour) or not ids:
            messagebox.showinfo('Confira o agendamento', 'Informe um horário como 18:30 e marque pelo menos uma opção pessoal.', parent=self.root)
            return
        if not confirm_action(self.root, 'Ativar limpeza diária',
                f'Limpar as opções pessoais marcadas todos os dias às {hour}?\n\n'
                'A exclusão será permanente e não pedirá nova confirmação. '
                'O computador precisa estar ligado e seu usuário conectado.', 'Ativar limpeza diária'):
            return
        self.schedule_busy = True
        self.refresh_schedule_status()
        self.schedule_text.set('Salvando o horário no Windows…')
        def done(value, error):
            self.schedule_busy = False
            self.refresh_schedule_status()
            if error:
                messagebox.showinfo('Agendamento', str(error), parent=self.root)
        self.work(lambda: configure(hour, ids), done)

    def disable_schedule(self):
        if self.schedule_busy:
            return
        self.schedule_busy = True
        self.refresh_schedule_status()
        def done(value, error):
            self.schedule_busy = False
            self.refresh_schedule_status()
            if error:
                messagebox.showinfo('Agendamento', str(error), parent=self.root)
        self.work(disable, done)

    def last_result(self):
        report = read_json(data_dir() / 'last-clean.json', {})
        if not isinstance(report, dict) or not report.get('at'):
            messagebox.showinfo('Última limpeza automática', 'Ainda não há resultado de uma limpeza automática.', parent=self.root)
            return
        self.show_text('Última limpeza automática', self.history_text(report))

    def history_text(self, entry):
        try:
            when = datetime.fromisoformat(entry['at']).strftime('%d/%m/%Y às %H:%M')
        except (KeyError, TypeError, ValueError):
            when = 'Data não informada'
        return (f"{when}\n{count(entry.get('deleted'))} arquivos removidos • {amount(count(entry.get('freed')))} liberados\n"
                + preservation_summary([entry]))

    def refresh_history(self):
        if not hasattr(self, 'history_tree'):
            return
        self.history_entries = self.local.history()
        self.history_tree.delete(*self.history_tree.get_children())
        for index, entry in enumerate(self.history_entries):
            when = datetime.fromisoformat(entry['at']).strftime('%d/%m/%Y às %H:%M')
            self.history_tree.insert('', 'end', iid=str(index), values=(when, 'Manual' if entry['mode'] == 'manual' else 'Automática', entry['deleted'], amount(entry['freed'])))
        self.history_status.set(f'{len(self.history_entries)} limpezas registradas' if self.history_entries else 'Seu histórico aparecerá aqui depois da primeira limpeza.')

    def history_details(self):
        selection = self.history_tree.selection()
        if selection:
            self.show_text('Detalhes da limpeza', self.history_text(self.history_entries[int(selection[0])]))
        else:
            messagebox.showinfo('Histórico', 'Selecione uma limpeza para consultar seus detalhes.', parent=self.root)

    def tab_changed(self, event=None):
        if hasattr(self, 'history_tree') and self.notebook.select() == str(self.pages['history']):
            self.refresh_history()
        if hasattr(self, 'schedule_text') and self.notebook.select() == str(self.pages['schedule']):
            self.refresh_schedule_status()

    def show_text(self, title, contents):
        from tkinter.scrolledtext import ScrolledText
        dialog = tk.Toplevel(self.root)
        dialog.title('CleanTemp • ' + title)
        dialog.configure(bg=BG)
        dialog.geometry('740x510')
        dialog.transient(self.root)
        text = ScrolledText(dialog, wrap='word', font=('Segoe UI', 11), bg=CARD, fg=TEXT, padx=18, pady=18)
        text.pack(fill='both', expand=True, padx=16, pady=16)
        text.insert('1.0', contents)
        text.configure(state='disabled')
        row = tk.Frame(dialog, bg=BG)
        row.pack(fill='x', padx=16, pady=(0, 16))
        def copy():
            dialog.clipboard_clear()
            dialog.clipboard_append(contents)
            copy_button.configure(text='Copiado')
        def save():
            filename = filedialog.asksaveasfilename(parent=dialog, title='Guardar resultado', defaultextension='.txt',
                initialfile='CleanTemp-resultado-' + datetime.now().strftime('%Y%m%d-%H%M') + '.txt', filetypes=[('Texto', '*.txt')])
            if filename:
                try:
                    Path(filename).write_text(contents, encoding='utf-8')
                except OSError:
                    messagebox.showinfo('Guardar resultado', 'Não foi possível guardar nesse local. Escolha outra pasta.', parent=dialog)
        copy_button = self.button(row, 'Copiar resultado', copy)
        copy_button.pack(side='left')
        self.button(row, 'Guardar em arquivo', save).pack(side='left', padx=8)
        self.button(row, 'Fechar', dialog.destroy).pack(side='right')

    def show_result(self):
        self.show_text('Resultado da limpeza', self.result.get())

    def start_updates(self):
        if self.auto_updates.get():
            self.update()
        if not getattr(self, 'update_timer', None):
            self.update_timer = self.root.after(60000, self.periodic_update)

    def save_update_preference(self):
        try:
            self.local.save_preferences({'automatic_updates': self.auto_updates.get()})
        except OSError:
            messagebox.showinfo('Preferência', 'Não foi possível guardar a preferência para a próxima abertura.', parent=self.root)
        if self.auto_updates.get():
            self.update()

    def update(self):
        if self.updating:
            return
        self.updating = True
        self.check_update_button.configure(state='disabled')
        self.update_text.configure(text='Verificando novidades…')
        def done(value, error):
            self.updating = False
            self.check_update_button.configure(state='normal')
            if error or not value:
                self.update_text.configure(text='Sem conexão. Você pode continuar usando normalmente.')
            elif value['state'] == 'available':
                self.update_text.configure(text='Nova versão disponível: ' + value['latest_version'])
                self.update_url = value['url']
                self.update_button.pack(side='left', padx=8)
            else:
                self.update_url = ''
                self.update_button.pack_forget()
                self.update_text.configure(text={'current': 'Você está usando a versão mais recente.', 'no_release': 'Ainda não há uma nova versão publicada.'}.get(value['state'], 'Sem novidades no momento. A limpeza funciona offline.'))
        self.work(lambda: checker.check(read_config()['github_repository']), done)
        if not getattr(self, 'update_timer', None):
            self.update_timer = self.root.after(60000, self.periodic_update)

    def periodic_update(self):
        self.update_timer = None
        if self.auto_updates.get():
            self.update()
        if not self.update_timer:
            self.update_timer = self.root.after(60000, self.periodic_update)

    def open_update(self):
        if self.update_url:
            webbrowser.open(self.update_url)

    def show_terms(self):
        from tkinter.scrolledtext import ScrolledText
        window = tk.Toplevel(self.root)
        window.title('CleanTemp • Termos de uso')
        window.geometry('760x560')
        window.transient(self.root)
        text = ScrolledText(window, wrap='word', font=('Segoe UI', 11), bg=CARD, fg=TEXT, padx=18, pady=18)
        text.pack(fill='both', expand=True)
        text.insert('1.0', (RESOURCE_ROOT / 'TERMS.txt').read_text('utf-8-sig'))
        text.configure(state='disabled')
        self.button(window, 'Fechar', window.destroy).pack(pady=8)

    def support(self, channel):
        url = read_config()['support'][channel]
        if url:
            webbrowser.open(url)
        else:
            messagebox.showinfo('Suporte', 'Em desenvolvimento. Este canal estará disponível em breve.', parent=self.root)

    def guide(self):
        try:
            os.startfile(str(RESOURCE_ROOT / 'output/pdf/cleantemp-primeiros-passos.pdf'))
        except OSError:
            messagebox.showinfo('Guia em PDF', 'Defina um leitor de PDF no Windows para abrir o guia.', parent=self.root)

    def tour(self):
        if self.tour_window and self.tour_window.winfo_exists():
            self.tour_window.lift()
            return
        window = self.tour_window = tk.Toplevel(self.root)
        window.title('CleanTemp • Primeiros passos')
        window.geometry('570x340')
        window.configure(bg=CARD)
        window.transient(self.root)
        window.grab_set()
        previous_tab = self.notebook.select()
        self.tour_index = 0
        progress = self.label(window, '', 10)
        progress.pack(anchor='w', padx=24, pady=(20, 8))
        title = self.label(window, '', 18, True)
        title.pack(anchor='w', padx=24, pady=8)
        text = self.label(window, '', 12)
        text.configure(wraplength=510)
        text.pack(fill='both', expand=True, padx=24, pady=8)
        controls = tk.Frame(window, bg=CARD)
        controls.pack(fill='x', padx=24, pady=20)
        def close():
            try:
                data_dir().mkdir(parents=True, exist_ok=True)
                (data_dir() / 'tour-seen').touch()
            except OSError:
                pass
            self.notebook.select(previous_tab)
            window.destroy()
        def move(delta):
            if self.tour_index + delta >= len(TOUR):
                close()
                return
            self.tour_index += delta
            render()
        self.button(controls, 'Saltar', close).pack(side='left')
        next_button = self.button(controls, 'Próximo', lambda: move(1), '#167f78')
        next_button.pack(side='right')
        previous = self.button(controls, 'Anterior', lambda: move(-1))
        previous.pack(side='right', padx=8)
        def render():
            tab = 'schedule' if self.tour_index == 4 else 'history' if self.tour_index == 5 else 'help' if self.tour_index == 6 else 'clean'
            self.notebook.select(self.pages[tab])
            progress.configure(text=f'Passo {self.tour_index + 1} de {len(TOUR)} • Nenhum arquivo será apagado neste guia')
            title.configure(text=TOUR[self.tour_index][0])
            text.configure(text=TOUR[self.tour_index][1])
            previous.configure(state='disabled' if self.tour_index == 0 else 'normal')
            next_button.configure(text='Concluir' if self.tour_index == len(TOUR) - 1 else 'Próximo')
        window.protocol('WM_DELETE_WINDOW', close)
        window.bind('<Escape>', lambda event: close())
        render()

    def close(self):
        if self.busy or self.schedule_busy:
            messagebox.showinfo('Aguarde', 'Aguarde a operação terminar antes de encerrar.', parent=self.root)
        else:
            self.root.destroy()
