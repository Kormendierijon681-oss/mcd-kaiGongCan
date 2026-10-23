const fs=require('fs'),vm=require('vm');
const target=process.argv[2]||require('path').join(__dirname,'..','index.html');
const html=fs.readFileSync(target,'utf8');
const src=html.match(/<script>([\s\S]*?)<\/script>/)[0].replace(/^<script>/,'').replace(/<\/script>$/,'');
const store={};
function E(id){ return store[id]||(store[id]={id,value:'',checked:false,textContent:'',innerHTML:'',addEventListener(){},onclick:null,
  classList:{add(){},remove(){},contains(){return false}}}); }
const document={getElementById:E,querySelectorAll:()=>[],createElement:()=>({style:{},select(){}}),body:{appendChild(){},removeChild(){}}};
const ctx={document,navigator:{},setTimeout,clearTimeout,console,Math,JSON,Set,Array,Object,String,Number,Date,
  requestAnimationFrame:()=>{},location:{search:''},URLSearchParams:URLSearchParams};
ctx.window=ctx;
vm.createContext(ctx);
vm.runInContext(src+'\n;globalThis.__plan=plan;globalThis.__last=()=>last',ctx);
module.exports={ctx,store,E};
if(require.main===module){
  console.log('自检目标: '+target);
  const cases=[[6,25,0,0],[4,30,0,0],[3,20,0,0],[10,35,0,0],[8,18,0,0],[6,25,1,0],[6,25,0,1],[6,25,1,1],
               [20,12,0,0],[1,10,0,0],[2,80,0,0],[20,40,0,0],[5,15,1,1],[12,22,0,1],[2,12,0,0]];
  let bad=0;
  for(const [p,b,s,bf] of cases){
    E('people').value=String(p); E('budget').value=String(b);
    E('noSpicy').checked=!!s; E('noBeef').checked=!!bf; E('withDrink').checked=true;
    ctx.__plan();
    const r=ctx.__last();
    const out=E('out').innerHTML;
    if(!r){ console.log(`ℹ️  ${p}人¥${b} 辣${s}牛${bf}: ${out.match(/<div class="empty">([^<]*)</)?.[1]||'—'}`); continue; }
    const names=r.picks.map(x=>x.n), uniq=new Set(names).size;
    const leak=r.picks.some(x=>(s&&x.s)||(bf&&x.b))||(r.drink&&((s&&r.drink.s)||(bf&&r.drink.b)));
    const over=r.used>r.total+1e-9;
    if(over||leak)bad++;
    console.log(`${over?'❌超支':(leak?'❌漏禁忌':'✅')} ${String(p).padStart(2)}人¥${String(b).padStart(2)} 辣${s}牛${bf} | 配${String(r.picks.length).padStart(2)}份 不重样${uniq} | 支出¥${r.used.toFixed(2)}/¥${r.total} (${(r.used/r.total*100).toFixed(0)}%) | 剩¥${Math.max(0,r.remain).toFixed(2)} | 饮${r.drink?r.drink.n:'-'} | 加购${r.addon.length}`);
    console.log("      "+names.join(' / '));
  }
  console.log(bad? `\n❌ ${bad} 个用例有问题`: "\n✅ 全部用例通过");
}
