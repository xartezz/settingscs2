"""Custom caption: no native white title bar, independent of Windows theme."""
import ctypes
import sys
import tkinter as tk
from ctypes import wintypes
from release_config import VERSION


def geometry(x, y, width, height):
    return f'{int(width)}x{int(height)}{int(x):+d}{int(y):+d}'


def resized(bounds, edge, dx, dy, minimum=(1080, 720)):
    x, y, w, h = bounds
    if 'e' in edge: w = max(minimum[0], w + dx)
    if 's' in edge: h = max(minimum[1], h + dy)
    if 'w' in edge:
        nw = max(minimum[0], w - dx); x += w - nw; w = nw
    if 'n' in edge:
        nh = max(minimum[1], h - dy); y += h - nh; h = nh
    return x, y, w, h


class WindowChrome:
    def __init__(self, root):
        self.root=root; self.maximized=False; self.normal=None; self.drag=None; self.resize_start=None
        root.overrideredirect(True)
        self.bar=tk.Frame(root,bg='#141416',height=54,highlightthickness=0)
        self.bar.pack(side='top',fill='x');self.bar.pack_propagate(False)
        brand=tk.Frame(self.bar,bg='#141416');brand.pack(side='left',padx=20)
        icon=tk.Label(brand,text='⌖',bg='#141416',fg='#ef4148',font=('Segoe UI',24,'bold'));icon.pack(side='left',padx=(0,10))
        text=tk.Frame(brand,bg='#141416');text.pack(side='left')
        name=tk.Label(text,text='SETTINGSCS2',bg='#141416',fg='#f3f3f1',font=('Segoe UI',10,'bold'),anchor='w');name.pack(anchor='w')
        version=tk.Label(text,text='DESKTOP  /  v'+VERSION,bg='#141416',fg='#7f828b',font=('Segoe UI',8),anchor='w');version.pack(anchor='w')
        badge=tk.Label(self.bar,text='  CS2  ',bg='#302023',fg='#ef777c',font=('Segoe UI',8,'bold'),pady=4);badge.pack(side='left',padx=14)
        controls=tk.Frame(self.bar,bg='#141416');controls.pack(side='right',padx=12)
        self.control(controls,'close',self.close,'Închide')
        self.max_button=self.control(controls,'max',self.toggle_maximize,'Maximizează / restaurează')
        self.control(controls,'min',self.minimize,'Minimizează')
        for widget in (self.bar,brand,text,icon,name,version,badge):
            widget.bind('<ButtonPress-1>',self.start_drag)
            widget.bind('<B1-Motion>',self.move)
            widget.bind('<ButtonRelease-1>',lambda e:setattr(self,'drag',None))
            widget.bind('<Double-Button-1>',lambda e:self.toggle_maximize())
        tk.Frame(root,bg='#2b292d',height=1).pack(side='top',fill='x')
        root.bind('<Alt-F4>',lambda e:self.close())
        root.after_idle(self.enable_taskbar)
        self.add_resize_edges()
    def control(self,parent,kind,command,description):
        c=tk.Canvas(parent,width=34,height=30,bg='#141416',highlightthickness=0,cursor='hand2',takefocus=1)
        c.pack(side='right',padx=3)
        def draw(active=False):
            c.delete('all');bg=('#ba343c' if kind=='close' else '#38383f') if active else '#242428'
            c.create_polygon(6,0,28,0,34,0,34,6,34,24,34,30,28,30,6,30,0,30,0,24,0,6,0,0,smooth=True,fill=bg)
            fg='#ffffff' if active else '#b8b9c1'
            if kind=='close':
                c.create_line(12,10,22,20,fill=fg,width=1.4);c.create_line(22,10,12,20,fill=fg,width=1.4)
            elif kind=='min':c.create_line(11,16,23,16,fill=fg,width=1.4)
            else:
                if self.maximized:c.create_rectangle(14,9,24,19,outline=fg)
                c.create_rectangle(11,12 if self.maximized else 10,21 if self.maximized else 23,22 if self.maximized else 21,outline=fg,fill=bg)
        c.bind('<Enter>',lambda e:draw(True));c.bind('<Leave>',lambda e:draw())
        c.bind('<FocusIn>',lambda e:draw(True));c.bind('<FocusOut>',lambda e:draw())
        c.bind('<Button-1>',lambda e:command());c.bind('<Return>',lambda e:command());c.bind('<space>',lambda e:command())
        c.redraw=draw;draw();return c
    def api(self):
        api=ctypes.WinDLL('user32',use_last_error=True)
        api.GetAncestor.argtypes=[wintypes.HWND,wintypes.UINT];api.GetAncestor.restype=wintypes.HWND
        api.ShowWindow.argtypes=[wintypes.HWND,ctypes.c_int];api.ShowWindow.restype=wintypes.BOOL
        return api,api.GetAncestor(self.root.winfo_id(),2)
    def enable_taskbar(self):
        if sys.platform!='win32':return
        try:
            self.root.update_idletasks();api,hwnd=self.api()
            get=api.GetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p)==8 else api.GetWindowLongW
            set_=api.SetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p)==8 else api.SetWindowLongW
            get.argtypes=[wintypes.HWND,ctypes.c_int];get.restype=ctypes.c_ssize_t
            set_.argtypes=[wintypes.HWND,ctypes.c_int,ctypes.c_ssize_t];set_.restype=ctypes.c_ssize_t
            # Keep app in taskbar/Alt-Tab even though Tk uses an undecorated window.
            set_(hwnd,-20,(get(hwnd,-20)|0x00040000)&~0x00000080)
            api.SetWindowPos.argtypes=[wintypes.HWND,wintypes.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,wintypes.UINT]
            api.SetWindowPos(hwnd,None,0,0,0,0,0x0027)
        except (OSError,AttributeError):pass
    def close(self):self.root.destroy()
    def minimize(self):
        if sys.platform=='win32':
            api,hwnd=self.api();api.ShowWindow(hwnd,6)
        else:
            self.root.overrideredirect(False);self.root.iconify()
            self.root.bind('<Map>',lambda e:self.root.overrideredirect(True),add='+')
    def bounds(self):
        return self.root.winfo_x(),self.root.winfo_y(),self.root.winfo_width(),self.root.winfo_height()
    def workarea(self):
        if sys.platform=='win32':
            try:
                class Info(ctypes.Structure):
                    _fields_=[('cbSize',wintypes.DWORD),('rcMonitor',wintypes.RECT),('rcWork',wintypes.RECT),('dwFlags',wintypes.DWORD)]
                api,hwnd=self.api();api.MonitorFromWindow.argtypes=[wintypes.HWND,wintypes.DWORD];api.MonitorFromWindow.restype=wintypes.HANDLE
                api.GetMonitorInfoW.argtypes=[wintypes.HANDLE,ctypes.POINTER(Info)];api.GetMonitorInfoW.restype=wintypes.BOOL
                info=Info();info.cbSize=ctypes.sizeof(info)
                if api.GetMonitorInfoW(api.MonitorFromWindow(hwnd,2),ctypes.byref(info)):
                    r=info.rcWork;return r.left,r.top,r.right-r.left,r.bottom-r.top
            except (OSError,AttributeError):pass
        return 0,0,self.root.winfo_screenwidth(),self.root.winfo_screenheight()
    def toggle_maximize(self):
        self.drag=None
        if self.maximized:
            self.maximized=False
            if self.normal:self.root.geometry(geometry(*self.normal))
        else:
            self.normal=self.bounds();self.maximized=True;self.root.geometry(geometry(*self.workarea()))
        self.max_button.redraw()
    def start_drag(self,event):
        self.drag=(event.x_root,event.y_root,self.bounds())
    def move(self,event):
        if not self.drag:return
        px,py,b=self.drag
        if self.maximized:
            if abs(event.x_root-px)+abs(event.y_root-py)<5:return
            ratio=max(0,min(1,(px-b[0])/max(1,b[2])))
            restored=self.normal or (0,0,1280,840)
            x=int(event.x_root-restored[2]*ratio);y=event.y_root-25
            self.maximized=False;self.root.geometry(geometry(x,y,restored[2],restored[3]));self.max_button.redraw()
            self.drag=(event.x_root,event.y_root,(x,y,restored[2],restored[3]));return
        self.root.geometry(geometry(b[0]+event.x_root-px,b[1]+event.y_root-py,b[2],b[3]))
    def add_resize_edges(self):
        specs=[('n',dict(relx=0,rely=0,relwidth=1,height=4)),('s',dict(relx=0,rely=1,relwidth=1,height=4,anchor='sw')),('w',dict(relx=0,rely=0,width=4,relheight=1)),('e',dict(relx=1,rely=0,width=4,relheight=1,anchor='ne')),('nw',dict(relx=0,rely=0,width=8,height=8)),('ne',dict(relx=1,rely=0,width=8,height=8,anchor='ne')),('sw',dict(relx=0,rely=1,width=8,height=8,anchor='sw')),('se',dict(relx=1,rely=1,width=8,height=8,anchor='se'))]
        for edge,placement in specs:
            grip=tk.Frame(self.root,bg='#242428',cursor={'n':'sb_v_double_arrow','s':'sb_v_double_arrow','e':'sb_h_double_arrow','w':'sb_h_double_arrow'}.get(edge,'sizing'))
            grip.place(**placement);grip.lift()
            grip.bind('<ButtonPress-1>',lambda e,edge=edge:self.start_resize(e,edge))
            grip.bind('<B1-Motion>',self.resize)
            grip.bind('<ButtonRelease-1>',lambda e:setattr(self,'resize_start',None))
            # Lift after the content is built, so all eight edges stay reachable.
            self.root.after_idle(grip.lift)
    def start_resize(self,event,edge):
        self.resize_start=None if self.maximized else (event.x_root,event.y_root,self.bounds(),edge)
    def resize(self,event):
        if self.resize_start:
            x,y,b,edge=self.resize_start
            self.root.geometry(geometry(*resized(b,edge,event.x_root-x,event.y_root-y)))
