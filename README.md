# CleanTemp 1.4.0

A janela está organizada em **Limpeza**, **Agendamento**, **Histórico** e **Ajuda**. Na limpeza, pesquise opções, marque pela primeira coluna ou pela tecla Espaço e confira o tamanho selecionado. A análise pode ser interrompida sem apagar arquivos. As confirmações identificam a ação e oferecem Cancelar.

O histórico guarda os últimos 60 resumos de limpezas manuais e automáticas somente neste computador, sem nomes ou caminhos dos arquivos. A aba Ajuda permite desligar a consulta automática de atualizações. Configurações inválidas de agendamento deixam a execução automática desativada por segurança.

Aplicativo para Windows criado por Edilson Enoque. Sem cadastro, com janela própria, limpeza offline e código aberto sob licença MIT.

## Instalar e usar

Use `dist/installer/CleanTemp-Setup-1.4.0-x64.exe` no Windows 10/11 x64. O pacote inclui Python e os componentes necessários; o usuário não instala bibliotecas. A instalação exige aceitar os termos e autorizar o Windows. A pasta padrão de Arquivos de Programas é obrigatória para manter a limpeza autorizada em uma instalação protegida.

Abra CleanTemp pelo menu Iniciar ou atalho. Clique em **Analisar**, marque as opções e use **Limpar selecionados**. Leia a confirmação: a exclusão é permanente e não passa pela Lixeira. A janela apresenta resultados detalhados. Feche a janela para encerrar. **Como usar** oferece um tour com Próximo, Anterior e Saltar.

Não há servidor HTTP nem navegador na inicialização do executável. Os termos aparecem dentro do aplicativo. O PDF abre no leitor padrão. Somente cliques explícitos em suporte e em **Ver nova versão** podem abrir páginas externas. A consulta periódica de atualizações é feita diretamente ao GitHub, sem abrir páginas, baixar ou executar instaladores automaticamente.

## Proteções e autorização

Somente temporários com mais de 24 horas são candidatos. A API nativa do Windows verifica o arquivo e obtém acesso exclusivo antes de pedir exclusão pelo mesmo handle. Diretórios, arquivos abertos, somente leitura, de sistema, links, junções e arquivos com hardlinks adicionais são preservados. Nenhuma pasta é removida. Installer, Windows Update, CBS, Defender e Prefetch continuam bloqueados.

Arquivos fechados ainda podem ser necessários a programas; por isso a lista permitida é restrita. Não alteramos permissões, não encerramos aplicações e não paramos serviços. A análise é uma estimativa e o tamanho lógico removido pode diferir do espaço livre mostrado pelo Windows.

O resultado distingue em uso, sem permissão, segurança, recentes, não encontrados e não verificados. Pastas sem acesso contam como eventos, sem estimar quantos arquivos contêm. Acesso negado não garante que administrador resolverá.

**Tentar limpar com autorização** fica disponível quando temporários do Windows têm itens sem permissão. O aplicativo principal permanece sem elevação. Um processo separado solicita UAC e confirma o local antes de limpar apenas Windows/Temp, obtido da API do Windows. Aceita somente o identificador fixo `system_temp`, nunca caminhos nem configurações de perfis do usuário. Cancelar não faz limpeza adicional. Todas as proteções permanecem ativas; o auxiliar mostra seu resultado e termina. Instalações fora da pasta padrão ou com links/junções recusam essa função.

## Agendamento

Desativado por padrão. Escolha as opções pessoais, informe HH:MM e confirme **Ativar / salvar horário**. Isso autoriza exclusões permanentes diárias sem nova pergunta. **Desativar** remove a tarefa; **Último resultado** mostra o resumo local.

O Windows executa `CleanTemp.exe --scheduled-clean` sem interface, senha armazenada ou elevação. Exige computador ligado e usuário conectado. Não acorda o computador nem recupera horários perdidos. O horário segue o fuso local do Windows. Somente Temp do usuário, Direct3D, NVIDIA e relatórios pessoais são elegíveis. A mesma trava impede limpezas manual, agendada e autorizada simultâneas. O agendamento nunca pede UAC.

## Suporte e privacidade

Discord, Telegram e WhatsApp usam cores e ícones próprios. Até links oficiais serem configurados em `app_config.json`, mostram **Em desenvolvimento**. Nenhuma mensagem ou relatório é enviado automaticamente. A ajuda offline está em `output/pdf/cleantemp-primeiros-passos.pdf` e acompanha a instalação.

Atualizações consultam releases públicas estáveis de `Einsamerwolf2/CleanTemp2`. O GitHub recebe as informações normais de uma conexão de internet, como o IP. Consultas são armazenadas por 15 minutos; falhas podem ser tentadas novamente após um minuto. Limpeza e ajuda continuam funcionando offline. Relatos podem ser publicados em https://github.com/Einsamerwolf2/CleanTemp2/issues, que pode exigir uma conta GitHub.

## Desinstalar

Use Configurações > Aplicativos > CleanTemp > Desinstalar. O desinstalador remove arquivos instalados, dependências privadas, atalhos e tarefas ligadas ao caminho desta instalação. Não remove o Python de outros programas nem componentes do Windows. Dados conhecidos da conta que executa o desinstalador também são removidos. Outras contas podem conservar pequenos registros em `%LOCALAPPDATA%\CleanTemp`, que podem apagar depois. Arquivos eliminados na limpeza não são recuperados.

Se ainda usa a antiga instalação 1.0.0 por usuário, desinstale-a antes para evitar duas cópias.

## Desenvolver e compilar

O usuário final usa o instalador; estas instruções são para desenvolvimento:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe backend/desktop.py
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
node --test frontend/tests/app.test.cjs
powershell -ExecutionPolicy Bypass -File packaging/build.ps1
```

O build usa PyInstaller e Inno Setup. A interface HTML e a API Flask ficam como alternativa de desenvolvimento no repositório e não são incluídas no executável nativo. O manifesto do aplicativo é `asInvoker`; somente o instalador e o auxiliar escolhido pelo usuário solicitam elevação. Instalação silenciosa exige `/ACCEPTTERMS=1`, apenas para quem já leu e aceitou os termos.

## Validação real e limites

Além dos testes de unidade, `--functional-check-report <arquivo.json>` cria uma pasta única de arquivos descartáveis no perfil local. Faz análise e exclusão reais, verifica preservação de arquivos abertos/recentes/somente leitura/hardlinks e usa uma tarefa real do Windows para executar a mesma rotina de limpeza agendada em um perfil isolado. A tarefa de validação é removida no final. Os arquivos restantes e o relatório servem como evidência. A rotina não limpa temporários reais do usuário ou do Windows.

O build executa a inicialização nativa e essa verificação no EXE empacotado. Qualquer bloqueio de execução ou falha é registrado e interrompe o build normal. O parâmetro explícito `-PackageWithoutRuntimeValidation` permite somente compilar o instalador, deixando registrado o que não foi validado; ele não contorna políticas do Windows nem transforma uma falha em sucesso.

A aprovação e o cancelamento de UAC precisam de validação interativa no aplicativo instalado, incluindo conta básica com credenciais de outro administrador. Os testes simulados desse fluxo não substituem a validação real. A política de controle de aplicações deste computador bloqueou um executável anterior; os relatórios da nova compilação registram o resultado atual. Não desative proteções para executar o programa.

## Uso por pessoas e entidades; assinatura para distribuição

A licença MIT permite uso pessoal, comercial e institucional, mantendo os avisos da licença. O CleanTemp não exige cadastro, ativação, pagamento ou conexão para limpar. Regras de segurança de cada computador continuam valendo; não é possível prometer execução irrestrita em todas as organizações.

Nesta máquina, a versão 1.3.0 foi bloqueada pelos eventos 3033 e 3077 de CodeIntegrity por exigência de assinatura. O certificado local encontrado pertence a outro aplicativo e é autoassinado: não foi usado, não foi exportado e não foi criada confiança artificial. Sem um certificado reconhecido ou uma autorização legítima do responsável pela política, não há validação do EXE instalado neste ambiente.

O build suporta um certificado reconhecido já instalado no repositório pessoal do desenvolvedor e o `signtool.exe` do Windows SDK:

```powershell
powershell -ExecutionPolicy Bypass -File packaging/build.ps1 -CertificateThumbprint <thumbprint> -SignToolPath <signtool.exe> -TimestampUrl <URL-HTTPS-do-servico-de-carimbo>
```

Esse fluxo assina o aplicativo, o instalador e o desinstalador. Rejeita certificados autoassinados e verifica as assinaturas. Nenhuma chave ou senha é incluída no repositório. Certificados em serviços remotos podem exigir integração específica do fornecedor. Assinatura identifica o editor; não substitui aprovação interna de uma organização nem garante ausência de alertas.

Resultado real disponível: `dist/functional-source-1.3.0.json` (análise, exclusão e agendamento reais em arquivos descartáveis). Resultado do pacote: `dist/release-validation.json`. O instalador 1.3.0 inclui as funcionalidades, mas permanece sem assinatura e não está aprovado para distribuição geral.

## Correção de distribuição (1.3.1)

O EXE de `build/CleanTemp` é intermediário e não inclui as DLLs ao lado. Não o execute nem distribua. Os intermediários novos ficam em `.tools/pyinstaller`. O executável intermediário antigo foi renomeado para `.build-only.bin` para evitar confusão. Use o instalador em `dist/installer`, ou distribua a pasta **inteira** `dist/CleanTemp`, incluindo `_internal`. O usuário final não instala Python, Visual C++, Flask ou ferramentas de desenvolvimento.

A conferência do pacote exige Python DLL, runtimes Visual C++, Tk e recursos; o instalador confere os componentes obrigatórios depois de copiá-los. O erro de Python DLL da imagem apontava para o intermediário em build, não para uma instalação em Arquivos de Programas. Atalhos antigos por usuário podem apontar para a versão anterior; desinstale essa versão antes de instalar a nova.

## Code signing policy

A integração SignPath está em `.github/workflows/sign-release.yml`. **Aprovação e credenciais ainda pendentes; não há assinatura SignPath ativa.** Veja `SIGNING.md` para candidatura, variáveis, segredo e configurações de artefato. Nada foi enviado à SignPath e nenhuma chave foi usada. O fluxo assina aplicativo e desinstalador, monta o instalador, valida o aplicativo assinado e depois assina o instalador. Ele é manual, só roda na branch padrão, exige configuração e não publica releases automaticamente. O resultado é um candidato para validação interativa da instalação/UAC.

Validação atual 1.3.1: o executável empacotado passou na criação da janela nativa e na exclusão/agendamento reais em arquivos descartáveis (`dist/smoke-test.json` e `dist/functional-packaged.json`, ambos frozen=true e ok=true). O bloqueio anterior não se repetiu nessa execução. Isso não é uma assinatura digital nem garante aprovação em outros computadores. A instalação interativa/UAC continua pendente.

Validação instalada 1.3.1 concluída: instalação em Program Files terminou com sucesso e o usuário confirmou a abertura normal. Os hashes dos componentes instalados coincidiram com o pacote. O próprio EXE instalado passou na janela nativa e na limpeza/agendamento reais isolados (`dist/installed-smoke-1.3.1.json` e `dist/installed-functional-1.3.1.json`). Os atalhos pessoais antigos foram conferidos; não foram encontrados na conferência final. A assinatura reconhecida continua pendente. O usuário aprovou UAC e confirmou a limpeza real no auxiliar instalado, que terminou com código 0. O cenário de cancelamento não foi exercitado nessa execução.
