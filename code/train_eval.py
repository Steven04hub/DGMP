from __future__ import division
import time
import os
#os.environ['CUDA_VISIBLE_DEVICES'] = '3,0'
import torch
import torch.nn.functional as F
from torch import tensor
from torch.optim import Adam, SGD
from sklearn.metrics import roc_auc_score, average_precision_score

def run(dataset, gpu_no, model, epochs, lr, weight_decay, early_stopping, logger=None):

    if gpu_no >= 0 and torch.cuda.is_available():
        torch.cuda.set_device(gpu_no)
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')

    valacc, val_losses, accs, durations = [], [], [], []
    # epoch_time = []
    data = dataset[0]
    #data = cv_data[runs]
    
    data = data.to(device)
 
    model.to(device).reset_parameters()
    
    optimizer = Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    if torch.cuda.is_available():
        torch.cuda.synchronize()

    t_start = time.perf_counter()

    best_val_loss = float('inf')
    test_acc = 0
    val_loss_history = []
    flag = 0
    
    for epoch in range(1, epochs + 1):
        flag = flag + 1
        train(model, optimizer, data)
        eval_info,logits = evaluate(model, data)
        eval_info['epoch'] = epoch

        if logger is not None:
            logger(eval_info)

        if eval_info['val_loss'] < best_val_loss:
            best_val_loss = eval_info['val_loss']
            val_acc = eval_info['val_acc']
            test_acc = eval_info['test_acc']
        # print(epoch)
        print(best_val_loss, test_acc)
        val_loss_history.append(eval_info['val_loss'])
        if early_stopping > 0 and epoch > epochs // 2:
            tmp = tensor(val_loss_history[-(early_stopping + 1):-1])
            if eval_info['val_loss'] > tmp.mean().item():
                break

        if torch.cuda.is_available():
            torch.cuda.synchronize()

        t_end = time.perf_counter()

        valacc.append(val_acc)
        val_losses.append(best_val_loss)
        accs.append(test_acc)
        durations.append(t_end - t_start)
        # print((t_end - t_start)/flag)
        # exit()

    vacc, loss, acc, duration = tensor(valacc), tensor(val_losses), tensor(accs), tensor(durations)

    print('Val Acc: {:.4f}, Val Loss: {:.4f}, Test Accuracy: {:.4f} ± {:.4f}, Duration: {:.4f}'.
          format(vacc.mean().item(),
                 loss.mean().item(),
                 acc.mean().item(),
                 acc.std().item(),
                 duration.mean().item()))
    return loss.mean().item(), acc.mean().item(), acc.std().item(), duration.mean().item(),logits


def train(model, optimizer, data):
    model.train()
    optimizer.zero_grad()
    
    out = model(data)
    
    loss = F.nll_loss(out[data.train_mask], data.y[data.train_mask])
    loss.backward()
    optimizer.step()


def evaluate(model, data):
    model.eval()

    with torch.no_grad():
        logits = model(data)
    probs = logits.exp()

    outs = {}
    for key in ['train', 'val', 'test']:
        mask = data['{}_mask'.format(key)]
        loss = F.nll_loss(logits[mask], data.y[mask]).item()
        pred = logits[mask].max(1)[1]
        acc = pred.eq(data.y[mask]).sum().item() / mask.sum().item()
        y_true = data.y[mask].cpu().numpy()
        y_score = probs[mask].cpu().numpy()
        if y_score.shape[1] == 1:
            score = y_score[:, 0]
        else:
            score = y_score
        try:
            if score.ndim == 1 or score.shape[1] == 1:
                auc = roc_auc_score(y_true, score)
                auprc = average_precision_score(y_true, score)
            else:
                auc = roc_auc_score(y_true, score, multi_class='ovr')
                auprc = average_precision_score(y_true, score, average='macro')
        except ValueError:
            auc = float('nan')
            auprc = float('nan')

        outs['{}_loss'.format(key)] = loss
        outs['{}_acc'.format(key)] = acc
        outs['{}_auc'.format(key)] = auc
        outs['{}_auprc'.format(key)] = auprc

    return outs,logits


#MT_task
# =============================================================================
# def run(dataset, gpu_no, model, epochs, lr, weight_decay, early_stopping, logger=None):
#     
#     torch.cuda.set_device(gpu_no)
#     # print(torch.cuda.is_available())
#     device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# 
#     valacc, val_losses, accs, durations = [], [], [], []
#     # epoch_time = []
#     data = dataset[0]
#     #data = cv_data[runs]
#     data = data.to(device)
# 
#     model.to(device).reset_parameters()
#     optimizer = Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
# 
#     if torch.cuda.is_available():
#         torch.cuda.synchronize()
# 
#     t_start = time.perf_counter()
# 
#     best_val_loss = float('inf')
#     test_acc = 0
#     val_loss_history = []
#     flag = 0
#     
#     for epoch in range(1, epochs + 1):
#         flag = flag + 1
#         train(model, optimizer, data)
#         eval_info,logits = evaluate(model, data)
#         eval_info['epoch'] = epoch
# 
#         if logger is not None:
#             logger(eval_info)
# 
#         if eval_info['val_loss'] < best_val_loss:
#             best_val_loss = eval_info['val_loss']
#             val_acc = eval_info['val_acc']
#             test_acc = eval_info['test_acc']
#         # print(epoch)
#         print(best_val_loss, test_acc)
#         val_loss_history.append(eval_info['val_loss'])
#         if early_stopping > 0 and epoch > epochs // 2:
#             tmp = tensor(val_loss_history[-(early_stopping + 1):-1])
#             if eval_info['val_loss'] > tmp.mean().item():
#                 break
# 
#         if torch.cuda.is_available():
#             torch.cuda.synchronize()
# 
#         t_end = time.perf_counter()
# 
#         valacc.append(val_acc)
#         val_losses.append(best_val_loss)
#         accs.append(test_acc)
#         durations.append(t_end - t_start)
#         # print((t_end - t_start)/flag)
#         # exit()
# 
#     vacc, loss, acc, duration = tensor(valacc), tensor(val_losses), tensor(accs), tensor(durations)
# 
#     print('Val Acc: {:.4f}, Val Loss: {:.4f}, Test Accuracy: {:.4f} ± {:.4f}, Duration: {:.4f}'.
#           format(vacc.mean().item(),
#                  loss.mean().item(),
#                  acc.mean().item(),
#                  acc.std().item(),
#                  duration.mean().item()))
#     return loss.mean().item(), acc.mean().item(), acc.std().item(), duration.mean().item(),logits
# 
# 
# def train(model, optimizer, data):
#     model.train()
#     optimizer.zero_grad()
#     out, r1, c1, c2 = model(data)
#     loss = F.nll_loss(out[data.train_mask], data.y[data.train_mask])/(c1 * c1) + r1/(c1 * c1) + 2* torch.log(c2 * c1)
#     loss.backward()
#     optimizer.step()
# 
# 
# def evaluate(model, data):
#     model.eval()
# 
#     with torch.no_grad():
#         logits,r1, c1, c2 = model(data)
# 
#     outs = {}
#     for key in ['train', 'val', 'test']:
#         mask = data['{}_mask'.format(key)]
#         loss = F.nll_loss(logits[mask], data.y[mask]).item()
#         pred = logits[mask].max(1)[1]
#         acc = pred.eq(data.y[mask]).sum().item() / mask.sum().item()
# 
#         outs['{}_loss'.format(key)] = loss
#         outs['{}_acc'.format(key)] = acc
# 
#     return outs,logits
# 
# =============================================================================
