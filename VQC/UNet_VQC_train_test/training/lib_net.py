import torch.nn as nn
import torch
import sys
import torch.nn.functional as F

from lib_qf import *
from lib_bn import *
from lib_vqc import *
from lib_utils import *

## Define the NN architecture
class Net(nn.Module):
    def __init__(self,img_size,layers,training,binary,debug="False"):
        super(Net, self).__init__()

        self.in_size = img_size*img_size
        self.training = training
        self.layer = len(layers)
        self.layers = layers
        self.binary = binary
        loop_in_size = self.in_size
        self.debug = debug
        for idx in range(self.layer):
            fc_name = "fc"+str(idx)
            if layers[idx][0]=='u':
                setattr(self, fc_name, BinaryLinearQuantumFirstLAYER(loop_in_size, layers[idx][1], bias=False))
            elif layers[idx][0]=='c':
                setattr(self, fc_name, BinaryLinearClassic(loop_in_size, layers[idx][1], bias=False))
            elif layers[idx][0]=='f':
                setattr(self, fc_name, nn.Linear(loop_in_size, layers[idx][1]))
            elif layers[idx][0]=='p':
                setattr(self, fc_name, BinaryLinear(loop_in_size, layers[idx][1], bias=False))
            elif layers[idx][0]=='p2a':
                setattr(self, fc_name, Prop2amp())
            elif layers[idx][0]=='v':
                if idx ==0:
                    loop_in_size = int(np.log2(loop_in_size))
                setattr(self, fc_name, VQC_Net(loop_in_size, layers[idx][1]))
            elif layers[idx][0]=='v10':
                setattr(self, fc_name, VQC_Net(loop_in_size, layers[idx][1],'vqc_10'))
            elif layers[idx][0]=='v5':
                setattr(self, fc_name, VQC_Net(loop_in_size, layers[idx][1],'vqc_5'))
            elif layers[idx][0]=='n':
                setattr(self, fc_name, QC_Norm_Correction_try2(num_features=layers[idx][1]))
            else:
                print("Not support layer name!")
                sys.exit(0)
            loop_in_size = layers[idx][1]


    def forward(self, x, training=1):
        x = x.view(-1, self.in_size)
        for layer_idx in range(self.layer):
            if self.binary and layer_idx==0:
                x = (binarize(x - 0.5) + 1) / 2
            x = getattr(self, "fc" + str(layer_idx))(x)

        if self.layers[-1][1] == 1:
            x = torch.cat((x, 1 - x), -1)

        return x


