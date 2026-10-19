# Assinatura do CleanTemp — ativação pendente

O aplicativo continua gratuito, aberto e sem cadastro para usuários. Assinatura é uma etapa de distribuição, não uma licença de uso. Nenhum certificado de desenvolvimento de outro projeto foi usado. Não crie confiança artificial nem desative a proteção do Windows para publicar.

## Etapa externa necessária

Solicite a avaliação do projeto em https://signpath.org/ (Apply). A aprovação não é automática. Antes de solicitar, publique o código atual e uma descrição honesta do projeto, sua licença MIT e do candidato disponível. A solicitação exige ação do proprietário; este repositório não cria conta, aceita termos ou envia dados por você.

Texto para a candidatura:

> CleanTemp is a MIT-licensed, offline-first Windows temporary-file cleaner maintained by Edilson Enoque. Source: https://github.com/Einsamerwolf2/CleanTemp2. The native Python/Tk desktop application includes its runtime and does not require users to install Python. Cleanup is restricted to explicit temporary locations and preserves open files, directories, protected attributes and links. Optional UAC cleanup is limited to Windows/Temp. Daily scheduling is opt-in and never elevated. No telemetry or automatic support-report submission is included. Update checks contact GitHub; support links open only at the user's request. We request code signing for our own application, Inno-generated uninstaller and installer. Third-party Python/Tk binaries are bundled with licenses and are not re-signed with our identity. A GitHub Actions workflow builds from source, retains artifact provenance and requires approval by the signing service. Installed helper UAC approval and user-confirmed cleanup were validated on the maintainer PC. Broader clean-machine testing is still needed.

Responsável pelo código, revisão e aprovação de releases: Edilson Enoque (`Einsamerwolf2`). Ative autenticação multifator no GitHub e no serviço. Se a SignPath aprovar o projeto, publique a atribuição exigida por ela na política de assinatura; não declare patrocínio antes da aprovação. O Windows poderá mostrar SignPath Foundation como editor da assinatura, enquanto o aplicativo mantém o crédito a Edilson Enoque.

## Configurar após aprovação

Crie o ambiente GitHub `code-signing`, com revisão obrigatória antes de executar o job e restrição à branch padrão. Adicione:

- Secret `SIGNPATH_API_TOKEN`: token gerado no serviço. Não coloque no código nem envie pelo chat.
- Variable `SIGNPATH_ORGANIZATION_ID`: organização informada pela SignPath.
- Variable `SIGNPATH_PROJECT_SLUG`: identificador do projeto aprovado.

No SignPath, configure a política `release-signing` com aprovação manual e dois artefatos:

- `cleantemp-native`: use `packaging/signpath-native.xml` como modelo e revise com a SignPath. Recebe somente `CleanTemp.exe` e `uninstaller.exe`.
- `cleantemp-installer`: use `packaging/signpath-installer.xml`. Recebe somente o instalador.

Os modelos restringem produto, editor e versão 1.4.0. Atualize os modelos ao alterar a versão. Revise as configurações com o serviço; o servidor é quem valida seu esquema e sua política. Os próprios Python/Tk e demais componentes de terceiros não são assinados com a identidade do projeto.

## Fluxo implementado

1. O GitHub compila a pasta completa do aplicativo, verifica DLLs e recursos.
2. O Inno gera o desinstalador para assinatura. Essa primeira compilação para intencionalmente após exportá-lo; não é uma falha do aplicativo.
3. A action oficial SignPath envia o artefato GitHub com aplicativo e desinstalador. Aguarda aprovação e baixa os arquivos assinados.
4. O projeto exige assinaturas Windows válidas e recoloca os arquivos nos caminhos esperados.
5. O mesmo Inno compila o instalador com o desinstalador já assinado. Não troque a versão do compilador entre essas etapas.
6. O aplicativo assinado passa pelo teste de janela e pela limpeza/agendamento reais em arquivos descartáveis. A validação de tarefa exige uma sessão de usuário disponível no runner Windows; se não houver, o job falha e deve ser executado num runner apropriado.
7. A SignPath assina o instalador final. O job verifica a assinatura e gera SHA256.
8. O artefato `cleantemp-signed-candidate` fica disponível para teste instalado e validação interativa de UAC. Não há publicação automática de release.

A assinatura remota ainda não foi executada: faltam a aprovação do serviço e as credenciais. A exportação local do desinstalador foi verificada. Os scripts nunca simulam uma assinatura ou aceitam `NotSigned` como sucesso.

## Diagnóstico de DLL

A captura recebida apontava para `G:\CleanTemp\build\CleanTemp\CleanTemp.exe`. Esse é um intermediário sem `_internal/python314.dll`. A DLL e os runtimes necessários estão no pacote em `dist/CleanTemp`. Distribua o instalador ou a pasta completa, nunca um EXE isolado da pasta build. A instalação final deve ser validada em Windows sem Python instalado.
