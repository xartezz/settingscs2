"""SETTINGSCS2 Desktop 0.4 — themed native UI, standard library only."""
import json
import queue
import threading
import os
import sqlite3
import subprocess
import sys
import uuid
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from core import validate_cfg, decode_link, install_cfg, launch_args, game_cfg_dir
from catalog import PLAYERS, preset
from window_style import WindowChrome, set_app_identity
from release_config import VERSION, REPOSITORY, SITE_URL
import updater

BASE = Path(os.getenv('LOCALAPPDATA', str(Path.home()))) / 'SettingsCS2'
BASE.mkdir(parents=True, exist_ok=True)
DB = sqlite3.connect(BASE / 'library.sqlite3')
DB.execute('CREATE TABLE IF NOT EXISTS configs (id TEXT PRIMARY KEY, name TEXT NOT NULL, content TEXT NOT NULL)')
DB.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
DB.execute('CREATE TABLE IF NOT EXISTS community (id TEXT PRIMARY KEY, name TEXT NOT NULL, content TEXT NOT NULL, metadata TEXT NOT NULL)')
DB.commit()
SITE = SITE_URL
BG, PANEL, FIELD, LINE = '#0b0c0e', '#141518', '#1c1d22', '#292b31'
WHITE, MUTED, RED, GREEN = '#f3f3f1', '#96989f', '#ef4148', '#88c4a2'
FONT = 'Segoe UI'
DISPLAY = 'Bahnschrift SemiCondensed'


def get_setting(key):
    row = DB.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
    return row[0] if row else ''


def put_setting(key, value):
    DB.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', (key, value)); DB.commit()


def add_config(name, content):
    validate_cfg(content)
    ident = uuid.uuid4().hex
    DB.execute('INSERT INTO configs VALUES (?,?,?)', (ident, name[:120], content)); DB.commit()
    return ident


def register_protocol():
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\Classes\settingscs2') as key:
        winreg.SetValueEx(key, '', 0, winreg.REG_SZ, 'URL:SettingsCS2')
        winreg.SetValueEx(key, 'URL Protocol', 0, winreg.REG_SZ, '')
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\Classes\settingscs2\shell\open\command') as key:
        command = f'"{sys.executable}" "%1"' if getattr(sys, "frozen", False) else f'"{sys.executable}" "{Path(__file__).resolve()}" "%1"'
        winreg.SetValueEx(key, '', 0, winreg.REG_SZ, command)


def label(parent, text, size=11, color=WHITE, bold=False, bg=None, **kwargs):
    return tk.Label(parent, text=text, font=(FONT, size, 'bold' if bold else 'normal'), bg=bg or parent.cget('bg'), fg=color, anchor='w', **kwargs)


def box(parent, bg=PANEL, **kwargs):
    return tk.Frame(parent, bg=bg, **kwargs)


def entry(parent, variable=None, **kwargs):
    return tk.Entry(parent, textvariable=variable, font=(FONT, 11), bg=FIELD, fg=WHITE,
                    insertbackground=RED, relief='flat', highlightthickness=1, highlightbackground=LINE,
                    highlightcolor=RED, selectbackground='#743036', **kwargs)


class Button(tk.Canvas):
    """Rounded native control with keyboard and hover states."""
    def __init__(self, parent, text, command, primary=False, width=160, height=42, quiet=False):
        super().__init__(parent, width=width, height=height, bg=parent.cget('bg'), highlightthickness=0, takefocus=1, cursor='hand2')
        self.text, self.command, self.primary, self.quiet = text, command, primary, quiet
        self.hover = False
        self.bind('<Configure>', lambda e:self.draw())
        self.bind('<Enter>', lambda e:self.state(True))
        self.bind('<Leave>', lambda e:self.state(False))
        self.bind('<FocusIn>', lambda e:self.state(True))
        self.bind('<FocusOut>', lambda e:self.state(False))
        self.bind('<Button-1>', lambda e:self.invoke())
        self.bind('<Return>', lambda e:self.invoke())
        self.bind('<space>', lambda e:self.invoke())
        self.draw()
    def state(self, value):
        self.hover=value; self.draw()
    def invoke(self):
        self.focus_set(); self.command()
    def draw(self):
        self.delete('all'); w=max(self.winfo_width(),int(self.cget('width'))); h=int(self.cget('height')); r=8
        fill=('#ff555c' if self.hover else RED) if self.primary else ('#2b2d34' if self.hover else (self.cget('bg') if self.quiet else FIELD))
        self.create_polygon(r,1,w-r,1,w-1,1,w-1,r,w-1,h-r,w-1,h-1,w-r,h-1,r,h-1,1,h-1,1,h-r,1,r,1,1,smooth=True,fill=fill,outline=RED if self.hover and not self.primary else fill)
        self.create_text(w/2,h/2,text=self.text,fill=WHITE,font=(FONT,10,'bold' if self.primary else 'normal'))


class App:
    def __init__(self, root):
        self.root=root; self.tab='pro'; self.rows=[]; self.nav={}; self.detail_active=False; self.back_action=None
        root.title('SETTINGSCS2 Desktop'); root.geometry('1280x840'); root.minsize(1080,720); root.configure(bg=BG)
        self.game=tk.StringVar(value=get_setting('game')); self.steam=tk.StringVar(value=get_setting('steam'))
        self.status=tk.StringVar(value='Bibliotecă locală  •  Gata de joc, în stilul tău.')
        self.chrome=WindowChrome(root)
        self.shell=box(root,bg=BG);self.shell.pack(fill='both',expand=True)
        self.build_shell(); self.navigate('pro'); self.root.after(2000,self.poll)
        self.root.bind('<Alt-Left>',lambda event:self.back())
        self.root.bind('<Escape>',lambda event:self.back())
        self.set_icon()
        self.update_repo=tk.StringVar(value=get_setting('update_repo') or REPOSITORY)
        self.update_auto=tk.BooleanVar(value=get_setting('update_auto')!='0')
        self.update_status=tk.StringVar(value='Versiune instalată: '+VERSION)
        self.update_events=queue.Queue();self.update_busy=False;self.available_update=None
        self.root.after(200,self.drain_updates)
        self.root.after(3000,lambda:self.check_update(False) if self.update_auto.get() and self.update_repo.get() else None)

    def set_icon(self):
        self.app_icon=tk.PhotoImage(width=32,height=32)
        self.app_icon.put('#101113',to=(0,0,32,32))
        for rectangle in [(14,4,18,12),(14,20,18,28),(4,14,12,18),(20,14,28,18)]:
            self.app_icon.put(RED,to=rectangle)
        self.root.iconphoto(True,self.app_icon)
    def back(self):
        if self.back_action:self.guard(self.back_action)
    def clear_page(self):
        for child in self.content.winfo_children():child.destroy()
        self.canvas.yview_moveto(0)
        self.page=box(self.content,bg=BG);self.page.pack(fill='both',expand=True,padx=30,pady=28)
    def detail_page(self,title,back):
        self.detail_active=True; self.back_action=back
        self.clear_page()
        self.crumb.configure(text='WORKSPACE   /   '+title.upper()[:55])
        head=box(self.page,bg=BG);head.pack(fill='x',pady=(0,22))
        self.btn(head,'←  Înapoi',self.back,width=115,quiet=True).pack(side='left')
        label(head,'ALT + ←',8,MUTED).pack(side='right')
        body=box(self.page,bg=BG);body.pack(fill='both',expand=True)
        return body
    def guard(self, fn):
        try: return fn()
        except Exception as exc: messagebox.showerror('SETTINGSCS2',str(exc),parent=self.root)
    def btn(self,parent,text,fn,**kwargs):
        return Button(parent,text,lambda:self.guard(fn),**kwargs)
    def build_shell(self):
        sidebar=box(self.shell,bg='#101113',width=220); sidebar.pack(side='left',fill='y'); sidebar.pack_propagate(False)
        logo=box(sidebar,bg='#101113'); logo.pack(fill='x',padx=24,pady=(30,0))
        label(logo,'⌖',30,RED,True).pack(side='left',padx=(0,7))
        word=box(logo,bg='#101113'); word.pack(side='left')
        label(word,'SETTINGS',15,bold=True).pack(anchor='w'); label(word,'CS2 / DESKTOP',10,RED,True).pack(anchor='w')
        label(sidebar,'WORKSPACE',8,'#62656c',True).pack(anchor='w',padx=26,pady=(40,13))
        for key,title in [('pro','⌖   Jucători pro'),('community','◈   Community'),('library','▦   Config-urile mele'),('settings','⚙   Setări')]:
            holder=box(sidebar,bg='#101113');holder.pack(fill='x',padx=14,pady=4)
            b=self.btn(holder,title,lambda k=key:self.navigate(k),width=192,height=46,quiet=True);b.pack();self.nav[key]=b
        bottom=box(sidebar,bg='#101113');bottom.pack(side='bottom',fill='x',padx=20,pady=24)
        self.btn(bottom,'Deschide site-ul  ↗',lambda:webbrowser.open(SITE),width=180,quiet=True).pack()
        tk.Frame(bottom,bg=LINE,height=1).pack(fill='x',pady=20)
        label(bottom,'●  COUNTER-STRIKE 2',9,GREEN,True).pack(anchor='w')
        label(bottom,'Desktop v'+VERSION+'  /  Local',9,MUTED).pack(anchor='w',pady=(6,0))
        right=box(self.shell,bg=BG);right.pack(side='left',fill='both',expand=True)
        top=box(right,bg=BG,height=76);top.pack(fill='x');top.pack_propagate(False)
        self.crumb=label(top,'',10,MUTED);self.crumb.pack(side='left',padx=32)
        self.btn(top,'↑  Importă config',self.import_file,primary=True,width=164).pack(side='right',padx=30,pady=16)
        tk.Frame(right,bg=LINE,height=1).pack(fill='x')
        bottom=box(right,bg='#101113');bottom.pack(side='bottom',fill='x')
        tk.Label(bottom,textvariable=self.status,bg='#101113',fg=MUTED,font=(FONT,9),anchor='w',wraplength=850,justify='left').pack(fill='x',padx=30,pady=11)
        area=box(right,bg=BG);area.pack(fill='both',expand=True)
        self.canvas=tk.Canvas(area,bg=BG,highlightthickness=0)
        scrollbar=tk.Scrollbar(area,orient='vertical',command=self.canvas.yview,bg=PANEL,troughcolor=BG,activebackground=RED,width=9)
        scrollbar.pack(side='right',fill='y');self.canvas.pack(side='left',fill='both',expand=True);self.canvas.configure(yscrollcommand=scrollbar.set)
        self.content=box(self.canvas,bg=BG);self.window=self.canvas.create_window(0,0,window=self.content,anchor='nw')
        self.canvas.bind('<Configure>',lambda e:self.canvas.itemconfigure(self.window,width=e.width))
        self.content.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.root.bind_all('<MouseWheel>',self.wheel)
    def wheel(self,e):
        if e.widget.winfo_toplevel()==self.root and not isinstance(e.widget,tk.Text):
            self.canvas.yview_scroll(-int(e.delta/120),'units')
    def navigate(self,tab):
        self.tab=tab;self.detail_active=False;self.back_action=None
        for key,b in self.nav.items():b.primary=key==tab;b.draw()
        self.crumb.configure(text='WORKSPACE   /   '+{'pro':'JUCĂTORI PRO','community':'COMMUNITY','library':'CONFIG-URILE MELE','settings':'SETĂRI'}[tab])
        self.clear_page()
        self.rows=DB.execute('SELECT id,name,content FROM configs ORDER BY rowid DESC').fetchall()
        getattr(self,'page_'+tab)()
    def title(self,kicker,title,subtitle):
        label(self.page,kicker,9,RED,True).pack(anchor='w')
        label(self.page,title,28,bold=True).pack(anchor='w',pady=(10,8))
        label(self.page,subtitle,10,MUTED,wraplength=780,justify='left').pack(anchor='w',pady=(0,25))
    def panel(self,parent=None):
        return box(parent or self.page,highlightthickness=1,highlightbackground=LINE)
    def note(self,parent,text):
        f=box(parent,bg='#241b1d');f.pack(fill='x',pady=(15,20))
        label(f,text,10,'#d2a9ab',wraplength=760,justify='left').pack(anchor='w',padx=16,pady=14)
    def page_pro(self):
        hero=self.panel();hero.configure(bg='#191316');hero.pack(fill='x',pady=(0,27))
        copy=box(hero,bg='#191316');copy.pack(side='left',padx=25,pady=24)
        label(copy,'●  BUILT FOR COUNTER-STRIKE 2',9,RED,True).pack(anchor='w')
        label(copy,'SETĂRILE LOR.',29,bold=True).pack(anchor='w',pady=(13,0))
        label(copy,'AVANTAJUL TĂU.',29,RED,True).pack(anchor='w')
        label(copy,'Alege un preset. Găsește-ți ritmul. Intră pe server.',10,MUTED).pack(anchor='w',pady=(13,18))
        self.btn(copy,'Explorează biblioteca  →',lambda:self.navigate('library'),primary=True,width=215).pack(anchor='w')
        art=tk.Canvas(hero,width=235,height=215,bg='#191316',highlightthickness=0);art.pack(side='right',padx=22)
        for r in [82,61,34]:art.create_oval(118-r,103-r,118+r,103+r,outline='#54282e',dash=(3,5) if r==61 else ())
        art.create_line(14,103,220,103,fill='#54282e');art.create_line(118,8,118,198,fill='#54282e')
        for x1,y1,x2,y2 in [(118,67,118,92),(118,114,118,139),(82,103,107,103),(129,103,154,103)]:art.create_line(x1,y1,x2,y2,fill=RED,width=4)
        art.create_text(118,207,text='PRECISION IS PERSONAL.',fill='#8f6269',font=(FONT,7,'bold'))
        row=box(self.page,bg=BG);row.pack(fill='x',pady=(0,16));label(row,'Jucători pro',21,bold=True).pack(side='left');label(row,'03 / PRESETURI',9,MUTED).pack(side='right')
        self.query=tk.StringVar(); search=entry(self.page,self.query);search.pack(fill='x',ipady=11,pady=(0,18));label(self.page,'Caută după nume, echipă sau rol',9,MUTED).pack(anchor='w',pady=(0,12))
        self.cards=box(self.page,bg=BG);self.cards.pack(fill='x');self.query.trace_add('write',lambda *_:self.render_players());self.render_players()
        label(self.page,'Snapshot: 12.11.2026 • ProSettings.net • Preseturi parțiale, nu fișiere originale.',9,MUTED).pack(anchor='w',pady=(12,0))
        banner=self.panel();banner.pack(fill='x',pady=(24,0))
        label(banner,'DE PE SITE, DIRECT ÎN JOC.',12,bold=True).pack(anchor='w',padx=20,pady=(18,7))
        label(banner,'Add to app  →  Biblioteca ta  →  Aplică și pornește CS2',10,MUTED).pack(anchor='w',padx=20,pady=(0,18))
    def render_players(self):
        for c in self.cards.winfo_children():c.destroy()
        for column in range(3):self.cards.columnconfigure(column,weight=0)
        filtered=[p for p in PLAYERS if self.query.get().lower() in (p['name']+' '+p['team']+' '+p['role']).lower()]
        for i,p in enumerate(filtered):
            self.cards.columnconfigure(i,weight=1,uniform='player')
            card=self.panel(self.cards);card.grid(row=0,column=i,sticky='nsew',padx=(0,12 if i<2 else 0))
            top=box(card,bg='#1b2320' if i<2 else '#292419');top.pack(fill='x')
            label(top,p['role'].upper(),8,p['accent'],True).pack(anchor='w',padx=18,pady=(17,8))
            label(top,p['name'],31,bold=True).pack(anchor='w',padx=18,pady=(4,5))
            label(top,p['team'],10,p['accent']).pack(anchor='w',padx=18,pady=(0,20))
            stats=box(card);stats.pack(fill='x',padx=18,pady=18)
            for j,(k,v) in enumerate([('DPI',p['dpi']),('SENS',p['sens']),('eDPI',round(p['dpi']*p['sens']))]):
                cell=box(stats);cell.pack(side='left',expand=True,fill='x');label(cell,k,8,MUTED).pack(anchor='w');label(cell,str(v),14,bold=True).pack(anchor='w',pady=(5,0))
            self.btn(card,'Vezi setările  ↗',lambda p=p:self.player_dialog(p),width=205).pack(fill='x',padx=16,pady=(0,16))
        if not filtered:label(self.cards,'Niciun jucător găsit. Încearcă altă căutare.',12,MUTED).pack(pady=35)
    def player_dialog(self,p):
        b=self.detail_page(p['name'],lambda:self.navigate('pro'))
        label(b,p['team'].upper()+' / '+p['role'].upper(),9,RED,True).pack(anchor='w')
        label(b,p['name'],33,bold=True).pack(anchor='w',pady=(8,3));label(b,p['real'],11,MUTED).pack(anchor='w')
        grid=box(b,bg=BG);grid.pack(fill='x',pady=20)
        for i,(k,v) in enumerate([('DPI',p['dpi']),('Sensibilitate',p['sens']),('Rezoluție',p['res']),('Polling rate',str(p['hz'])+' Hz')]):
            cell=self.panel(grid);cell.grid(row=0,column=i,sticky='ew',padx=(0,8));grid.columnconfigure(i,weight=1)
            label(cell,k,9,MUTED).pack(anchor='w',padx=12,pady=(12,5));label(cell,str(v),13,bold=True).pack(anchor='w',padx=12,pady=(0,12))
        label(b,'MOUSE  /  '+p['mouse'],10,MUTED).pack(anchor='w',pady=(0,15))
        label(b,'PREVIZUALIZARE CONFIG',9,MUTED,True).pack(anchor='w',pady=(0,8));self.code(b,preset(p)).pack(fill='both',expand=True)
        label(b,'Preset parțial • Date din 12.11.2026 • DPI și video se setează manual.',9,MUTED).pack(anchor='w',pady=12)
        actions=box(b,bg=BG);actions.pack(fill='x')
        self.btn(actions,'＋  Adaugă în bibliotecă',lambda:self.save_player(p),primary=True,width=220).pack(side='left')
        self.btn(actions,'Sursa setărilor  ↗',lambda:webbrowser.open('https://prosettings.net/players/'+('m0nesy' if p['id']=='monesy' else p['id'])+'/'),width=175).pack(side='right')
    def save_player(self,p):
        content=preset(p)
        row=DB.execute('SELECT id FROM configs WHERE name=? AND content=?',(p['name'],content)).fetchone()
        if not row:add_config(p['name'],content)
        self.navigate('library');self.status.set(p['name']+' este în biblioteca ta.')
    def code(self,parent,text,editable=False,height=9):
        t=tk.Text(parent,bg='#101114',fg='#d0d1d6',insertbackground=RED,relief='flat',padx=16,pady=15,wrap='word',font=('Consolas',10),height=height,undo=True,highlightthickness=1,highlightbackground=LINE)
        t.insert('1.0',text);t.tag_configure('comment',foreground='#777d88')
        for i,line in enumerate(text.splitlines(),1):
            if line.lstrip().startswith('//'):t.tag_add('comment',f'{i}.0',f'{i}.end')
        if not editable:t.configure(state='disabled')
        return t
    def page_library(self):
        self.title('YOUR CONFIG COLLECTION','Config-urile mele.','Preseturile pro și config-urile importate, pregătite pentru următorul meci.')
        metrics=box(self.page,bg=BG);metrics.pack(fill='x',pady=(0,24))
        for title,value in [('CONFIG-URI SALVATE',str(len(self.rows)).zfill(2)),('STOCARE','Pe acest PC'),('BACKUP','La suprascriere')]:
            m=self.panel(metrics);m.pack(side='left',fill='x',expand=True,padx=(0,12));label(m,title,8,MUTED,True).pack(anchor='w',padx=18,pady=(15,7));label(m,value,18,bold=True).pack(anchor='w',padx=18,pady=(0,15))
        self.library_query=tk.StringVar();entry(self.page,self.library_query).pack(fill='x',ipady=11,pady=(0,7));label(self.page,'Caută în biblioteca ta',9,MUTED).pack(anchor='w',pady=(0,18))
        self.library_rows=box(self.page,bg=BG);self.library_rows.pack(fill='x');self.library_query.trace_add('write',lambda *_:self.render_library());self.render_library()
    def render_library(self):
        for child in self.library_rows.winfo_children():child.destroy()
        rows=[r for r in self.rows if self.library_query.get().lower() in r[1].lower()]
        if not rows:
            empty=self.panel(self.library_rows);empty.pack(fill='x');label(empty,'Biblioteca ta începe aici.' if not self.rows else 'Niciun config găsit.',19,bold=True).pack(padx=30,pady=(40,12));label(empty,'Importă un .cfg sau alege un preset din Jucători pro.',11,MUTED).pack(pady=(0,20));self.btn(empty,'↑  Importă config',self.import_file,primary=True,width=180).pack(pady=(0,40));return
        for row in rows:
            c=self.panel(self.library_rows);c.pack(fill='x',pady=(0,10))
            label(c,'{ }',24,RED,True).pack(side='left',padx=20,pady=20)
            info=box(c);info.pack(side='left',fill='x',expand=True)
            label(info,row[1][:42],13,bold=True).pack(anchor='w');label(info,f'.cfg   /   {len(row[2].encode("utf-8")):,} bytes   /   Salvat local',9,MUTED).pack(anchor='w',pady=(6,0))
            self.btn(c,'Deschide  ↗',lambda r=row:self.config_dialog(r),width=130).pack(side='right',padx=15)
    def config_dialog(self,row):
        b=self.detail_page(row[1],lambda:self.navigate('library'))
        label(b,'CONFIG WORKSPACE',9,RED,True).pack(anchor='w');label(b,row[1][:50],24,bold=True).pack(anchor='w',pady=(10,5))
        label(b,'Verifică comenzile înainte de aplicare. Închide CS2 înainte de lansare.',10,MUTED).pack(anchor='w',pady=(0,20))
        preview=self.code(b,row[2]);preview.pack(fill='both',expand=True)
        actions=box(b,bg=BG);actions.pack(fill='x',pady=15)
        self.btn(actions,'Exportă .cfg',lambda:self.export(row),width=120).pack(side='left',padx=(0,8))
        self.btn(actions,'Editează',lambda:self.edit_dialog(row),width=100).pack(side='left',padx=(0,8))
        self.btn(actions,'Șterge',lambda:self.delete(row),width=85,quiet=True).pack(side='left')
        self.note(b,'Fișier dedicat pentru fiecare config. La suprascriere se creează un backup .bak; autoexec.cfg rămâne neatins.')
        launch=box(b,bg=BG);launch.pack(fill='x')
        self.btn(launch,'Aplică în fișiere',lambda:self.apply(row,False),width=180).pack(side='left')
        self.btn(launch,'▶  Aplică și pornește CS2',lambda:self.apply(row,True),primary=True,width=245).pack(side='right')
    def edit_dialog(self,row):
        b=self.detail_page('Editează config',lambda:self.config_dialog(row))
        label(b,'NUMELE CONFIG-ULUI',9,MUTED,True).pack(anchor='w',pady=(0,8))
        name=tk.StringVar(value=row[1]);entry(b,name).pack(fill='x',ipady=10,pady=(0,15))
        text=self.code(b,row[2],True);text.pack(fill='both',expand=True)
        def save():
            value=name.get().strip()
            if not value or len(value)>120:raise ValueError('Numele trebuie să aibă între 1 și 120 caractere.')
            content=validate_cfg(text.get('1.0','end-1c'))
            DB.execute('UPDATE configs SET name=?,content=? WHERE id=?',(value,content,row[0]));DB.commit()
            self.config_dialog((row[0],value,content));self.status.set('Modificări salvate în bibliotecă. Aplică din nou pentru a actualiza fișierul din joc.')
        self.btn(b,'Salvează modificările',save,primary=True,width=210).pack(anchor='e',pady=(20,0))
    def page_community(self):
        self.title('MADE BY PLAYERS','Setup-ul tău. Comunitatea ta.','Adaugă propriul config, perifericele și detaliile care fac diferența.')
        self.note(self.page,'COMMUNITY LOCAL  /  Config-urile de aici rămân pe acest PC. Conturile și publicarea online nu sunt încă disponibile; browserul are o bibliotecă separată.')
        self.btn(self.page,'＋  Adaugă propriul setup',self.community_form,primary=True,width=235).pack(anchor='w',pady=(0,23))
        rows=DB.execute('SELECT id,name,content,metadata FROM community ORDER BY rowid DESC').fetchall()
        if not rows:
            card=self.panel();card.pack(fill='x');label(card,'Primul setup poate fi al tău.',20,bold=True).pack(anchor='w',padx=24,pady=(30,12));label(card,'Un config, un nickname și perifericele cu care joci.',11,MUTED).pack(anchor='w',padx=24,pady=(0,30))
        for row in rows:
            meta=json.loads(row[3]);c=self.panel();c.pack(fill='x',pady=(0,14))
            label(c,meta['author'].upper()+' / LOCAL',9,RED,True).pack(anchor='w',padx=20,pady=(20,8));label(c,row[1],19,bold=True).pack(anchor='w',padx=20)
            label(c,meta.get('description',''),10,MUTED,wraplength=750,justify='left').pack(anchor='w',padx=20,pady=10)
            label(c,'MOUSE  '+(meta.get('mouse') or '—')+'     /     TASTATURĂ  '+(meta.get('keyboard') or '—'),10,MUTED,wraplength=750).pack(anchor='w',padx=20)
            buttons=box(c);buttons.pack(fill='x',padx=20,pady=18)
            self.btn(buttons,'Adaugă în bibliotecă',lambda r=row:self.copy_community(r),width=195).pack(side='left')
            self.btn(buttons,'Șterge',lambda r=row:self.delete_community(r),width=85,quiet=True).pack(side='right')
    def copy_community(self,row):
        if not DB.execute('SELECT id FROM configs WHERE name=? AND content=?',(row[1],row[2])).fetchone():add_config(row[1],row[2])
        self.navigate('library');self.status.set('Config Community adăugat în bibliotecă.')
    def delete_community(self,row):
        if messagebox.askyesno('Șterge setup-ul','Ștergi acest setup din Community local?',parent=self.root):
            DB.execute('DELETE FROM community WHERE id=?',(row[0],));DB.commit();self.navigate('community')
    def community_form(self):
        b=self.detail_page('Adaugă setup',lambda:self.navigate('community'));fields={}
        label(b,'CREEAZĂ UN SETUP LOCAL',18,bold=True).pack(anchor='w',pady=(0,15))
        for key,title in [('name','Numele config-ului'),('author','Nickname'),('mouse','Mouse'),('keyboard','Tastatură'),('description','Descriere scurtă')]:
            label(b,title,9,MUTED).pack(anchor='w',pady=(8,4));fields[key]=tk.StringVar(value=get_setting('nickname') if key=='author' else '');entry(b,fields[key]).pack(fill='x',ipady=8)
        file=tk.StringVar();label(b,'FIȘIER .CFG / MAXIMUM 256 KB',9,MUTED).pack(anchor='w',pady=(20,8))
        def choose():
            path=filedialog.askopenfilename(parent=self.root,filetypes=[('Config CS2','*.cfg')])
            if path:file.set(path)
        self.btn(b,'Alege fișierul .cfg',choose,width=180).pack(anchor='w');tk.Label(b,textvariable=file,bg=BG,fg=MUTED,wraplength=650,font=(FONT,9)).pack(anchor='w',pady=5)
        def save():
            data={k:v.get().strip() for k,v in fields.items()}
            if not data['name'] or not data['author']:raise ValueError('Completează numele config-ului și nickname-ul.')
            if any(len(v)>240 for v in data.values()):raise ValueError('Folosește maximum 240 de caractere per câmp.')
            content=self.read_file(file.get());name=data.pop('name')[:120]
            DB.execute('INSERT INTO community VALUES (?,?,?,?)',(uuid.uuid4().hex,name,content,json.dumps(data)));DB.commit();put_setting('nickname',data['author'])
            self.navigate('community');self.status.set('Setup salvat pe acest PC.')
        self.btn(b,'Salvează setup-ul',save,primary=True,width=190).pack(anchor='e',pady=(15,0))
    def page_settings(self):
        self.title('MAKE IT YOURS','Pregătește terenul.','Configurează o singură dată folderele. Apoi alegi config-ul și intri în joc.')
        for title,subtitle,var,picker in [('Instalare Counter-Strike 2','Folderul care conține game / bin / win64 / cs2.exe',self.game,self.pick_game),('Steam','Fișierul Steam.exe folosit pentru lansare',self.steam,self.pick_steam)]:
            c=self.panel();c.pack(fill='x',pady=(0,18));label(c,title,16,bold=True).pack(anchor='w',padx=22,pady=(22,7));label(c,subtitle,10,MUTED).pack(anchor='w',padx=22)
            r=box(c);r.pack(fill='x',padx=22,pady=18);entry(r,var).pack(side='left',fill='x',expand=True,ipady=11,padx=(0,12));self.btn(r,'Alege folderul' if picker==self.pick_game else 'Alege Steam.exe',picker,width=155).pack(side='right')
        self.btn(self.page,'Verifică și salvează',self.save_paths,primary=True,width=210).pack(anchor='w',pady=(0,23))
        self.note(self.page,'BACKUP AUTOMAT  /  Înainte de suprascrierea unui fișier settingscs2_*.cfg, versiunea anterioară este păstrată lângă el ca .bak. Backup-ul nu acoperă toate setările schimbate în joc.')
        label(self.page,'LEGĂTURĂ CU SITE-UL',10,MUTED,True).pack(anchor='w',pady=(5,12));self.btn(self.page,'Reactivează Add to app',register_protocol,width=220).pack(anchor='w')
        label(self.page,'Dacă ai mutat aplicația în alt folder, reactivează legătura.',10,MUTED).pack(anchor='w',pady=10)
        c=self.panel();c.pack(fill='x',pady=(22,0))
        label(c,'Actualizări / v'+VERSION,17,bold=True).pack(anchor='w',padx=22,pady=(20,8))
        label(c,'Repository public de încredere: utilizator/settingscs2',10,MUTED).pack(anchor='w',padx=22)
        entry(c,self.update_repo).pack(fill='x',padx=22,pady=12,ipady=10)
        tk.Checkbutton(c,text='Verifică automat la pornire',variable=self.update_auto,bg=PANEL,fg=WHITE,selectcolor=FIELD,activebackground=PANEL,activeforeground=WHITE,font=(FONT,10)).pack(anchor='w',padx=18)
        row=box(c);row.pack(fill='x',padx=22,pady=12)
        self.btn(row,'Salvează',self.save_update_settings,width=100).pack(side='left',padx=(0,10))
        self.btn(row,'Verifică actualizări',self.check_update,width=180).pack(side='left',padx=(0,10))
        self.btn(row,'Instalează și repornește',self.install_update,primary=True,width=220).pack(side='left')
        tk.Label(c,textvariable=self.update_status,bg=PANEL,fg=MUTED,font=(FONT,10),wraplength=750,justify='left').pack(anchor='w',padx=22,pady=(0,20))

    def save_update_settings(self):
        repo=updater.repository(self.update_repo.get())
        put_setting('update_repo',repo);put_setting('update_auto','1' if self.update_auto.get() else '0')
        self.available_update=None;self.update_status.set('Repository salvat. Verifică actualizările.')
    def update_job(self,kind,fn):
        if self.update_busy:return
        self.update_busy=True
        def run():
            try:self.update_events.put((kind,fn(),None))
            except Exception as error:self.update_events.put((kind,None,str(error)))
        threading.Thread(target=run,daemon=True).start()
    def check_update(self,manual=True):
        if self.update_busy:return
        try:repo=updater.repository(self.update_repo.get())
        except ValueError as error:
            if manual:self.update_status.set(str(error))
            return
        self.update_status.set('Se verifică GitHub…')
        self.update_job('check',lambda:updater.latest(repo,VERSION))
    def install_update(self):
        if self.update_busy:return
        if not self.available_update:
            self.update_status.set('Apasă mai întâi Verifică actualizări.');return
        release=dict(self.available_update)
        if not messagebox.askyesno('Instalează actualizarea?',
                'Versiunea '+release['version']+' din '+release['repo']+' va fi descărcată și instalată. Aplicația se închide și repornește. Salvează întâi modificările din editor. Biblioteca și config-urile se păstrează.',parent=self.root):return
        self.update_status.set('Se descarcă și se verifică installerul…')
        self.status.set('Actualizare în curs. Așteaptă verificarea download-ului.')
        self.update_job('download',lambda:updater.download(release,BASE/'updates'))
    def drain_updates(self):
        try:
            while True:
                kind,result,error=self.update_events.get_nowait();self.update_busy=False
                if error:
                    self.update_status.set('Actualizare indisponibilă: '+error)
                    self.status.set('Actualizarea nu s-a efectuat. Detalii în Setări.');continue
                if kind=='check':
                    self.available_update=result
                    text='Ești la zi: v'+VERSION if result is None else 'Disponibil: v'+result['version']+' — instalează din Setări.'
                    self.update_status.set(text);self.status.set(text)
                elif kind=='download':
                    try:
                        if sys.platform!='win32':raise ValueError('Installerul necesită Windows.')
                        log=BASE/'update-install.log'
                        subprocess.Popen([str(result),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/LOG='+str(log)],shell=False)
                        self.root.destroy();return
                    except Exception as exc:
                        self.update_status.set('Installerul nu a pornit: '+str(exc))
        except queue.Empty:pass
        self.root.after(200,self.drain_updates)
    def save_paths(self):
        game_cfg_dir(self.game.get());launch_args(self.steam.get(),'settingscs2_'+'0'*32+'.cfg')
        put_setting('game',self.game.get());put_setting('steam',self.steam.get());self.status.set('✓  CS2 și Steam verificate. Setările au fost salvate.')
    def pick_game(self):
        p=filedialog.askdirectory(title='Alege folderul Counter-Strike Global Offensive',parent=self.root)
        if p:self.game.set(p)
    def pick_steam(self):
        p=filedialog.askopenfilename(title='Alege Steam.exe',filetypes=[('Steam','Steam.exe')],parent=self.root)
        if p:self.steam.set(p)
    def read_file(self,path):
        file=Path(path)
        if not file.is_file() or file.suffix.lower()!='.cfg' or file.stat().st_size>262144:raise ValueError('Alege un fișier .cfg de maximum 256 KB.')
        return validate_cfg(file.read_text(encoding='utf-8-sig'))
    def import_file(self):
        path=filedialog.askopenfilename(filetypes=[('Config CS2','*.cfg')],parent=self.root)
        if path:add_config(Path(path).stem,self.read_file(path));self.navigate('library');self.status.set('✓  Config importat. Deschide-l pentru previzualizare și aplicare.')
    def export(self,row):
        path=filedialog.asksaveasfilename(defaultextension='.cfg',initialfile='settingscs2_export.cfg',filetypes=[('Config CS2','*.cfg')],parent=self.root)
        if path:Path(path).write_text(row[2],encoding='utf-8');self.status.set('✓  Config exportat.')
    def delete(self,row):
        if messagebox.askyesno('Șterge din bibliotecă','Ștergi '+row[1]+'? Fișierul din joc rămâne neatins.',parent=self.root):
            DB.execute('DELETE FROM configs WHERE id=?',(row[0],));DB.commit();self.navigate('library')
    def apply(self,row,launch=False):
        current=DB.execute('SELECT id,name,content FROM configs WHERE id=?',(row[0],)).fetchone()
        if not current:raise ValueError('Config-ul nu mai există în bibliotecă.')
        args=launch_args(self.steam.get(),'settingscs2_'+row[0]+'.cfg') if launch else None
        game_cfg_dir(self.game.get())
        if not messagebox.askyesno('Aplică '+current[1]+'?','Ai închis CS2 și ai verificat comenzile?\nSe scrie fișierul dedicat acestui preset. Config-ul poate modifica setări și bind-uri.',parent=self.root):return
        target,backup=install_cfg(self.game.get(),current[0],current[2]);put_setting('game',self.game.get())
        self.status.set('✓  Config instalat.'+(' Backup creat.' if backup else '')+'  exec '+target.name)
        if args:
            subprocess.Popen(args,shell=False);put_setting('steam',self.steam.get());self.status.set('✓  Pornire cerută prin Steam cu +exec '+target.name+'. Verifică aplicarea în joc.')
    def poll(self):
        rows=DB.execute('SELECT id,name,content FROM configs ORDER BY rowid DESC').fetchall()
        if rows!=self.rows:
            self.rows=rows
            if self.tab=='library' and not self.detail_active:self.navigate('library')
            self.status.set('Biblioteca a fost actualizată. Config nou sau modificat disponibil.')
        self.root.after(2000,self.poll)


def main():
    set_app_identity()
    root=tk.Tk()
    if sys.platform!='win32':
        root.withdraw();messagebox.showerror('Windows necesar','Această versiune este pentru Windows.');root.destroy();return
    try:register_protocol()
    except OSError as exc:messagebox.showwarning('Add to app indisponibil',str(exc)+'\nImportul manual rămâne disponibil.')
    app=App(root)
    if len(sys.argv)>1:
        def handle():
            name,content=decode_link(sys.argv[1]);add_config(name,content);app.navigate('library');app.status.set('✓  Config primit de pe site. Verifică-l înainte de aplicare.')
        app.guard(handle)
    root.mainloop()

if __name__=='__main__':main()

