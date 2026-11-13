"""Custom caption: no native white title bar, independent of Windows theme."""
import ctypes
import sys
import tkinter as tk
from ctypes import wintypes
from release_config import VERSION
from glass import rounded_points


APP_USER_MODEL_ID = 'SettingsCS2.Desktop'


def set_app_identity():
    """Match installed shortcuts; call before creating any Tk windows."""
    if sys.platform != 'win32':
        return False
    try:
        shell = ctypes.WinDLL('shell32', use_last_error=True)
        setter = shell.SetCurrentProcessExplicitAppUserModelID
        setter.argtypes = [wintypes.LPCWSTR]
        setter.restype = ctypes.c_long
        return setter(APP_USER_MODEL_ID) == 0
    except (OSError, AttributeError):
        return False


def repair_taskbar_window(api, hwnd, already_registered=False):
    """Register the real wrapper HWND with Explorer after Tk has mapped it."""
    if not hwnd:
        return False
    get = api.GetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else api.GetWindowLongW
    set_ = api.SetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p) == 8 else api.SetWindowLongW
    get.argtypes = [wintypes.HWND, ctypes.c_int]; get.restype = ctypes.c_ssize_t
    set_.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]; set_.restype = ctypes.c_ssize_t
    api.IsWindowVisible.argtypes = [wintypes.HWND]; api.IsWindowVisible.restype = wintypes.BOOL
    api.IsIconic.argtypes = [wintypes.HWND]; api.IsIconic.restype = wintypes.BOOL
    api.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
    api.SetWindowPos.restype = wintypes.BOOL
    # Do not restore a minimized app or map a window that Tk is still creating.
    if not api.IsWindowVisible(hwnd) or api.IsIconic(hwnd):
        return False
    style = get(hwnd, -20)
    desired = (style | 0x00040000) & ~(0x00000080 | 0x08000000)
    owner = get(hwnd, -8)
    if already_registered and style == desired and not owner:
        return True
    # Explorer must see a fresh hide -> style change -> show transition.
    api.ShowWindow(hwnd, 0)
    try:
        set_(hwnd, -20, desired)
        if owner:
            set_(hwnd, -8, 0)
        api.SetWindowPos(hwnd, None, 0, 0, 0, 0, 0x0037)
    finally:
        api.ShowWindow(hwnd, 8)  # SW_SHOWNA: never steal focus on restore.
    return get(hwnd, -20) == desired and get(hwnd, -8) == 0


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
        name=tk.Label(text,text='PerfSettings',bg='#141416',fg='#f3f3f1',font=('Segoe UI',10,'bold'),anchor='w');name.pack(anchor='w')
        version=tk.Label(text,text='PERFORMANCE HUB  /  v'+VERSION,bg='#141416',fg='#7f828b',font=('Segoe UI',8),anchor='w');version.pack(anchor='w')
        badge=tk.Label(self.bar,text='  CS2  ',bg='#302023',fg='#ef777c',font=('Segoe UI',8,'bold'),pady=4);badge.pack(side='left',padx=14)
        controls=tk.Frame(self.bar,bg='#141416');controls.pack(side='right',padx=12)
        self.control(controls,'close',self.close,'Close')
        self.max_button=self.control(controls,'max',self.toggle_maximize,'Maximize / restore')
        self.control(controls,'min',self.minimize,'Minimize')
        for widget in (self.bar,brand,text,icon,name,version,badge):
            widget.bind('<ButtonPress-1>',self.start_drag)
            widget.bind('<B1-Motion>',self.move)
            widget.bind('<ButtonRelease-1>',lambda e:setattr(self,'drag',None))
            widget.bind('<Double-Button-1>',lambda e:self.toggle_maximize())
        tk.Frame(root,bg='#2b292d',height=1).pack(side='top',fill='x')
        root.bind('<Alt-F4>',lambda e:self.close())
        self._taskbar_hwnd=None; self._taskbar_job=None; self._taskbar_repairing=False
        root.bind('<Map>',self.on_map,add='+')
        self.schedule_taskbar_repair()
        self.add_resize_edges()
    def control(self,parent,kind,command,description):
        c=tk.Canvas(parent,width=34,height=30,bg='#141416',highlightthickness=0,cursor='hand2',takefocus=1)
        c.pack(side='right',padx=3)
        c.amount=0.;c.job=None;c.target=0.
        def draw(active=None):
            c.delete('all');target='#ba343c' if kind=='close' else '#454654'
            base='#24242c'
            bg='#'+''.join(f'{round(int(base[i:i+2],16)+(int(target[i:i+2],16)-int(base[i:i+2],16))*c.amount):02x}' for i in (1,3,5))
            active=c.amount>.5
            c.create_polygon(*rounded_points(0,0,34,30,8),fill=bg,outline='#3c3e48')
            fg='#ffffff' if active else '#b8b9c1'
            if kind=='close':
                c.create_line(12,10,22,20,fill=fg,width=1.4);c.create_line(22,10,12,20,fill=fg,width=1.4)
            elif kind=='min':c.create_line(11,16,23,16,fill=fg,width=1.4)
            else:
                if self.maximized:c.create_rectangle(14,9,24,19,outline=fg)
                c.create_rectangle(11,12 if self.maximized else 10,21 if self.maximized else 23,22 if self.maximized else 21,outline=fg,fill=bg)
        def frame():
            c.job=None
            c.amount=c.target if getattr(self.root,'reduce_motion',False) else c.amount+(c.target-c.amount)*.4
            if abs(c.target-c.amount)<.02:c.amount=c.target
            draw()
            if c.amount!=c.target:c.job=c.after(16,frame)
        def hover(value):
            c.target=float(value)
            if c.job:c.after_cancel(c.job);c.job=None
            frame()
        def dispose(event):
            if event.widget==c and c.job:c.after_cancel(c.job);c.job=None
        c.bind('<Destroy>',dispose)
        c.bind('<Enter>',lambda e:hover(True));c.bind('<Leave>',lambda e:hover(False))
        c.bind('<FocusIn>',lambda e:hover(True));c.bind('<FocusOut>',lambda e:hover(False))
        c.bind('<Button-1>',lambda e:command());c.bind('<Return>',lambda e:command());c.bind('<space>',lambda e:command())
        c.redraw=draw;draw();return c
    def api(self):
        api=ctypes.WinDLL('user32',use_last_error=True)
        api.GetAncestor.argtypes=[wintypes.HWND,wintypes.UINT];api.GetAncestor.restype=wintypes.HWND
        api.ShowWindow.argtypes=[wintypes.HWND,ctypes.c_int];api.ShowWindow.restype=wintypes.BOOL
        return api,api.GetAncestor(self.root.winfo_id(),2)
    def on_map(self,event):
        if event.widget == self.root:
            self.schedule_taskbar_repair()
    def schedule_taskbar_repair(self):
        if sys.platform=='win32' and self._taskbar_job is None and not self._taskbar_repairing:
            self._taskbar_job=self.root.after(150,self.enable_taskbar)
    def enable_taskbar(self):
        self._taskbar_job=None
        if sys.platform!='win32' or self._taskbar_repairing:return
        self._taskbar_repairing=True
        try:
            api,hwnd=self.api()
            if repair_taskbar_window(api,hwnd,self._taskbar_hwnd==hwnd):
                self._taskbar_hwnd=hwnd
        except (OSError,AttributeError):
            self._taskbar_hwnd=None
        finally:
            self._taskbar_repairing=False
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


