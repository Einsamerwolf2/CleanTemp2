const $ = id => document.getElementById(id);
let token = '', folders = [], busy = false;
const size = bytes => {const units = ['B','KB','MB','GB','TB']; let i=0; while(bytes>=1024 && i<4){bytes/=1024;i++;} return `${bytes.toLocaleString('pt', {maximumFractionDigits:2})} ${units[i]}`;};
function log(message){$('log').textContent = message;}
function selected(){return [...document.querySelectorAll('.choice:checked')].map(c=>c.value);}
function controls(){
  $('scan').disabled = busy || !token;
  $('clean').disabled = busy || !selected().length;
  const choices = [...document.querySelectorAll('.choice')];
  choices.forEach(c=>c.disabled=busy);
  $('all').disabled = busy || !choices.length;
  $('all').checked = choices.length>0 && choices.every(c=>c.checked);
  $('all').indeterminate = choices.some(c=>c.checked) && !choices.every(c=>c.checked);
}
async function api(path, options={}){
  const response = await fetch(`/api/${path}`, options);
  const data = await response.json();
  if(!response.ok) throw new Error(data.error || 'Falha na operação.');
  return data;
}
function render(){
  $('folders').replaceChildren();
  for(const folder of folders){
    const row=document.createElement('div'); row.className='folder';
    const check=document.createElement('input'); check.type='checkbox'; check.value=folder.id; check.setAttribute('aria-label',folder.name);
    if(folder.enabled && folder.exists && folder.file_count>0){check.className='choice';check.addEventListener('change',controls);} else check.disabled=true;
    const detail=document.createElement('div');detail.className='details';
    const title=document.createElement('b');title.textContent=folder.name;
    const path=document.createElement('span');path.className='path';path.textContent=folder.path;
    const reason=document.createElement('span');reason.className='reason';reason.textContent=folder.reason || (!folder.exists?'Pasta não encontrada':`${folder.file_count} arquivos temporários • ${folder.skipped} itens sem acesso`);
    detail.append(title,path,reason);
    const bytes=document.createElement('span');bytes.className='size';bytes.textContent=folder.enabled?size(folder.size_bytes):'Protegido';
    row.append(check,detail,bytes);$('folders').append(row);
  }
}
async function scan(){
  const data=await api('scan');folders=data.folders;render();
  $('total').textContent=size(data.total_size_bytes);
  $('count').textContent=`${folders.reduce((sum,f)=>sum+f.file_count,0)} arquivos temporários encontrados`;
  return data;
}
$('scan').addEventListener('click',async()=>{
  busy=true;controls();log('Analisando pastas…');
  try{await scan();log('Análise concluída. Selecione as pastas que deseja limpar.');}catch(e){log(e.message);}finally{busy=false;controls();}
});
$('all').addEventListener('change',()=>{document.querySelectorAll('.choice').forEach(c=>c.checked=$('all').checked);controls();});
$('clean').addEventListener('click',async()=>{
  const ids=selected();if(!ids.length || !confirm(`Apagar permanentemente os arquivos temporários de ${ids.length} pastas?`))return;
  busy=true;controls();log('Limpando arquivos…');
  try{
    const data=await api('clean',{method:'POST',headers:{'Content-Type':'application/json','X-CleanTemp-Token':token},body:JSON.stringify({ids})});
    const result=`${data.deleted_files} arquivos apagados • ${size(data.freed_bytes)} removidos\n${data.skipped} arquivos ou pastas não puderam ser acessados ou limpos.\n`+data.results.map(r=>`${r.name}: ${r.file_count} arquivos, ${size(r.size_bytes)} removidos${r.reason?' — '+r.reason:''}`).join('\n');
    const labels={in_use:'Em uso',needs_permission:'Sem permissão',safety:'Preservados por segurança',recent:'Modificados há menos de um dia',missing:'Não encontrados na verificação',unverified:'Não foi possível verificar'};
    log(result+'\n'+Object.entries(labels).map(([key,label])=>`${label}: ${data.preserved?.[key] || 0}`).join('\n'));
    try{await scan();}catch(e){log(result+'\nNão foi possível atualizar a análise: '+e.message);}
  }catch(e){log(e.message);}finally{busy=false;controls();}
});
(async()=>{try{const data=await api('status');token=data.windows?data.token:'';$('status').textContent=data.windows?(data.admin?'Acesso completo':'Limpeza do seu usuário'):'Disponível apenas no Windows';}catch(e){log('O CleanTemp foi encerrado. Abra o aplicativo novamente para continuar.');}controls();})();

let checkingUpdate = false;
async function checkUpdates(){
  if(checkingUpdate)return;
  checkingUpdate=true;$('check-update').disabled=true;
  $('update-status').textContent='Procurando uma nova versão…';
  try{
    const data=await api('updates');
    const messages={
      unconfigured:'As novidades do CleanTemp aparecerão aqui quando estiverem disponíveis.',
      current:'Você já tem a versão mais recente.',
      no_release:'Ainda não há uma nova versão publicada.',
      offline:'Sem conexão no momento. Você pode continuar limpando normalmente.',
      unavailable:'Não foi possível verificar agora. Você pode continuar limpando normalmente.'
    };
    $('update-status').textContent=data.state==='available'?`A versão ${data.latest_version} está disponível. Atualize quando quiser.`:(messages[data.state] || messages.unavailable);
    $('update-link').hidden=true;
    if(data.state==='available' && safeLink(data.url,['github.com'])){
      $('update-link').href=data.url;$('update-link').hidden=false;
    }
  }catch(e){$('update-status').textContent='Não foi possível verificar agora. Você pode continuar limpando normalmente.';}
  finally{checkingUpdate=false;$('check-update').disabled=false;}
}
function safeLink(value, hosts){
  try{const url=new URL(value);return url.protocol==='https:' && hosts.includes(url.hostname) && !url.username && !url.password && (!url.port || url.port==='443');}catch{return false;}
}
async function loadInfo(){
  try{
    const info=await api('info');
    const channels={discord:['Discord',['discord.gg','discord.com']],telegram:['Telegram',['t.me']],whatsapp:['WhatsApp',['wa.me','api.whatsapp.com']]};
    for(const [key,[name,hosts]] of Object.entries(channels)){
      const url=info.support[key];
      if(!safeLink(url,hosts))continue;
      const link=document.createElement('a');link.id=`support-${key}`;link.className=`button support-${key}`;link.innerHTML=$(`support-${key}`).innerHTML;link.href=url;link.target='_blank';link.rel='noopener noreferrer';
      $(`support-${key}`).replaceWith(link);
    }
    if(info.github_repository){
      const url=`https://github.com/${info.github_repository}`;
      if(safeLink(url,['github.com'])){$('source-link').href=url;$('source-link').hidden=false;}
    }
  }catch{ /* The cleaner remains usable when optional information is unavailable. */ }
  await checkUpdates();
}
$('check-update').addEventListener('click',checkUpdates);
window.addEventListener('online',checkUpdates);
// Retry while open so a restored connection is detected even if the browser
// did not receive an online event. The server caches successful lookups.
setInterval(()=>{if(!document.hidden)checkUpdates();},60000);
loadInfo();


for(const channel of ['discord','telegram','whatsapp']){
  $(`support-${channel}`).addEventListener('click',()=>{
    $('support-status').textContent='Em desenvolvimento. Este canal de suporte estará disponível em breve.';
  });
}
