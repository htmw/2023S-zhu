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

            # if tank == self.tank_player: #cannot do this here !!!!!!!!!!!!!!!!!!!
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
    def __init__(self, map_id=2):
        step_size = 5

        # self.tank_player = Tank('./tank/pic/tank_huge', './tank/pic/bullet_huge', 200, 390, step_size, 'p')
        self.tank_player = Tank('./tank/pic/tank_huge', './tank/pic/bullet_huge', 300, 390, step_size, 'p')
        # self.tank_player = Tank('./tank/pic/tank_huge', './tank/pic/bullet_huge', 200, 370, step_size, 'p')
        self.tanks = []
        self.tanks.append(self.tank_player)
        self.tanks.append(Tank('./tank/pic/tank_red', './tank/pic/bullet_red', 0, 0, step_size, 'e')) #e: npc, p: player
        # self.tanks.append(Tank('./tank/pic/tank_red', './tank/pic/bullet_red', 0, 370, step_size, 'e')) #e: npc, p: player
        # self.tanks.append(Tank('./tank/pic/tank_blue', './tank/pic/bullet_blue', 200, 0, step_size, 'e'))
        # self.tanks.append(Tank('./tank/pic/tank_black', './tank/pic/bullet_black', 405, 0, step_size, 'e'))
        # self.tanks.append(Tank('./tank/pic/tank_black', './tank/pic/bullet_black', 405, 405, step_size, 'e'))

        # self.tanks[1].change_dir('right')
        # self.tanks[2].change_dir('down')
        # self.tanks[3].change_dir('left')

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
            actions.append(self.calc_best_action(tank, px, py, self.zmap.data))
        return actions
    
    def get_rewards(self):
        px = self.tank_player.x
        py = self.tank_player.y
        best_actions = ['no']
        for idx, tank in enumerate(self.tanks[1:]): #self.tanks[0] is player tank
            # if px <= (tank.x + 4) <= px+11:
            #     # print(f'tank {idx} x ok')
            #     if tank.y < py and tank.dir == 1:
            #         # print(f'tank {idx} x ok and dir ok')
            #         area = self.zmap.data[tank.y:py, tank.x+3:tank.x+6].sum()
            #         if area <= 0:
            #             # print(f'tank {idx} x ok and dir ok and area ok')
            #             if self.actions[idx+1] == 'fire':
            #                 self.rewards[idx+1] = 0.5 #self.tanks[0] is player tank
            #                 continue
            #     elif tank.y > py and tank.dir == 0:
            #         # print(f'tank {idx} x ok and dir ok')
            #         area = self.zmap.data[py:tank.y, tank.x+3:tank.x+6].sum()
            #         if area <= 0:
            #             # print(f'tank {idx} x ok and dir ok and area ok')
            #             if self.actions[idx+1] == 'fire':
            #                 self.rewards[idx+1] = 0.5 #self.tanks[0] is player tank
            #                 continue

            # if py <= (tank.y + 4) <= py+11:
            #     # print(f'tank {idx} y ok')
            #     if tank.x < px and tank.dir == 3:
            #         # print(f'tank {idx} y ok and dir ok')
            #         area = self.zmap.data[tank.y+3:tank.y+6, tank.x:px].sum()
            #         if area <= 0:
            #             # print(f'tank {idx} y ok and dir ok and area ok')
            #             if self.actions[idx+1] == 'fire':
            #                 self.rewards[idx+1] = 0.5 #self.tanks[0] is player tank
            #                 continue
            #     elif tank.x > px and tank.dir == 2:
            #         # print(f'tank {idx} y ok and dir ok')
            #         area = self.zmap.data[tank.y+3:tank.y+6, px:tank.x].sum()
            #         if area <= 0:
            #             # print(f'tank {idx} y ok and dir ok and area ok')
            #             if self.actions[idx+1] == 'fire':
            #                 self.rewards[idx+1] = 0.5 #self.tanks[0] is player tank
            #                 continue

            action = self.calc_best_action(tank, px, py, self.zmap.data)
            best_actions.append(action)
            if self.actions[idx+1] == action:
                self.rewards[idx+1] = 0.3
            else:
                self.rewards[idx+1] = -0.1

            # if px <= (tank.x + 4) <= px+11: #x ok
            #     if self.actions[idx+1] == 'left' or self.actions[idx+1] == 'right':
            #         self.rewards[idx+1] = -0.1
            #     else:
            #         if py < tank.y:
            #             if self.actions[idx+1] == 'up':
            #                 self.rewards[idx+1] = 0.3
            #             else:
            #                 self.rewards[idx+1] = -0.1
            #         elif py > tank.y:
            #             if self.actions[idx+1] == 'down':
            #                 self.rewards[idx+1] = 0.3
            #             else:
            #                 self.rewards[idx+1] = -0.1
            #     continue

            # if py <= (tank.y + 4) <= py+11: # y ok
            #     if self.actions[idx+1] == 'up' or self.actions[idx+1] == 'down':
            #         self.rewards[idx+1] = -0.1
            #     else:
            #         if px < tank.x:
            #             if self.actions[idx+1] == 'left':
            #                 self.rewards[idx+1] = 0.3
            #             else:
            #                 self.rewards[idx+1] = -0.1
            #         elif px > tank.x:
            #             if self.actions[idx+1] == 'right':
            #                 self.rewards[idx+1] = 0.3
            #             else:
            #                 self.rewards[idx+1] = -0.1
            #     continue


            # diff_x = np.abs(px - tank.x)
            # diff_y = np.abs(py - tank.y)
            # if diff_x < diff_y:
            #     if px < tank.x:
            #         if self.actions[idx+1] == 'left':
            #             self.rewards[idx+1] = 0.3
            #         else:
            #             self.rewards[idx+1] = -0.1
            #     elif px > tank.x:
            #         if self.actions[idx+1] == 'right':
            #             self.rewards[idx+1] = 0.3
            #         else:
            #             self.rewards[idx+1] = -0.1
            # else:
            #     if py < tank.y:
            #         if self.actions[idx+1] == 'up':
            #             self.rewards[idx+1] = 0.3
            #         else:
            #             self.rewards[idx+1] = -0.1
            #     elif py > tank.y:
            #         if self.actions[idx+1] == 'down':
            #             self.rewards[idx+1] = 0.3
            #         else:
            #             self.rewards[idx+1] = -0.1

            # if self.rewards[idx+1] <= 0:
            #     self.rewards[idx+1] = -1

        # if self.rewards[1] > 0:
        #     print(self.rewards[1:], self.tanks[1].dir, self.actions[1])
        return self.rewards, best_actions
    
    def change_player_pos_randomly(self):
        if np.random.rand() < 0.3:
            self.tank_player.x = np.random.randint(0, 78)
            self.tank_player.y = np.random.randint(0, 78)
    
class ThreadTrain(QThread):
    def __init__(self, paint_signal):
        super().__init__()

        self.paint_signal = paint_signal
        self.zgame = ZGame()
        self.paint_cnt = 0

        self.brain = Brain()

    def run(self):
        step = 0
        while True:
            states = self.zgame.get_states() #cur state
            actions = self.brain.choose_actions(states)
            # print(actions)

            self.zgame.step(actions) #process
            img = self.zgame.paint()
            states_ = self.zgame.get_states() #next state
            rewards, best_actions = self.zgame.get_rewards() #rewards
            # print(rewards)

            self.brain.store(states, actions[1:], rewards[1:], states_, best_actions[1:]) #skip player tank

            step += 1
            if step >= 100 and step % 5 == 0:
                self.brain.learn()

            states = states_

            self.paint_cnt += 1
            if self.paint_cnt >= 20:
                self.paint_cnt = 0
                self.paint_signal.emit(img, states_, best_actions[1:])

            self.zgame.change_player_pos_randomly()
    
class ZWidget(QWidget):
    paint_signal = pyqtSignal(QImage, list, list)
    def __init__(self):
        super().__init__()
        self.init_ui()

        self.img = None
        self.states_ = None
        self.paint_signal.connect(self.paint_slot)
        self.show()

        self.thread_train = ThreadTrain(self.paint_signal)
        self.thread_train.start()

        self.flag = False

    def init_ui(self):
        self.resize(550, 550)  # resize
        self.move(600, 200)  # move
        self.setWindowTitle('NN Tank Game')

    def paintEvent(self, e):
        rect = e.region().rects()[0] #may contains more rect
        sx, sy, ex, ey = rect.left(), rect.top(), rect.right(), rect.bottom()
        w = ex - sx
        h = ey - sy
        painter = QPainter(self)

        if self.img is not None:
            painter.drawImage(0, 0, self.img)

        # np_img = np.random.randint(0, 255, [90, 90, 3], np.uint8)
        # q_img = QImage(np_img.data, np_img.shape[1], np_img.shape[0], np_img.shape[1]*3, QImage.Format_RGB888)
        # painter.drawImage(5, 455, q_img)

        if self.states_ is None:
            return
        
        for i, ch in enumerate(self.states_[0]): #paint state[0], which is enemy_0's state
            np_img = np.zeros((90, 90, 3), np.uint8)
            np_img[:, :, 0] = ch * 200
            q_img = QImage(np_img.data, np_img.shape[1], np_img.shape[0], np_img.shape[1]*3, QImage.Format_RGB888)
            painter.drawImage(5 + i * (90 + 5), 455, q_img)

        i = 3
        for state in self.states_[1:]: #ch1 and ch2 are the same for all states
            np_img = np.zeros((90, 90, 3), np.uint8)
            np_img[:, :, 0] = state[2, :, :] * 200
            q_img = QImage(np_img.data, np_img.shape[1], np_img.shape[0], np_img.shape[1]*3, QImage.Format_RGB888)
            painter.drawImage(5 + i * (90 + 5), 455, q_img)
            i += 1

    def keyPressEvent(self, e):
        if e.key() == 49: #1
            print('train start')
            # self.thread_train.start()
        elif e.key() == 50: #2
            self.thread_train.zgame.tanks[1].x, self.thread_train.zgame.tanks[1].y = 0, 0
            self.thread_train.zgame.tanks[2].x, self.thread_train.zgame.tanks[2].y = 40, 0
            self.thread_train.zgame.tanks[3].x, self.thread_train.zgame.tanks[3].y = 80, 0
        elif e.key() == 16777235: #up
            if self.thread_train.zgame.tank_player.dir != 0:
                self.thread_train.zgame.tank_player.change_dir('up')
            else:
                self.thread_train.zgame.tank_player.move_forward(self.thread_train.zgame.zmap.data)
        elif e.key() == 16777237: #down
            if self.thread_train.zgame.tank_player.dir != 1:
                self.thread_train.zgame.tank_player.change_dir('down')
            else:
                self.thread_train.zgame.tank_player.move_forward(self.thread_train.zgame.zmap.data)
        elif e.key() == 16777234: #left
            if self.thread_train.zgame.tank_player.dir != 2:
                self.thread_train.zgame.tank_player.change_dir('left')
            else:
                self.thread_train.zgame.tank_player.move_forward(self.thread_train.zgame.zmap.data)
        elif e.key() == 16777236: #right
            if self.thread_train.zgame.tank_player.dir != 3:
                self.thread_train.zgame.tank_player.change_dir('right')
            else:
                self.thread_train.zgame.tank_player.move_forward(self.thread_train.zgame.zmap.data)

    def paint_slot(self, img, states_, best_actions):
        # if not self.flag:
        #     self.flag = True
        # else:
        #     return
        self.img = img
        self.states_ = states_
        # print(best_actions)
        self.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    tm = ZWidget()
    sys.exit(app.exec_())
