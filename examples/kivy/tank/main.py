import threading
import time

from kivy.uix.rst import RstDocument
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.slider import Slider
from kivy.animation import Animation

try:
    from jnius import detach
except:
    def detach():
        pass

import nxt
import nxt.bluesock
import nxt.brick
import nxt.motor


class SelfCenteringSlider(Slider):
    """center the center automatically if released"""
    def on_touch_up(self, touch):
        if self.collide_point(touch.pos[0], touch.pos[1]):
            Animation(value=0,duration=.2,t='out_back').start(self)


class TankApp(App):

    def build(self):
        self.manager = ScreenManager(transition=SlideTransition(
            duration=.15))
        self.init_log()
        self._doc = RstDocument(text='')

        search_screen = Screen(name='search')
        search_screen.add_widget(self._doc)
        self.manager.add_widget(search_screen)

        tank_screen = Screen(name='tank')
        layout = BoxLayout(orientation='horizontal')
        self._leftSlider = SelfCenteringSlider(min=-100, max=100, value=0,orientation='vertical')
        self._rightSlider = SelfCenteringSlider(min=-100, max=100, value=0,orientation='vertical')
        layout.add_widget(self._leftSlider)
        layout.add_widget(self._rightSlider)
        tank_screen.add_widget(layout)
        self.manager.add_widget(tank_screen)

        self.manager.current = 'search'
        return self.manager

    def init_log(self):
        self._logbuffer = ['Tank Demo',
                           '=========',
                           '::',
                           '']

    def log(self,message):
        """log a message to the console and gui"""
        print(message)
        self._logbuffer.append(message)

    def on_start(self):
        self._brick = None
        self._connect_thread = threading.Thread(target=self.find_brick)
        self._connect_thread.start()
        Clock.schedule_interval(self.update_displayed_text, 0.5)
        Clock.schedule_interval(self.check_brick_connection, 1.5)

    def check_brick_connection(self,dt):
        """wait for find_brick thread to complete, then print info"""
        self.log(' Searching for a brick...')
        self._connect_thread.join(timeout=0.5)
        if not self._connect_thread.isAlive():
            Clock.unschedule(self.check_brick_connection)
            if self._brick:
                self.log(' brick found :-)')
                info = self._brick.get_device_info()
                self.log(' Name:{}'.format(info[0].strip('\x00')))
                self.log(' Address:{}'.format(info[1]))
                self.log(' Firmware:{}'.format(self._brick.get_firmware_version()))
                self.log(' Battery:{}mV'.format(self._brick.get_battery_level()))
                Clock.schedule_once(self.start_tank,1.0)
            else:
                self.log(' brick not found :-(')
                self.log(' Check brick is powered on and paired.')

    def find_brick(self):
        try:
            self._brick = nxt.find_one_brick(debug=True)
        finally:
            # kivy/android will crash here if we don't detach
            print('detaching thread')
            detach()

    def update_displayed_text(self,dt):
        self._doc.text = '\n'.join(self._logbuffer)
        self._doc.scroll_y = 0  # scroll to bottom

    def start_tank(self,dt):
        self._motleft = nxt.motor.Motor(self._brick, nxt.motor.PORT_B)
        self._motright = nxt.motor.Motor(self._brick, nxt.motor.PORT_C)
        self.manager.current = 'tank'
        Clock.schedule_interval(self.update_motors, 0.1)

    def update_motors(self,dt):
        start = time.time()
        self._motleft.run(power=self._leftSlider.value)
        self._motright.run(power=self._rightSlider.value)
        interval = time.time()-start
        print('updated in:{:.03}'.format(interval))

    def on_touch_down(self, touch):
        print touch

if __name__ == '__main__':
    TankApp().run()