from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

import random

class Stuff():
    def __init__(self, x, y):
        self.x, self.y = x, y

        self.stuff_infos = [
            ('./zpic/level.png', 'level'),
            ('./zpic/speed.png', 'speed'),
            ('./zpic/score.png', 'score'),
        ]
        stuff_info = random.choice(self.stuff_infos)
        self.img = QImage(stuff_info[0])
        self.type = stuff_info[1]

    def paint(self, painter: QPainter):
        painter.drawImage(self.x*5, self.y*5, self.img)

    def set_pos(self, x, y):
        stuff_info = random.choice(self.stuff_infos)
        self.img = QImage(stuff_info[0])
        self.type = stuff_info[1]
        self.x, self.y = x, y