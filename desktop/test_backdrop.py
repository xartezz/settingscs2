import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from backdrop import AnimatedBackdrop,particle_position

class BackdropTests(unittest.TestCase):
    def canvas(self,reduced=False,visible=True):
        canvas=object.__new__(AnimatedBackdrop)
        canvas.root=SimpleNamespace(reduce_motion=reduced,winfo_viewable=lambda:visible)
        canvas.started=0;canvas.job=None
        canvas.after=Mock(return_value='timer');canvas.after_cancel=Mock();canvas.draw=Mock()
        return canvas
    def test_moves_and_stays_inside_bounds(self):
        for i in range(32):
            first=particle_position(i,0,1080,720)
            second=particle_position(i,2,1080,720)
            self.assertNotEqual(first,second)
            self.assertTrue(0<=second[0]<1080 and 0<=second[1]<720)
    def test_animation_and_cleanup(self):
        canvas=self.canvas();canvas.tick()
        canvas.draw.assert_called_once()
        self.assertEqual(canvas.after.call_args.args[0],40)
        canvas.dispose(SimpleNamespace(widget=canvas))
        canvas.after_cancel.assert_called_once_with('timer')
        self.assertIsNone(canvas.job)
    def test_reduce_motion_and_hidden_window(self):
        for reduced,visible in [(True,True),(False,False)]:
            canvas=self.canvas(reduced,visible);canvas.tick()
            canvas.draw.assert_not_called()
    def test_draw_reuses_items(self):
        canvas=self.canvas();canvas.lines=list(range(5));canvas.particles=list(range(5,37))
        canvas.winfo_width=lambda:1080;canvas.winfo_height=lambda:720
        canvas.coords=Mock()
        AnimatedBackdrop.draw(canvas,0)
        initial=canvas.coords.call_args_list[:]
        canvas.coords.reset_mock();AnimatedBackdrop.draw(canvas,2)
        self.assertEqual(canvas.coords.call_count,37)
        self.assertNotEqual(initial,canvas.coords.call_args_list)

if __name__=='__main__':unittest.main()
