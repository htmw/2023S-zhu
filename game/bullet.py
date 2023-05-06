from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class Bullet():
    def __init__(self, img_prefix, dir, x, y, step_size, who_am_i, level):
        self.dir = dir
        self.imgs = []
        if self.dir == 0:
            self.imgs.append(QImage(img_prefix + '_up.gif'))
        if self.dir == 1:
            self.imgs.append(QImage(img_prefix + '_down.gif'))
        if self.dir == 2:
            self.imgs.append(QImage(img_prefix + '_left.gif'))
        if self.dir == 3:
            self.imgs.append(QImage(img_prefix + '_right.gif'))
        self.imgs.append(QImage('./tank/pic/explosion1.gif'))
        self.imgs.append(QImage('./tank/pic/explosion2.gif'))
        self.imgs.append(QImage('./tank/pic/explosion3.gif'))
        self.imgs.append(QImage('./tank/pic/explosion4.gif'))
        self.imgs.append(QImage('./tank/pic/explosion5.gif'))

        self.bullet_size = self.imgs[0].size().width() #tank is a square, this is side length
        self.x, self.y = x, y
        self.step_size = step_size #move 5 pixels per time
        # assert self.bullet_size % self.step_size == 0
        self.bullet_size //= self.step_size

        self.state = 0 #initial state
        self.who_am_i = who_am_i
        self.level = level

    def paint(self, painter: QPainter):
        if self.state == 0:
            painter.drawImage(self.x*self.step_size, self.y*self.step_size, self.imgs[self.state])
        elif self.state <= 5:
            k = 4 - self.bullet_size // 2
            if self.dir == 0:
                x = (self.x - k) * self.step_size
                y = (self.y - 5) * self.step_size
            if self.dir == 1:
                x = (self.x - k) * self.step_size
                y = (self.y) * self.step_size
            if self.dir == 2:
                x = (self.x - 5) * self.step_size
                y = (self.y - k) * self.step_size
            if self.dir == 3:
                x = (self.x) * self.step_size
                y = (self.y - k) * self.step_size
            painter.drawImage(x, y, self.imgs[self.state])

    def move_forward(self, zmap, tanks=[]):
        if self.state != 0:
            return False
        if self.dir == 0:
            return self.move_up(zmap, tanks)
        if self.dir == 1:
            return self.move_down(zmap, tanks)
        if self.dir == 2:
            return self.move_left(zmap, tanks)
        if self.dir == 3:
            return self.move_right(zmap, tanks)
        
    def move_up(self, zmap, tanks):
        if self.y <= 0:
            return False
        for i in range(self.bullet_size):
            x = self.x + i
            # print(zmap[self.y-1, x], self.y-1, x)
            if zmap[self.y-1, x] == 1:
                return False
            
        for tank in tanks:
            # print(tank.x, self.x, tank.tank_size, self.bullet_size)
            if self.who_am_i == tank.who_am_i:
                continue
            if self.x + self.bullet_size > tank.x and self.x < tank.x+tank.tank_size and self.y + self.bullet_size > tank.y and self.y < tank.y+tank.tank_size:
                tank.life -= self.level
                # print('uuuuuuu', tank.life)
                return False
        self.y -= 2
        return True
    
    def move_down(self, zmap, tanks):
        if self.y >= (zmap.shape[0] - self.bullet_size):
            return False
        for i in range(self.bullet_size):
            x = self.x + i
            # print(zmap[self.y+9, x], self.y+9, x)
            if zmap[self.y+self.bullet_size, x] == 1:
                return False
        for tank in tanks:
            if self.who_am_i == tank.who_am_i:
                continue
            if self.x + self.bullet_size > tank.x and self.x < tank.x+tank.tank_size and self.y + self.bullet_size > tank.y and self.y < tank.y+tank.tank_size:
                tank.life -= self.level
                # print('ddddddd', tank.life)
                return False
        self.y += 2
        return True
    
    def move_left(self, zmap, tanks):
        if self.x <= 0:
            return False
        for i in range(self.bullet_size):
            y = self.y + i
            # print(zmap[self.y-1, x], self.y-1, x)
            if zmap[y, self.x-1] == 1:
                return False
        for tank in tanks:
            if self.who_am_i == tank.who_am_i:
                continue
            if self.x + self.bullet_size > tank.x and self.x < tank.x+tank.tank_size and self.y + self.bullet_size > tank.y and self.y < tank.y+tank.tank_size:
                tank.life -= self.level
                # print('lllll', tank.life)
                return False
        self.x -= 2
        return True
    
    def move_right(self, zmap, tanks):
        if self.x >= (zmap.shape[1] - self.bullet_size):
            return False
        for i in range(self.bullet_size):
            y = self.y + i
            # print(zmap[self.y+9, x], self.y+9, x)
            if zmap[y, self.x+self.bullet_size] == 1:
                return False
        for tank in tanks:
            if self.who_am_i == tank.who_am_i:
                continue
            if self.x + self.bullet_size > tank.x and self.x < tank.x+tank.tank_size and self.y + self.bullet_size > tank.y and self.y < tank.y+tank.tank_size:
                tank.life -= self.level
                # print('rrrrrr', tank.life)
                return False
        self.x += 2
        return True
