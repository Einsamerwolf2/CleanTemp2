"""Create the offline first-steps guide included with CleanTemp."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf/cleantemp-primeiros-passos.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
fonts = Path('C:/Windows/Fonts')
pdfmetrics.registerFont(TTFont('Guide', str(fonts / 'segoeui.ttf')))
pdfmetrics.registerFont(TTFont('GuideBold', str(fonts / 'segoeuib.ttf')))
pdfmetrics.registerFontFamily('Guide', normal='Guide', bold='GuideBold')
NAVY = colors.HexColor('#102136')
TEAL = colors.HexColor('#087d75')
MUTED = colors.HexColor('#52667d')
styles = {
    'title': ParagraphStyle('title', fontName='GuideBold', fontSize=30, leading=36, textColor=NAVY, spaceAfter=12),
    'subtitle': ParagraphStyle('subtitle', fontName='Guide', fontSize=12, leading=18, textColor=MUTED, spaceAfter=14),
    'h2': ParagraphStyle('h2', fontName='GuideBold', fontSize=15, leading=20, textColor=TEAL, spaceBefore=12, spaceAfter=6),
    'body': ParagraphStyle('body', fontName='Guide', fontSize=10.5, leading=16, textColor=NAVY, spaceAfter=10),
    'card': ParagraphStyle('card', fontName='Guide', fontSize=10.5, leading=16, textColor=NAVY, spaceAfter=0),
    'number': ParagraphStyle('number', fontName='GuideBold', fontSize=24, leading=30, textColor=TEAL),
    'small': ParagraphStyle('small', fontName='Guide', fontSize=9, leading=14, textColor=MUTED, spaceAfter=8),
}

def p(text, style='body'):
    return Paragraph(text, styles[style])

def card(title, text):
    table = Table([[p(f'<b>{title}</b><br/>{text}', 'card')]], colWidths=[475])
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#eef8f6')),('BOX',(0,0),(-1,-1),0.6,colors.HexColor('#b5ddd6')),('LEFTPADDING',(0,0),(-1,-1),14),('RIGHTPADDING',(0,0),(-1,-1),14),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12)]))
    return table

def step(number, title, text):
    table = Table([[p(str(number),'number'), p(f'<b>{title}</b><br/>{text}', 'card')]], colWidths=[42,433])
    table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,-1),0.5,colors.HexColor('#dce6eb'))]))
    return table

def page(canvas, doc):
    width, height = A4
    canvas.saveState()
    canvas.drawImage(str(ROOT / 'assets/cleantemp.png'), 56, height-52, width=24, height=24, mask='auto')
    canvas.setFont('GuideBold',10)
    canvas.setFillColor(NAVY)
    canvas.drawString(88,height-43,'CleanTemp')
    canvas.setFont('Guide',8)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(width-56,height-43,'Guia de primeiros passos | v1.4.0')
    canvas.setStrokeColor(colors.HexColor('#dce6eb'))
    canvas.line(56,45,width-56,45)
    canvas.setFont('Guide',8)
    canvas.drawString(56,30,'CleanTemp - Criado por Edilson Enoque')
    canvas.drawRightString(width-56,30,f'{doc.page} / 4')
    canvas.restoreState()

story = [p('CleanTemp','title'),p('Primeiros passos • Versão 1.4.0','subtitle'),p('Instalar e abrir','h2'),p('Abra o instalador oficial, leia e aceite os termos. A instalação padrão é em Program Files\\CleanTemp e exige autorização de administrador. O aplicativo funciona como usuário normal e inclui Python e todas as bibliotecas.'),p('Abra CleanTemp pelo menu Iniciar. Todas as funções aparecem na própria janela, sem abrir navegador. Nenhum cadastro é necessário.'),p('Sua primeira limpeza','h2'),step(1,'Analisar','Na aba Limpeza, clique em Analisar. Nenhum arquivo é apagado. Parar análise interrompe a leitura e descarta a seleção parcial.'),step(2,'Escolher','Use a primeira coluna ou Espaço para marcar opções. Pesquise pelo nome e confira o tamanho selecionado. Áreas protegidas permanecem bloqueadas.'),step(3,'Confirmar','Clique em Limpar selecionados. Confirme apenas se concordar com a exclusão permanente, sem passar pela Lixeira.'),card('Como usar','O passeio oferece Próximo, Anterior, Saltar e Concluir. Ele apenas explica e não apaga arquivos.'),PageBreak(),p('Segurança e horário','title'),p('O que será preservado','h2'),p('Somente temporários com mais de 24 horas são considerados. Todas as pastas são mantidas. Arquivos abertos, somente leitura, de sistema, links e arquivos sem acesso ou verificação ficam preservados. Windows Installer, Windows Update, CBS, Defender e Prefetch permanecem protegidos.'),card('Cuidados','Um arquivo fechado ainda pode ser necessário a outro programa. Não force exclusões nem altere permissões para obter mais espaço.'),p('Limpeza automática','h2'),p('Na aba Agendamento, desativada por padrão. Escolha as opções pessoais e informe o horário no formato HH:MM. Clique em Ativar / salvar horário e leia a confirmação: ela autoriza a exclusão diária sem uma nova pergunta.'),p('O Windows executa a limpeza sem abrir a interface, somente com o computador ligado e seu usuário conectado. Não exige senha armazenada, não eleva permissões, não acorda o computador e não recupera horários perdidos. O horário segue o relógio local do Windows.'),p('Use Desativar para cancelar. Último resultado mostra o resumo da limpeza automática. Arquivos abertos e protegidos continuam preservados.'),p('Fechar e desinstalar','h2'),p('Feche a janela quando terminar. Um agendamento ativado continua no Windows. Para remover o programa, use Configurações > Aplicativos > CleanTemp > Desinstalar. O desinstalador remove os arquivos, dependências privadas, atalhos e tarefas vinculadas à instalação. Outros programas não são afetados. Pequenos registros de outras contas podem permanecer em AppData/Local/CleanTemp.'),PageBreak(),p('Autorização opcional','title'),p('Quando é necessária?','h2'),p('Depois de analisar ou limpar, alguns temporários do Windows podem permanecer por falta de permissão. Nesse caso, o botão Tentar limpar com autorização fica disponível. A limpeza normal continua disponível sem administrador.'),p('Como funciona','h2'),step(1,'Escolher','Clique em Tentar limpar com autorização. Leia o aviso e continue somente se concordar.'),step(2,'Aprovar no Windows','O Windows poderá pedir aprovação ou credenciais de administrador. Cancelar não inicia limpeza adicional. O aplicativo não guarda sua senha.'),step(3,'Confirmar o local','Uma janela auxiliar confirma a pasta Temp do Windows e a exclusão permanente. Ela mostra o resultado e termina. A janela principal continua com acesso normal.'),card('Proteções mantidas','Mesmo com autorização, arquivos abertos, recentes, protegidos e não verificados continuam preservados. Nenhuma pasta é removida. O agendamento nunca pede autorização de administrador.'),p('Instalação e resultados','h2'),p('Esta função exige o aplicativo instalado na pasta padrão de Arquivos de Programas. O resultado separa itens em uso, sem permissão, preservados por segurança, recentes, não encontrados e não verificados. Uma pasta sem acesso conta como um item; seu conteúdo não é estimado.'),PageBreak(),p('Precisa de ajuda?','title'),p('Canais de assistência','h2'),p('Na aba Ajuda, escolha Discord, Telegram ou WhatsApp. Até os links oficiais serem configurados, os botões mostram Em desenvolvimento. Nenhuma mensagem ou relatório é enviado automaticamente. O atendimento externo exige internet; a limpeza, o tour e este PDF funcionam offline.'),p('Enquanto os canais estão em desenvolvimento','h2'),p('Registre um relato na página do projeto. O GitHub pode pedir login para publicar; a aplicação não exige cadastro.'),p('<link href="https://github.com/Einsamerwolf2/CleanTemp2/issues" color="#087d75">github.com/Einsamerwolf2/CleanTemp2/issues</link>'),card('Pedido de assistência','Versão do CleanTemp: 1.4.0<br/>Versão do Windows: ...<br/>O que tentei fazer: ...<br/>O que aconteceu: ...<br/>Mensagem exibida: ...<br/>Acontece sempre ou às vezes? ...'),p('Proteja seus dados','h2'),p('Revise imagens e registros antes de compartilhar. Esconda caminhos privados, nomes e documentos. Nunca envie senhas, tokens ou códigos de acesso.'),p('Se não abrir','h2'),p('Abra apenas uma cópia pelo menu Iniciar. Anote a mensagem de erro e solicite assistência. Reinstale somente pelo projeto oficial. Não é necessário instalar Python.'),p('Atualizações','h2'),p('Histórico guarda até 60 resumos locais, sem nomes de arquivos. Na Ajuda, você pode desativar a consulta automática de versões. Com internet, o CleanTemp consulta versões publicadas no GitHub. Ele oferece o link para atualizar; não baixa nem instala nada automaticamente. A limpeza funciona sem conexão.'),p('Criado por Edilson Enoque • Código aberto sob licença MIT.','small')]

doc = SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=60, leftMargin=60, topMargin=76, bottomMargin=62, title='CleanTemp - Primeiros passos', author='Edilson Enoque', subject='Instalação, uso seguro e assistência')
doc.build(story, onFirstPage=page, onLaterPages=page)
print(OUT)

