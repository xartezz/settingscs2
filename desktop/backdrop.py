"""A persistent animated canvas around the readable, opaque content surface."""
import math
import time
import tkinter as tk

def particle_position(index,seconds,width,height):
    # Repeatable paths; no random allocations or accumulating canvas items.
    x=((index*137.3+seconds*(8+index%5))%max(1,width))
    y=(index*89.7+math.sin(seconds*.35+index)*24)%max(1,height)
    return x,y

class AnimatedBackdrop(tk.Canvas):
    def __init__(self,parent,root):
        super().__init__(parent,bg='#0b0c12',highlightthickness=0)
        self.root=root;self.job=None;self.started=time.monotonic();self.paused_at=None;self.last_size=None
        self.lines=[self.create_line(0,0,1,1,fill=color,width=width,smooth=True) for color,width in [('#1e1423',32),('#3c1b2b',12),('#8c344b',2),('#23233b',18),('#54517d',1)]]
        self.particles=[self.create_oval(0,0,3,3,fill='#bd5266' if i%3 else '#7c789d',outline='') for i in range(32)]
        self.host=tk.Frame(self,bg='#0c0d12')
        self.surface=self.create_window(0,0,window=self.host,anchor='nw')
        self.bind('<Configure>',self.layout)
        self.bind('<Destroy>',self.dispose)
        self.tick()
    def layout(self,event=None):
        w=max(1,self.winfo_width());h=max(1,self.winfo_height())
        inset=28 if w>=900 else 12
        width=min(1180,max(1,w-inset*2));height=max(1,h-74)
        self.coords(self.surface,(w-width)/2,50)
        self.itemconfigure(self.surface,width=width,height=height)
        self.draw(0 if getattr(self.root,'reduce_motion',False) else time.monotonic()-self.started)
    def draw(self,t):
        w=max(1,self.winfo_width());h=max(1,self.winfo_height())
        for i,line in enumerate(self.lines):
            pts=[]
            for step in range(17):
                x=w*step/16
                y=(24 if i<3 else h-12)+math.sin(step*.43+t*.7+(0 if i<3 else 2))*(16 if i<3 else 9)
                pts.extend((x,y))
            self.coords(line,*pts)
        for i,particle in enumerate(self.particles):
            x,y=particle_position(i,t,w,h);r=1.5+(i%3)*.6
            self.coords(particle,x-r,y-r,x+r,y+r)
    def tick(self):
        self.job=None
        if self.root.winfo_viewable() and not getattr(self.root,'reduce_motion',False):
            self.draw(time.monotonic()-self.started)
        self.job=self.after(40 if not getattr(self.root,'reduce_motion',False) else 250,self.tick)
    def dispose(self,event):
        if event.widget==self and self.job:
            self.after_cancel(self.job);self.job=None
