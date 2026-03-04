"""
JOB HUNTER BOT v4.0
Menu con botones + sitios web personalizados + 11 portales + canales Telegram
Deploy: Railway.app
"""
import os,json,time,hashlib,logging,re,threading
from datetime import datetime
from html import escape as he
import requests
from bs4 import BeautifulSoup

try:
    from telegram import Update,InlineKeyboardButton as IKB,InlineKeyboardMarkup as IKM
    from telegram.ext import Application,CommandHandler,CallbackQueryHandler,MessageHandler,ContextTypes,filters
    PTB=True
except ImportError:
    PTB=False

try:
    import asyncio
    from telethon import TelegramClient,events
    TEL=True
except ImportError:
    TEL=False

TK=os.environ.get("TELEGRAM_BOT_TOKEN","")
CI=os.environ.get("TELEGRAM_CHAT_ID","")
API_ID=os.environ.get("TELEGRAM_API_ID","")
API_HASH=os.environ.get("TELEGRAM_API_HASH","")
TG_PHONE=os.environ.get("TELEGRAM_PHONE","")
INTERVAL=int(os.environ.get("SEARCH_INTERVAL_MINUTES","60"))
CF="/tmp/bot_config.json"
SF="/tmp/seen_jobs.json"

logging.basicConfig(level=logging.INFO,format="%(asctime)s [%(levelname)s] %(message)s")
L=logging.getLogger("JH")

DC={
    "match_keywords":["support","soporte","help desk","helpdesk","service desk","IT","technical","tecnico","monitoreo","monitoring","NOC","network","redes","QA","testing","tester","desktop","system","admin","analyst","analista","remote","remoto","cybersecurity","ciberseguridad","troubleshoot","tickets","incidencias","mesa de ayuda","infraestructura","windows","linux","servidor"],
    "exclude_keywords":["senior developer","lead engineer","architect","machine learning","data scientist","PhD","director","VP ","chief ","CTO","CFO"],
    "telegram_channels":["remotojob","vacantesremotas","STEMJobsLATAM","Empleos_En_Venezuela","tecnoempleo_remoto"],
    "custom_sites":[],
    "awaiting_input":None,
}

def lc():
    try:
        with open(CF,"r") as f:
            c=json.load(f)
            for k in DC:
                if k not in c: c[k]=DC[k]
            return c
    except: sc(DC); return DC.copy()

def sc(c):
    with open(CF,"w") as f: json.dump(c,f,ensure_ascii=False,indent=2)

def ls2():
    try:
        with open(SF,"r") as f: return set(json.load(f))
    except: return set()

def ss(s):
    with open(SF,"w") as f: json.dump(list(s),f)

def mi(t): return hashlib.md5(t.encode()).hexdigest()[:16]

def mp(title,desc="",cfg=None):
    if cfg is None: cfg=lc()
    t=f"{title} {desc}".lower()
    for ex in cfg.get("exclude_keywords",[]):
        if ex.lower() in t: return False
    return any(kw.lower() in t for kw in cfg.get("match_keywords",[]))

def stg(msg):
    if not TK or not CI: return False
    try:
        r=requests.post(f"https://api.telegram.org/bot{TK}/sendMessage",
            json={"chat_id":CI,"text":msg,"parse_mode":"HTML","disable_web_page_preview":False},timeout=10)
        return r.status_code==200
    except Exception as e: L.error(f"TG: {e}"); return False

def fj(j):
    m=f"<b>{he(j.get('title',''))}</b>\n"
    for k in ["company","location","salary","source","date"]:
        if j.get(k): m+=f"{he(str(j[k]))}\n"
    if j.get("url"): m+=f'\n<a href="{j["url"]}">Ver oferta</a>'
    return m

def sg(url,hdr=None,to=15):
    try:
        h=hdr or {}
        h.setdefault("User-Agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        h.setdefault("Accept-Language","es-ES,es;q=0.9,en;q=0.8")
        r=requests.get(url,headers=h,timeout=to); r.raise_for_status(); return r
    except Exception as e: L.warning(f"GET {url[:50]}: {e}"); return None

# ============================================================
# MENU CON BOTONES
# ============================================================
if PTB:
    def main_menu():
        return IKM([
            [IKB("🔍 Buscar ahora",callback_data="do_search")],
            [IKB("📝 Keywords",callback_data="menu_kw"),IKB("🚫 Excluidas",callback_data="menu_ex")],
            [IKB("📡 Canales TG",callback_data="menu_ch"),IKB("🌐 Sitios web",callback_data="menu_sites")],
            [IKB("⚙️ Config",callback_data="menu_config")],
        ])

    def kw_menu():
        return IKM([
            [IKB("📋 Ver keywords",callback_data="kw_list")],
            [IKB("➕ Agregar",callback_data="kw_add"),IKB("➖ Quitar",callback_data="kw_remove")],
            [IKB("⬅️ Menu principal",callback_data="main")],
        ])

    def ex_menu():
        return IKM([
            [IKB("📋 Ver excluidas",callback_data="ex_list")],
            [IKB("➕ Excluir palabra",callback_data="ex_add"),IKB("➖ Quitar exclusion",callback_data="ex_remove")],
            [IKB("⬅️ Menu principal",callback_data="main")],
        ])

    def ch_menu():
        return IKM([
            [IKB("📋 Ver canales",callback_data="ch_list")],
            [IKB("➕ Agregar canal",callback_data="ch_add"),IKB("➖ Quitar canal",callback_data="ch_remove")],
            [IKB("⬅️ Menu principal",callback_data="main")],
        ])

    def sites_menu():
        return IKM([
            [IKB("📋 Ver sitios",callback_data="sites_list")],
            [IKB("➕ Agregar sitio web",callback_data="sites_add")],
            [IKB("➖ Quitar sitio",callback_data="sites_remove")],
            [IKB("⬅️ Menu principal",callback_data="main")],
        ])

    async def cmd_start(u:Update,c:ContextTypes.DEFAULT_TYPE):
        await u.message.reply_text(
            "🤖 <b>Job Hunter Bot v4.0</b>\n\n"
            "Busco trabajo en <b>11 portales</b> + los sitios que tu agregues + canales de Telegram.\n\n"
            "Usa los botones para navegar:",
            parse_mode="HTML",reply_markup=main_menu())

    async def button_handler(u:Update,c:ContextTypes.DEFAULT_TYPE):
        q=u.callback_query
        await q.answer()
        d=q.data
        cfg=lc()

        # MENU PRINCIPAL
        if d=="main":
            await q.edit_message_text("🤖 <b>Job Hunter Bot v4.0</b>\n\nUsa los botones:",parse_mode="HTML",reply_markup=main_menu())

        # BUSCAR
        elif d=="do_search":
            await q.edit_message_text("🔍 <b>Buscando en todos los portales...</b>\nTe aviso cuando termine.",parse_mode="HTML",reply_markup=IKM([[IKB("⬅️ Menu",callback_data="main")]]))
            threading.Thread(target=run_search,daemon=True).start()

        # KEYWORDS
        elif d=="menu_kw":
            await q.edit_message_text("📝 <b>Keywords</b>\nPalabras que busca el bot:",parse_mode="HTML",reply_markup=kw_menu())
        elif d=="kw_list":
            kws=cfg.get("match_keywords",[])
            t="📝 <b>Keywords activas:</b>\n\n"+"\n".join(f"• {he(k)}" for k in kws)+f"\n\nTotal: {len(kws)}"
            await q.edit_message_text(t,parse_mode="HTML",reply_markup=kw_menu())
        elif d=="kw_add":
            cfg["awaiting_input"]="kw_add"; sc(cfg)
            await q.edit_message_text("✏️ <b>Escribe la keyword que quieres agregar:</b>\n\nEjemplo: mesa de ayuda",parse_mode="HTML",reply_markup=IKM([[IKB("❌ Cancelar",callback_data="menu_kw")]]))
        elif d=="kw_remove":
            cfg["awaiting_input"]="kw_remove"; sc(cfg)
            await q.edit_message_text("✏️ <b>Escribe la keyword que quieres quitar:</b>",parse_mode="HTML",reply_markup=IKM([[IKB("❌ Cancelar",callback_data="menu_kw")]]))

        # EXCLUSIONES
        elif d=="menu_ex":
            await q.edit_message_text("🚫 <b>Exclusiones</b>\nPalabras que el bot ignora:",parse_mode="HTML",reply_markup=ex_menu())
        elif d=="ex_list":
            exl=cfg.get("exclude_keywords",[])
            t="🚫 <b>Palabras excluidas:</b>\n\n"+"\n".join(f"• {he(k)}" for k in exl)+f"\n\nTotal: {len(exl)}"
            await q.edit_message_text(t,parse_mode="HTML",reply_markup=ex_menu())
        elif d=="ex_add":
            cfg["awaiting_input"]="ex_add"; sc(cfg)
            await q.edit_message_text("✏️ <b>Escribe la palabra que quieres excluir:</b>\n\nEjemplo: data scientist",parse_mode="HTML",reply_markup=IKM([[IKB("❌ Cancelar",callback_data="menu_ex")]]))
        elif d=="ex_remove":
            cfg["awaiting_input"]="ex_remove"; sc(cfg)
            await q.edit_message_text("✏️ <b>Escribe la exclusion que quieres quitar:</b>",parse_mode="HTML",reply_markup=IKM([[IKB("❌ Cancelar",callback_data="menu_ex")]]))

        # CANALES TELEGRAM
        elif d=="menu_ch":
            st="ACTIVO" if (TEL and API_ID) else "INACTIVO"
            await q.edit_message_text(f"📡 <b>Canales de Telegram</b>\nEstado: {st}",parse_mode="HTML",reply_markup=ch_menu())
        elif d=="ch_list":
            chs=cfg.get("telegram_channels",[])
            t="📡 <b>Canales:</b>\n\n"+"\n".join(f"• @{he(c)}" for c in chs)+f"\n\nTotal: {len(chs)}"
            await q.edit_message_text(t,parse_mode="HTML",reply_markup=ch_menu())
        elif d=="ch_add":
            cfg["awaiting_input"]="ch_add"; sc(cfg)
            await q.edit_message_text("✏️ <b>Escribe el nombre del canal:</b>\n\nEjemplo: remotojob",parse_mode="HTML",reply_markup=IKM([[IKB("❌ Cancelar",callback_data="menu_ch")]]))
        elif d=="ch_remove":
            cfg["awaiting_input"]="ch_remove"; sc(cfg)
            await q.edit_message_text("✏️ <b>Escribe el canal que quieres quitar:</b>",parse_mode="HTML",reply_markup=IKM([[IKB("❌ Cancelar",callback_data="menu_ch")]]))

        # SITIOS WEB PERSONALIZADOS
        elif d=="menu_sites":
            await q.edit_message_text("🌐 <b>Sitios web personalizados</b>\nAgrega cualquier pagina que publique ofertas de empleo.\nEl bot la revisara en cada busqueda.",parse_mode="HTML",reply_markup=sites_menu())
        elif d=="sites_list":
            sites=cfg.get("custom_sites",[])
            if sites:
                t="🌐 <b>Sitios personalizados:</b>\n\n"+"\n".join(f"• {he(s.get('name',''))}: {he(s.get('url',''))}" for s in sites)
            else:
                t="🌐 <b>No hay sitios personalizados.</b>\nAgrega uno con el boton ➕"
            await q.edit_message_text(t,parse_mode="HTML",reply_markup=sites_menu())
        elif d=="sites_add":
            cfg["awaiting_input"]="sites_add"; sc(cfg)
            await q.edit_message_text("✏️ <b>Envia la URL del sitio web:</b>\n\nEjemplo: https://www.yoursite.com/empleos\n\nEl bot va a escanear esa pagina buscando ofertas que coincidan con tus keywords.",parse_mode="HTML",reply_markup=IKM([[IKB("❌ Cancelar",callback_data="menu_sites")]]))
        elif d=="sites_remove":
            cfg["awaiting_input"]="sites_remove"; sc(cfg)
            sites=cfg.get("custom_sites",[])
            if sites:
                t="✏️ <b>Escribe el nombre del sitio a quitar:</b>\n\n"+"\n".join(f"• {s.get('name','')}" for s in sites)
            else:
                t="No hay sitios para quitar"
            await q.edit_message_text(t,parse_mode="HTML",reply_markup=IKM([[IKB("❌ Cancelar",callback_data="menu_sites")]]))

        # CONFIG
        elif d=="menu_config":
            sites=cfg.get("custom_sites",[])
            t=(f"⚙️ <b>Configuracion:</b>\n\n"
               f"📝 Keywords: {len(cfg.get('match_keywords',[]))}\n"
               f"🚫 Excluidas: {len(cfg.get('exclude_keywords',[]))}\n"
               f"📡 Canales TG: {len(cfg.get('telegram_channels',[]))}\n"
               f"🌐 Sitios web: {len(sites)}\n"
               f"⏰ Intervalo: {INTERVAL} min\n"
               f"📊 Portales fijos: 11")
            await q.edit_message_text(t,parse_mode="HTML",reply_markup=IKM([[IKB("⬅️ Menu",callback_data="main")]]))

    async def text_handler(u:Update,c:ContextTypes.DEFAULT_TYPE):
        """Maneja texto libre cuando el bot espera input del usuario."""
        cfg=lc()
        action=cfg.get("awaiting_input")
        if not action: return
        txt=u.message.text.strip()
        cfg["awaiting_input"]=None
        reply=""

        if action=="kw_add":
            kw=txt.lower()
            if kw not in [k.lower() for k in cfg["match_keywords"]]:
                cfg["match_keywords"].append(kw)
                reply=f"✅ Keyword agregada: <b>{he(kw)}</b>"
            else: reply=f"Ya existe: {he(kw)}"
            sc(cfg)
            await u.message.reply_text(reply,parse_mode="HTML",reply_markup=kw_menu())

        elif action=="kw_remove":
            kw=txt.lower(); n=len(cfg["match_keywords"])
            cfg["match_keywords"]=[k for k in cfg["match_keywords"] if k.lower()!=kw]
            if len(cfg["match_keywords"])<n: reply=f"✅ Eliminada: <b>{he(kw)}</b>"
            else: reply=f"No encontrada: {he(kw)}"
            sc(cfg)
            await u.message.reply_text(reply,parse_mode="HTML",reply_markup=kw_menu())

        elif action=="ex_add":
            if txt.lower() not in [k.lower() for k in cfg["exclude_keywords"]]:
                cfg["exclude_keywords"].append(txt)
                reply=f"✅ Excluida: <b>{he(txt)}</b>"
            else: reply=f"Ya excluida: {he(txt)}"
            sc(cfg)
            await u.message.reply_text(reply,parse_mode="HTML",reply_markup=ex_menu())

        elif action=="ex_remove":
            kw=txt.lower(); n=len(cfg["exclude_keywords"])
            cfg["exclude_keywords"]=[k for k in cfg["exclude_keywords"] if k.lower()!=kw]
            if len(cfg["exclude_keywords"])<n: reply=f"✅ Ya no se excluye: <b>{he(kw)}</b>"
            else: reply=f"No encontrada: {he(kw)}"
            sc(cfg)
            await u.message.reply_text(reply,parse_mode="HTML",reply_markup=ex_menu())

        elif action=="ch_add":
            ch=txt.replace("@","").replace("https://t.me/","").replace("https://t.me/joinchat/","invite_").strip()
            if ch not in cfg["telegram_channels"]:
                cfg["telegram_channels"].append(ch)
                reply=f"✅ Canal agregado: <b>@{he(ch)}</b>"
            else: reply=f"Ya existe: @{he(ch)}"
            sc(cfg)
            await u.message.reply_text(reply,parse_mode="HTML",reply_markup=ch_menu())

        elif action=="ch_remove":
            ch=txt.replace("@","").strip()
            if ch in cfg["telegram_channels"]:
                cfg["telegram_channels"].remove(ch)
                reply=f"✅ Eliminado: @{he(ch)}"
            else: reply=f"No encontrado: @{he(ch)}"
            sc(cfg)
            await u.message.reply_text(reply,parse_mode="HTML",reply_markup=ch_menu())

        elif action=="sites_add":
            url=txt.strip()
            if not url.startswith("http"): url="https://"+url
            # Extraer nombre del dominio
            try:
                from urllib.parse import urlparse
                name=urlparse(url).netloc.replace("www.","")
            except:
                name=url[:40]
            cfg.setdefault("custom_sites",[])
            if not any(s.get("url")==url for s in cfg["custom_sites"]):
                cfg["custom_sites"].append({"name":name,"url":url})
                reply=f"✅ Sitio agregado: <b>{he(name)}</b>\n{he(url)}\n\nSe revisara en cada busqueda."
            else: reply=f"Ya existe: {he(url)}"
            sc(cfg)
            await u.message.reply_text(reply,parse_mode="HTML",reply_markup=sites_menu())

        elif action=="sites_remove":
            name=txt.lower().strip()
            sites=cfg.get("custom_sites",[])
            n=len(sites)
            cfg["custom_sites"]=[s for s in sites if s.get("name","").lower()!=name]
            if len(cfg["custom_sites"])<n: reply=f"✅ Sitio eliminado: <b>{he(txt)}</b>"
            else: reply=f"No encontrado: {he(txt)}"
            sc(cfg)
            await u.message.reply_text(reply,parse_mode="HTML",reply_markup=sites_menu())

# ============================================================
# 11 FUENTES FIJAS + SITIOS PERSONALIZADOS
# ============================================================

def search_linkedin():
    j,cfg=[],lc()
    for q in ["soporte+tecnico+remoto","help+desk+remoto","IT+support+remote+spanish","monitoreo+redes+remoto","service+desk+remoto","network+monitoring+remote","QA+tester+remoto"]:
        r=sg(f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={q}&f_WT=2&start=0")
        if not r: continue
        try:
            soup=BeautifulSoup(r.text,"html.parser")
            for card in soup.find_all("li")[:8]:
                te=card.find("h3",class_="base-search-card__title")
                ce=card.find("h4",class_="base-search-card__subtitle")
                le=card.find("span",class_="job-search-card__location")
                ae=card.find("a",class_="base-card__full-link")
                de=card.find("time")
                t=te.get_text(strip=True) if te else ""
                if t and mp(t,"",cfg):
                    j.append({"id":mi(f"li_{t}_{ce.get_text(strip=True) if ce else ''}"),"title":t,"company":ce.get_text(strip=True) if ce else "","location":le.get_text(strip=True) if le else "Remoto","url":ae["href"].split("?")[0] if ae and ae.get("href") else "","date":de.get("datetime","")[:10] if de else "","source":"LinkedIn"})
        except: pass
        time.sleep(2)
    return j

def search_computrabajo():
    j,cfg=[],lc()
    for url,cc in [("https://www.computrabajo.com.ve/trabajo-de-soporte-tecnico","VE"),("https://www.computrabajo.com.ve/trabajo-de-help-desk","VE"),("https://www.computrabajo.com.ve/trabajo-de-monitoreo","VE"),("https://co.computrabajo.com/trabajo-de-soporte-tecnico-remoto","CO"),("https://co.computrabajo.com/trabajo-de-help-desk-remoto","CO"),("https://www.computrabajo.com.ar/trabajo-de-soporte-tecnico-remoto","AR"),("https://www.computrabajo.com.mx/trabajo-de-soporte-tecnico-remoto","MX"),("https://pe.computrabajo.com/trabajo-de-soporte-tecnico-remoto","PE"),("https://www.computrabajo.cl/trabajo-de-soporte-tecnico-remoto","CL"),("https://ec.computrabajo.com/trabajo-de-soporte-tecnico-remoto","EC")]:
        r=sg(url)
        if not r: continue
        try:
            soup=BeautifulSoup(r.text,"html.parser")
            for art in (soup.find_all("article") or soup.find_all("div",class_="box_offer"))[:8]:
                te=art.find("a",class_="js-o-link") or art.find("a",class_="fc_base") or art.find("h2") or art.find("a")
                t=te.get_text(strip=True) if te else ""
                lk=""
                if te and te.get("href"): lk=te["href"] if te["href"].startswith("http") else url.split("/trabajo")[0]+te["href"]
                if t and mp(t,"",cfg): j.append({"id":mi(f"ct_{t}_{cc}"),"title":t,"company":"","location":cc,"url":lk,"date":datetime.now().strftime("%Y-%m-%d"),"source":f"Computrabajo {cc}"})
        except: pass
        time.sleep(3)
    return j

def search_remoteok():
    j,cfg=[],lc()
    r=sg("https://remoteok.com/api",hdr={"User-Agent":"JobHunterBot/4.0"})
    if not r: return j
    try:
        for i in r.json():
            if not isinstance(i,dict) or "id" not in i: continue
            if mp(i.get("position",""),i.get("description",""),cfg):
                j.append({"id":f"rok_{i['id']}","title":i.get("position",""),"company":i.get("company",""),"location":"Remoto","salary":i.get("salary",""),"url":i.get("url",f"https://remoteok.com/l/{i['id']}"),"date":i.get("date","")[:10],"source":"RemoteOK"})
    except: pass
    return j

def search_remotive():
    j,cfg=[],lc()
    for cat in ["qa","customer-support","devops-sysadmin","all-others"]:
        r=sg(f"https://remotive.com/api/remote-jobs?category={cat}&limit=20")
        if not r: continue
        try:
            for i in r.json().get("jobs",[]):
                if mp(i.get("title",""),i.get("description",""),cfg):
                    j.append({"id":f"rem_{i.get('id','')}","title":i.get("title",""),"company":i.get("company_name",""),"location":i.get("candidate_required_location","Remoto"),"salary":i.get("salary",""),"url":i.get("url",""),"date":i.get("publication_date","")[:10],"source":"Remotive"})
        except: pass
        time.sleep(1)
    return j

def search_jobicy():
    j,cfg=[],lc()
    r=sg("https://jobicy.com/api/v2/remote-jobs?count=30&tag=support,qa,sysadmin,helpdesk,monitoring,network,it")
    if not r: return j
    try:
        for i in r.json().get("jobs",[]):
            if mp(i.get("jobTitle",""),i.get("jobDescription",""),cfg):
                j.append({"id":f"jbc_{i.get('id','')}","title":i.get("jobTitle",""),"company":i.get("companyName",""),"location":i.get("jobGeo","Remoto"),"url":i.get("url",""),"date":i.get("pubDate","")[:10],"source":"Jobicy"})
    except: pass
    return j

def search_arbeitnow():
    j,cfg=[],lc()
    r=sg("https://www.arbeitnow.com/api/job-board-api")
    if not r: return j
    try:
        for i in r.json().get("data",[]):
            if i.get("remote") and mp(i.get("title",""),i.get("description",""),cfg):
                j.append({"id":f"arb_{i.get('slug','')}","title":i.get("title",""),"company":i.get("company_name",""),"location":i.get("location","Remoto"),"url":i.get("url",""),"date":i.get("created_at","")[:10],"source":"Arbeitnow"})
    except: pass
    return j

def _scr(url,pf,src,cfg):
    j=[]
    r=sg(url)
    if not r: return j
    try:
        soup=BeautifulSoup(r.text,"html.parser")
        for a in soup.find_all("a",href=True):
            h=a.get("href","")
            if pf not in h: continue
            t=a.get_text(strip=True)
            if t and len(t)>10 and mp(t,"",cfg):
                fu=h if h.startswith("http") else url.rstrip("/").rsplit("/",1)[0]+h
                j.append({"id":mi(f"{src}_{t}"),"title":t,"company":"","location":"LATAM Remoto","url":fu,"date":datetime.now().strftime("%Y-%m-%d"),"source":src})
    except: pass
    return j

def search_weremoto():
    cfg,j=lc(),[]
    for c in ["atencion-al-cliente","tecnologia","administracion"]:
        j+=_scr(f"https://www.weremoto.com/{c}","/trabajo/","WeRemoto",cfg); time.sleep(2)
    return j

def search_remotejobslat(): return _scr("https://remotejobs.lat/","/job/","RemoteJobs.lat",lc())

def search_empleate():
    cfg,j=lc(),[]
    for t in ["soporte-tecnico","help-desk","sistemas"]:
        j+=_scr(f"https://www.empleate.com/venezuela/empleos-de-{t}","/empleo","Empleate VE",cfg); time.sleep(2)
    return j

def search_hireline(): return _scr("https://hireline.io/remoto","/empleos/","Hireline",lc())

def search_getonboard():
    cfg,j=lc(),[]
    for c in ["sistemas-redes","soporte"]:
        j+=_scr(f"https://www.getonbrd.com/empleos/{c}","/empleos/","GetOnBoard",cfg); time.sleep(2)
    return j

# === SITIOS WEB PERSONALIZADOS ===
def search_custom_sites():
    """Escanea sitios web agregados por el usuario."""
    cfg=lc()
    sites=cfg.get("custom_sites",[])
    j=[]
    for site in sites:
        url=site.get("url","")
        name=site.get("name","custom")
        if not url: continue
        L.info(f"  Custom: {name}...")
        r=sg(url)
        if not r: continue
        try:
            soup=BeautifulSoup(r.text,"html.parser")
            # Buscar en todos los links y textos de la pagina
            for a in soup.find_all("a",href=True):
                t=a.get_text(strip=True)
                h=a.get("href","")
                if t and len(t)>10 and mp(t,"",cfg):
                    fu=h if h.startswith("http") else url.rstrip("/") + ("" if h.startswith("/") else "/") + h
                    j.append({"id":mi(f"cust_{name}_{t}"),"title":t,"company":"","location":"(verificar)","url":fu,"date":datetime.now().strftime("%Y-%m-%d"),"source":f"🌐 {name}"})
            # Tambien buscar en parrafos, divs, spans con texto largo
            for tag in soup.find_all(["p","div","span","li","h2","h3","h4"]):
                txt=tag.get_text(strip=True)
                if txt and 20<len(txt)<300 and mp(txt,"",cfg):
                    parent_link=tag.find_parent("a")
                    link=parent_link["href"] if parent_link and parent_link.get("href") else url
                    if not link.startswith("http"): link=url.rstrip("/")+link
                    jid=mi(f"cust_{name}_{txt[:80]}")
                    if not any(x["id"]==jid for x in j):
                        j.append({"id":jid,"title":txt[:120],"company":"","location":"(verificar)","url":link,"date":datetime.now().strftime("%Y-%m-%d"),"source":f"🌐 {name}"})
        except Exception as e:
            L.warning(f"Custom site {name}: {e}")
        time.sleep(2)
    return j

# === MONITOREO CANALES TELEGRAM ===
async def channel_monitor():
    if not TEL or not API_ID: return
    cl=TelegramClient("/tmp/tg_s",int(API_ID),API_HASH)
    @cl.on(events.NewMessage)
    async def h(ev):
        cfg=lc()
        chs=[c.lower() for c in cfg.get("telegram_channels",[])]
        ch=await ev.get_chat()
        un=(getattr(ch,"username","") or "").lower()
        if un not in chs: return
        txt=ev.raw_text or ""
        if len(txt)<20: return
        jw=["vacante","empleo","trabajo","buscamos","remoto","soporte","help desk","IT","aplicar","postular","CV","USD","contratando","hiring","monitoreo","requisitos"]
        if not any(w in txt.lower() for w in jw): return
        if not mp(txt[:200],txt[200:],cfg): return
        seen=ls2()
        mid=mi(f"tg_{un}_{txt[:100]}")
        if mid in seen: return
        seen.add(mid); ss(seen)
        pv=txt[:300].replace("<","&lt;").replace(">","&gt;")
        if len(txt)>300: pv+="..."
        m=f"<b>📡 Oferta en Telegram</b>\n@{he(un)}\n\n{pv}"
        if hasattr(ev.message,'id'): m+=f'\n\n<a href="https://t.me/{un}/{ev.message.id}">Ver mensaje</a>'
        stg(m)
    await cl.start(phone=TG_PHONE)
    L.info("Channel monitor ON")
    for c in lc().get("telegram_channels",[]):
        try: await cl.get_entity(c); L.info(f"  @{c} OK")
        except: L.warning(f"  @{c} fail")
    await cl.run_until_disconnected()

# === BUSQUEDA PRINCIPAL ===
def run_search():
    now=datetime.now().strftime("%Y-%m-%d %H:%M")
    L.info(f"Search: {now}")
    seen,aj=ls2(),[]
    for n,fn in [("LinkedIn",search_linkedin),("Computrabajo",search_computrabajo),("RemoteOK",search_remoteok),("Remotive",search_remotive),("Jobicy",search_jobicy),("Arbeitnow",search_arbeitnow),("WeRemoto",search_weremoto),("RemoteJobs.lat",search_remotejobslat),("Empleate",search_empleate),("Hireline",search_hireline),("GetOnBoard",search_getonboard),("Sitios custom",search_custom_sites)]:
        L.info(f"  {n}...")
        try: x=fn(); L.info(f"    {len(x)}"); aj.extend(x)
        except Exception as e: L.error(f"    {e}")
    uq={j["id"]:j for j in aj}
    nw=[j for j in uq.values() if j["id"] not in seen]
    L.info(f"  Total:{len(uq)} New:{len(nw)}")
    st=0
    for j in nw:
        if stg(fj(j)): seen.add(j["id"]); st+=1; time.sleep(1.5)
    ss(seen)
    cfg=lc(); ns=len(cfg.get("custom_sites",[]))
    if st: stg(f"\n<b>Resumen:</b> {st} nuevas de {len(uq)}\n11 portales + {ns} sitios custom\nProxima en {INTERVAL} min")
    L.info(f"  Sent:{st}")

def sloop():
    time.sleep(15); run_search()
    while True:
        time.sleep(INTERVAL*60)
        try: run_search()
        except Exception as e: L.error(f"Err:{e}"); time.sleep(60)

if __name__=="__main__":
    L.info("JOB HUNTER BOT v4.0")
    if not TK or not CI: L.error("Set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID"); exit(1)
    stg("<b>🤖 Job Hunter Bot v4.0</b>\n\nEnvia /start para abrir el menu\n\n✨ Nuevo: Menu con botones\n🌐 Nuevo: Agrega sitios web personalizados\n\n11 portales + tus sitios + canales TG\nBusqueda cada "+str(INTERVAL)+" min")
    threading.Thread(target=sloop,daemon=True).start()
    if TEL and API_ID and API_HASH:
        def _tl():
            lp=asyncio.new_event_loop(); asyncio.set_event_loop(lp); lp.run_until_complete(channel_monitor())
        threading.Thread(target=_tl,daemon=True).start()
    if PTB:
        app=Application.builder().token(TK).build()
        app.add_handler(CommandHandler("start",cmd_start))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,text_handler))
        L.info("Bot ready")
        app.run_polling(allowed_updates=[Update.MESSAGE,Update.CALLBACK_QUERY])
    else:
        while True: time.sleep(3600)
