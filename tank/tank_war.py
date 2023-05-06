# coding=utf-8


from tkinter import *
import time, random
import tkinter as tk
# Width and height of the window
WIN_WIDTH = 600
WIN_HEIGHT = 600

# Width and height of enemies' tanks
E_TANK_WIDTH = 45
E_TANK_HEIGHT = 45

# Number of enemy tanks
E_TANK_NUM = 10

# Width and height of the bullet of enemies' tank
E_BULLET_WIDTH = 16
E_BULLET_HEIGHT = 16

# Width and height of player's tank
P_TANK_WIDTH = 45
P_TANK_HEIGHT = 45

P_BULLET_WIDTH = 28
P_BULLET_HEIGHT = 28

# status of tanks
ACTIVE = "active"
EXPLODE = "explode"
USELESS = "useless"

DIRECTIONS = ["up", "left", "down", "right"]

win = Tk()
can = Canvas(win, width=WIN_WIDTH, height=WIN_HEIGHT)
can.pack()


_pos = False

# import background pictures
bg = PhotoImage(file="pic/bg.gif")
can.create_image(0, 0, image=bg, anchor="nw")

# A dictionart to store tanks' images
tanks_img = {}

# images of a blue tank (4 directions)
blue_tank = {}
for d in DIRECTIONS:
    blue_tank[d] = PhotoImage(file="pic/tank_blue_" + d + ".gif")

# images of a black tank (4 directions)
black_tank = {}
for d in DIRECTIONS:
    black_tank[d] = PhotoImage(file="pic/tank_black_" + d + ".gif")

# images of a red tank (4 directions)
red_tank = {}
for d in DIRECTIONS:
    red_tank[d] = PhotoImage(file="pic/tank_red_" + d + ".gif")

# images of a huge(player's) tank (4 directions)
huge_tank = {}
for d in DIRECTIONS:
    huge_tank[d] = PhotoImage(file="pic/tank_huge_" + d + ".gif")

tanks_img["blue"] = blue_tank
tanks_img["red"] = red_tank
tanks_img["black"] = black_tank
tanks_img["huge"] = huge_tank

explosion = []
for i in range(5):
    explosion.append(PhotoImage(file="pic/explosion" + str(i + 1) + ".gif"))

bullets_img = {}

blue_bullet = {}
for d in DIRECTIONS:
    blue_bullet[d] = PhotoImage(file="pic/bullet_blue_" + d + ".gif")

red_bullet = {}
for d in DIRECTIONS:
    red_bullet[d] = PhotoImage(file="pic/bullet_red_" + d + ".gif")

black_bullet = {}
for d in DIRECTIONS:
    black_bullet[d] = PhotoImage(file="pic/bullet_black_" + d + ".gif")

huge_bullet = {}
for d in DIRECTIONS:
    huge_bullet[d] = PhotoImage(file="pic/bullet_huge_" + d + ".gif")

bullets_img["blue"] = blue_bullet
bullets_img["red"] = red_bullet
bullets_img["black"] = black_bullet
bullets_img["huge"] = huge_bullet
from tkinter.filedialog import askopenfilename, asksaveasfilename
player_lives = 10
score = 0
_boss = True

def save_game():
    global player_lives
    global score
    filename = asksaveasfilename(defaultextension='.txt', filetypes=[("history files", ".txt")], initialdir="data/")
    with open(filename, "w") as file:
        
        file.write(f"{player_lives},{score}\n")
        file.close()


def load_game():
    global player_lives
    global score
    filename = askopenfilename(defaultextension='.txt', filetypes=[("history files", ".txt")], initialdir="data/")

    with open(filename) as file:
        for item in file:
            r,s = item.split(",")
            player_lives = int(r)
            score = int(s)
            
        file.close()


def pos(event):
    global _pos
    print("pos")
    _pos = not _pos

def boss(event):
    global _boss
    _boss = not _boss


def create_menu(window):
    MenuBar = Menu(window)

    window.config(menu=MenuBar)
    fileBar = Menu(MenuBar, tearoff=0)
    fileBar.add_command(label="Load", command=load_game)
    fileBar.add_command(label="Save", command=save_game)

    MenuBar.add_cascade(label="Game", menu=fileBar)
create_menu(win)

class Tank():

    def __init__(self, x, y, d, c):
        
        self.color = c
        self.dir = d
        self.speed = 5
        self.drawable = can.create_image(x, y,
                                         image=tanks_img[self.color][self.dir],
                                         anchor="nw")
        self.state = ACTIVE
        self.e_count = 0
 
        if self.color == "huge":
            self.width = P_TANK_WIDTH
            self.height = P_TANK_HEIGHT
        else:
            self.width = E_TANK_WIDTH
            self.height = E_TANK_HEIGHT

    def update_pos_img(self):
        if self.state == USELESS:
            pass

        elif self.state == EXPLODE:
            can.itemconfig(self.drawable, image=explosion[self.e_count])
            self.e_count += 1
            if self.e_count == 5:
                self.state = USELESS
                self.e_count = 0

        elif self.state == ACTIVE:
            t_pos = self.get_pos()

            if t_pos[0] < 0:
                self.dir = random.choice(["down", "up", "right"])
            elif t_pos[1] < 0:
                self.dir = random.choice(["down", "left", "right"])
            elif t_pos[2] > WIN_WIDTH:
                self.dir = random.choice(["down", "up", "left"])
            elif t_pos[3] > WIN_HEIGHT:
                self.dir = random.choice(["left", "up", "right"])

            can.itemconfig(self.drawable, image=tanks_img[self.color][self.dir])

            if self.dir == "up":
                can.move(self.drawable, 0, -self.speed)
            elif self.dir == "left":
                can.move(self.drawable, -self.speed, 0)
            elif self.dir == "down":
                can.move(self.drawable, 0, self.speed)
            elif self.dir == "right":
                can.move(self.drawable, self.speed, 0)

    def create_bullet(self):
        b_w = E_BULLET_WIDTH
        if self.color == "huge":
            b_e = P_BULLET_WIDTH
        else:
            b_w = E_BULLET_WIDTH
            b_h = E_BULLET_HEIGHT

        b_pos = self.get_pos()
        if self.dir == "up":
            b_pos = [b_pos[0] + (self.width-b_w)/2, b_pos[1]]
        elif self.dir == "down":
            b_pos = [b_pos[0] + (self.width-b_w)/2, b_pos[1] + self.height]
        elif self.dir == "left":
            b_pos = [b_pos[0], b_pos[1] + (self.height-b_w)/2]
        elif self.dir == "right":
            b_pos = [b_pos[0] + self.width, b_pos[1] + (self.height - b_w)/2]

        b = Bullet(b_pos, self.color, self.dir, b_w)
        return b


    def get_pos(self):
        b_pos = can.coords(self.drawable)
        b_pos = b_pos + [b_pos[0] + self.width, b_pos[1] + self.height]
        return b_pos


    def set_dir_up(self, event):
        self.dir = "up"


    def set_dir_down(self, event):
        self.dir = "down"

    def set_dir_left(self, event):
        self.dir = "left"

    def set_dir_right(self, event):
        self.dir = "right"


class Bullet():
    def __init__(self, pos, c, d, w):
        self.color = c
        self.width = w
        self.dir = d
        self.imgs = bullets_img[self.color]
        self.speed = 10
        self.drawable = can.create_image(pos[0], pos[1], image=self.imgs[self.dir], anchor="nw")
        self.state = ACTIVE

    def update_pos(self):
        can.itemconfig(self.drawable, image=self.imgs[self.dir])
        if self.dir == "up":
            can.move(self.drawable, 0, -self.speed)
        elif self.dir == "left":
            can.move(self.drawable, -self.speed, 0)
        elif self.dir == "down":
            can.move(self.drawable, 0, self.speed)
        elif self.dir == "right":
            can.move(self.drawable, self.speed, 0)

    def update_state(self):
        b_pos = self.get_pos()

        if b_pos[0] < 0 or b_pos[1] < 0 or \
                        b_pos[2] > WIN_WIDTH or b_pos[3] > WIN_HEIGHT:
            self.state = USELESS

    def get_pos(self):
        b_pos = can.coords(self.drawable)
        b_pos = b_pos + [b_pos[0] + self.width, b_pos[1] + self.width]
        return b_pos

enemy_tanks = []
enemy_bullets = []

for i in range(E_TANK_NUM):
    x = random.randint(0, WIN_WIDTH - E_TANK_WIDTH)
    y = random.randint(0, WIN_HEIGHT - E_TANK_WIDTH)
    d = random.choice(["up", "left", "down", "right"])
    c = random.choice(["red", "blue", "black"])
    enemy_tanks.append(Tank(x, y, d, c))

player_tank = Tank(10, 10, "down", "huge")
player_bullets = []


def shoot(event):
    player_bullets.append(player_tank.create_bullet())


# Bind keys with respond functions
can.bind_all('<Up>', player_tank.set_dir_up)
can.bind_all('<Left>', player_tank.set_dir_left)
can.bind_all('<Down>', player_tank.set_dir_down)
can.bind_all('<Right>', player_tank.set_dir_right)
can.bind_all('<space>', shoot)
can.bind_all('p',pos)
can.bind_all('b',boss)

def is_collide(a, b):
    if a[0] < b[2] and a[1] < b[3] and a[2] > b[0] and a[3] > b[1]:
        return True
    else:
        return False


def delete_useless(obj_list):
    new_obj_list = []
    for obj in obj_list:
        if obj.state == USELESS:
            can.delete(obj.drawable)
            del obj
        else:
            new_obj_list.append(obj)
    return new_obj_list


count = 0

lives_text = can.create_text(10, 10, anchor='nw', text='lives: '+str(player_lives),
                       font=('Consolas', 15))

score_text = can.create_text(150, 10, anchor='nw', text='score: '+str(score),
                       font=('Consolas', 15))

stautes = can.create_text(350, 10, anchor='nw', text='status: '+str(score),
                       font=('Consolas', 15))

running = True

while running:




    # player_tank.update_pos_img()

    if not _pos:
        player_tank.update_pos_img()
        for t in enemy_tanks:
            t.update_pos_img()
            if count % 20 == 0:
                enemy_bullets.append(t.create_bullet())

        for b in enemy_bullets:
            b.update_state()
            b.update_pos()

            if _boss and is_collide(b.get_pos(), player_tank.get_pos()):
                b.state = USELESS
                player_tank.state = EXPLODE

        for b in player_bullets:
            b.update_state()
            b.update_pos()
            for t in enemy_tanks:
                if is_collide(b.get_pos(), t.get_pos()):
                    b.state = USELESS
                    t.state = EXPLODE

    enemy_bullets = delete_useless(enemy_bullets)
    enemy_tanks = delete_useless(enemy_tanks)
    player_bullets = delete_useless(player_bullets)

    # Calculation of hp and score
    score = (E_TANK_NUM - len(enemy_tanks))*10

    if player_tank.state == USELESS:
        player_lives -= 1
        if player_lives > 0:
            player_tank.state = ACTIVE

    can.itemconfig(lives_text, text='lives: '+str(player_lives))
    can.itemconfig(score_text, text='score: '+str(score))
    can.itemconfig(stautes, text='Pause: '+str(_pos))
    # Game is end or not
    if player_tank.state == USELESS:
        can.create_text(WIN_WIDTH/2, WIN_HEIGHT/2,
                    text='YOU LOSE!\nscore:'+str(score),
                    font=('Lithos Pro Regular', 30))
        running = False

    if len(enemy_tanks) < 5:
        for i in range(5):
            x = random.randint(0, WIN_WIDTH - E_TANK_WIDTH)
            y = random.randint(0, WIN_HEIGHT - E_TANK_WIDTH)
            d = random.choice(["up", "left", "down", "right"])
            c = random.choice(["red", "blue", "black"])
            enemy_tanks.append(Tank(x, y, d, c))



    if len(enemy_tanks) == 0:
        can.create_text(WIN_WIDTH / 2, WIN_HEIGHT / 2,
                        text='YOU WIN!\nscore:' + str(score),
                        font=('Lithos Pro Regular', 30))
        running = False

    count += 1
    can.update()
    time.sleep(0.05)


can.mainloop()
