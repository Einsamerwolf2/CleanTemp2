const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname,'../src/app.js'),'utf8');
function setup(update){
  const elements = new Map();
  const element = id => {
    if(!elements.has(id)) elements.set(id,{id,hidden:false,disabled:false,textContent:'',listeners:{},addEventListener(event,fn){this.listeners[event]=fn;},replaceWith(value){elements.set(id,value);}});
    return elements.get(id);
  };
  const context = vm.createContext({
    document:{hidden:false,getElementById:element,querySelectorAll:()=>[],createElement:()=>({})},
    window:{addEventListener(){}},setInterval(){}, URL, confirm:()=>false,
    fetch:async url=>({ok:true,json:async()=>{
      if(url.endsWith('status'))return {windows:true,admin:false,token:'local-token'};
      if(url.endsWith('info'))return {github_repository:'owner/CleanTemp',support:{discord:'https://discord.gg/test',telegram:'https://t.me/test',whatsapp:''}};
      if(update instanceof Error)throw update;
      return update;
    }})
  });
  vm.runInContext(source,context);
  return {context,element};
}
const flush = () => new Promise(resolve=>setImmediate(resolve));
test('offline update lookup leaves cleaning controls available',async()=>{
  const {element}=setup(new Error('offline'));await flush();
  assert.equal(element('scan').disabled,false);
  assert.match(element('update-status').textContent,/continuar limpando/);
  assert.equal(element('check-update').disabled,false);
});
test('configured support opens official links and missing WhatsApp shows development message',async()=>{
  const {context,element}=setup({state:'current'});await flush();
  assert.equal(element('support-discord').href,'https://discord.gg/test');
  assert.equal(element('support-telegram').rel,'noopener noreferrer');
  element('support-whatsapp').listeners.click();
  assert.match(element('support-status').textContent,/Em desenvolvimento/);
  assert.equal(vm.runInContext("safeLink('javascript:alert(1)', ['github.com'])",context),false);
  assert.equal(vm.runInContext("safeLink('https://github.com.evil.example', ['github.com'])",context),false);
});
test('new version exposes a GitHub link without starting a download',async()=>{
  const {element}=setup({state:'available',latest_version:'v1.1.0',url:'https://github.com/owner/CleanTemp/releases/tag/v1.1.0'});await flush();
  assert.equal(element('update-link').hidden,false);
  assert.match(element('update-link').href,/github.com/);
  assert.match(element('update-status').textContent,/v1.1.0/);
  assert.equal(element('scan').disabled,false);
});

