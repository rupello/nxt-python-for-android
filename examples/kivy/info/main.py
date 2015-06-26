import threading

from kivy.uix.rst import RstDocument
from kivy.uix.popup import Popup
from kivy.uix.bubble import Button
from kivy.app import App
from kivy.clock import Clock

try:
    from jnius import detach
except:
    def detach():
        pass

import nxt
import nxt.bluesock
import nxt.brick

class LogDisplayWidget(RstDocument):
    def __init__(self, title='',**kwargs):
        self._logbuffer = [title,
                           '========',
                           '::',
                           '']
        Clock.schedule_interval(self.update_displayed_text, 0.5)
        super(LogDisplayWidget, self).__init__(**kwargs)

    def update_displayed_text(self,dt):
        self.text = '\n'.join(self._logbuffer)
        self.scroll_y = 0  # scroll to bottom

    def log(self,message):
        """lod a message to the console and gui"""
        print(message)
        self._logbuffer.append(message)


class BrickFinder(object):
    def __init__(self):
        self.brick = None

    def start(self):
        self._connect_thread = threading.Thread(target=self._run_find_brick)
        self._connect_thread.start()

    def _run_find_brick(self):
        try:
            self.brick = nxt.find_one_brick(debug=True)
        finally:
            # kivy/android will crash here if we don't detach
            print('detaching thread')
            detach()

    def searching(self):
        self._connect_thread.join(timeout=0.1)
        return self._connect_thread.isAlive()


class BrickFinderWidget(LogDisplayWidget):
    def __init__(self,title='',**kwargs):
        self._bf = BrickFinder()
        super(BrickFinderWidget, self).__init__(title,**kwargs)

    def start(self):
        self._bf.start()
        Clock.schedule_once(self.check_brick_connection, 1.5)

    def check_brick_connection(self,dt):
        """wait for find_brick thread to complete, then print info"""
        self.log(' Searching for a brick...')
        if self._bf.searching():
            # check back later
            Clock.schedule_once(self.check_brick_connection,1.5)
        else:
            if self._bf.brick:
                self.log(' brick found :-)')
                info = self._bf.brick.get_device_info()
                self.log(' Name:{}'.format(info[0].strip('\x00')))
                self.log(' Address:{}'.format(info[1]))
                self.log(' Firmware:{}'.format(self._bf.brick.get_firmware_version()))
                self.log(' Battery:{}mV'.format(self._bf.brick.get_battery_level()))
            else:
                self.log(' brick not found :-(')
                self.log(' Check brick is powered on and paired.')


class InfoApp(App):
    def build(self):
        self._bfw = BrickFinderWidget(title='NXT Demo')
        return self._bfw


    def on_start(self):
        self._bfw.start()



if __name__ == '__main__':
    InfoApp().run()