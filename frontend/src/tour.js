(() => {
  'use strict';
  const get = id => document.getElementById(id);
  const dialog = get('quick-tour');
  const storageKey = 'cleantemp.tour.v1';
  const steps = [
    {title:'Bem-vindo ao CleanTemp', symbol:'✦', target:'cleaning-summary', preview:'Analisar → Selecionar → Limpar', text:'Liberte espaço em três passos. Pode usar o CleanTemp sem cadastro e sem internet. Vamos mostrar onde encontrar cada opção.'},
    {title:'1. Descubra o que pode limpar', symbol:'1', target:'scan', preview:'Analisar', text:'Clique em Analisar para procurar temporários com mais de um dia. Esta etapa só verifica os arquivos: nada é apagado. Aguarde o resultado antes de continuar.'},
    {title:'2. Escolha os temporários', symbol:'2', target:'folder-section', preview:'☑ Selecionar disponíveis', text:'Marque as opções que deseja limpar. Pode usar Selecionar disponíveis para marcar todas as opções permitidas. As opções protegidas ou sem arquivos ficam indisponíveis.'},
    {title:'3. Confirme a limpeza', symbol:'3', target:'clean', preview:'Limpar selecionados', text:'Clique em Limpar selecionados e leia a confirmação. A exclusão é permanente. Se mudar de ideia, cancele. Arquivos abertos ou que não possam ser verificados serão preservados; pastas não serão apagadas.'},
    {title:'Confira o resultado', symbol:'✓', target:'results-section', preview:'Como foi a limpeza', text:'Veja quantos arquivos foram apagados e quanto espaço foi removido. Alguns arquivos podem ficar por estarem protegidos ou em uso. Isso é esperado: não é necessário forçar sua exclusão.'},
    {title:'Peça ajuda quando precisar', symbol:'?', target:'support-section', preview:'Discord • Telegram • WhatsApp', text:'Se algo não funcionar, use a área Precisa de ajuda? e escolha um canal. Enquanto o atendimento não estiver disponível, aparecerá Em desenvolvimento. Nenhuma mensagem é enviada automaticamente; nunca envie senhas ou tokens.'},
    {title:'Tenha o guia sempre à mão', symbol:'↓', target:'guide-link', preview:'Como usar • Guia em PDF', text:'O Guia em PDF explica a limpeza, os cuidados e como solicitar assistência. Pode guardá-lo para ler offline. Para rever este passeio, clique em Como usar. As atualizações são opcionais e precisam de internet.'}
  ];
  let position = 0;
  let previousFocus = null;
  let highlighted = null;
  function remember(){try{localStorage.setItem(storageKey,'seen');}catch{/* Storage can be disabled. */}}
  function seen(){try{return localStorage.getItem(storageKey)==='seen';}catch{return false;}}
  function clearHighlight(){if(highlighted)highlighted.classList.remove('tour-highlight');highlighted=null;}
  function render(){
    const step = steps[position];
    get('tour-title').textContent = step.title;
    get('tour-description').textContent = step.text;
    get('tour-symbol').textContent = step.symbol;
    get('tour-preview').textContent = step.preview;
    get('tour-progress').textContent = `Passo ${position+1} de ${steps.length}`;
    get('tour-bar').value = position+1;
    get('tour-prev').disabled = position===0;
    get('tour-next').textContent = position===steps.length-1?'Concluir':'Próximo';
    clearHighlight();
    highlighted = get(step.target);
    if(highlighted){
      highlighted.classList.add('tour-highlight');
      highlighted.scrollIntoView({block:'center',behavior:'instant'});
    }
    get('tour-title').focus({preventScroll:true});
  }
  function open(){
    if(dialog.open)return;
    position=0;previousFocus=document.activeElement;
    dialog.showModal();render();
  }
  function close(){
    remember();clearHighlight();dialog.close();
    if(previousFocus && typeof previousFocus.focus==='function')previousFocus.focus({preventScroll:true});
  }
  get('start-tour').addEventListener('click',open);
  get('tour-prev').addEventListener('click',()=>{if(position>0){position--;render();}});
  get('tour-next').addEventListener('click',()=>{if(position===steps.length-1)close();else{position++;render();}});
  get('tour-skip').addEventListener('click',close);
  dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
  if(!seen())open();
})();
