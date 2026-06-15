# -*- coding: utf-8 -*-
"""Render _dashboard_data.json into a single self-contained dashboard.html."""
import json

data = json.load(open('_dashboard_data.json', encoding='utf-8'))
blob = json.dumps(data, ensure_ascii=False)

HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FPTE 2026 — Campeonato por Clubes (STAH)</title>
<style>
  :root{
    --bg:#0f1320; --panel:#171c2e; --line:#283150; --txt:#e7ebf5; --mut:#94a0c0;
    --accent:#ffcc4d; --me:#36d399; --me2:#0c8a5b; --pend:#f59e0b; --pendbg:#3a2c12;
    --sel:#5aa9ff;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--txt);font:14px/1.45 system-ui,Segoe UI,Roboto,sans-serif}
  header{padding:16px 22px;border-bottom:1px solid var(--line);display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
  header h1{font-size:18px;margin:0}
  header .sub{color:var(--mut);font-size:13px}
  header .me{color:var(--me);font-weight:600}
  .wrap{max-width:1280px;margin:0 auto;padding:16px 22px}
  .tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
  .tab{padding:8px 13px;border:1px solid var(--line);background:var(--panel);color:var(--mut);
       border-radius:8px;cursor:pointer;font-size:13px;white-space:nowrap}
  .tab.active{color:#1a1f2e;background:var(--accent);border-color:var(--accent);font-weight:600}
  .tab.geral{border-color:var(--me2)}
  .tab.geral.active{background:var(--me);border-color:var(--me)}
  .summary{font-size:15px;margin:2px 0 14px}
  .summary b{color:var(--me)}
  .controls{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:11px 14px;margin-bottom:14px;font-size:13px}
  .controls label{display:inline-flex;align-items:center;gap:6px;margin-right:14px;color:var(--mut);cursor:pointer}
  .controls .ttl{color:var(--mut);margin-right:10px;font-weight:600}
  .grid{display:grid;grid-template-columns:300px 1fr;gap:18px}
  @media(max-width:880px){.grid{grid-template-columns:1fr}}
  .panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}
  .panel h2{margin:0 0 10px;font-size:13px;color:var(--mut);font-weight:600;text-transform:uppercase;letter-spacing:.04em}
  table{width:100%;border-collapse:collapse}
  th,td{text-align:left;padding:7px 6px;border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums}
  th{color:var(--mut);font-weight:600;font-size:11px}
  td.num,th.num{text-align:right}
  #standings tbody tr{cursor:pointer}
  #standings tbody tr:hover td{background:rgba(90,169,255,.08)}
  tr.me td{color:var(--me)}                                   /* STAH: subtle green text */
  #standings tbody tr.sel td{background:#274d7d;font-weight:700;box-shadow:inset 4px 0 0 var(--sel)}
  #standings tbody tr.sel .club{color:#eaf2ff}
  #standings tbody tr.sel .pts{color:#ffe39a}
  .rank{width:30px;text-align:center}
  .club{font-weight:500}
  .pts{font-weight:700;color:var(--accent)}
  tr.me .pts{color:var(--me)}
  .chip{display:inline-block;padding:2px 8px;border-radius:99px;font-size:11px;font-weight:600;white-space:nowrap}
  .chip.ok{color:var(--me);background:rgba(54,211,153,.12);border:1px solid var(--me2)}
  .chip.pend{color:var(--pend);background:var(--pendbg);border:1px solid #6b4e16;cursor:help}
  .note{color:var(--mut);font-size:11px;margin-top:10px;line-height:1.6}
  .chartbox{overflow-x:auto}
  .full{grid-column:1/-1}
  .bk-sub{color:var(--mut);font-size:12px;font-weight:400;text-transform:none;letter-spacing:0;margin-left:8px}
</style>
</head>
<body>
<header>
  <h1>FPTE 2026 — Campeonato por Clubes</h1>
  <span class="sub">Posição em <b id="today"></b> · clube em destaque: <span class="me" id="myclub"></span></span>
  <span class="sub" id="scoring"></span>
</header>
<div class="wrap">
  <div class="tabs" id="tabs"></div>
  <div class="controls" id="controls" style="display:none"></div>
  <div class="summary" id="summary"></div>
  <div class="grid">
    <div class="panel">
      <h2>Classificação (top 5 + STAH)</h2>
      <table id="standings"><thead><tr>
        <th class="rank">#</th><th>Clube</th><th class="num">Pts</th>
      </tr></thead><tbody></tbody></table>
      <div class="note">💡 Clique em um clube para ver suas disciplinas e requisitos abaixo.</div>
    </div>
    <div class="panel">
      <h2>Evolução ao longo do ano (top 5 + STAH)</h2>
      <div class="chartbox"><svg id="chart" width="900" height="540"></svg></div>
    </div>
    <div class="panel full">
      <h2>Detalhe por disciplina <span class="bk-sub" id="bk-sub"></span></h2>
      <table id="breakdown"><thead><tr>
        <th>Disciplina</th><th class="num">Score</th><th class="num">Posição</th>
        <th class="num">Clubes</th><th class="num">Pontos</th><th>Requisitos obrigatórios</th>
      </tr></thead><tbody></tbody></table>
      <div class="note">
        Requisitos por disciplina: <b>≥3 etapas online · 1 regional · a final</b>.
        <span class="chip ok">✓ Apto</span> = todos cumpridos ·
        <span class="chip pend">Falta: …</span> = pendente (a final ocorre em dezembro).
      </div>
    </div>
  </div>
</div>
<script>
const DATA = __DATA__;
const COLORS=["#ffcc4d","#5aa9ff","#ff7eb6","#c792ea","#ffa657","#79c0ff","#f778ba"];
const ME=DATA.my_club, N=DATA.dates.length, MINON=3, GERAL='Geral';
document.getElementById('today').textContent=DATA.today;
document.getElementById('myclub').textContent=ME;
document.getElementById('scoring').textContent=
  'score do clube por disciplina: 3 melhores online + melhor regional + final (sem multiplicadores)';

const tabNames=[GERAL, ...DATA.group_order];
let active=GERAL;
let selected=new Set(DATA.overall_default);   // groups counted in the Overall
let selClub=ME;                               // club shown in the detail panel

const tabs=document.getElementById('tabs');
tabNames.forEach(g=>{
  const b=document.createElement('div');
  b.className='tab'+(g===GERAL?' geral':''); b.textContent=g; b.dataset.g=g;
  b.onclick=()=>{active=g;render();}; tabs.appendChild(b);
});

function medal(r){return r===1?'🥇':r===2?'🥈':r===3?'🥉':r+'º';}
function statusChip(req){
  if(!req) return '<span class="chip pend">sem dados</span>';
  const miss=[];
  if(!req.online_ok) miss.push((MINON-req.online)+'× online');
  if(!req.regional_ok) miss.push('regional');
  if(!req.final_ok) miss.push('final');
  if(!miss.length) return '<span class="chip ok">✓ Apto</span>';
  const tip=`online ${req.online}/3 · regional ${req.regional}/1 · final ${req.final}/1`;
  return `<span class="chip pend" title="${tip}">Falta: ${miss.join(', ')}</span>`;
}
function minRank(pairs){const r={};pairs.forEach((p,i)=>{r[p[0]]=(i===0||p[1]<pairs[i-1][1])?i+1:r[pairs[i-1][0]];});return r;}

// ---------- Overall (client-side, depends on selected groups) ----------
function computeOverall(){
  const gs=[...selected]; const clubs=new Set();
  gs.forEach(g=>Object.keys(DATA.matrix[g]||{}).forEach(c=>clubs.add(c)));
  const all={};
  clubs.forEach(c=>{const a=new Array(N).fill(0);
    gs.forEach(g=>{const m=(DATA.matrix[g]||{})[c]; if(m)for(let i=0;i<N;i++)a[i]+=m[i];}); all[c]=a;});
  const pairs=[...clubs].map(c=>[c,all[c][N-1]]).sort((a,b)=>b[1]-a[1]);
  const ranks=minRank(pairs);
  const show=[...new Set([...pairs.slice(0,5).map(p=>p[0]), ...(clubs.has(ME)?[ME]:[])])];
  const standings=show.map(c=>({club:c,pts:all[c][N-1],rank:ranks[c],is_me:c===ME}));
  const series={}; show.forEach(c=>series[c]=all[c]);
  return {standings, series, clubsAll:clubs};
}

// detail rows (per discipline, w/ requisites) for a club in the current scope
function detailFor(club){
  if(active===GERAL){
    let out=[];
    [...selected].forEach(g=>((DATA.club_detail[g]||{})[club]||[]).forEach(e=>
      out.push({...e, discipline:g+' · '+e.discipline})));
    return out.sort((a,b)=>b.pts-a.pts);
  }
  return ((DATA.club_detail[active]||{})[club]||[]).slice();
}

function render(){
  [...tabs.children].forEach(t=>t.classList.toggle('active',t.dataset.g===active));
  const ctr=document.getElementById('controls');
  let G;
  if(active===GERAL){ ctr.style.display='block'; renderControls(); G=computeOverall(); }
  else{ ctr.style.display='none'; G=DATA.groups[active]; }
  // keep selected club valid in this scope; else default to STAH or leader
  const present=new Set(G.standings.map(s=>s.club));
  const hasDetail=detailFor(selClub).length>0;
  if(!hasDetail) selClub = (detailFor(ME).length? ME : (G.standings[0]&&G.standings[0].club));
  renderSummary(G); renderStandings(G); drawChart(G); renderDetail();
}

function renderControls(){
  const ctr=document.getElementById('controls');
  let h='<span class="ttl">Incluir no Geral:</span>';
  DATA.group_order.forEach(g=>{h+=`<label><input type="checkbox" data-g="${g}" ${selected.has(g)?'checked':''}> ${g}</label>`;});
  ctr.innerHTML=h;
  ctr.querySelectorAll('input').forEach(cb=>cb.onchange=()=>{
    cb.checked?selected.add(cb.dataset.g):selected.delete(cb.dataset.g); render();});
}

function renderSummary(G){
  const s=document.getElementById('summary');
  const me=G.standings.find(x=>x.is_me);
  const scope=active===GERAL?'no Geral':'em '+active;
  if(me){const lead=G.standings[0];
    const extra=me.rank===1?'líder! 🏆':`líder: ${lead.club} (${lead.pts} pts)`;
    s.innerHTML=`<b>${ME}</b>: ${medal(me.rank)} ${scope} · ${me.pts} pontos &nbsp;—&nbsp; ${extra}`;
  }else s.innerHTML=`<b>${ME}</b> ainda não pontua ${scope}.`;
}

function renderStandings(G){
  const tb=document.querySelector('#standings tbody'); tb.innerHTML='';
  G.standings.forEach(s=>{
    const tr=document.createElement('tr');
    if(s.is_me)tr.classList.add('me'); if(s.club===selClub)tr.classList.add('sel');
    tr.innerHTML=`<td class="rank">${medal(s.rank)}</td><td class="club">${s.club}</td><td class="num pts">${s.pts}</td>`;
    tr.onclick=()=>{selClub=s.club; renderStandings(G); renderDetail();};
    tb.appendChild(tr);
  });
}

function renderDetail(){
  document.getElementById('bk-sub').textContent =
    `— ${selClub} ${active===GERAL?'(grupos selecionados)':'· '+active}`;
  const rows=detailFor(selClub);
  const tb=document.querySelector('#breakdown tbody'); tb.innerHTML='';
  if(!rows.length){tb.innerHTML='<tr><td colspan="6" style="color:var(--mut)">Sem disciplinas pontuadas neste escopo.</td></tr>';return;}
  rows.forEach(b=>{
    const tr=document.createElement('tr');
    tr.innerHTML=`<td>${b.discipline}</td><td class="num">${b.score}</td><td class="num">${b.rank}º</td>`+
                 `<td class="num">${b.n_clubs}</td><td class="num pts">${b.pts}</td><td>${statusChip(b.req)}</td>`;
    tb.appendChild(tr);
  });
}

function drawChart(G){
  const svg=document.getElementById('chart');
  const W=900,H=540,pad={l:38,r:175,t:14,b:46};
  const dates=DATA.dates, n=N, series=G.series, clubs=Object.keys(series);
  let ymax=1; clubs.forEach(c=>series[c].forEach(v=>ymax=Math.max(ymax,v)));
  ymax=Math.ceil(ymax/5)*5;
  const X=i=>pad.l+(W-pad.l-pad.r)*(n<=1?0:i/(n-1));
  const Y=v=>H-pad.b-(H-pad.t-pad.b)*(v/ymax);
  let s=''; const step=Math.max(1,Math.round(ymax/8));
  for(let g=0;g<=ymax;g+=step){
    s+=`<line x1="${pad.l}" y1="${Y(g)}" x2="${W-pad.r}" y2="${Y(g)}" stroke="#283150"/>`;
    s+=`<text x="${pad.l-6}" y="${Y(g)+4}" fill="#94a0c0" font-size="11" text-anchor="end">${g}</text>`;
  }
  dates.forEach((d,i)=>{ if(i%Math.ceil(n/12)!==0 && i!==n-1)return;
    s+=`<text x="${X(i)}" y="${H-pad.b+16}" fill="#94a0c0" font-size="10" text-anchor="middle">${d}</text>`;});
  const ends=[];
  clubs.forEach((c,ci)=>{
    const isSel=c===selClub, isMe=c===ME;
    const col=isMe?'#36d399':COLORS[ci%COLORS.length];
    const wdt=isSel?3.8:2, op=isSel?1:(isMe?.9:.55);
    const path=series[c].map((v,i)=>`${i?'L':'M'}${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join(' ');
    s+=`<path d="${path}" fill="none" stroke="${col}" stroke-width="${wdt}" opacity="${op}"/>`;
    const lv=series[c][n-1];
    s+=`<circle cx="${X(n-1)}" cy="${Y(lv)}" r="${isSel?5:3}" fill="${col}" opacity="${op}"/>`;
    ends.push({c,col,v:lv,y:Y(lv),me:isMe,sel:isSel});
  });
  ends.sort((a,b)=>a.y-b.y);
  const gap=16, top=pad.t+6, bot=H-pad.b;
  for(let i=0;i<ends.length;i++){let y=ends[i].y; if(i>0&&y<ends[i-1].ly+gap)y=ends[i-1].ly+gap;
    ends[i].ly=Math.min(Math.max(y,top),bot);}
  // selected label drawn last so its high-contrast pill sits on top
  [...ends].sort((a,b)=>(a.sel?1:0)-(b.sel?1:0)).forEach(e=>{
    const lx=X(n-1)+8, label=`${e.c} - ${e.v}`;
    s+=`<line x1="${X(n-1)}" y1="${e.y}" x2="${lx}" y2="${e.ly}" stroke="${e.col}" stroke-width="1" opacity="${e.sel?.85:.4}"/>`;
    if(e.sel){
      const w=label.length*7.0+12;
      s+=`<rect x="${lx}" y="${e.ly-10}" width="${w}" height="19" rx="5" fill="${e.col}"/>`;
      s+=`<text x="${lx+6}" y="${e.ly+4}" fill="#0f1320" font-size="12.5" font-weight="700">${label}</text>`;
    }else{
      s+=`<text x="${lx+3}" y="${e.ly+4}" fill="${e.col}" font-size="12" font-weight="${e.me?600:500}" opacity="${e.me?1:.85}">${label}</text>`;
    }
  });
  svg.innerHTML=s;
}
render();
</script>
</body>
</html>
"""

open('dashboard.html', 'w', encoding='utf-8').write(HTML.replace('__DATA__', blob))
print('wrote dashboard.html')
