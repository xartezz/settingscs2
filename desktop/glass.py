"""Opaque glass-inspired surfaces, compatible with standard Tk on Windows."""
import math
import tkinter as tk

def rounded_points(x,y,w,h,r=12):
    points=[]
    for cx,cy,start in [(x+w-r,y+r,-90),(x+w-r,y+h-r,0),(x+r,y+h-r,90),(x+r,y+r,180)]:
        for step in range(7):
            angle=math.radians(start+step*15)
            points.extend((cx+r*math.cos(angle),cy+r*math.sin(angle)))
    return points

class GlassPanel(tk.Frame):
    """Small corner masks and a soft highlight, without whole-window opacity."""
    def __init__(self,parent,**kwargs):
        kwargs.pop('highlightthickness',None);kwargs.pop('highlightbackground',None)
        super().__init__(parent,bg='#181a20',**kwargs)
        self._corners=[];self._job=None;self._motion=None;self._level=0.;self._target=0.
        outer=parent.cget('bg')
        for position,anchor in [((0,0),'nw'),((1,0),'ne'),((0,1),'sw'),((1,1),'se')]:
            c=tk.Canvas(self,width=12,height=12,bg=outer,highlightthickness=0,takefocus=0)
            c.place(relx=position[0],rely=position[1],anchor=anchor)
            self._corners.append((c,position))
        self._sheen=tk.Frame(self,height=1,bg='#343744')
        self._sheen.place(x=12,y=0,relwidth=1,width=-24)
        self.bind('<Enter>',lambda event:self._hover(True))
        self.bind('<Leave>',self._leave)
        self.bind('<Configure>',self._schedule)
        self.bind('<Destroy>',self._dispose)
    def _schedule(self,event=None):
        if not self._job:self._job=self.after_idle(self._paint)
    def _paint(self):
        self._job=None
        for c,(right,bottom) in self._corners:
            c.delete('all');x=-12 if right else 0;y=-12 if bottom else 0
            c.create_oval(x,y,x+24,y+24,fill=self.cget('bg'),outline=self._edge(),width=1)
            c.tk.call('raise',c._w)
    def _edge(self):
        return '#'+''.join(f'{round(a+(b-a)*self._level):02x}' for a,b in zip((54,57,67),(110,75,89)))
    def _leave(self,event):
        x=self.winfo_pointerx()-self.winfo_rootx();y=self.winfo_pointery()-self.winfo_rooty()
        if not (0<=x<self.winfo_width() and 0<=y<self.winfo_height()):self._hover(False)
    def _hover(self,value):
        self._target=float(value)
        if self._motion:self.after_cancel(self._motion);self._motion=None
        self._animate()
    def _animate(self):
        self._motion=None
        self._level=self._target if getattr(self.winfo_toplevel(),'reduce_motion',False) else self._level+(self._target-self._level)*.3
        if abs(self._target-self._level)<.02:self._level=self._target
        self._sheen.configure(bg=self._edge());self._schedule()
        if self._level!=self._target:self._motion=self.after(16,self._animate)
    def _dispose(self,event):
        if event.widget==self:
            for job in (self._job,self._motion):
                if job:self.after_cancel(job)
            self._job=None;self._motion=None
