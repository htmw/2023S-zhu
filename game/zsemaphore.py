from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class ZSemaphore(QSemaphore):
    def __init__(self, value=0):
        super().__init__(value)

        self.data = []
        self.lock = QMutex()

    def acquire(self):
        super().acquire()
        self.lock.lock()
        data = self.data.pop(0)
        self.lock.unlock()
        return data

    def release(self, data):
        self.lock.lock()
        self.data.append(data)
        self.lock.unlock()
        return super().release(1)

    # def clear(self):
    #     while super().acquire(blocking=False) is True:
    #         pass
    #     self.lock.lock()
    #     self.data = []
    #     self.lock.unlock()

if __name__ == '__main__':
    zsem = ZSemaphore()

    zsem.release(['sssss', 34])
    zsem.release(2)
    # zsem.clear()
    ret = zsem.acquire()
    print(ret)
    ret = zsem.acquire()
    print(ret)
    ret = zsem.acquire()
    print(ret)
