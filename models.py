import torch
import torch.nn as nn
from torch.nn import init

import math
import numpy as np

'''
try:
    from networks.resample2d_package.resample2d import Resample2d
    from networks.channelnorm_package.channelnorm import ChannelNorm

    from networks import FlowNetC
    from networks import FlowNetS
    from networks import FlowNetSD
    from networks import FlowNetFusion

    from networks.submodules import *
except:
    from .networks.resample2d_package.resample2d import Resample2d
    from .networks.channelnorm_package.channelnorm import ChannelNorm

    from .networks import FlowNetC
    from .networks import FlowNetS
    from .networks import FlowNetSD
    from .networks import FlowNetFusion

    from .networks.submodules import *
'Parameter count = 162,518,834'
'''
from networks import FlowNetS
from networks.submodules import *
import pdb


class FlowNet2S(FlowNetS.FlowNetS):
    def __init__(self, args, batchNorm=False, div_flow=20):
        super(FlowNet2S,self).__init__(args, input_channels = 6, batchNorm=batchNorm)
        self.rgb_max = args.rgb_max
        self.div_flow = div_flow
        
    def forward(self, inputs):
        #pdb.set_trace()
        rgb_mean = inputs.contiguous().view(inputs.size()[:2]+(-1,)).mean(dim=-1).view(inputs.size()[:2] + (1,1,1,))
        x = (inputs - rgb_mean) / self.rgb_max
        x = torch.cat( (x[:,:,0,:,:], x[:,:,1,:,:]), dim = 1)


        out_conv1 = self.conv1(x)

        out_conv2 = self.conv2(out_conv1)
        out_conv3 = self.conv3_1(self.conv3(out_conv2))
        out_conv4 = self.conv4_1(self.conv4(out_conv3))
        out_conv5 = self.conv5_1(self.conv5(out_conv4))
        out_conv6 = self.conv6_1(self.conv6(out_conv5))

        flow6       = self.predict_flow6(out_conv6)
        flow6_up    = self.upsampled_flow6_to_5(flow6)
        out_deconv5 = self.deconv5(out_conv6)
        
        concat5 = torch.cat((out_conv5,out_deconv5,flow6_up),1)
        flow5       = self.predict_flow5(concat5)
        flow5_up    = self.upsampled_flow5_to_4(flow5)
        out_deconv4 = self.deconv4(concat5)
        
        concat4 = torch.cat((out_conv4,out_deconv4,flow5_up),1)
        flow4       = self.predict_flow4(concat4)
        flow4_up    = self.upsampled_flow4_to_3(flow4)
        out_deconv3 = self.deconv3(concat4)
        
        concat3 = torch.cat((out_conv3,out_deconv3,flow4_up),1)
        flow3       = self.predict_flow3(concat3)
        flow3_up    = self.upsampled_flow3_to_2(flow3)
        out_deconv2 = self.deconv2(concat3)

        concat2 = torch.cat((out_conv2,out_deconv2,flow3_up),1)
        flow2 = self.predict_flow2(concat2)

        if self.training:
            return flow2,flow3,flow4,flow5,flow6
        else:
            return self.upsample1(flow2*self.div_flow)

