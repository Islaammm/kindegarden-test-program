const $=id=>document.getElementById(id);
function el(t,c,txt){const e=document.createElement(t);if(c)e.className=c;if(txt!=null)e.textContent=txt;return e}
async function api(url,opts){const r=await fetch(url,opts);if(r.status===401){location.href="/";throw new Error("401")}return r}
const Score={chosen:null,curId:null,editing:false,showAns:false};
/* Baholash tugmalari: hakam paneli va admin paneli uchun umumiy */
function renderScoring(box,s,showQ,reload){
  const c=s.current;
  if(!c){box.replaceChildren();return false}
  if(Score.editing&&c.id===Score.curId)return true;
  box.replaceChildren();
  if(Score.curId!==c.id){Score.chosen=c.mine;Score.curId=c.id;Score.editing=false;Score.showAns=false}
  else if(c.mine!=null&&Score.chosen==null)Score.chosen=c.mine;
  const mx=s.max_score||5;
  if(showQ)box.append(el("div","muted","Savol "+c.ord),el("div","big",c.text));
  if(c.answer){
    const row=el("div","answer");
    const txt=el("span","ans-text",Score.showAns?c.answer:"••••••••");
    const eye=el("button","eye-btn");eye.type="button";
    const paint=()=>{eye.setAttribute("aria-pressed",Score.showAns);eye.setAttribute("aria-label",Score.showAns?"Javobni yashirish":"Javobni ko'rsatish");
      eye.innerHTML='<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>'+(Score.showAns?'<path d="M4 4l16 16"/>':'')+'</svg>';
      txt.textContent=Score.showAns?c.answer:"••••••••"};
    eye.onclick=()=>{Score.showAns=!Score.showAns;paint()};paint();
    row.append(el("b","","To'g'ri javob:"),txt,eye);box.append(row);
  }
  if(c.panel&&c.panel.length){
    const row=el("div","judge-dots");
    c.panel.forEach(j=>{
      const d=el("span","judge-dot "+(j.scored?"ok":"wait"),String(j.num));
      d.setAttribute("aria-label","Hakam "+j.num+": "+(j.scored?"baho qo'ydi":"hali qo'ymadi"));
      row.append(d);
    });
    box.append(row);
  }
  box.append(el("b","","Javobni baholang (1 dan "+mx+" gacha)"));
  const sc=el("div","scale");
  for(let i=1;i<=mx;i++){
    const b=el("button",Score.chosen===i?"sel":"");b.type="button";
    b.setAttribute("aria-label",i+" ball");
    b.append(document.createTextNode(i),el("small","",i===1?"ball":"ball"));
    b.onclick=()=>{Score.chosen=i;Score.editing=true;[...sc.children].forEach((x,k)=>x.className=(k+1===i)?"sel":"")};
    sc.append(b);
  }
  box.append(sc);
  const send=el("button","btn",c.mine==null?"Bahoni yuborish":"Bahoni yangilash");send.type="button";
  send.onclick=async()=>{
    if(!Score.chosen)return;
    const r=await api("/api/baho",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({id:c.id,ball:Score.chosen})});
    if(!r.ok){const j=await r.json();alert(j.error)}
    Score.editing=false;reload();
  };
  box.append(send);
  if(c.mine!=null)box.append(el("span","badge ok","Sizning bahoyingiz: "+c.mine));
  return true;
}
