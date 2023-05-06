import os

class Trans:
    def __init__(self, language='cn'):
        self.t = {
            'start': ['开始游戏', 'Start'],
            'setting': ['设置', 'Setting'],
            'exit': ['退出', 'Exit'],
            'input_level': ['输入关卡', 'Input Level'],
            'ok': ['确认', 'OK'],
            'pause': ['暂停', 'Pause'],
            'life': ['生命', 'Life'],
            'level': ['子弹等级', 'Bullet Level'],
            'speed': ['子弹速度', 'Bullet Speed'],
            'score': ['分数', 'Score'],
        }

        self.i = 0 if language == 'cn' else 1

    def s(self, key):
        return self.t[key][self.i]
    
    def set_language(self, language):
        self.i = 0 if language == 'cn' else 1

    def trans(self):
        self.i = (self.i + 1) % 2

if __name__ == '__main__':
    trans = Trans()

    print(trans.get_str('ok'))
    trans.trans()
    print(trans.get_str('ok'))
    trans.trans()
    print(trans.get_str('ok'))
