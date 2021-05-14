import torch
import torch.nn as nn
import torch.nn.functional as F

dev = "cuda" if torch.cuda.is_available() else "cpu"
device = torch.device(dev)

class OhemCELoss(nn.Module):

    def __init__(self, thresh, ignore_lb=255):
        super(OhemCELoss, self).__init__()
        self.thresh = -torch.log(torch.tensor(thresh, requires_grad=False, dtype=torch.float)).to(device)
        self.ignore_lb = ignore_lb
        self.criteria = nn.CrossEntropyLoss(ignore_index=ignore_lb, reduction='none')

    def forward(self, logits, labels):

        # convert to long tensor (required by cross entropy)
        labels = labels.long()
        loss = self.criteria(logits, labels).view(-1)

        n_min = labels[labels != self.ignore_lb].numel() // 16
        loss_hard = loss[loss > self.thresh]
        if loss_hard.numel() < n_min:
            loss_hard, _ = loss.topk(n_min)
        return torch.mean(loss_hard)

    def simple_cross_entropy(self, logits, labels):
        loss = self.criteria(logits, labels).view(-1)
        return torch.mean(loss)
