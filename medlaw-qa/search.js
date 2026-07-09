// medlaw-qa — dependency-free retrieval engine (Architecture A)
// Chinese bigram inverted index over structured fields + 條號 + 案由 + 判決結果摘要.
// No external library, fully offline. Full-text (整篇全文) deep search is Phase B1 (sql.js).
(function(global){
  'use strict';

  // record shape (compact): {i,c,y,w,n,d,u,l,g,a,r,b,url}
  //   i=id c=court y=year w=字別 n=案號 d=裁判日期 u=案由 l=laws[] g=類別
  //   a=條號[] (e.g. "藥事法§83") r=判決結果摘要 b=據案由起訴laws[] url
  function searchableText(r){
    return [r.c, r.u, (r.l||[]).join(' '), (r.a||[]).join(' '), r.r, r.g].join(' ');
  }

  function tokenize(s){
    s=(s||'').toLowerCase();
    var toks=[], m;
    var re=/[a-z0-9]+/g;                       // latin / digits (e.g. 條號數字)
    while((m=re.exec(s))) toks.push(m[0]);
    var cjk=s.match(/[㐀-鿿]+/g)||[];   // CJK runs -> overlapping bigrams (+ unigram if len 1)
    for(var k=0;k<cjk.length;k++){
      var run=cjk[k];
      if(run.length===1){ toks.push(run); continue; }
      for(var i=0;i<run.length-1;i++) toks.push(run.slice(i,i+2));
    }
    return toks;
  }
  function uniq(a){ var s={},o=[]; for(var i=0;i<a.length;i++){ if(!s[a[i]]){s[a[i]]=1;o.push(a[i]);} } return o; }

  var Engine = {
    records: [],
    inv: null,        // token -> array of record indices
    built: false,
    build: function(records){
      this.records = records || [];
      this.inv = Object.create(null);
      for(var idx=0; idx<this.records.length; idx++){
        var toks = uniq(tokenize(searchableText(this.records[idx])));
        for(var t=0;t<toks.length;t++){
          var tok=toks[t];
          (this.inv[tok] || (this.inv[tok]=[])).push(idx);
        }
      }
      this.built = true;
      return this;
    },
    ryear: function(d){ // "2026-07-02" -> 民國 115
      var y=parseInt((d||'').slice(0,4),10); return y? y-1911 : null;
    },
    // filt: {laws:[], article:{law,art}, court, year, category, causeLaw}
    _passFilter: function(r, filt){
      if(!filt) return true;
      if(filt.laws && filt.laws.length){
        var ok=false; for(var i=0;i<filt.laws.length;i++){ if((r.l||[]).indexOf(filt.laws[i])>=0){ok=true;break;} }
        if(!ok) return false;
      }
      if(filt.article){
        var key=filt.article.law+'§'+filt.article.art;
        if((r.a||[]).indexOf(key)<0) return false;
      }
      if(filt.court && (r.c||'').indexOf(filt.court)<0) return false;
      if(filt.year && this.ryear(r.d)!==filt.year) return false;
      if(filt.category && r.g!==filt.category) return false;
      if(filt.causeLaw && (r.b||[]).indexOf(filt.causeLaw)<0) return false;
      return true;
    },
    // returns {total, hits:[record...]} ranked
    search: function(q, filt, limit){
      limit = limit||1e9;   // default: return the FULL ranked list (UI paginates)
      var self=this, i, idx, r;
      var qToks = uniq(tokenize(q||''));
      var scored=[];
      if(qToks.length===0){
        // no free text -> return all filter-matching, newest first
        for(i=0;i<this.records.length;i++){ r=this.records[i]; if(this._passFilter(r,filt)) scored.push([i,0]); }
        scored.sort(function(a,b){ return self.records[b[0]].d < self.records[a[0]].d ? -1 : 1; });
        return { total: scored.length, hits: scored.slice(0,limit).map(function(s){return self.records[s[0]];}) };
      }
      // score by number of distinct query tokens present in the record
      var score = Object.create(null);
      for(var t=0;t<qToks.length;t++){
        var postings = this.inv[qToks[t]];
        if(!postings) continue;
        for(var p=0;p<postings.length;p++){ idx=postings[p]; score[idx]=(score[idx]||0)+1; }
      }
      for(idx in score){
        r=this.records[idx];
        if(!this._passFilter(r,filt)) continue;
        scored.push([idx|0, score[idx]]);
      }
      scored.sort(function(a,b){
        if(b[1]!==a[1]) return b[1]-a[1];                 // more query-tokens matched first
        return self.records[b[0]].d < self.records[a[0]].d ? -1 : 1;  // then newer
      });
      return { total: scored.length, hits: scored.slice(0,limit).map(function(s){return self.records[s[0]];}) };
    },
    // count-only for a pure structured filter (statistical questions)
    count: function(filt){
      var n=0; for(var i=0;i<this.records.length;i++){ if(this._passFilter(this.records[i],filt)) n++; } return n;
    }
  };

  Engine.tokenize = tokenize;
  global.SearchEngine = Engine;
})(typeof window!=='undefined'?window:globalThis);
