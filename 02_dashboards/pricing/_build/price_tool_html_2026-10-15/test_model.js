const {makeModel,K}=require('./model.js'); const D=require('./payload.json');
const M=makeModel(D); const S={}; D.pad_parts.forEach(p=>S['p:'+p]={ALL:'0'}); D.pad_l3.forEach(i=>S['l3:'+i]={ALL:'0'});
const o=M.run(S,0.053,0.05); const ex=[0,0,0,0]; let base=0;
D.rows.forEach((r,i)=>{for(let k=0;k<4;k++){ex[k]+=r[5+k]*o.mv[k][i];base+=r[5+k]}});
console.log(ex.map(x=>x.toFixed(2)), (ex.reduce((a,b)=>a+b)/base).toFixed(6), o.s2);
const e=require('./expected_ref.json'); console.log(['PR00','UTI','UMI','OTH'].map(k=>e.extra[k].toFixed(2)), e.s2.PR00);
