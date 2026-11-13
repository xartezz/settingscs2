import json
import unittest
from unittest.mock import patch
from preferences import parse_games,serialize_games
from onboarding import show_intro

class Widget:
    def __init__(self,*args,**kwargs):self.text=kwargs.get('text','');self.primary=kwargs.get('primary',False)
    def pack(self,*args,**kwargs):pass
    def pack_configure(self,**kwargs):pass
    def cget(self,key):return '#181a20'
    def create_oval(self,*args,**kwargs):pass
    def create_text(self,*args,**kwargs):pass
    def configure(self,**kwargs):self.__dict__.update(kwargs)
    def draw(self):pass

class FakeApp:
    def __init__(self):self.page=Widget();self.crumb=Widget();self.buttons=[];self.destination=None
    def clear_page(self):pass
    def panel(self):return Widget()
    def btn(self,parent,text,command,**kwargs):
        button=Widget(text=text,**kwargs);button.command=command;self.buttons.append(button);return button
    def animate_page(self):pass
    def update_game_label(self):pass
    def navigate(self,destination):self.destination=destination

class Preferences(unittest.TestCase):
    def test_invalid_and_unknown_values(self):
        for raw in ('',None,'{}','"cs2"','["unknown"]'):
            self.assertEqual(parse_games(raw),[])
        self.assertEqual(parse_games('["fivem","cs2","cs2",null]'),['cs2','fivem'])
        with self.assertRaises(ValueError):serialize_games([])
    def test_intro_requires_selection_and_persists_fivem_only(self):
        app=FakeApp();settings={}
        with patch('onboarding.tk.Canvas',Widget):
            show_intro(app,lambda *a,**k:Widget(),lambda *a,**k:Widget(),lambda k:settings.get(k,''),lambda k,v:settings.update({k:v}))
        app.buttons[-1].command()
        self.assertEqual(settings,{})
        app.buttons[1].command();app.buttons[-1].command()
        self.assertEqual(app.destination,'fivem')
        self.assertEqual(settings['intro_complete'],'1')
        self.assertEqual(parse_games(settings['interests']),['fivem'])
        # Reopening restores selection; adding CS2 keeps both interests.
        app2=FakeApp()
        with patch('onboarding.tk.Canvas',Widget):
            show_intro(app2,lambda *a,**k:Widget(),lambda *a,**k:Widget(),lambda k:settings.get(k,''),lambda k,v:settings.update({k:v}))
        self.assertTrue(app2.buttons[1].primary)
        app2.buttons[0].command();app2.buttons[-1].command()
        self.assertEqual(app2.destination,'pro')
        self.assertEqual(parse_games(settings['interests']),['cs2','fivem'])

if __name__=='__main__':unittest.main()
