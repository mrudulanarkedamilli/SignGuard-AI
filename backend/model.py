
import torch
import torch.nn as nn
import torch.nn.functional as F


class SiameseNetwork(nn.Module):
    def __init__(self):
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4)),

            nn.Flatten(),
            nn.Linear(64 * 4 * 4, 128)
        )

    def forward_once(self, x):
        embedding = self.encoder(x)
        return F.normalize(embedding, p=2, dim=1)

    def forward(self, img1, img2):
        output1 = self.forward_once(img1)
        output2 = self.forward_once(img2)
        return output1, output2


class ContrastiveLoss(nn.Module):
    def __init__(self, margin=1.0):
        super().__init__()
        self.margin = margin

    def forward(self, output1, output2, label):
        distance = F.pairwise_distance(output1, output2)

        loss = (
            label * distance.pow(2)
            + (1 - label)
            * torch.clamp(self.margin - distance, min=0).pow(2)
        )

        return loss.mean()


if __name__ == "__main__":
    model = SiameseNetwork()

    img1 = torch.randn(2, 1, 155, 220)
    img2 = torch.randn(2, 1, 155, 220)

    output1, output2 = model(img1, img2)

    print("Siamese CNN created successfully!")
    print("Embedding 1:", output1.shape)
    print("Embedding 2:", output2.shape)
