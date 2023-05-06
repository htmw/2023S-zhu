from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import sys
sys.path.append('./')
from game.bullet import Bullet

class Tank():
    def __init__(self, tank_img_prefix, bullet_img_prefix, x, y, step_size, who_am_i, life=3, level=1):
        self.imgs = []
        if tank_img_prefix.startswith('./tank/pic'):
            self.imgs.append(QImage(tank_img_prefix + '_up.gif'))
            self.imgs.append(QImage(tank_img_prefix + '_down.gif'))
            self.imgs.append(QImage(tank_img_prefix + '_left.gif'))
            self.imgs.append(QImage(tank_img_prefix + '_right.gif'))
        else:
            self.imgs.append(QImage(tank_img_prefix + '_up.png'))
            self.imgs.append(QImage(tank_img_prefix + '_down.png'))
            self.imgs.append(QImage(tank_img_prefix + '_left.png'))
            self.imgs.append(QImage(tank_img_prefix + '_right.png'))

        if self.imgs[0].size().width() != 45 and self.imgs[0].size().width() != 60:
            for i in range(len(self.imgs)):
                p = QPixmap(self.imgs[i])
                p = p.scaled(60, 60)
                self.imgs[i] = QImage(p)
                # print(self.imgs[i].size())

        self.bullet_img_prefix = bullet_img_prefix

        self.tank_size = self.imgs[0].size().width() #tank is a square, this is side length
        self.x, self.y = x // step_size, y // step_size
        self.step_size = step_size #move 5 pixels per time
        self.dir = 0 #0 1 2 3 : up down left right
        assert self.tank_size % self.step_size == 0
        self.tank_size //= self.step_size

        self.fire_t = 0
        self.who_am_i = who_am_i
        self.life = life
        self.level = level
        self.fire_speed = 1
        self.score = 0

    def paint(self, painter: QPainter):
        # painter.drawImage(self.x-self.tank_size//2, self.y-self.tank_size//2, self.imgs[self.dir])
        painter.drawImage(self.x*self.step_size, self.y*self.step_size, self.imgs[self.dir])

    def move(self, zmap, dir):
        if dir == 'up':
            self.dir = 0
            return self.move_up(zmap)
        elif dir == 'down':
            self.dir = 1
            return self.move_down(zmap)
        elif dir == 'left':
            self.dir = 2
            return self.move_left(zmap)
        elif dir == 'right':
            self.dir = 3
            return self.move_right(zmap)        
        
    def move_up(self, zmap):
        if self.y <= 0:
            return False
        for i in range(self.tank_size):
            x = self.x + i
            # print(zmap[self.y-1, x], self.y-1, x)
            if zmap[self.y-1, x] == 1:
                return False
        self.y -= 1
        return True
    
    def move_down(self, zmap):
        if self.y >= (zmap.shape[0] - self.tank_size):
            return False
        for i in range(self.tank_size):
            x = self.x + i
            # print(zmap[self.y+9, x], self.y+9, x)
            if zmap[self.y+self.tank_size, x] == 1:
                return False
        self.y += 1
        return True
    
    def move_left(self, zmap):
        if self.x <= 0:
            return False
        for i in range(self.tank_size):
            y = self.y + i
            # print(zmap[self.y-1, x], self.y-1, x)
            if zmap[y, self.x-1] == 1:
                return False
        self.x -= 1
        return True
    
    def move_right(self, zmap):
        if self.x >= (zmap.shape[1] - self.tank_size):
            return False
        for i in range(self.tank_size):
            y = self.y + i
            # print(zmap[self.y+9, x], self.y+9, x)
            if zmap[y, self.x+9] == 1:
                return False
        self.x += 1
        return True

    def fire(self):
        if self.fire_t > 0:
            return None
        self.fire_t = 10
        if self.dir == 0:
            bullet = Bullet(self.bullet_img_prefix, self.dir, self.x+3, self.y, self.step_size, self.who_am_i, self.level)
        if self.dir == 1:
            bullet = Bullet(self.bullet_img_prefix, self.dir, self.x+3, self.y+9, self.step_size, self.who_am_i, self.level)
        if self.dir == 2:
            bullet = Bullet(self.bullet_img_prefix, self.dir, self.x, self.y+3, self.step_size, self.who_am_i, self.level)
        if self.dir == 3:
            bullet = Bullet(self.bullet_img_prefix, self.dir, self.x+9, self.y+3, self.step_size, self.who_am_i, self.level)
        return bullet