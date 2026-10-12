# CleanTemp Lite

Aplicativo local para Windows com backend Flask e interface HTML/CSS/JavaScript, sem dependências de CDN. A janela é aberta no navegador padrão.

## Executar

Instale Python 3.10 ou superior com o launcher `py`. Dê duplo clique em `iniciar.bat`. Na primeira execução, o script prepara `.venv` e instala Flask (requer internet). Acesse http://127.0.0.1:5000. Feche o terminal ou pressione Ctrl+C para encerrar. Para acessar pastas do sistema, execute o script como administrador, se necessário.

Alternativamente:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe backend/app.py
```

## Organização

- `backend/app.py`: servidor local, validação da API e entrega do frontend.
- `backend/cleaner.py`: catálogo de caminhos, análise e exclusão.
- `backend/requirements.txt`: dependências; `requiremets.txt` mantido como compatibilidade.
- `frontend/index.html`: painel principal.
- `frontend/src/app.js` e `styles.css`: comportamento e aparência.
- `frontend/src/windows_cleaner_dashboard.html`: redirecionamento do painel antigo.

## Regras de limpeza

Os caminhos vêm de `windows_temporary_directories_reference.md` e das variáveis do Windows (`SystemRoot`, `USERPROFILE`, `LOCALAPPDATA`, `ProgramData`, `TEMP`). Também são incluídas as pastas Temp do usuário e do sistema.

A análise conta somente arquivos modificados há mais de 24 horas. Nenhuma limpeza ocorre ao abrir o aplicativo ou analisar. Selecione as pastas e confirme no painel para excluir permanentemente os arquivos elegíveis. Diretórios raiz e subpastas são preservados; arquivos bloqueados são ignorados e as falhas são contabilizadas. O espaço exibido é a soma dos tamanhos lógicos dos arquivos excluídos, não uma medição dos blocos livres do disco.

Explorer permite apenas `thumbcache_*.db`. Links simbólicos e junções não são percorridos. Installer, Windows Update, CBS, Defender e Prefetch são exibidos como protegidos, pois sua limpeza indiscriminada pode interferir na manutenção do sistema. O documento de referência é um inventário, não uma autorização para excluir todo o conteúdo dessas pastas.

O servidor escuta somente em 127.0.0.1:5000, sem debug ou CORS aberto. Requisições de exclusão exigem um token da sessão e IDs do catálogo; a API não aceita caminhos enviados pelo cliente. Não execute várias instâncias nem altere links/pastas durante a limpeza.

## Verificação

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
```

Os testes usam arquivos descartáveis; não limpam pastas reais do Windows.

## Suporte e atualizações

O CleanTemp não exige cadastro. O rodapé apresenta apenas o nome do aplicativo e do criador. Os canais de suporte são abertos somente quando a pessoa clica; nenhum relatório é enviado automaticamente.

Configure `app_config.json` antes de distribuir:

```json
{
  "github_repository": "SEU_USUARIO/CleanTemp",
  "support": {
    "discord": "https://discord.gg/SEU_CONVITE",
    "telegram": "https://t.me/SEU_USUARIO",
    "whatsapp": ""
  }
}
```

Substitua os exemplos pelos endereços reais. Enquanto não forem configurados, os três botões mostram “Em desenvolvimento” ao clicar. Para ativar WhatsApp, informe `https://wa.me/NUMERO_COM_CODIGO_DO_PAIS` para abrir o canal. Os links devem usar HTTPS e os domínios oficiais dos canais.

A verificação consulta a última release pública estável no GitHub, ao abrir e periodicamente enquanto o painel estiver visível, além de tentar novamente quando a conexão voltar. Consultas bem-sucedidas são reutilizadas por 15 minutos; falhas podem ser tentadas novamente após um minuto. O botão de verificação usa o mesmo intervalo para evitar excesso de consultas. A API pública dispensa conta ou token. Use tags `v1.0.1`, `v1.1.0`, etc.; a versão instalada é definida em `backend/settings.py`. A aplicação apenas avisa e oferece um link, sem baixar ou executar arquivos de atualização.

A limpeza e todos os recursos visuais funcionam sem internet após a preparação inicial. O iniciador instala dependências apenas se ainda faltarem; não executa `pip install` a cada abertura. Esta versão ainda usa Python e navegador: a primeira preparação precisa de Python instalado e internet para obter Flask. Para distribuir a usuários sem esses pré-requisitos será necessário gerar posteriormente um instalador com as dependências incluídas.

Configuração e atualizações ficam em módulos separados (`settings.py`, `updates.py`) para permitir evolução sem alterar o mecanismo de limpeza. O código está sob licença MIT em `LICENSE`; o repositório configurado é https://github.com/Einsamerwolf2/CleanTemp2.

