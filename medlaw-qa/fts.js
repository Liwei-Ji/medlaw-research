// medlaw-qa — Architecture B1: browser full-text search, plain JS (no WASM, no index build).
// Loads data/fulltext.json.gz (ALL 14,031 判決全文), gunzips (native DecompressionStream),
// then does brute-force AND-substring scan (~50ms/query) + snippet. No prebuilt index needed.
// Needs to be served over http(s) (fetch of the .gz is blocked on file://).
window.FTS = (function(){
  var docs=null, byId=null, loading=null;
  function available(){ return 'DecompressionStream' in window; }
  function ready(){ return !!docs; }

  function load(onProgress){
    if(docs) return Promise.resolve(true);
    if(loading) return loading;
    loading=(async function(){
      onProgress&&onProgress('下載全文資料（約 78MB，首次較久）…');
      var resp=await fetch('data/fulltext.json.gz');
      if(!resp.ok) throw new Error('無法取得全文資料檔');
      var stream=resp.body.pipeThrough(new DecompressionStream('gzip'));
      onProgress&&onProgress('解壓與解析全文…');
      docs=JSON.parse(await new Response(stream).text());
      byId=Object.create(null);
      for(var i=0;i<docs.length;i++) byId[docs[i].i]=i;
      return true;
    })();
    return loading;
  }

  function snippet(body, terms){
    var pos=-1;
    for(var i=0;i<terms.length;i++){ var p=body.indexOf(terms[i]); if(p>=0 && (pos<0||p<pos)) pos=p; }
    if(pos<0) return body.slice(0,90);
    var s=Math.max(0,pos-28), e=Math.min(body.length, pos+62);
    var seg=(s>0?'…':'')+body.slice(s,e)+(e<body.length?'…':'');
    for(var j=0;j<terms.length;j++){ if(terms[j]) seg=seg.split(terms[j]).join('【'+terms[j]+'】'); }
    return seg;
  }

  // brute-force: for each doc require ALL terms as substrings; rank by total term frequency
  function search(q, limit){
    limit=limit||1e9;
    var terms=(q||'').trim().split(/\s+/).filter(Boolean);
    if(!terms.length) return {total:0,hits:[],terms:[]};
    var scored=[];
    for(var i=0;i<docs.length;i++){
      var b=docs[i].t, ok=true;
      for(var t=0;t<terms.length;t++){ if(b.indexOf(terms[t])<0){ ok=false; break; } }
      if(!ok) continue;
      var sc=0; for(var u=0;u<terms.length;u++){ sc += b.split(terms[u]).length-1; }
      scored.push({d:i, sc:sc});
    }
    scored.sort(function(a,b){ return b.sc-a.sc || (docs[b.d].i<docs[a.d].i?-1:1); });
    var hits=scored.slice(0,limit).map(function(o){ return { i:docs[o.d].i, snip:snippet(docs[o.d].t, terms) }; });
    return {total:scored.length, hits:hits, terms:terms};
  }
  function getBody(id){ var i=byId[id]; return i==null?'':docs[i].t; }

  return { available:available, ready:ready, load:load, search:search, getBody:getBody };
})();
