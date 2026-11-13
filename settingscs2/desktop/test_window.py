import unittest
from unittest.mock import Mock, patch
from window_style import geometry, resized, WindowChrome

class WindowTests(unittest.TestCase):
    def test_negative_monitor_coordinates(self):
        self.assertEqual(geometry(-1500,20,1280,840),'1280x840-1500+20')
    def test_resize_clamps_and_preserves_opposite_edge(self):
        self.assertEqual(resized((100,100,1280,840),'nw',1000,1000),(300,220,1080,720))
        self.assertEqual(resized((100,100,1280,840),'se',100,200),(100,100,1380,1040))
    def controller(self):
        c=WindowChrome.__new__(WindowChrome);c.root=Mock();c.max_button=Mock();c.maximized=False;c.normal=None;c.drag=None
        c.bounds=Mock(return_value=(100,100,1280,840));c.workarea=Mock(return_value=(-1920,0,1920,1040))
        return c
    def test_maximize_restore(self):
        c=self.controller();c.toggle_maximize();self.assertTrue(c.maximized)
        c.root.geometry.assert_called_with('1920x1040-1920+0')
        c.toggle_maximize();self.assertFalse(c.maximized)
        c.root.geometry.assert_called_with('1280x840+100+100')
    def test_drag_and_resize_disabled_while_maximized(self):
        c=self.controller();c.start_drag(Mock(x_root=200,y_root=120));c.move(Mock(x_root=240,y_root=160))
        c.root.geometry.assert_called_with('1280x840+140+140')
        c.maximized=True;c.start_resize(Mock(x_root=0,y_root=0),'se');self.assertIsNone(c.resize_start)
    def test_native_minimize_without_showing_caption(self):
        c=self.controller();api=Mock();c.api=Mock(return_value=(api,123))
        with patch('window_style.sys.platform','win32'):c.minimize()
        api.ShowWindow.assert_called_once_with(123,6)
        c.root.overrideredirect.assert_not_called()

if __name__=='__main__':unittest.main()
