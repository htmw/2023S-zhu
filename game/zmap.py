from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import numpy as np

z1 = [
    '0000000000',
    '0000000000',
    '0000000000',
    '0000000000',
    '0000000000',
    '0000000000',
    '0000000000',
    '0000000000',
    '0000000000',
    '0000000000',
]

z2 = [
    '0000000000',
    '0001110000',
    '0001010000',
    '0001010000',
    '0001010000',
    '0001110000',
    '0000000000',
    '0000000000',
    '0000000000',
    '0000000000',
]

z3 = [
    '0000000000',
    '0001110000',
    '0001010000',
    '0001010000',
    '0001010000',
    '0011011000',
    '0010001000',
    '0011111000',
    '0000000000',
    '0000000000',
]

z4 = [
    '0000000000',
    '0000000000',
    '0001010000',
    '0001010000',
    '0001010000',
    '0000000000',
    '0000000000',
    '0000000000',
    '0000000000',
    '0000000000',
]

z5 = [
    '0000000000',
    '0000010000',
    '0000010000',
    '0000010000',
    '0000010000',
    '0000010000',
    '0000010000',
    '0011111100',
    '0000000000',
    '0000000000',
]

class ZMap():
    def __init__(self, w=450, h=450, step_size=5, z=1):
        assert w % step_size == 0
        assert h % step_size == 0
        self.w, self.h = w, h
        self.step_size = step_size

        self.img_war = QImage('./zpic/war.png')
        self.img_ground = QImage('./zpic/ground.png')
        assert self.img_ground.size() == self.img_ground.size()
        self.war_size = self.img_war.size().width() #tank is a square, this is side length
        
        if z == 1:
            self.map = z1
        elif z == 2:
            self.map = z2
        elif z == 3:
            self.map = z3
        elif z == 4:
            self.map = z4
        elif z == 5:
            self.map = z5

        assert self.h == len(self.map) * self.war_size
        assert self.w == len(self.map[0]) * self.war_size

        self.data = np.zeros((w//step_size, h//step_size), dtype=np.float32)
        assert self.war_size % step_size == 0
        k = self.war_size // step_size
        for y, line in enumerate(self.map):
            for x, p in enumerate(line):
                if p == '0':
                    self.data[y*k:(y+1)*k, x*k:(x+1)*k] = 0
                else:
                    self.data[y*k:(y+1)*k, x*k:(x+1)*k] = 1

        # for y in range(self.data.shape[0]):
        #     for x in range(self.data.shape[1]):
        #         print('%d' % int(self.data[y, x]), end='')
        #     print()

    def paint(self, painter: QPainter):
        for y, line in enumerate(self.map):
            for x, p in enumerate(line):
                if p == '0':
                    painter.drawImage(int(x*self.war_size), int(y*self.war_size), self.img_ground)
                else:
                    painter.drawImage(int(x*self.war_size), int(y*self.war_size), self.img_war)

    def set_map_id(self, id):
        if id == 1:
            self.map = z1
        elif id == 2:
            self.map = z2
        elif id == 3:
            self.map = z3
