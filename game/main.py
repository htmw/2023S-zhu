import sys
import random
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

sys.path.append('./')
from game.tank import Tank, Bullet
from game.zmap import ZMap

class ThreadBullet(QThread):
    signal_bullet = pyqtSignal(Bullet)

    def __init__(self,
                zmap,
                tanks,
                signal_update):
        super().__init__()
        self.zmap = zmap
        self.tanks = tanks
        self.bullets = []
        self.signal_update = signal_update

        self.signal_bullet.connect(self.slot_bullet)

    def run(self):
        while True:
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
                # print(idx, end = ' ')
                self.bullets.pop(idx)

            # print(len(self.bullets))
            self.signal_update.emit()
            self.usleep(100000)

    def slot_bullet(self, bullet):
        self.bullets.append(bullet)

class ThreadControl(QThread):
    def __init__(self,
                zmap,
                tanks,
                tank_player,
                signal_update,
                signal_bullet):
        super().__init__()
        self.zmap = zmap
        self.tanks = tanks
        self.tank_player = tank_player
        self.signal_update = signal_update
        self.signal_bullet = signal_bullet

    def run(self):
        random.seed(1234)
        k = 0
        while True:
            # delete_idx = []
            for i, tank in enumerate(self.tanks):
                if tank.life == 0:
                    # delete_idx.append(i)
                    tank.life = 1
                    if tank == self.tank_player:
                        tank.x = 78
                        tank.y = 78
                    else:
                        tank.x = 0
                        tank.y = 0
                    continue

                if tank == self.tank_player:
                    continue
                # tank.change_dir('left') #for debug

                action = random.choice(['change_dir', 'move', 'move', 'move', 'fire'])
                # action = 'fire' #for debug
                # print(action)
                if action == 'move':
                    tank.move_forward(self.zmap)
                elif action == 'change_dir':
                    dir = random.choice(['up', 'down', 'left', 'right'])
                    tank.change_dir(dir)
                elif action == 'fire':
                    bullet = tank.fire()
                    if bullet is not None:
                        self.signal_bullet.emit(bullet)

                # tank.change_dir('right')
                # tank.move_forward(self.zmap)

                # k += 1
                # if k >= 30:
                #     k = 0
                #     self.tanks.pop(0)

            # for idx in delete_idx[::-1]:
                # self.tanks.pop(idx)

            self.signal_update.emit()
            self.usleep(100000)

class ZGame(QWidget):
    signal_update = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

        step_size = 5

        self.tank_player = Tank('./tank/pic/tank_huge', './tank/pic/bullet_huge', 200, 390, step_size, 'p')
        # self.tank_player = Tank('./tank/pic/tank_red', './tank/pic/bullet_black', 240, 180, step_size, 'p')
        self.tanks = []
        self.tanks.append(self.tank_player)
        self.tanks.append(Tank('./tank/pic/tank_red', './tank/pic/bullet_red', 0, 0, step_size, 'e')) #e: npc, p: player
        self.tanks.append(Tank('./tank/pic/tank_blue', './tank/pic/bullet_blue', 200, 0, step_size, 'e'))
        self.tanks.append(Tank('./tank/pic/tank_black', './tank/pic/bullet_black', 405, 0, step_size, 'e'))

        self.zmap = ZMap(450, 450, step_size, 1)
        self.show()

        self.signal_update.connect(self.slot_update)
        self.thread_bullet = ThreadBullet(self.zmap.data, self.tanks, self.signal_update)
        self.thread_bullet.start()

        self.thread_control = ThreadControl(self.zmap.data, self.tanks, self.tank_player, self.signal_update, self.thread_bullet.signal_bullet)
        self.thread_control.start()

        #for debug
        # self.tanks_enemy[0].change_dir('right')
        # self.thread_bullet.bullets.append(self.tanks_enemy[0].fire())

    def init_ui(self):
        self.resize(450, 450)  # resize
        self.move(600, 300)  # move
        self.setWindowTitle('NN Tank Game')

    def paintEvent(self, e):
        rect = e.region().rects()[0] #may contains more rect
        sx, sy, ex, ey = rect.left(), rect.top(), rect.right(), rect.bottom()
        w = ex - sx
        h = ey - sy

        painter = QPainter(self)
        # painter.begin()

        self.zmap.paint(painter)
        for tank in self.thread_control.tanks:
            tank.paint(painter)

        for tank in self.thread_bullet.bullets:
            tank.paint(painter)

        painter.end()

    def keyPressEvent(self, e):
        if e.key() == 16777235: #up
            if self.tank_player.dir != 0:
                self.tank_player.change_dir('up')
            else:
                self.tank_player.move_forward(self.zmap.data)
        elif e.key() == 16777237: #down
            if self.tank_player.dir != 1:
                self.tank_player.change_dir('down')
            else:
                self.tank_player.move_forward(self.zmap.data)
        elif e.key() == 16777234: #left
            if self.tank_player.dir != 2:
                self.tank_player.change_dir('left')
            else:
                self.tank_player.move_forward(self.zmap.data)
        elif e.key() == 16777236: #right
            if self.tank_player.dir != 3:
                self.tank_player.change_dir('right')
            else:
                self.tank_player.move_forward(self.zmap.data)
        elif e.key() == 32:
            bullet = self.tank_player.fire()
            if bullet is not None:
                self.thread_bullet.bullets.append(bullet)
            else:
                self.tank_player.fire_t = 0

    def slot_update(self):
        self.update()
        # print(self.tanks_enemy)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    tm = ZGame()
    sys.exit(app.exec_())
