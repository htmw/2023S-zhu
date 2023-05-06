import torch

class Model(torch.nn.Module):
    def __init__(self):
        super().__init__()

        self.conv1 = torch.nn.Conv2d(in_channels=3, out_channels=8, kernel_size=(5, 5), stride=(2, 2))
        self.act1 = torch.nn.PReLU(8)
        self.conv2 = torch.nn.Conv2d(in_channels=8, out_channels=8, kernel_size=(5, 5), stride=(2, 2))
        self.act2 = torch.nn.PReLU(8)
        self.conv3 = torch.nn.Conv2d(in_channels=8, out_channels=8, kernel_size=(5, 5), stride=(2, 2))
        self.act3 = torch.nn.PReLU(8)
        self.linear_out = torch.nn.Linear(in_features=8*8*8, out_features=5)
        # self.act_out = torch.nn.Sigmoid()

    def forward(self, inputs):
        x = self.conv1(inputs)
        x = self.act1(x)
        x = self.conv2(x)
        x = self.act2(x)
        x = self.conv3(x)
        x = self.act3(x)
        x = x.reshape(x.shape[0], -1)
        x = self.linear_out(x)
        # x = self.act_out(x)
        # print(x.shape)
        return x

if __name__ == '__main__':
    pass