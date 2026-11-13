"""Rich inline profiles; all displayed settings are from the dated catalog snapshot."""
import tkinter as tk
import webbrowser
from catalog import preset

BG, PANEL, MUTED, RED = '#0b0c0e', '#141518', '#96989f', '#ef4148'

def icon(parent,kind):
    c=tk.Canvas(parent,width=30,height=30,bg=parent.cget('bg'),highlightthickness=0)
    opts=dict(fill=RED,width=2)
    if kind=='mouse':
        c.create_oval(8,3,23,27,outline=RED,width=2);c.create_line(15,4,15,12,**opts)
    elif kind=='crosshair':
        c.create_oval(6,6,24,24,outline=RED,width=2)
        for line in [(15,1,15,10),(15,20,15,29),(1,15,10,15),(20,15,29,15)]:c.create_line(*line,**opts)
    elif kind=='video':
        c.create_rectangle(3,5,27,22,outline=RED,width=2);c.create_line(15,22,15,27,**opts);c.create_line(9,27,21,27,**opts)
    elif kind=='gear':
        c.create_rectangle(2,7,28,24,outline=RED,width=2)
        for y in (12,17):
            for x in (7,12,17,22):c.create_rectangle(x,y,x+2,y+1,fill=RED,outline='')
        c.create_line(10,21,21,21,**opts)
    elif kind=='viewmodel':
        c.create_polygon(15,2,27,9,27,23,15,29,3,23,3,9,outline=RED,fill='',width=2)
        for line in [(3,9,15,16,27,9),(15,16,15,29),(15,2,15,16)]:c.create_line(*line,**opts)
    else:
        c.create_line(11,7,4,15,11,23,**opts);c.create_line(21,7,28,15,21,23,**opts);c.create_line(18,5,14,25,**opts)
    return c

def render_profile(app,p,label,box):
    body=app.detail_page(p['name'],lambda:app.navigate('pro'))
    hero=app.panel(body);hero.configure(bg='#1c1418');hero.pack(fill='x',pady=(0,18))
    avatar=tk.Canvas(hero,width=100,height=110,bg='#1c1418',highlightthickness=0)
    avatar.pack(side='left',padx=22,pady=22)
    avatar.create_oval(3,8,97,102,fill='#302027',outline='#68313c',width=2)
    avatar.create_text(50,55,text=p['name'][:2].upper(),fill='#f3f3f1',font=('Segoe UI',27,'bold'))
    info=box(hero,bg='#1c1418');info.pack(side='left',fill='x',expand=True,pady=24)
    label(info,'PRO PLAYER  /  COUNTER-STRIKE 2',9,RED,True).pack(anchor='w')
    label(info,p['name'],36,bold=True).pack(anchor='w',pady=(5,2))
    label(info,p['real']+'  ·  '+p['country'],11,MUTED).pack(anchor='w')
    label(info,p['team']+'   /   '+p['role'],10,p['accent'],True).pack(anchor='w',pady=(8,0))
    actions=box(body,bg=BG);actions.pack(fill='x',pady=(0,14))
    app.btn(actions,'＋  Add preset to library',lambda:app.save_player(p),primary=True,width=225).pack(side='left',padx=(0,10))
    app.btn(actions,'Copy preset',lambda:app.copy_text(preset(p)),width=135).pack(side='left')
    app.btn(actions,'Source  ↗',lambda:webbrowser.open(p['source']),width=115,quiet=True).pack(side='right')
    label(body,'SNAPSHOT  /  NOV 12, 2026    •    Partial preset; DPI and video require manual setup.',9,MUTED,wraplength=780).pack(anchor='w',pady=(0,22))
    nav=box(body,bg=BG);nav.pack(fill='x',pady=(0,18))
    sections={}
    def section(key,title,caption):
        panel=app.panel(body);panel.pack(fill='x',pady=(0,18));sections[key]=panel
        heading=box(panel);heading.pack(fill='x',padx=20,pady=(18,8))
        icon(heading,key).pack(side='left',padx=(0,10));label(heading,title,18,bold=True).pack(side='left')
        label(panel,caption,10,MUTED,wraplength=740,justify='left').pack(anchor='w',padx=22,pady=(0,16))
        return panel
    def stats(parent,items):
        grid=box(parent);grid.pack(fill='x',padx=22,pady=(0,20))
        for i,(key,value) in enumerate(items):
            grid.columnconfigure(i%4,weight=1,uniform='stats')
            cell=box(grid,bg='#1a1c21');cell.grid(row=i//4,column=i%4,sticky='nsew',padx=3,pady=3)
            label(cell,key,9,MUTED,wraplength=150).pack(anchor='w',padx=12,pady=(12,5))
            label(cell,str(value),12,bold=True,wraplength=150).pack(anchor='w',padx=12,pady=(0,12))
    mouse=section('mouse','Mouse settings',p['mouse'])
    stats(mouse,[('DPI',p['dpi']),('Sensitivity',p['sens']),('eDPI',round(p['dpi']*p['sens'])),('Zoom sensitivity',1),('Polling rate',str(p['hz'])+' Hz'),('Windows sensitivity',p['windows'])])
    cross=section('crosshair','Crosshair','Interactive illustration of the recorded values. Preview zoom does not change your config.')
    preview=tk.Canvas(cross,height=150,bg='#17201e',highlightthickness=0);preview.pack(fill='x',padx=22,pady=(0,10))
    zoom=tk.DoubleVar(value=4);light=tk.BooleanVar(value=False)
    def redraw(*_):
        preview.delete('all');w=max(200,preview.winfo_width());h=150;scale=zoom.get();cx=w/2;cy=h/2
        preview.configure(bg='#b2b7ae' if light.get() else '#17201e')
        gridcolor='#9da297' if light.get() else '#22332b'
        for x in range(0,w,30):preview.create_line(x,0,x,h,fill=gridcolor)
        for y in range(0,h,30):preview.create_line(0,y,w,y,fill=gridcolor)
        gap=p['crosshair']['gap']*scale;length=p['crosshair']['length']*scale;thick=max(1,p['crosshair']['thickness']*scale)
        for x1,y1,x2,y2 in [(cx-gap-length,cy,cx-gap,cy),(cx+gap,cy,cx+gap+length,cy),(cx,cy-gap-length,cx,cy-gap),(cx,cy+gap,cx,cy+gap+length)]:
            if p['crosshair']['outline']:preview.create_line(x1,y1,x2,y2,fill='#000000',width=thick+2)
            preview.create_line(x1,y1,x2,y2,fill=p['crosshair']['color'],width=thick)
        preview.create_text(14,16,text='CROSSHAIR LAB / ILLUSTRATIVE',fill='#445044' if light.get() else '#819487',anchor='w',font=('Segoe UI',8,'bold'))
    preview.bind('<Configure>',redraw)
    controls=box(cross);controls.pack(fill='x',padx=22,pady=(0,16))
    def toggle():light.set(not light.get());redraw()
    app.btn(controls,'Switch background',toggle,width=180).pack(side='left')
    label(controls,'Preview zoom',9,MUTED).pack(side='left',padx=(18,8))
    tk.Scale(controls,from_=1,to=8,resolution=1,orient='horizontal',variable=zoom,command=redraw,bg=PANEL,fg='#f3f3f1',troughcolor='#292b31',highlightthickness=0,activebackground=RED,length=180).pack(side='left')
    c=p['crosshair'];stats(cross,[('Style','Static cross'),('Follow recoil','No'),('Center dot','No'),('Length (px)',c['length']),('Thickness (px)',c['thickness']),('Gap (px)',c['gap']),('Outline','Yes' if c['outline'] else 'No'),('Color',c['color'].upper()),('Opacity',255)])
    view=section('viewmodel','Viewmodel','Position and field of view included in the partial preset.')
    stats(view,[('Field of view',68),('Offset X',2.5),('Offset Y',0),('Offset Z',-1.5)])
    video=section('video','Video settings','Reference values — set these manually in CS2.')
    stats(video,[('Resolution',p['res']),('Aspect ratio','4:3'),('Scaling','Stretched'),('Display mode','Fullscreen'),('Brightness',p['brightness']),('MSAA',p['msaa']),('V-Sync','Disabled'),('NVIDIA Reflex',p['reflex'])])
    gear=section('gear','Peripherals','Only documented equipment is shown; missing gear is not guessed.')
    stats(gear,[('Mouse',p['mouse']),('Keyboard','Not documented'),('Headset','Not documented'),('Monitor','Not documented')])
    config=section('code','Config preview','Generated sensitivity and viewmodel preset. This is not the player’s original config or a crosshair share code.')
    app.code(config,preset(p),height=10).pack(fill='x',padx=22,pady=(0,20))
    for key,title in [('mouse','Mouse'),('crosshair','Crosshair'),('viewmodel','Viewmodel'),('video','Video'),('gear','Gear'),('code','Config')]:
        app.btn(nav,title,lambda k=key:app.scroll_to(sections[k]),width=110,height=36,quiet=True).pack(side='left',padx=(0,5))
