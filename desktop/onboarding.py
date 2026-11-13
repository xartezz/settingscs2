"""First-run game selection in the main window, reused from Settings."""
import tkinter as tk
from preferences import parse_games,serialize_games

def show_intro(app,label,box,get_setting,put_setting):
    app.detail_active=True;app.back_action=None;app.clear_page()
    app.crumb.configure(text='WELCOME TO PERFSETTINGS')
    selected=set(parse_games(get_setting('interests')))
    label(app.page,'YOUR GAMES. YOUR PERFORMANCE.',10,'#ef4148',True).pack(anchor='w')
    label(app.page,'Make it your workspace.',30,bold=True).pack(anchor='w',pady=(12,8))
    label(app.page,'Choose the games you care about. You can change this any time.',11,'#96989f').pack(anchor='w',pady=(0,24))
    controls={}
    def toggle(game):
        if game in selected:selected.remove(game)
        else:selected.add(game)
        for key,button in controls.items():
            button.primary=key in selected;button.text='✓  Selected' if key in selected else '＋  Select';button.draw()
        hint.configure(text='Ready when you are.' if selected else 'Choose at least one game to continue.')
    for game,title,kicker,description,mark in [
        ('cs2','Counter-Strike 2','AVAILABLE NOW','Pro settings, crosshair previews and your config library.','CS2'),
        ('fivem','FiveM','COMING SOON','Save your interest. FiveM presets and installation are not available yet.','V')]:
        panel=app.panel();panel.pack(fill='x',pady=(0,14),ipady=8)
        art=tk.Canvas(panel,width=76,height=76,bg=panel.cget('bg'),highlightthickness=0)
        art.pack(side='left',padx=20,pady=18)
        art.create_oval(3,3,73,73,fill='#2b2029',outline='#68404c',width=2)
        art.create_text(38,38,text=mark,fill='#f3f3f1',font=('Segoe UI',22,'bold'))
        copy=box(panel,bg=panel.cget('bg'));copy.pack(side='left',fill='x',expand=True,pady=18)
        label(copy,kicker,8,'#ef777c',True).pack(anchor='w')
        label(copy,title,21,bold=True).pack(anchor='w',pady=(5,6))
        label(copy,description,10,'#96989f',wraplength=400,justify='left').pack(anchor='w')
        button=app.btn(panel,'✓  Selected' if game in selected else '＋  Select',lambda g=game:toggle(g),primary=game in selected,width=125)
        button.pack(side='right',padx=20);controls[game]=button
    hint=label(app.page,'Choose at least one game to continue.' if not selected else 'Ready when you are.',10,'#96989f')
    hint.pack(anchor='w',pady=(12,8))
    def finish():
        if not selected:hint.configure(text='Choose at least one game to continue.',fg='#ef777c');return
        put_setting('interests',serialize_games(selected));put_setting('intro_complete','1')
        app.selected_games=parse_games(get_setting('interests'))
        app.update_game_label()
        app.navigate('pro' if 'cs2' in selected else 'fivem')
    app.btn(app.page,'Continue to PerfSettings  →',finish,primary=True,width=280,height=48).pack(anchor='w',pady=(8,10))
    app.animate_page()
