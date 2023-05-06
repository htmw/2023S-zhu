import sys
import random
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

sys.path.append('./')
from game.tank import Tank, Bullet
from game.zmap import ZMap

from nn.brain import Brain

class ZControl:
    def __init__(self,
                zmap,
                tanks,
                tank_player):
        self.zmap = zmap
        self.tanks = tanks
        self.tank_player = tank_player

        self.bullets = []
        random.seed(1234)

    def update_bullet(self):
        delete_idx = []
        for idx, bullet in enumerate(self.bullets):
            if not bullet.move_forward(self.zmap, self.tanks):
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
                tank.life = 1
                if tank == self.tank_player:
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
                continue

            # if tank == self.tank_player:
            #     if np.random.rand() < 0.5:
            #         tank.x = np.random.randint(0, 78)
            #         tank.y = np.random.randint(0, 78)

            # if tank == self.tank_player: #don't update player tank
            #     continue
            # tank.change_dir('left') #for debug

            # action = random.choice(['change_dir', 'move', 'move', 'move', 'fire'])
            # action = 'fire' #for debug
            # print(action)
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

class ZGame:
    def __init__(self, map_id=1):
        step_size = 5

        self.tank_player = Tank('./tank/pic/tank_huge', './tank/pic/bullet_huge', 300, 390, step_size, 'p')
        self.tanks = []
        self.tanks.append(self.tank_player)
        self.tanks.append(Tank('./tank/pic/tank_red', './tank/pic/bullet_red', 0, 0, step_size, 'e')) #e: npc, p: player
        self.tanks.append(Tank('./tank/pic/tank_blue', './tank/pic/bullet_blue', 200, 0, step_size, 'e'))
        self.tanks.append(Tank('./tank/pic/tank_black', './tank/pic/bullet_black', 405, 0, step_size, 'e'))

        self.zmap = ZMap(450, 450, step_size, map_id)
        self.control = ZControl(self.zmap.data, self.tanks, self.tank_player)
        self.rewards = [0.0 for _ in range(len(self.tanks))]

    def paint(self, w=450, h=450):
        img = QImage(w, h, QImage.Format.Format_RGB888)
        painter = QPainter(img)

        self.zmap.paint(painter)
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
            tank.fire_t -= 1

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
    
class ThreadTest(QThread):
    def __init__(self, paint_signal, map_id):
        super().__init__()

        self.paint_signal = paint_signal
        self.zgame = ZGame(map_id)
        self.paint_cnt = 0

        self.brain = Brain()
        self.brain.load('./model_eval_00001000.ckpt')

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

            self.usleep(200000)
        self.run = True
    
class ZWidget(QMainWindow):
    paint_signal = pyqtSignal(QImage, list)
    def __init__(self):
        super().__init__()
        self.init_ui()

        self.init_menu()

        self.img = None
        self.states_ = None
        self.paint_signal.connect(self.paint_slot)
        self.show()

        # self.thread_test = ThreadTest(self.paint_signal, 1)
        # self.thread_test.start()
        self.thread_test = None

    def init_ui(self):
        self.resize(550, 600)  # resize
        self.move(600, 200)  # move
        self.setWindowTitle('NN Tank Game')

    def init_menu(self):
        menu_bar = self.menuBar()
        menu1 = menu_bar.addMenu('关卡')
        action1 = menu1.addAction('第1关')
        action1.triggered.connect(lambda: self.slot_menu(1))
        action2 = menu1.addAction('第2关')
        action2.triggered.connect(lambda: self.slot_menu(2))
        action3 = menu1.addAction('第3关')
        action3.triggered.connect(lambda: self.slot_menu(3))

    def paintEvent(self, e):
        rect = e.region().rects()[0] #may contains more rect
        sx, sy, ex, ey = rect.left(), rect.top(), rect.right(), rect.bottom()
        w = ex - sx
        h = ey - sy
        painter = QPainter(self)

        if self.img is not None:
            painter.drawImage(0, 25, self.img)

        # np_img = np.random.randint(0, 255, [90, 90, 3], np.uint8)
        # q_img = QImage(np_img.data, np_img.shape[1], np_img.shape[0], np_img.shape[1]*3, QImage.Format_RGB888)
        # painter.drawImage(5, 455, q_img)

        if self.states_ is None:
            return
        
        for i, ch in enumerate(self.states_[0]): #paint state[0], which is enemy_0's state
            np_img = np.zeros((90, 90, 3), np.uint8)
            np_img[:, :, 0] = ch * 200
            q_img = QImage(np_img.data, np_img.shape[1], np_img.shape[0], np_img.shape[1]*3, QImage.Format_RGB888)
            painter.drawImage(5 + i * (90 + 5), 505, q_img)

        i = 3
        for state in self.states_[1:]: #ch1 and ch2 are the same for all states
            np_img = np.zeros((90, 90, 3), np.uint8)
            np_img[:, :, 0] = state[2, :, :] * 200
            q_img = QImage(np_img.data, np_img.shape[1], np_img.shape[0], np_img.shape[1]*3, QImage.Format_RGB888)
            painter.drawImage(5 + i * (90 + 5), 505, q_img)
            i += 1

    def keyPressEvent(self, e):
        if e.key() == 49: #1
            print('train start')
            # self.thread_test.start()
        elif e.key() == 50: #2
            self.thread_test.zgame.tanks[1].x, self.thread_test.zgame.tanks[1].y = 0, 0
            # self.thread_test.zgame.tanks[2].x, self.thread_test.zgame.tanks[2].y = 40, 0
            # self.thread_test.zgame.tanks[3].x, self.thread_test.zgame.tanks[3].y = 80, 0
        elif e.key() == 16777235: #up
            self.thread_test.zgame.tank_player.move(self.thread_test.zgame.zmap.data, 'up')
        elif e.key() == 16777237: #down
            self.thread_test.zgame.tank_player.move(self.thread_test.zgame.zmap.data, 'down')
        elif e.key() == 16777234: #left
            self.thread_test.zgame.tank_player.move(self.thread_test.zgame.zmap.data, 'left')
        elif e.key() == 16777236: #right
            self.thread_test.zgame.tank_player.move(self.thread_test.zgame.zmap.data, 'right')
        elif e.key() == 32:
            bullet = self.thread_test.zgame.tank_player.fire()
            if bullet is not None:
                self.thread_test.zgame.control.bullets.append(bullet)

    def paint_slot(self, img, states_):
        self.img = img
        self.states_ = states_
        self.update()

    def slot_menu(self, action):
        if self.thread_test is not None:
            self.thread_test.run = False
            while not self.thread_test.run: #wait
                pass
        if action == 1:
            # self.thread_test.zgame.zmap.set_map_id(1)
            self.thread_test = ThreadTest(self.paint_signal, 1)
        elif action == 2:
            # self.thread_test.zgame.zmap.set_map_id(2)
            self.thread_test = ThreadTest(self.paint_signal, 2)
        elif action == 3:
            # self.thread_test.zgame.zmap.set_map_id(3)
            self.thread_test = ThreadTest(self.paint_signal, 3)
        self.thread_test.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    tm = ZWidget()
    sys.exit(app.exec_())
