#!/usr/bin/env python
# coding: utf-8

# # 开发 AI 应用
# 
# 未来，AI 算法在日常生活中的应用将越来越广泛。例如，你可能想要在智能手机应用中包含图像分类器。为此，在整个应用架构中，你将使用一个用成百上千个图像训练过的深度学习模型。未来的软件开发很大一部分将是使用这些模型作为应用的常用部分。
# 
# 在此项目中，你将训练一个图像分类器来识别不同的花卉品种。可以想象有这么一款手机应用，当你对着花卉拍摄时，它能够告诉你这朵花的名称。在实际操作中，你会训练此分类器，然后导出它以用在你的应用中。我们将使用[此数据集](http://www.robots.ox.ac.uk/~vgg/data/flowers/102/index.html)，其中包含 102 个花卉类别。你可以在下面查看几个示例。 
# 
# <img src='assets/Flowers.png' width=500px>
# 
# 该项目分为多个步骤：
# 
# * 加载和预处理图像数据集
# * 用数据集训练图像分类器
# * 使用训练的分类器预测图像内容
# 
# 我们将指导你完成每一步，你将用 Python 实现这些步骤。建议在基本完成提示代码的情况下再开启GPU调试。
# 
# 完成此项目后，你将拥有一个可以用任何带标签图像的数据集进行训练的应用。你的网络将学习花卉，并成为一个命令行应用。但是，你对新技能的应用取决于你的想象力和构建数据集的精力。例如，想象有一款应用能够拍摄汽车，告诉你汽车的制造商和型号，然后查询关于该汽车的信息。构建你自己的数据集并开发一款新型应用吧。
# 
# 首先，导入你所需的软件包。建议在代码开头导入所有软件包。当你创建此 notebook 时，如果发现你需要导入某个软件包，确保在开头导入该软件包。

# In[1]:


get_ipython().run_line_magic('matplotlib', 'inline')
get_ipython().run_line_magic('config', "InlineBackend.figure_format = 'retina'")
# Imports here
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
from torchvision import datasets, transforms
from torchvision import models
from torch import nn
from torch.nn import functional as F
from torch.autograd import Variable
from collections import OrderedDict
import time
from PIL import Image
import json


# ## 加载数据
# 
# 在此项目中，你将使用 `torchvision` 加载数据（[文档](http://pytorch.org/docs/master/torchvision/transforms.html#)）。数据应该和此 notebook 一起包含在内，否则你可以[在此处下载数据](https://s3.amazonaws.com/content.udacity-data.com/nd089/flower_data.tar.gz)。数据集分成了三部分：训练集、验证集和测试集。对于训练集，你需要变换数据，例如随机缩放、剪裁和翻转。这样有助于网络泛化，并带来更好的效果。你还需要确保将输入数据的大小调整为 224x224 像素，因为预训练的网络需要这么做。
# 
# 验证集和测试集用于衡量模型对尚未见过的数据的预测效果。对此步骤，你不需要进行任何缩放或旋转变换，但是需要将图像剪裁到合适的大小。
# 
# 对于所有三个数据集，你都需要将均值和标准差标准化到网络期望的结果。均值为 `[0.485, 0.456, 0.406]`，标准差为 `[0.229, 0.224, 0.225]`。这样使得每个颜色通道的值位于 -1 到 1 之间，而不是 0 到 1 之间。

# In[2]:


train_dir = '/data/flowers/train'
valid_dir = '/data/flowers/valid'
test_dir = '/data/flowers/test'


# 提示：
# - train数据集的transforms需要进行裁剪，均值和标准化，并且要对图像进行随机缩放、剪裁和翻转等等，有助于网络泛化，test和valid数据集的transforms只需要裁剪到合适的大小并进行均值和标准化。综上所述，valid数据集和test数据集使用同一个transform即可
# - 注意需要先resize图片，再crop，否则对于较大图片可能crop不到花朵部分
# - datasets设置时注意参数的变化（目录的不同）
# - loader设置时，train的loader的参数注意设置：shuffle = True，来增加训练图像时的随机性。

# In[3]:


# TODO: 定义transforms
train_transforms = transforms.Compose([
                                    transforms.RandomRotation(30),
                                    transforms.RandomResizedCrop(224, scale=(0.1, 1.0)),
                                    transforms.RandomHorizontalFlip(),
                                    transforms.ToTensor(),
                                    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
                                ])
test_transforms = transforms.Compose([
                                    transforms.Resize(256),
                                    transforms.CenterCrop(224),
                                    transforms.ToTensor(),
                                    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
                                ])
# TODO: 使用dir路径定义datasets，注意配置相对应的transforms
train_datasets = datasets.ImageFolder(train_dir, transform=train_transforms)
valid_datasets = datasets.ImageFolder(valid_dir, transform=test_transforms)
test_dataset = datasets.ImageFolder(test_dir, transform=test_transforms)
# TODO: 使用datasets定义dataloaders
train_loader = torch.utils.data.DataLoader(train_datasets, batch_size=32, shuffle=True)
valid_loader = torch.utils.data.DataLoader(valid_datasets, shuffle=True)
test_loader = torch.utils.data.DataLoader(test_dataset, shuffle=True)


# ### 标签映射
# 
# 你还需要加载从类别标签到类别名称的映射。你可以在文件 `cat_to_name.json` 中找到此映射。它是一个 JSON 对象，可以使用 [`json` 模块](https://docs.python.org/2/library/json.html)读取它。这样可以获得一个从整数编码的类别到实际花卉名称的映射字典。

# In[4]:


with open('cat_to_name.json', 'r') as f:
    cat_to_name = json.load(f)


# In[5]:


def imshowtensor(image, ax=None, title=None, normalize=True):
    """Imshow for Tensor."""
    if ax is None:
        fig, ax = plt.subplots()
    image = image.numpy().transpose((1, 2, 0))

    if normalize:
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        image = std * image + mean
        image = np.clip(image, 0, 1)

    ax.imshow(image)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.tick_params(axis='both', length=0)
    ax.set_xticklabels('')
    ax.set_yticklabels('')

    return ax


# In[6]:


images, labels = next(iter(train_loader))
fig, axes = plt.subplots(figsize=(24, 6), ncols=6)

for i in range(6):
    ax = axes[i]
    flower_name = cat_to_name[str(labels.numpy()[i])]
    imshowtensor(images[i], ax=ax, title=flower_name)


# In[7]:


images, labels = next(iter(train_loader))

image = images[0].numpy().transpose((1, 2, 0))
mean = np.array([0.485, 0.456, 0.406])
std = np.array([0.229, 0.224, 0.225])
image = std * image + mean
image = np.clip(image, 0, 1)

plt.imshow(image)


# # 构建和训练分类器
# 
# 数据准备好后，就开始构建和训练分类器了。和往常一样，你应该使用 `torchvision.models` 中的某个预训练模型获取图像特征。使用这些特征构建和训练新的前馈分类器。
# 
# 这部分将由你来完成。如果你想与他人讨论这部分，欢迎与你的同学讨论！你还可以在论坛上提问或在工作时间内咨询我们的课程经理和助教导师。
# 
# 请参阅[审阅标准](https://review.udacity.com/#!/rubrics/1663/view)，了解如何成功地完成此部分。你需要执行以下操作：
# 
# * 加载[预训练的网络](https://pytorch.org/docs/stable/torchvision/models.html)
# * 使用 ReLU 激活函数和丢弃定义新的未训练前馈网络作为分类器
# * 使用反向传播训练分类器层，并使用预训练的网络获取特征
# * 跟踪验证集的损失和准确率，以确定最佳超参数
# 
# 按照提示逐步完成项目，检查确保每部分都达到预期效果，然后再完成下个部分。你可能会发现，当你实现每部分时，可能需要回去修改之前的代码，这很正常！
# 
# 训练时，确保仅更新前馈网络的权重。如果一切构建正确的话，验证准确率应该能够超过 70%。确保尝试不同的超参数（学习速率、分类器中的单元、周期等），寻找最佳模型。保存这些超参数并用作项目下个部分的默认值。
# 
# 下面让我们开始吧！

# 提示1：
# - 挑选一个模型，加载预训练模型（既然是*预*训练的模型，那么注意参数pretrained应为True）

# In[8]:


# resnet18 = models.resnet18(pretrained=True)
# alexnet = models.alexnet(pretrained=True)
# squeezenet = models.squeezenet1_0(pretrained=True)
vgg16 = models.vgg16(pretrained=True)
# densenet = models.densenet161(pretrained=True)
# inception = models.inception_v3(pretrained=True)
# TODO
model = vgg16


# 提示2：
# - [冻结模型梯度权重](https://pytorch.org/docs/stable/notes/autograd.html?highlight=param%20requires_grad)，设置每一层的param.requires_grad标志

# In[9]:


# TODO
for param in model.parameters():
    param.requires_grad = False


# 提示3：
# - 增加全连接层，dropout层，以及Relu激活函数
# - 修改classifier层的主要目的是为了适应我们的分类要求，即最终的输出层要输出102种花卉分类（即要有一层全连接层输出为102，**不要**在输出层后加dropout）
# - 全连接层后使用[LogSoftmax](https://pytorch.org/docs/stable/nn.html?highlight=nllloss#torch.nn.LogSoftmax)或者[softmax](https://pytorch.org/docs/stable/nn.html?highlight=nllloss#torch.nn.softmax)，来得出每种花的概率

# In[10]:


classifier = nn.Sequential(OrderedDict([
                                ('fc1', nn.Linear(25088, 4096)),
                                ('relu1', nn.ReLU(inplace=True)),
                                ('dropout1', nn.Dropout()),
                                ('fc2', nn.Linear(4096, 4096)),
                                ('relu2', nn.ReLU(inplace=True)),
                                ('dropout2', nn.Dropout()),
                                ('output', nn.Linear(4096, 102))
                            ]))

model.classifier = classifier
# 将模型转入gpu
model.cuda()


# 提示4：
# - 设置[损失函数](https://pytorch.org/docs/stable/nn.html?highlight=nllloss#torch.nn.NLLLoss)
# - 设置[优化器](https://pytorch.org/docs/stable/optim.html)

# In[11]:


# TODO
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.classifier.parameters(), lr=0.00)


# 提示5：
# - 分别写成两个函数用于训练模型和测试模型(课程中写到了一个代码中)，便于调试代码，以及增加程序的可读性
# - 因为模型已经转入gpu，这里注意需要将数据也转入gpu
# - 注意输出训练测试过程，把控模型是否欠拟合或者过拟合
# - 模型训练时要model.train()，模型测试时要model.eval()，让模型进入训练或者测试的模式中

# In[12]:


# TODO: 训练网络，需要有loss和accuracy打印输出
def train(model, loader):
    steps = 0
    print_every = 10
    running_loss = 0
    accuracy = 0
    model.train()
    for images, labels in loader:
        steps += 1
        images, labels = images.cuda(), labels.cuda()
        optimizer.zero_grad()
        output = model.forward(images)
        loss = criterion(output, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
        
        model.eval()
        valid_images, valid_labels = next(iter(valid_loader))
        valid_images, valid_labels = valid_images.cuda(), valid_labels.cuda()
        valid_output = model.forward(valid_images)
        ps = torch.exp(valid_output)
        equality = (valid_labels.data == ps.max(1)[1])
        accuracy += equality.type_as(torch.FloatTensor()).mean()
        if steps % print_every == 0:
            print("Epoch Steps: {}.. ".format(int(steps/print_every)),
                  "Training Loss: {:.3f}.. ".format(running_loss/print_every),
                  "Accuracy: {:.3f}".format(accuracy/print_every))
            running_loss = 0
            accuracy = 0
        model.train()


# In[13]:


# TODO:测试网络，使用验证集或者测试集，训练模型时使用验证集，测试模型最终结果使用测试集
# 需要有loss和accuracy打印输出
def test(model, loader):
    accuracy = 0
    test_loss = 0
    model.eval()
    for images, labels in valid_loader:
        # images = images.resize_(images.size()[0], 150528)
        images, labels = images.cuda(), labels.cuda()
        output = model.forward(images)
        test_loss += criterion(output, labels).item()

        ps = torch.exp(output)
        equality = (labels.data == ps.max(1)[1])
        accuracy += equality.type_as(torch.FloatTensor()).mean()

    print("Test Loss: {:.3f}.. ".format(test_loss/len(loader)),
          "Test Accuracy: {:.3f}".format(accuracy/len(loader)))


# In[14]:


epoch = 3 #TODO 修改epoch次数
for e in range(1, epoch):
    print("Epoch: {}/{}".format(e, epoch))
    train(model, train_loader)
    test(model, valid_loader)


# ## 测试网络
# 
# 建议使用网络在训练或验证过程中从未见过的测试数据测试训练的网络。这样，可以很好地判断模型预测全新图像的效果。用网络预测测试图像，并测量准确率，就像验证过程一样。如果模型训练良好的话，你应该能够达到大约 70% 的准确率。

# In[15]:


# TODO: 在测试集上进行测试，需要输出结果
test(model, test_loader)


# ## 保存检查点
# 
# 训练好网络后，[保存模型](https://pytorch.org/docs/stable/torch.html?highlight=torch%20save#torch.save)，以便稍后加载它并进行预测。你可能还需要保存其他内容，例如从类别到索引的映射，索引是从某个图像数据集中获取的：`image_datasets['train'].class_to_idx`。你可以将其作为属性附加到模型上，这样稍后推理会更轻松。

# 提示：
# - 创建checkpoint字典，字典中最少需要包含模型model相关和题目中要求的image_datasets['train'].class_to_idx
# - 使用torch.save保存checkpoint字典

# In[16]:


# TODO: Save the checkpoint
checkpoint = {
    "input_size": 25088,
    "output_size": 102,
    "hidden_layers": [4096, 4096],
    "state_dict": model.state_dict(),
    'class_to_idx': train_datasets.class_to_idx
}

torch.save(checkpoint, 'checkpoint.pth')


# ## 加载检查点
# 
# 此刻，建议写一个可以加载检查点并重新构建模型的函数。这样的话，你可以回到此项目并继续完善它，而不用重新训练网络。

# 提示：
# - 加载”保存检查点“所保存的文件，用于恢复模型
# - 注意torch的save会原模原样保存你需要保存的数据，因为你保存的是字典，从文件加载出来的就是一个字典类型的数据，按照字典方式操作即可。比如
# ```
# #保存：
# dict1 = {"A" : 1, "B": 2}
# torch.save(dict1, filepath)
# #加载：
# checkpoint = torch.load(filepath)
# A = checkpoint["A"]
# B = checkpoint["B"]
# ```
# - image_datasets['train'].class_to_idx，这个是指花朵本身对应的文件夹名称（数字）到模型预测出来的名称（数字）的一个对应关系，是一个字典形式，为了后面方便查询（通过预测出来的名称来得到真正的花朵所在文件夹的名称），这里需要将class_to_idx这个字典键key和值value颠倒过来
# - 题目要求是函数，所以函数最终需要返回可以用于预测的模型以及颠倒后的class_to_idx

# In[17]:


# TODO: Write a function that loads a checkpoint and rebuilds the model
def load_checkpoint(filepath):
    checkpoint = torch.load(filepath)
    model = models.vgg16(pretrained=True)
    input_size = checkpoint['input_size']
    output_size = checkpoint['output_size']
    hidden_layers = checkpoint['hidden_layers']
    state_dict = checkpoint['state_dict']
    class_to_idx = checkpoint['class_to_idx']
    model_list = list()
    model_list.append(('fc1', nn.Linear(input_size, hidden_layers[0])))
    model_list.append(('relu1', nn.ReLU(inplace=True)))
    model_list.append(('dropout1', nn.Dropout()))
    hidden_layers_len = len(hidden_layers)
    for i in range(hidden_layers_len-1):
        model_list.append(('fc'+str(i+2), nn.Linear(hidden_layers[i], hidden_layers[i+1])))
        model_list.append(('relu'+str(i+2), nn.ReLU(inplace=True)))
        model_list.append(('dropout'+str(i+2), nn.Dropout()))
    model_list.append(('output', nn.Linear(hidden_layers[-1], output_size)))

    classifier = nn.Sequential(OrderedDict(model_list))

    model.classifier = classifier
    
    return model, dict(zip(class_to_idx.values(), class_to_idx.keys()))


# In[18]:


model, class_to_idx = load_checkpoint('checkpoint.pth')


# # 类别推理

# 首先，你需要处理输入图像，使其可以用于你的网络。
# 
# ## 图像处理
# 
# 你需要使用 `PIL` 加载图像（[文档](https://pillow.readthedocs.io/en/latest/reference/Image.html)）。建议写一个函数来处理图像，使图像可以作为模型的输入。该函数应该按照训练的相同方式处理图像。
# 
# 首先，调整图像大小，使最小的边为 256 像素，并保持宽高比。为此，可以使用 [`thumbnail`](http://pillow.readthedocs.io/en/3.1.x/reference/Image.html#PIL.Image.Image.thumbnail) 或 [`resize`](http://pillow.readthedocs.io/en/3.1.x/reference/Image.html#PIL.Image.Image.thumbnail) 方法。然后，你需要从图像的中心裁剪出 224x224 的部分。
# 
# 图像的颜色通道通常编码为整数 0-255，但是该模型要求值为浮点数 0-1。你需要变换值。使用 Numpy 数组最简单，你可以从 PIL 图像中获取，例如 `np_image = np.array(pil_image)`。
# 
# 和之前一样，网络要求图像按照特定的方式标准化。均值应标准化为 `[0.485, 0.456, 0.406]`，标准差应标准化为 `[0.229, 0.224, 0.225]`。你需要用每个颜色通道减去均值，然后除以标准差。
# 
# 最后，PyTorch 要求颜色通道为第一个维度，但是在 PIL 图像和 Numpy 数组中是第三个维度。你可以使用 [`ndarray.transpose`](https://docs.scipy.org/doc/numpy-1.13.0/reference/generated/numpy.ndarray.transpose.html)对维度重新排序。颜色通道必须是第一个维度，并保持另外两个维度的顺序。

# 提示：
# - 按照上述要求来写即可，特别提示维度排序：np_image.transpose((2, 0, 1))，这个样子是指将第三个维度（颜色）换到了第一个维度上，其他两个维度保持顺序
# - 另外要注意，np和PIL的很多操作都是在返回值中进行修改，而不会对原数据进行修改，务必要进行赋值操作
# - 运行下面的测试，如果出现下面的图，则编写正确：
# <img src='assets/1_flower.png'>

# In[19]:


def process_image(image):
    ''' Scales, crops, and normalizes a PIL image for a PyTorch model,
        returns an Numpy array
    '''
    # TODO: Process a PIL image for use in a PyTorch model
    img_pil = Image.open(image)
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    img_tensor = preprocess(img_pil)
    return img_tensor


# 要检查你的项目，可以使用以下函数来转换 PyTorch 张量并将其显示在  notebook 中。如果 `process_image` 函数可行，用该函数运行输出应该会返回原始图像（但是剪裁掉的部分除外）。

# In[20]:


def imshow(image, ax=None, title=None):
    """Imshow for Tensor."""
    if ax is None:
        fig, ax = plt.subplots()
    
    # PyTorch tensors assume the color channel is the first dimension
    # but matplotlib assumes is the third dimension
    image = image.numpy().transpose((1, 2, 0))
    
    # Undo preprocessing
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    image = std * image + mean
    
    # Image needs to be clipped between 0 and 1 or it looks like noise when displayed
    image = np.clip(image, 0, 1)
    
    ax.imshow(image)
    
    return ax


# 测试一下，跟提示中出现同样的花朵后才可进行下一道题：

# In[21]:


img_tensor = process_image(train_dir+"/1/image_06735.jpg")
imshow(img_tensor)


# ## 类别预测
# 
# 可以获得格式正确的图像后 
# 
# 现在，使用训练的网络进行推理的函数。即你将向网络中传入一个图像路径，并预测图像中的花卉类别。这里实现了 `predict` 的函数，该函数会接受图像和模型，然后返回概率在前 $K$ 的类别及其概率。
# 
# 要获得前 $K$ 个值，在张量中使用 [`x.topk(k)`](http://pytorch.org/docs/master/torch.html#torch.topk)。该函数会返回前 `k` 个概率和对应的类别索引。使用  `class_to_idx`将这些索引转换为实际类别标签，或者从用来加载数据的[ `ImageFolder`](https://pytorch.org/docs/master/torchvision/datasets.html?highlight=imagefolder#torchvision.datasets.ImageFolder)进行转换。

# In[22]:


# 只是示例，不要运行，可以看出predict接收了图像的path以及加载出来的模型，返回了预测的种类索引和各个种类的概率
# probs, classes = predict(image_path, model)
# print(probs)
# print(classes)
print(cat_to_name[class_to_idx[0]])


# In[23]:


# 不需要修改，运行即可
def predict(image_path, model, topk=5):
    ''' Predict the class (or classes) of an image using a trained deep learning model.
    '''
    model.eval()
    img_tensor = process_image(image_path)
    img_tensor.unsqueeze_(0)
    img_tensor = img_tensor.type(torch.cuda.FloatTensor)
    model.cuda()
    with torch.no_grad():
        output = model(Variable(img_tensor.cuda()))
    ps = torch.exp(output)
    probs, index = ps.topk(topk)
    probs = probs.cpu().detach().numpy().tolist()[0]
    index = index.cpu().detach().numpy().tolist()[0]
    index = [class_to_idx[i] for i in index]
    return probs, index


# 尝试调用预测一下，如果你的模型测出来概率最高的那个种类是1，即可进行下一道题的操作，否则你可能需要反复修改之前所有涉及到模型的问题，或者检查下加载检查点中的class_to_idx是否正确颠倒。

# In[24]:


probs, classes = predict(train_dir+"/1/image_06735.jpg", model)
print(probs)
print(classes)
print([cat_to_name[cls] for cls in classes])


# ## 检查运行状况
# 
# 你已经可以使用训练的模型做出预测，现在检查模型的性能如何。即使测试准确率很高，始终有必要检查是否存在明显的错误。使用 `matplotlib` 将前 5 个类别的概率以及输入图像绘制为条形图，应该如下所示：
# 
# <img src='assets/inference_example.png' width=300px>
# 
# 你可以使用 `cat_to_name.json` 文件（应该之前已经在 notebook 中加载该文件）将类别整数编码转换为实际花卉名称。要将 PyTorch 张量显示为图像，请使用定义如下的 `imshow` 函数。

# 提示：
# - cat_to_name.json是文件夹的目录和真实花朵名称的对应关系，通过上一步predict得出的index对应到cat_to_name即可得到名称

# In[43]:


# TODO: Display an image along with the top 5 classes
# 参数分别为测试花朵的路径，花朵种类的文件夹名称，模型，以及topk
def show_result(path, classname, model, topk):
    plt.rcParams["figure.figsize"] = (10,5)
    plt.subplot(211)
    # img_tensor = process_image(path)
    probs, classes = predict(path, model)
    image = process_image(path)
    axs = imshow(image, ax = plt)
    axs.axis('off')
    axs.title(cat_to_name[str(classname)])
    plt.subplot(212)
    classes_name = [cat_to_name[str(index)] for index in np.array(classes)]
    plt.barh(classes_name, probs, 0.8, linewidth=4.0, align = 'center')
    plt.show()


# 接下来测试一下，希望你绘制的图中，概率最高的花朵种类名称为trumpet creeper。

# In[44]:


#直接运行
show_result(test_dir+"/101/image_07949.jpg", "101", model, 5)


# In[ ]:




