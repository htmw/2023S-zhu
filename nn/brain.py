import numpy as np
import torch
import random

import sys
sys.path.append('./')
from nn.model import Model

action_names = ['up', 'down', 'left', 'right', 'fire']
action_ids = {
    'up': 0,
    'down': 1,
    'left': 2,
    'right': 3,
    'fire': 4
}

class Brain():
    def __init__(self):
        self.model_eval = Model()
        self.model_target = Model()
        self.model_target.eval()
        for p in self.model_target.parameters():
            p.requires_grad = False

        self.optimizer = torch.optim.Adam(self.model_eval.parameters(), lr= 0.001)

        self.mem = []
        self.learn_step = 0
        self.loss_fn = torch.nn.MSELoss()

    def choose_actions(self, states: list, ratio=0.9):
        states = np.stack((states), axis=0).astype(np.float32)
        states = torch.from_numpy(states)
        actions = self.model_eval(states)

        actions_out = []
        # actions_out.append(random.choice(['up', 'down', 'left', 'right', 'move', 'move', 'move']))#, 'fire'])) #for player tank, move randomly
        actions_out.append('no')#, 'fire'])) #for player tank, move randomly
        for action in actions:
            if np.random.rand() < ratio:
                max_idx = action.argmax().detach().numpy()
                actions_out.append(action_names[max_idx])
            else:
                actions_out.append(random.choice(action_names))
        return actions_out
    
    def store(self, states, actions, rewards, states_, best_actions):
        # print(len(states), len(states_), len(actions), len(rewards))
        for i in range(len(states)):
            self.mem.append((states[i], actions[i], rewards[i], states_[i], best_actions[i]))

        if len(self.mem) > 1000:
            self.mem = self.mem[-1000:]
        # print(len(self.mem))

    def learn(self):
        batch = random.sample(self.mem, 32)
        states = [b[0] for b in batch]
        states = np.stack((states), axis=0).astype(np.float32)
        states = torch.from_numpy(states)
        # print(states.shape)

        evals = self.model_eval(states)

        states_ = [b[3] for b in batch]
        states_ = np.stack((states_), axis=0).astype(np.float32)
        states_ = torch.from_numpy(states_)
        # print(states_.shape)

        targets = self.model_target(states_)
        targets = targets.max(dim=-1).values

        rewards = [b[2] for b in batch]
        targets = torch.Tensor(rewards) + 0.6 * targets

        eval_real = torch.zeros_like(targets)
        for i, b in enumerate(batch):
            action_id = action_ids[b[1]]
            eval_real[i] = evals[i][action_id]

        loss = torch.mean(torch.abs(eval_real - targets))

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        # print(self.learn_step, loss.detach().cpu().numpy())

        self.learn_step += 1
        if self.learn_step % 500 == 0:
            self.update_target_net_and_save()

    def learn_v2(self):
        batch = random.sample(self.mem, 32)
        states = [b[0] for b in batch]
        states = np.stack((states), axis=0).astype(np.float32)
        states = torch.from_numpy(states)
        # print(states.shape)

        evals = self.model_eval(states)
        best = [action_ids[b[-1]] for b in batch]
        targets = torch.zeros_like(evals)
        acc = 0
        for i, b in enumerate(best):
            targets[i][b] = 1
            if b == evals[i].argmax():
                acc += 1
        loss = self.loss_fn(evals, targets)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        print(self.learn_step, loss.detach().cpu().numpy(), acc/32)

        self.learn_step += 1
        if self.learn_step % 500 == 0:
            self.update_target_net_and_save()

    def update_target_net_and_save(self):
        self.model_target.load_state_dict(self.model_eval.state_dict())
        torch.save(self.model_eval.state_dict(), './model_eval_%08d.ckpt' % self.learn_step)

    def load(self, ckpt):
        state_dict = torch.load(ckpt)
        # print(state_dict)
        self.model_eval.load_state_dict(state_dict)

if __name__ == '__main__':
    states = [np.zeros((3, 90, 90)), np.zeros((3, 90, 90))]

    brain = Brain()
    brain.choose_actions(states)