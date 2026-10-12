# Guia de Diretórios Temporários e Caches do Windows

Este documento lista os diretórios e pastas ocultas do Windows (além de `temp`, `%temp%` e `prefetch`) que acumulam arquivos residuais e cache. Esta lista serve de referência para o desenvolvimento da sua aplicação em Python e JavaScript para limpeza de disco em ambiente Windows.

---

## 📂 1. Arquivos de Atualizações do Sistema

* **`C:\Windows\SoftwareDistribution\Download`**
  * **Descrição:** Armazena arquivos residuais de instalações antigas do Windows Update.
  * **Segurança:** Seguro para limpeza quando o Windows Update não está a aplicar atualizações no momento.

* **`C:\Windows\Installer`** *(Apenas subpastas ocultas de patches antigos)*
  * **Descrição:** Guarda instaladores antigos.
  * **Atenção:** Delete apenas arquivos temporários soltos ou utilize ferramentas especializadas (como o PatchCleaner) para evitar corromper instaladores ativos.

---

## 🖼️ 2. Caches do Explorador de Arquivos e Gráficos

* **`%userprofile%\AppData\Local\Microsoft\Windows\Explorer`**
  * **Descrição:** Guarda o cache de miniaturas (`thumbcache_*.db`) de imagens e vídeos do sistema.
  * **Segurança:** Seguro para apagar (o Windows irá regenerá-los automaticamente conforme necessário).

* **`%userprofile%\AppData\Local\D3DSCache`**
  * **Descrição:** Contém arquivos de cache do Direct3D utilizados por jogos e aplicações gráficas pesadas.
  * **Segurança:** Seguro para apagar.

* **`%userprofile%\AppData\Local\NVIDIA\DXCache`** *(ou caminhos equivalentes da AMD/Intel)*
  * **Descrição:** Guarda o cache de sombreadores de vídeo da placa gráfica.
  * **Segurança:** Seguro para apagar.

---

## 📝 3. Relatórios de Erros e Logs do Sistema

* **`%userprofile%\AppData\Local\Microsoft\Windows\WER\ReportArchive`**
  * **Descrição:** Relatórios arquivados de travamento de programas enviados à Microsoft.
  * **Segurança:** Totalmente seguro para limpeza.

* **`%userprofile%\AppData\Local\Microsoft\Windows\WER\ReportQueue`**
  * **Descrição:** Fila de relatórios de erros aguardando envio.
  * **Segurança:** Totalmente seguro para limpeza.

* **`C:\ProgramData\Microsoft\Windows\WER\ReportArchive`**
  * **Descrição:** Relatórios de erros gerais do sistema compartilhados por todos os usuários.
  * **Segurança:** Totalmente seguro para limpeza.

* **`C:\Windows\Logs\CBS`**
  * **Descrição:** Arquivos de log gerados por verificações de integridade do sistema (como o comando `sfc /scannow`).
  * **Segurança:** Seguro para apagar (exige privilégios de Administrador).

---

## 🛡️ 4. Logs de Segurança e Verificação

* **`C:\ProgramData\Microsoft\Windows Defender\Scans\History\Store`**
  * **Descrição:** Histórico e relatórios antigos de varreduras do antivírus nativo (Windows Defender).
  * **Segurança:** Seguro para limpeza (exige privilégios de Administrador).

---

## 🚀 5. Bônus: Caches de Desenvolvimento (Node.js e Python)

* **`%userprofile%\.npm\_cacache`**
  * **Descrição:** O cache global de pacotes do npm.
  * **Dica de Limpeza:** Pode ser limpo diretamente via terminal executando `npm cache clean --force`.

* **`%userprofile%\AppData\Local\pip\cache`**
  * **Descrição:** Cache de pacotes baixados pelo pip para projetos Python.
  * **Segurança:** Seguro para apagar para liberar espaço em disco.

---

> **Nota para o Desenvolvedor:** Lembre-se de que caminhos que envolvem a pasta `C:\Windows` ou `C:\ProgramData` exigem que a sua aplicação Python/JS seja executada com **privilégios de Administrador (Elevated Privileges)** para conseguir ler e apagar os ficheiros com sucesso.