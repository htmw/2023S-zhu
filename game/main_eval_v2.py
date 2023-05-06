import os, sys
import random
import typing
from PyQt5.QtCore import QObject
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import pyaudio
from scipy.io import wavfile

sys.path.append('./')
from game.tank import Tank, Bullet
from game.zmap import ZMap
from game.stuff import Stuff
from game.zsemaphore import ZSemaphore

from nn.brain import Brain
from game.trans import Trans

class ZControl:
    def __init__(self,
                zmap,
                tanks,
                tank_player,
                stuff,
                signal_new_stuff,
                sem):
        self.zmap = zmap
        self.tanks = tanks
        self.tank_player = tank_player
        self.stuff = stuff
        self.signal_new_stuff = signal_new_stuff
        self.sem = sem

        self.bullets = []
        random.seed(1234)

    def update_bullet(self):
        delete_idx = []
        for idx, bullet in enumerate(self.bullets):
            if not bullet.move_forward(self.zmap, self.tanks):
                if bullet.who_am_i == 'p' and bullet.state == 0:
                    print('boom')
                    self.sem.release('boom')
                bullet.state += 1
                if bullet.state >= 6:
                    delete_idx.append(idx)

        for idx in delete_idx[::-1]:
            '''
            eg:
                a = ['a', 'b', 'c']
                we are going to delete idx 0 2
                if idx 0 is deleted, a = ['b', 'c']
                now we cannot delete idx 2, because it's not exist
                we should delete idx 2 firt, and get a = ['a', 'b']
                and then, idx 0 can be deleted
            '''
            self.bullets.pop(idx)

    def update_tank(self, actions):
        # delete_idx = []
        assert len(actions) == len(self.tanks)
        rewards = [0.0 for _ in range(len(self.tanks))]
        for i, (tank, action) in enumerate(zip(self.tanks, actions)):
            if tank.life <= 0:
                print(f'tank {i} die')
                # delete_idx.append(i)
                tank.life = 3
                if tank == self.tank_player:
                    tank.life = 10
                    k = random.randint(0, 4)
                    if k == 0:
                        tank.x = 78
                        tank.y = 78
                    elif k == 1:
                        tank.x = 0
                        tank.y = 78
                    elif k == 2:
                        tank.x = 78
                        tank.y = 0
                    else:
                        tank.x = 0
                        tank.y = 0
                else:
                    tank.x = 0
                    tank.y = 0
                    self.tank_player.score += (100 * tank.level)
                continue

            if tank == self.tank_player:
                px, py = tank.x, tank.y
                if px <= (self.stuff.x + 4) <= px+11: #x ok
                    if py <= (self.stuff.y + 4) <= py+11: # y ok
                        print('eat stuff')
                        if self.stuff.type == 'speed':
                            tank.fire_speed += 1
                        elif self.stuff.type == 'level':
                            tank.level += 1
                        elif self.stuff.type == 'score':
                            tank.score += 100
                        self.stuff.type = 'none' #防止多次触发
                        self.signal_new_stuff.emit()

            if action in ['up', 'down', 'left', 'right']:
                if not tank.move(self.zmap, action):
                    rewards[i] = -0.1 #failed to move, punishment
            elif action == 'fire':
                bullet = tank.fire()
                if bullet is not None:
                    self.bullets.append(bullet)
            else: #no action
                pass
        return rewards

    def step(self, actions):
        self.update_bullet()
        return self.update_tank(actions)
    
class ThreadMusic(QThread):
    def __init__(self, sem:ZSemaphore):
        super().__init__()

        p = pyaudio.PyAudio()
        self.stream = p.open(format=p.get_format_from_width(2),
                        channels=1,
                        rate=16000,
                        output=True)
        
        sr, self.pcm_fire = wavfile.read('./zmusic/fire.wav')
        sr, self.pcm_boom = wavfile.read('./zmusic/boom.wav')
        self.sem = sem
        # self.stream.write(pcm)

    def run(self):
        while True:
            music_id = self.sem.acquire()
            if music_id == 'boom':
                self.stream.write(self.pcm_boom)
            else:
                self.stream.write(self.pcm_fire)

class ZGame(QObject):
    signal_new_stuff = pyqtSignal()

    def __init__(self, map_id=1, player_tank_info=None, sem=None):
        super().__init__()
        step_size = 5

        self.signal_new_stuff.connect(self.slot_new_stuff)

        if player_tank_info is None:
            self.tank_player = Tank('./tank/pic/tank_huge', './tank/pic/bullet_huge', 390, 390, step_size, 'p', life=10)
        else:
            self.tank_player = Tank(player_tank_info['prefix'], './tank/pic/bullet_huge', 390, 390, step_size, 'p', life=10, level=player_tank_info['level'])
        # self.tank_player.fire_speed = 2 #test
        self.tanks = []
        self.tanks.append(self.tank_player)
        self.tanks.append(Tank('./tank/pic/tank_red', './tank/pic/bullet_red', 0, 0, step_size, 'e', level=3)) #e: npc, p: player
        self.tanks.append(Tank('./tank/pic/tank_blue', './tank/pic/bullet_blue', 200, 0, step_size, 'e', level=2))
        self.tanks.append(Tank('./tank/pic/tank_black', './tank/pic/bullet_black', 405, 0, step_size, 'e', level=1))

        self.zmap = ZMap(450, 450, step_size, map_id)

        x, y = self.random_pos()
        self.stuff = Stuff(x, y)

        self.control = ZControl(self.zmap.data, self.tanks, self.tank_player, self.stuff, self.signal_new_stuff, sem)
        self.rewards = [0.0 for _ in range(len(self.tanks))]

    def random_pos(self):
        while True:
            x = np.random.randint(0, 78)
            y = np.random.randint(0, 78)
            # if self.zmap.data[y*45:y*45+45, x*45:x*45+45].sum() > 0:
            if self.zmap.data[y:y+9, x:x+9].sum() > 0:
                continue
            return x, y

    def paint(self, w=450, h=450):
        img = QImage(w, h, QImage.Format.Format_RGB888)
        painter = QPainter(img)

        self.zmap.paint(painter)

        self.stuff.paint(painter)

        for tank in self.control.tanks:
            tank.paint(painter)

        for bullet in self.control.bullets:
            bullet.paint(painter)

        painter.end()
        # img.save('./img.png')
        return img
    
    def step(self, actions):
        self.actions = actions
        self.rewards = self.control.step(actions)
        for tank in self.tanks:
            tank.fire_t -= tank.fire_speed

    def get_states(self): #states: list of all enemy's state
        ch1 = self.zmap.data #map
        ch2 = np.zeros_like(ch1) #player tank
        ch2[self.tank_player.y:self.tank_player.y+self.tank_player.tank_size, self.tank_player.x:self.tank_player.x+self.tank_player.tank_size] = 1

        states = [] #states[0] is the state for enemy0 ....
        for tank in self.tanks[1:]: #self.tanks[0] is player tank
            ch3 = np.zeros_like(ch1)
            ch3[tank.y:tank.y+tank.tank_size, tank.x:tank.x+tank.tank_size] = 1
            if tank.dir == 0: #up
                ch3[tank.y:tank.y+tank.tank_size//3, tank.x:tank.x+tank.tank_size//3] = 0
                ch3[tank.y:tank.y+tank.tank_size//3, tank.x+tank.tank_size//3*2:tank.x+tank.tank_size] = 0
            elif tank.dir == 1: #down
                ch3[tank.y+tank.tank_size//3*2:tank.y+tank.tank_size, tank.x:tank.x+tank.tank_size//3] = 0
                ch3[tank.y+tank.tank_size//3*2:tank.y+tank.tank_size, tank.x+tank.tank_size//3*2:tank.x+tank.tank_size] = 0
            elif tank.dir == 2: #left
                ch3[tank.y:tank.y+tank.tank_size//3, tank.x:tank.x+tank.tank_size//3] = 0
                ch3[tank.y+tank.tank_size//3*2:tank.y+tank.tank_size, tank.x:tank.x+tank.tank_size//3] = 0
            elif tank.dir == 3: #right
                ch3[tank.y:tank.y+tank.tank_size//3, tank.x+tank.tank_size//3*2:tank.x+tank.tank_size] = 0
                ch3[tank.y+tank.tank_size//3*2:tank.y+tank.tank_size, tank.x+tank.tank_size//3*2:tank.x+tank.tank_size] = 0
            state = np.stack((ch1.copy(), ch2.copy(), ch3))
            states.append(state)
        return states
    
    def calc_best_action(self, tank, px, py, zmap):
        if px <= (tank.x + 4) <= px+11: #x ok
            if py < tank.y:
                if tank.dir == 0:
                    return 'fire'
                return 'up'
            else:
                if tank.dir == 1:
                    return 'fire'
                return 'down'
        if py <= (tank.y + 4) <= py+11: # y ok
            if px < tank.x:
                if tank.dir == 2:
                    return 'fire'
                return 'left'
            else:
                if tank.dir == 3:
                    return 'fire'
                return 'right'
        
        diff_x = np.abs(px - tank.x)
        diff_y = np.abs(py - tank.y)
        if diff_x < diff_y:
            if px < tank.x:
                return 'left'
            else:
                return 'right'
        else:
            if py < tank.y:
                return 'up'
            else:
                return 'down'
            
    def calc_best_actions(self):
        px = self.tank_player.x
        py = self.tank_player.y

        actions = ['no']
        for i, tank in enumerate(self.tanks[1:]):
            if np.random.rand() < 0.8:
                actions.append(self.calc_best_action(tank, px, py, self.zmap.data))
            else:
                actions.append(random.choice(['up', 'down', 'left', 'tight', 'fire']))
        return actions
    
    def slot_new_stuff(self):
        x, y = self.random_pos()
        self.stuff.set_pos(x, y)
    
class ThreadTest(QThread):
    def __init__(self, paint_signal, map_id, player_tank_info, sem):
        super().__init__()

        self.paint_signal = paint_signal
        self.zgame = ZGame(map_id, player_tank_info, sem)
        self.paint_cnt = 0

        self.brain = Brain()
        self.brain.load('./model_eval_00001000.ckpt')
        self.p = False

    def run(self):
        step = 0
        states = self.zgame.get_states() #cur state
        self.run = True
        while self.run:
            actions = self.brain.choose_actions(states, ratio=1.0)
            actions = self.zgame.calc_best_actions()
            print(actions)
            self.zgame.step(actions) #process
            img = self.zgame.paint()
            states_ = self.zgame.get_states() #next state
            self.paint_signal.emit(img, states_)
            states = states_
            while self.p:
                self.usleep(100000)
            self.usleep(200000)
        self.run = True

    def pause(self):
        self.p = not self.p

class ZWidgetGame(QWidget):
    paint_signal = pyqtSignal(QImage, list)
    def __init__(self, signal, trans):
        super().__init__()
        # self.init_ui()

        self.signal = signal
        self.trans = trans

        self.img = None
        self.states_ = None
        self.paint_signal.connect(self.paint_slot)
        self.show()

        # self.thread_test = ThreadTest(self.paint_signal, 1)
        # self.thread_test.start()
        self.thread_test = None
        self.map_id = 2

        self.sem = ZSemaphore()
        self.thread_music = ThreadMusic(self.sem)
        self.thread_music.start()

    def paintEvent(self, e):
        rect = e.region().rects()[0] #may contains more rect
        sx, sy, ex, ey = rect.left(), rect.top(), rect.right(), rect.bottom()
        w = ex - sx
        h = ey - sy
        painter = QPainter(self)

        if self.img is not None:
            painter.drawImage(0, 0, self.img)

        if self.thread_test is None:
            return
        
        painter.drawText(0, 480, self.trans.s('pause') if self.thread_test.p else '')
        tank = self.thread_test.zgame.tank_player
        painter.drawText(0, 500, '%s:%d' % (self.trans.s('life'), 0 if tank.life < 0 else tank.life))
        painter.drawText(100, 500, '%s:%d' % (self.trans.s('speed'), tank.fire_speed))
        painter.drawText(200, 500, '%s:%d' % (self.trans.s('level'), tank.level))
        painter.drawText(300, 500, '%s:%d' % (self.trans.s('score'), tank.score))
        painter.end()

    def keyPressEvent(self, e):
        if e.key() == 87:#16777235: #up
            self.thread_test.zgame.tank_player.move(self.thread_test.zgame.zmap.data, 'up')
        elif e.key() == 83:#16777237: #down
            self.thread_test.zgame.tank_player.move(self.thread_test.zgame.zmap.data, 'down')
        elif e.key() == 65:#16777234: #left
            self.thread_test.zgame.tank_player.move(self.thread_test.zgame.zmap.data, 'left')
        elif e.key() == 68:#16777236: #right
            self.thread_test.zgame.tank_player.move(self.thread_test.zgame.zmap.data, 'right')
        elif e.key() == 70:#32:
            bullet = self.thread_test.zgame.tank_player.fire()
            if bullet is not None:
                self.thread_test.zgame.control.bullets.append(bullet)
                self.sem.release('fire')
        elif e.key() == 80:
            self.thread_test.pause()
        elif e.key() == 81: #Q
            if self.thread_test is not None:
                self.thread_test.run = False
                while not self.thread_test.run: #wait
                    pass
                self.signal.emit('game_end')
        else:
            print(e.key())
            
    def paint_slot(self, img, states_):
        self.img = img
        self.states_ = states_
        self.update()

    def start(self, map_id, player_tank_info):
        # if self.thread_test is not None:
        #     self.thread_test.run = False
        #     while not self.thread_test.run: #wait
        #         pass

        self.thread_test = ThreadTest(self.paint_signal, map_id, player_tank_info, self.sem)
        self.thread_test.start()

    def zupdate(self):
        self.update()

class ZWidgetMain(QWidget):
    def __init__(self, signal, trans:Trans):
        super().__init__()

        self.signal = signal
        self.trans = trans
        vbox = QVBoxLayout()
        self.btn_start = QPushButton(self.trans.s('start'))
        self.btn_start.clicked.connect(lambda: self.btn_slot('start'))
        self.btn_set = QPushButton(self.trans.s('setting'))
        self.btn_set.clicked.connect(lambda: self.btn_slot('set'))
        self.btn_exit = QPushButton(self.trans.s('exit'))
        self.btn_exit.clicked.connect(lambda: self.btn_slot('exit'))
        vbox.addWidget(self.btn_start)
        vbox.addWidget(self.btn_set)
        vbox.addWidget(self.btn_exit)

        self.setLayout(vbox)

    def btn_slot(self, cmd):
        self.signal.emit(cmd)

    def zupdate(self):
        self.btn_start.setText(self.trans.s('start'))
        self.btn_set.setText(self.trans.s('setting'))
        self.btn_exit.setText(self.trans.s('exit'))

class ZWidgetSet(QWidget):
    def __init__(self, signal, trans):
        super().__init__()

        self.signal = signal
        self.trans = trans

        hbox = QHBoxLayout()
        self.label = QLabel(self.trans.s('input_level'))
        hbox.addWidget(self.label)
        self.et_map_id = QLineEdit('1')
        hbox.addWidget(self.et_map_id)

        self.btn_ok = QPushButton(self.trans.s('ok'))
        self.btn_ok.clicked.connect(lambda: self.btn_slot('ok'))

        files = os.listdir('./zpic/player_tanks')
        self.ids = []
        for f in files:
            fb = os.path.basename(f)[:-4]
            if fb.endswith('_down'):
                self.ids.append((fb[:-5], os.path.join('./zpic/player_tanks', f)))
        # print(self.ids)

        self.combox = QComboBox()
        self.combox.addItems([k[0] for k in self.ids])
        self.combox.currentIndexChanged.connect(self.slot_change_tank)
        self.img_tank = QLabel()
        # print(pixmap.size(), self.ids[0][1])
        self.img_tank.setPixmap(QPixmap(self.ids[0][1]))
        hbox_player_tank = QHBoxLayout()
        hbox_player_tank.addWidget(self.combox)
        hbox_player_tank.addWidget(self.img_tank)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(hbox_player_tank)
        vbox.addWidget(self.btn_ok)

        self.setLayout(vbox)

    def btn_slot(self, cmd):
        self.signal.emit(cmd)

    def zupdate(self):
        self.label.setText(self.trans.s('input_level'))
        self.btn_ok.setText(self.trans.s('ok'))

    def slot_change_tank(self):
        print(self.combox.currentIndex())
        self.img_tank.setPixmap(QPixmap(self.ids[self.combox.currentIndex()][1]))
        print(QPixmap(self.ids[self.combox.currentIndex()][1]).size())

    def get_tank_info(self):
        info = {
            'prefix': self.ids[self.combox.currentIndex()][1][:-9], #_down.png
            'level': self.combox.currentIndex() + 1
        }
        return info

class ZWidget(QWidget):
    signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.trans = Trans()

        self.img_back = QImage('./zpic/back.png')

        self.signal.connect(self.slot)

        self.widget_main = ZWidgetMain(self.signal, self.trans)
        self.widget_game = ZWidgetGame(self.signal, self.trans)
        self.widget_game.setVisible(False)
        self.widget_set = ZWidgetSet(self.signal, self.trans)
        self.widget_set.setVisible(False)

        hbox = QHBoxLayout()
        hbox.addWidget(self.widget_main)
        hbox.addWidget(self.widget_game)
        hbox.addWidget(self.widget_set)

        self.setLayout(hbox)

        self.resize(470, 540)  # resize
        self.move(600, 200)  # move
        self.setWindowTitle('Tank-War')

        self.show()
        self.paint_back = True
        self.map_id = 2

    def slot(self, cmd):
        print(cmd)
        if cmd == 'start':
           self.widget_main.setVisible(False)
           self.widget_game.setVisible(True)
           map_id = self.widget_set.et_map_id.text()
           player_tank_info = self.widget_set.get_tank_info()
           self.widget_game.start(int(map_id), player_tank_info)
           self.paint_back = False
           self.update()
        elif cmd == 'set':
            self.widget_main.setVisible(False)
            self.widget_set.setVisible(True)
        elif cmd == 'exit':
            self.close()
        elif cmd == 'ok':
            self.widget_set.setVisible(False)
            self.widget_main.setVisible(True)
        elif cmd == 'game_end':
            self.widget_main.setVisible(True)
            self.widget_game.setVisible(False)
            self.paint_back = True

    def keyPressEvent(self, e):
        if e.key() == 76: #l
            self.trans.trans()
            self.widget_main.zupdate()
            self.widget_set.zupdate()
            self.widget_game.zupdate()
            return
        self.widget_game.keyPressEvent(e)

    def paintEvent(self, e):
        rect = e.region().rects()[0] #may contains more rect
        sx, sy, ex, ey = rect.left(), rect.top(), rect.right(), rect.bottom()
        w = ex - sx
        h = ey - sy
        painter = QPainter(self)

        if self.paint_back:
            painter.drawImage(0, 0, self.img_back)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    tm = ZWidget()
    sys.exit(app.exec_())
