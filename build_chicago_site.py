"""Build a self-contained LOCAL web app for the Chicago experience recommender.
Reads precomputed business scores (Drive, read-only), computes per-construct recommendation sets,
and writes index.html + data.js to a LOCAL folder (fast, no Drive write-timeout).
Run:  python3 ~/build_chicago_site.py
Then: cd ~/chicago_experience_site && python3 -m http.server 8000   ->  http://localhost:8000
Add/remove constructs by editing the CONS list below.
"""
import os, json, numpy as np, pandas as pd

DRIVE = "/Users/yuy1273/Library/CloudStorage/GoogleDrive-yue127123@gmail.com/Shared drives/Learning_in_cities_Data/experience_city_project_2007_2021/website_dat"
SRC   = os.path.join(DRIVE, "output", "chicago_eligible_master.csv")
OUT   = os.path.expanduser("~/chicago_experience_site"); os.makedirs(OUT, exist_ok=True)
CAP, MIN_REV, PCT = 400, 30, 0.05

# vendor Leaflet locally so the page loads instantly (no CDN round-trip)
import urllib.request
for _url, _fn in [("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js","leaflet.js"),
                  ("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css","leaflet.css")]:
    _p = os.path.join(OUT, _fn)
    if not os.path.exists(_p):
        try: urllib.request.urlretrieve(_url, _p); print("vendored", _fn)
        except Exception as e: print("could not vendor", _fn, "-", e)

d = pd.read_csv(SRC); d = d[d.review_count >= MIN_REV].copy()
Z = lambda s: (s - s.mean())/s.std()
RICH_DIMS = ["Psychological_Richness","FG_Richness","Curiosity_Stretching","Surprise","Perspective_Change","Exploration_Behavior"]
d["rich_composite"] = np.mean([Z(d[c+"_Score"]).to_numpy() for c in RICH_DIMS], axis=0)

CAT_GROUP = {"TP_Museum_Gallery":"Culture","TP_Arts_Performance":"Culture","TP_Library_Knowledge":"Culture",
 "TP_Book_Hobby_Epistemic":"Culture","TP_Animal_Exhibits":"Culture","TP_Restaurant_Dining":"Food","TP_Cafe_Bistro":"Food",
 "TP_Bar_Nightlife":"Food","TP_Winery_Brewery":"Food","TP_Grocery_Supermarket":"Food","TP_Park_Nature":"Nature",
 "TP_Plaza_Promenade":"Nature","TP_Sports_Active":"Active","TP_Entertainment_Play":"Active","TP_Stadium_Arena":"Active",
 "TP_Family_Kids":"Active","TP_Retail_General":"Retail","TP_Shopping_Mall":"Retail","TP_Pop_Up_Market":"Retail",
 "TP_Makers_Coworking":"Retail","TP_Community_Civic":"Civic","TP_Laundromat_Social":"Civic",
 "TP_Wellness_Relaxation":"Wellness","TP_Personal_Grooming":"Wellness"}
d["grp"] = d.primary_taxonomy_code.map(lambda t: CAT_GROUP.get(str(t),"Other"))

# --- Fix the over-broad TP_Community_Civic bin: it dumped sports/rec + medical into "Civic".
#     Regroup those by the REAL Google category; keep only genuine community places as Civic. ---
import re as _re
_cat = d["category"].fillna("").astype(str)
_active = _re.compile(r"recreation|escape room|axe|sport|gym|fitness|golf|skydiv|climb|paintball|equestrian|boat club|yacht|arcade|adventure|bowling", _re.I)
_drop   = _re.compile(r"optometr|eye care|chiropract|funeral|animal hospital|veterinar|physician|audiolog|urgent care|mental health|dental|\bclinic\b|day care|addiction|pregnancy|health cent|after school|massage therap", _re.I)
_civ = d["grp"] == "Civic"
d.loc[_civ & _cat.str.contains(_active), "grp"] = "Active"     # axe-throwing, rec centers, gyms, clubs -> Active
d.loc[_civ & _cat.str.contains(_drop),   "grp"] = "_DROP"      # optometrists, funeral homes, clinics -> not experiences
d = d[d["grp"] != "_DROP"].copy()

MO, NU, EB = "'Montserrat',sans-serif", "'Nunito',sans-serif", "'EB Garamond',serif"
# key, score column, label, blurb, emoji, font, tile CSS filter, gradient palette, page bg, ink, on-landing?, nature-floor?
M = lambda a,b,c2,d2: f"linear-gradient(125deg,{a} 0%,{b} 38%,{c2} 66%,{d2} 100%)"   # smooth metallic sheen
CONS = [
 ("rich","rich_composite","Psychologically Rich","novel, varied, mind-stretching","&#9733;",MO,"none",
   ["#5b2a86","#b5179e","#f72585","#ff8500","#ffd60a"],M("#14111a","#4b2a52","#1a1620","#241a2b"),"#f3f5f8",True,True),
 ("happy","Happiness_Score","Happy","warm, comfortable, joyful","&#9728;",NU,"saturate(1.15) brightness(1.05)",
   ["#ffe5a8","#ffc878","#f5a65b","#e08a4a","#d2691e"],M("#fbf6ec","#ffe7b0","#f3ddb0","#efe2c4"),"#4a3f2e",True,False),
 ("meaning","Meaningfulness_Score","Meaningful","purposeful, moving, significant","&#10047;",EB,"sepia(.4) saturate(1.5) contrast(.95)",
   ["#2c2a4a","#4f518c","#7b6ca8","#b298dc","#dabfff"],M("#16182a","#3a3c66","#1c1e30","#22243f"),"#e8e6f5",True,False),
 ("learning","Learning_Knowledge_Score","Learning","discover & learn something new","&#128218;",MO,"saturate(1.1) hue-rotate(-12deg)",
   ["#053b3b","#0e7c7b","#17becf","#7fe3dd","#d6fff6"],M("#0d1a1b","#0f6f6b","#0a1f20","#10302f"),"#e6f4f1",False,False),
 ("curiosity","Curiosity_Stretching_Score","Curious","sparks questions & wonder","&#10067;",NU,"brightness(1.05) saturate(1.25)",
   ["#0a3d62","#0a79b8","#3fa7e0","#7fd0ff","#d6f0ff"],M("#0f1822","#1f6f9e","#0e1a24","#13283a"),"#eaf2f8",False,False),
 ("surprise","Surprise_Score","Surprising","unexpected, awe-striking","&#10024;",MO,"contrast(1.2) saturate(1.3)",
   ["#5c1a10","#b3321b","#ff5722","#ff9a3c","#ffd56b"],M("#1a1211","#7a3320","#1e1413","#33201c"),"#ffece6",False,False),
 ("vitality","Vitality_Aliveness_Score","Alive","energizing, makes you feel alive","&#9889;",NU,"saturate(1.3) brightness(1.08)",
   ["#16400f","#2f8f2f","#5fd35f","#a8f0a0","#e6ffe0"],M("#0d160f","#2f7d2f","#0f1a12","#18301a"),"#eafaea",False,False),
 ("exploration","Exploration_Behavior_Score","Exploratory","invites you to wander & try","&#129517;",MO,"sepia(.2) saturate(1.2)",
   ["#3a2c14","#8a5a2b","#c98b3a","#e8c07a","#f6e6c8"],M("#161310","#8a5a2b","#1b1813","#2c2418"),"#f3ead8",False,False),
 ("selfexp","Self_Expansion_Score","Expansive","broadens your sense of self","&#127904;",EB,"hue-rotate(18deg) saturate(1.2)",
   ["#3a1245","#7b2a8f","#b85cd6","#dca8ff","#f3e8ff"],M("#140f1a","#7b2a8f","#18121f","#251830"),"#f3e8ff",False,False),
 ("perspective","Perspective_Change_Score","Perspective","shifts how you see things","&#128301;",EB,"grayscale(.4) sepia(.3)",
   ["#13315c","#2f6690","#5aa0c4","#bfae6e","#f0d98c"],M("#101319","#2f6690","#14171c","#1c222c"),"#e9eef4",False,False),
]

def recs(col, nature):
    cut = d[col].quantile(1-PCT); sel = d[col] >= cut
    if nature and (d.grp=="Nature").any():
        nat = d.grp=="Nature"; sel = sel | (nat & (d[col] >= d.loc[nat,col].quantile(1-PCT)))
    sub = d[sel].nlargest(CAP, col); out=[]
    for r in sub.itertuples():
        if pd.isna(r.latitude): continue
        out.append({"name":r.name,"cat":str(r.category).split(",")[0],"grp":r.grp,
            "lat":round(float(r.latitude),5),"lon":round(float(r.longitude),5),
            "score":round(float(getattr(r,col)),3),"rev":int(r.review_count),
            "rating":None if pd.isna(r.avg_rating) else round(float(r.avg_rating),1),
            "url":r.url if isinstance(r.url,str) else None})
    return out

DATA  = {c[0]: recs(c[1], c[11]) for c in CONS}
THEME = {c[0]: {"bg":c[8],"ink":c[9],"font":c[5],"filter":c[6],"pal":c[7]} for c in CONS}
LABEL = {c[0]: c[2] for c in CONS}
ZC = os.path.join(DRIVE,"ref","us_zip_centroids.csv")
_zc = pd.read_csv(ZC, dtype={"zipcode":str}); _zc = _zc[_zc.state_abbr.isin(["IL","IN","WI"])]
ZIPXY = {r.zipcode:[round(float(r.latitude),5),round(float(r.longitude),5)] for r in _zc.itertuples()}
with open(os.path.join(OUT,"data.js"),"w") as f:
    f.write("window.DATA="+json.dumps(DATA,ensure_ascii=False)+";\nwindow.ZIPXY="+json.dumps(ZIPXY)+";")
print("constructs:", {c[0]:len(DATA[c[0]]) for c in CONS})

OPTIONS = "".join(f'<option value="{c[0]}">{c[2]}</option>' for c in CONS)
CARD_COL={"rich":"#c1604f","happy":"#d9a441","meaning":"#4f7d8c"}   # three basic colors, Wes-Anderson muted
CARDS = "".join(
 f'<div class="choice" style="font-family:{c[5]};background:{CARD_COL.get(c[0],"#7e9c96")}" onclick="enter(\'{c[0]}\')"><span class="em">{c[4]}</span>{c[2]}<small>{c[3]}</small></div>'
 for c in CONS if c[10])

INDEX = r"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Chicago — Experience Atlas</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&family=Nunito:wght@400;700;800&family=EB+Garamond:ital@0;1&family=Pixelify+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#15131a;--ink:#f3f5f8;--font:'Montserrat',sans-serif}
*{box-sizing:border-box}html,body{margin:0;height:100%;overflow:hidden;background:var(--bg);color:var(--ink);
 font-family:var(--font);transition:background .9s ease,color .9s ease}
#map{position:absolute;top:64px;left:16px;right:16px;bottom:16px;border-radius:16px;overflow:hidden;box-shadow:0 14px 44px rgba(0,0,0,.32)}
.leaflet-container{border-radius:16px}.leaflet-tile-pane{transition:filter 1s ease}
#gate{position:fixed;inset:0;z-index:1000;display:flex;flex-direction:column;align-items:center;justify-content:center;
 background:linear-gradient(180deg,#bcd6d4 0%,#e7d6c2 56%,#e1a9a0 100%);transition:opacity 1s ease;padding:20px;overflow:hidden}
#gate.hide{opacity:0;pointer-events:none}
#gate h1{font-family:'Pixelify Sans',cursive;font-weight:700;font-size:46px;margin:0 0 8px;color:#3a4a52;text-shadow:3px 3px 0 #f4ece0}
#gate p{font-family:'Nunito',sans-serif;color:#5f6d6a;font-size:14px;margin:0 0 30px}
#skyline{position:absolute;left:0;right:0;bottom:0;height:62%;z-index:0;pointer-events:none}
#skyline svg{width:100%;height:100%;display:block}
#gate h1,#gate p,#gate .choices,#gate .gatehint{position:relative;z-index:1}
.choices{display:flex;gap:22px;flex-wrap:wrap;justify-content:center;max-width:680px}
.choice{width:230px;height:190px;border-radius:18px;cursor:pointer;display:flex;flex-direction:column;align-items:center;
 justify-content:center;color:#fbf3e6;font-family:'Pixelify Sans',cursive;font-weight:700;font-size:27px;
 border:3px solid #2f3a45;box-shadow:6px 6px 0 #2f3a45;transition:transform .18s ease,box-shadow .18s ease}
.choice small{font-family:'Nunito',sans-serif;font-weight:700;font-size:12px;opacity:.85;margin-top:10px;max-width:194px;text-align:center}
.choice:hover{transform:translate(-3px,-4px);box-shadow:10px 10px 0 #2f3a45}
.choice .em{font-size:42px;margin-bottom:8px}
.gatehint{color:#8e96a4;font-size:12px;margin-top:26px}
#bar{position:fixed;top:14px;left:50%;transform:translateX(-50%);z-index:800;display:none;gap:10px;align-items:center;
 background:linear-gradient(180deg,rgba(40,44,54,.92),rgba(24,27,34,.92));border:1px solid rgba(200,210,225,.3);
 padding:9px 14px;border-radius:16px;box-shadow:0 10px 30px rgba(0,0,0,.45);backdrop-filter:blur(8px)}
#bar.show{display:flex}#bar .lbl{font-family:'Pixelify Sans',cursive;font-weight:700;font-size:16px;color:#eef2f7;margin-right:2px}
select{font-family:'Pixelify Sans',cursive;font-size:13px;padding:7px 10px;border-radius:10px;border:1px solid rgba(190,200,215,.4);
 background:rgba(12,14,20,.7);color:#eef2f7;outline:none;cursor:pointer}
#legend{position:fixed;bottom:16px;left:16px;z-index:800;background:rgba(255,255,255,.92);color:#333;padding:8px 11px;
 border-radius:10px;font-family:'Pixelify Sans',cursive;font-size:11px;box-shadow:0 6px 20px rgba(0,0,0,.25);display:none}#legend.show{display:block}
#zipin{font-family:'Pixelify Sans',cursive;width:62px;font-size:13px;padding:7px 8px;border-radius:10px;border:1px solid rgba(190,200,215,.4);background:rgba(12,14,20,.7);color:#eef2f7;text-align:center}
#zipgo{font-family:'Pixelify Sans',cursive;font-size:13px;padding:7px 12px;border-radius:10px;border:0;background:#e0b13a;color:#1a1a1a;cursor:pointer}
#disc{position:fixed;bottom:16px;right:16px;z-index:800;max-width:300px;font-size:10px;color:#9aa3b0;
 background:rgba(20,22,30,.7);padding:6px 9px;border-radius:8px;display:none}#disc.show{display:block}
.mk{transition:transform .18s cubic-bezier(.2,1.5,.4,1);transform-origin:center bottom}
.mk:hover{transform:scale(1.6) translateY(-4px)}
@keyframes hop{0%{transform:scale(1)}30%{transform:scale(1.7) translateY(-10px)}100%{transform:scale(1)}}
.mk.hop{animation:hop .6s ease}
.leaflet-popup-content{font-family:var(--font)}.pname{font-size:16px;font-weight:800;margin-bottom:2px}
.pcat{color:#666;font-size:12px}.pmeta{margin-top:5px;font-size:12px}.plink{margin-top:6px;display:inline-block}
</style></head><body>
<div id="map"></div>
<div id="bar"><span class="lbl" id="barTitle">Rich</span>
 <select id="selConstruct">__OPTIONS__</select>
 <select id="selCat"><option value="All">All places</option><option>Culture</option><option>Food</option>
  <option>Nature</option><option>Active</option><option>Retail</option><option>Civic</option><option>Wellness</option></select>
 <input id="zipin" placeholder="ZIP" maxlength="5"><button id="zipgo">Go</button></div>
<div id="legend"></div>
<div id="disc" class="show">Scores aggregate public Google reviews (2016&ndash;2021): a place's tendency to <i>afford</i>
 the experience as visitors described it &mdash; not a guarantee or causal claim. Links via Google Maps.</div>
<div id="gate">__SKYLINE__<h1>Where do you want to explore?</h1>
 <p>Choose an experience &mdash; Chicago, from millions of visitor reviews.</p>
 <div class="choices">__CARDS__</div>
 <div class="gatehint">&mdash; or pick more experiences from the menu after you enter &mdash;</div></div>
<script src="data.js"></script>
<script>
var SYM={Culture:"🎨",Food:"🍕",Nature:"🌳",Active:"🎢",Retail:"🛍️",Civic:"🏛️",Wellness:"💆",Other:"📍"};
var THEME=__THEME__, LABEL=__LABEL__;
var map=L.map("map",{zoomControl:true,attributionControl:false}).setView([41.83,-87.72],11);
L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png").addTo(map);
var layer=L.layerGroup().addTo(map), cur="rich";
function lerp(a,b,t){return Math.round(a+(b-a)*t);}
function hx(h){return [parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16)];}
function grad(p,t){t=Math.max(0,Math.min(1,t));var n=p.length-1,i=Math.min(n-1,Math.floor(t*n)),f=t*n-i;
 var a=hx(p[i]),b=hx(p[i+1]);return "rgb("+lerp(a[0],b[0],f)+","+lerp(a[1],b[1],f)+","+lerp(a[2],b[2],f)+")";}
function size(r){return Math.round(Math.max(13,Math.min(46,13+4*Math.sqrt(r))));}
function render(){layer.clearLayers();var arr=window.DATA[cur],cat=document.getElementById("selCat").value;
 var ss=arr.map(function(p){return p.score;}),mn=Math.min.apply(null,ss),mx=Math.max.apply(null,ss);
 arr.forEach(function(p){if(cat!=="All"&&p.grp!==cat)return;
  var col=grad(THEME[cur].pal,(p.score-mn)/(mx-mn||1)),px=size(p.rev);
  var icon=L.divIcon({className:"",iconSize:[px,px],iconAnchor:[px/2,px/2],
   html:"<div class='mk' style='width:"+px+"px;height:"+px+"px;background:"+col+";border:2px solid rgba(20,20,30,.45);border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:"+Math.round(px*0.58)+"px;box-shadow:1px 1px 0 rgba(0,0,0,.35)'>"+(SYM[p.grp]||"📍")+"</div>"});
  var lk=p.url?"<a class='plink' href='"+p.url+"' target='_blank' rel='noopener'>Open in Google Maps →</a>":"";
  var html="<div class='pname'>"+p.name+"</div><div class='pcat'>"+p.cat+" · "+p.grp+"</div>"+
   "<div class='pmeta'>"+LABEL[cur]+" score "+p.score+" · "+p.rev+" reviews"+(p.rating?(" · ★"+p.rating):"")+"</div>"+lk;
  var mk=L.marker([p.lat,p.lon],{icon:icon}).bindPopup(html);
  mk.on("click",function(e){var el=e.target.getElement();if(el){var dv=el.querySelector(".mk");if(dv){dv.classList.add("hop");setTimeout(function(){dv.classList.remove("hop");},600);}}});
  layer.addLayer(mk);});
 document.getElementById("legend").innerHTML="🎨 Culture 🍕 Food 🌳 Nature 🎢 Active 🛍️ Retail 🏛️ Civic 💆 Wellness<br><i>size = #reviews · color = "+LABEL[cur]+" score</i>";}
function applyTheme(){var t=THEME[cur];var R=document.documentElement.style;
 R.setProperty("--bg",t.bg);R.setProperty("--ink",t.ink);R.setProperty("--font",t.font);
 var tp=document.querySelector(".leaflet-tile-pane");if(tp)tp.style.filter=t.filter;
 document.getElementById("barTitle").textContent=LABEL[cur];}
function enter(c){cur=c;document.getElementById("selConstruct").value=c;applyTheme();render();
 document.getElementById("gate").classList.add("hide");document.getElementById("bar").classList.add("show");
 document.getElementById("legend").classList.add("show");
 setTimeout(function(){map.invalidateSize();map.flyTo([41.85,-87.66],12,{duration:1.6});},150);}
document.getElementById("selConstruct").onchange=function(){cur=this.value;applyTheme();render();};
document.getElementById("selCat").onchange=render;
function flyZip(){var z=(document.getElementById("zipin").value||"").trim();
 if(window.ZIPXY&&window.ZIPXY[z]){map.flyTo(window.ZIPXY[z],14,{duration:1.5});}}
document.getElementById("zipgo").onclick=flyZip;
document.getElementById("zipin").addEventListener("keydown",function(e){if(e.key==="Enter")flyZip();});
</script></body></html>"""
import math
def gen_skyline():
    # Wes-Anderson muted palette, Chicago SIGNATURE architecture (flat, recognizable)
    G=360; P=[]; WIN="#e0b13a"
    def wins(x,y,w,col=WIN,step=13):
        for wx in range(x+8,x+w-6,step):
            for wy in range(y+12,G-12,17):
                if (wx*3+wy)%3: P.append(f'<rect x="{wx}" y="{wy}" width="4" height="6" fill="{col}" opacity="0.85"/>')
    # back filler buildings (muted sage / teal)
    for x,w,h,c in [(0,86,120,"#7e9c96"),(78,64,90,"#688f8f"),(360,52,140,"#83a0a4"),(540,46,150,"#6f9296"),
                    (800,60,150,"#7e9c96"),(862,52,120,"#688f8f"),(1180,80,130,"#7e9c96"),(1250,70,150,"#688f8f")]:
        P.append(f'<rect x="{x}" y="{G-h}" width="{w+2}" height="{h}" fill="{c}"/>')
    # Marina City — twin "corncob" towers (x~140)
    for mx in (132,196):
        P.append(f'<rect x="{mx}" y="{G-208}" width="48" height="208" fill="#efe3cf"/>')
        P.append(f'<path d="M{mx} {G-208} q24 -30 48 0 z" fill="#efe3cf"/>')
        for ry in range(G-198,G-8,15): P.append(f'<rect x="{mx}" y="{ry}" width="48" height="3" fill="#cdbfa6"/>')
    # Wrigley Building — cream + clock tower (x~270)
    P.append(f'<rect x="270" y="{G-250}" width="66" height="250" fill="#f1e8d6"/>')
    P.append(f'<rect x="292" y="{G-300}" width="22" height="52" fill="#f1e8d6"/>')
    P.append(f'<circle cx="303" cy="{G-284}" r="8" fill="#d9a441"/>'); wins(270,G-245,66,"#c79a52")
    # Willis Tower — stepped black bundle + twin antennas (x~430, tallest)
    P.append(f'<rect x="430" y="{G-338}" width="74" height="338" fill="#33404a"/>')
    P.append(f'<rect x="446" y="{G-372}" width="42" height="36" fill="#33404a"/>')
    P.append(f'<rect x="454" y="{G-410}" width="3" height="40" fill="#efe3cf"/><rect x="476" y="{G-416}" width="3" height="46" fill="#efe3cf"/>')
    wins(430,G-334,74,WIN,16)
    # John Hancock — tapered with X-bracing + antennas (x~560)
    P.append(f'<polygon points="560,{G} 628,{G} 616,{G-300} 572,{G-300}" fill="#2d3640"/>')
    P.append(f'<rect x="586" y="{G-338}" width="3" height="38" fill="#efe3cf"/><rect x="600" y="{G-338}" width="3" height="38" fill="#efe3cf"/>')
    P.append(f'<line x1="572" y1="{G-300}" x2="624" y2="{G-150}" stroke="#1c242c" stroke-width="2.5"/><line x1="616" y1="{G-300}" x2="564" y2="{G-150}" stroke="#1c242c" stroke-width="2.5"/>')
    # Tribune Tower — stone gothic crown (x~660)
    P.append(f'<rect x="660" y="{G-236}" width="54" height="236" fill="#d8cdb8"/>')
    for gx in range(662,712,9): P.append(f'<rect x="{gx}" y="{G-256}" width="4" height="22" fill="#d8cdb8"/>')
    wins(660,G-231,54,"#a98a52",11)
    # Cloud Gate "The Bean" on the ground (x~930)
    P.append(f'<ellipse cx="930" cy="{G-16}" rx="48" ry="22" fill="#aeb8be"/><ellipse cx="918" cy="{G-22}" rx="17" ry="7" fill="#dfe6ea" opacity="0.85"/>')
    # Navy Pier Ferris wheel (x~1080, dusty pink)
    cx,cy,r=1080,250,58
    P.append(f'<line x1="{cx-40}" y1="{G}" x2="{cx}" y2="{cy}" stroke="#9a8d7e" stroke-width="3"/><line x1="{cx+40}" y1="{G}" x2="{cx}" y2="{cy}" stroke="#9a8d7e" stroke-width="3"/>')
    P.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#d98b8b" stroke-width="3"/>')
    for a in range(0,360,30):
        ex=cx+r*math.cos(math.radians(a)); ey=cy+r*math.sin(math.radians(a))
        P.append(f'<line x1="{cx}" y1="{cy}" x2="{ex:.0f}" y2="{ey:.0f}" stroke="#d98b8b" stroke-width="1.3" opacity="0.65"/>')
        P.append(f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="4" fill="#e0b13a"/>')
    P.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="#d98b8b"/>')
    P.append('<circle cx="120" cy="58" r="26" fill="#f4ecd6"/>')  # moon
    return '<svg viewBox="0 0 1320 360" preserveAspectRatio="xMidYMax slice" xmlns="http://www.w3.org/2000/svg">'+"".join(P)+'</svg>'
SKYLINE='<div id="skyline">'+gen_skyline()+'</div>'
INDEX = (INDEX.replace("__OPTIONS__", OPTIONS).replace("__CARDS__", CARDS).replace("__SKYLINE__", SKYLINE)
         .replace("__THEME__", json.dumps(THEME)).replace("__LABEL__", json.dumps(LABEL)))
# NOTE: index.html is now the hand-maintained source of truth (glass UI, pixel art, portal,
# avatar live there and must NOT be auto-overwritten). This script writes a reference copy to
# index.generated.html instead — diff it by hand if you ever want to pull scaffolding changes.
with open(os.path.join(OUT,"index.generated.html"),"w") as f: f.write(INDEX)
print("wrote", os.path.join(OUT,"index.generated.html"), "(reference only) | constructs:", len(CONS))
print("RUN:  cd ~/chicago_experience_site && python3 -m http.server 8000   ->  http://localhost:8000")
