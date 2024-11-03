import torch
import time
from torch import nn as nn
from basicsr.utils.registry import ARCH_REGISTRY
from .arch_util import ResidualBlockNoBN, flow_warp, make_layer
from basicsr.archs.ChanDynamic_GMLP import CWGDN
import torch.nn.functional as F
from basicsr.archs.wave_tf import DWT, IWT
from basicsr.archs.wave_tf import HaarDownsampling
from basicsr.archs.kpn_pixel import IDynamicDWConv
from einops import rearrange
import os

@ARCH_REGISTRY.register()
class Deblur(nn.Module):
    def __init__(self, num_feat=64, num_block=15):
        super().__init__()
        self.num_feat = num_feat

        # extractor & reconstruction
        self.feat_extractor = nn.Conv3d(3, num_feat, (1, 3, 3), 1, (0, 1, 1), bias=True)
        self.recons = nn.Conv3d(num_feat, 3, (1, 3, 3), 1, (0, 1, 1), bias=True)

        # wave tf
        self.wave = HaarDownsampling(num_feat)
        self.x_wave_1_conv1 = nn.Conv2d(num_feat * 3, num_feat * 3, 1, 1, 0, groups=3)
        self.x_wave_1_conv2 = nn.Conv2d(num_feat * 3, num_feat * 3, 1, 1, 0, groups=3)
        # wave pro
        self.x_wave_2_conv1 = nn.Conv2d(num_feat * 3, num_feat * 3, 1, 1, 0, groups=3)
        self.x_wave_2_conv2 = nn.Conv2d(num_feat * 3, num_feat * 3, 1, 1, 0, groups=3)

        # transformer
        transformer_scale4 = []
        for _ in range(5):
            transformer_scale4.append(
                nn.Sequential(CWGDN(dim=num_feat, ffn_expansion_factor=4, bias=False, LayerNorm_type='WithBias'))
            )
        self.transformer_scale4 = nn.Sequential(*transformer_scale4)

        # propogation branch
        self.forward_propagation = manual_conv3d_propagation_forward(num_feat, num_block)
        # activation functions
        self.lrelu = nn.LeakyReLU(negative_slope=0.1, inplace=True)

    def forward(self, lrs):
        time_start = time.time()
        # print(lrs.size())
        b, t, c, h, w = lrs.size()
        lrs_feature = self.feat_extractor(rearrange(lrs, 'b t c h w -> b c t h w'))     # b c t h w
        # scale1
        tf_input_feature = rearrange(lrs_feature, 'b c t h w -> (b t) c h w')
        tf_wave1_l, tf_wave1_h = self.wave(tf_input_feature)
        tf_wave1_h = self.x_wave_1_conv2(self.lrelu(self.x_wave_1_conv1(tf_wave1_h)))
        # scale2
        tf_wave2_l, tf_wave2_h = self.wave(tf_wave1_l)
        tf_wave2_l = rearrange(self.transformer_scale4(rearrange(tf_wave2_l, '(b t) c h w -> b t c h w', b=b)), 'b t c h w -> (b t) c h w')
        tf_wave2_h = self.x_wave_2_conv2(self.lrelu(self.x_wave_2_conv1(tf_wave2_h)))
        # scale1
        tf_wave1_l = self.wave(torch.cat([tf_wave2_l, tf_wave2_h], dim=1), rev=True)
        tf_wave1_l = rearrange(self.forward_propagation(rearrange(tf_wave1_l, '(b t) c h w -> b t c h w', b=b)), 'b t c h w -> (b t) c h w')
        pro_feat = rearrange(self.wave(torch.cat([tf_wave1_l, tf_wave1_h], dim=1), rev=True), '(b t) c h w -> b t c h w', b=b)
        # reconstruction
        out = rearrange(self.recons(rearrange(pro_feat, 'b t c h w -> b c t h w')), 'b c t h w -> b t c h w')
        time_end = time.time()
        print("inference time:", time_end - time_start)
        
        with open('./log.txt', 'a') as f:
            f.write(f'{time_end - time_start}\n')
        
        return out.contiguous() + lrs


class ResidualBlocks2D(nn.Module):
    def __init__(self, num_feat=64, num_block=30):
        super().__init__()
        self.main = nn.Sequential(
            make_layer(ResidualBlockNoBN, num_block, num_feat=num_feat))

    def forward(self, fea):
        return self.main(fea)


class manual_conv3d_propagation_backward(nn.Module):
    def __init__(self, num_feat=64, num_block=15):
        super().__init__()
        self.num_feat = num_feat
        self.conv1 = nn.Conv2d(num_feat * 2, num_feat * 2, 3, 1, 1, bias=True)
        self.conv2 = nn.Conv2d(num_feat, num_feat, 3, 1, 1, bias=True)
        self.conv3 = nn.Conv2d(num_feat, num_feat, 3, 1, 1, bias=True)
        self.kernel_conv_pixel = IDynamicDWConv(num_feat, 3, 1, 4, 1)
        self.lrelu = nn.LeakyReLU(negative_slope=0.1, inplace=True)
        self.resblock_bcakward2d = ResidualBlocks2D(num_feat, num_block)

    def forward(self, feature):
        # predefine
        b, t, c, h, w = feature.size()                           # b t 64 256 256
        backward_list = []
        feat_prop = feature.new_zeros(b, c, h, w)
        # propagation
        for i in range(t - 1, -1, -1):
            x_feat = feature[:, i, :, :, :]
            # fusion propagation
            feat_fusion = torch.cat([x_feat, feat_prop], dim=1)       # b 128 256 256
            feat_fusion = self.lrelu(self.conv1(feat_fusion))   # b 128 256 256
            feat_prop1, feat_prop2 = torch.split(feat_fusion, self.num_feat, dim=1)
            feat_prop1 = feat_prop1 * torch.sigmoid(self.conv2(feat_prop1))
            # print('?????????',torch.min(feat_prop1)) # 出現超大的負數跟正數
            # print('>>>>>>>>>',torch.max(feat_prop1))
            feat_prop2 = feat_prop2 * torch.sigmoid(self.conv3(feat_prop2))
            feat_prop = feat_prop1 + feat_prop2

            # dynamic conv
            feat_prop = self.kernel_conv_pixel(feat_prop)
            # resblock2D
            feat_prop = self.resblock_bcakward2d(feat_prop)
            backward_list.append(feat_prop)

        backward_list = backward_list[::-1]
        conv3d_feature = torch.stack(backward_list, dim=1)      # b 64 t 256 256
        return conv3d_feature


class manual_conv3d_propagation_forward(nn.Module):
    def __init__(self, num_feat=64, num_block=15):
        super().__init__()
        self.num_feat = num_feat
        self.conv_range_limit1 = nn.Conv2d(num_feat,num_feat, 3, 1, 1, bias=True)
        self.conv_range_limit2 = nn.Conv2d(num_feat,num_feat, 3, 1, 1, bias=True)
        self.conv_range_limit3 = nn.Conv2d(num_feat,num_feat, 3, 1, 1, bias=True)

        self.conv1 = nn.Conv2d(num_feat * 2, num_feat * 2, 3, 1, 1, bias=True)
        self.conv2 = nn.Conv2d(num_feat, num_feat, 3, 1, 1, bias=True)
        self.conv3 = nn.Conv2d(num_feat, num_feat, 3, 1, 1, bias=True)
        self.kernel_conv_pixel = IDynamicDWConv(num_feat, 3, 1, 4, 1)
        self.lrelu = nn.LeakyReLU(negative_slope=0.1, inplace=True)
        self.resblock_bcakward2d = ResidualBlocks2D(num_feat, num_block)

    def forward(self, feature):
        # predefine
        # 取消backward之後得到的是2,15,64,128,128
        b, t, c, h, w = feature.size()                          # b t 64 256 256
        forward_list = []
        feat_prop = feature.new_zeros(b, c, h, w)
        if os.path.exists('/home/youzhe0305/DLP_Final_Project/tensor_temp/temp.pth'):
            feat_prop = torch.load('/home/youzhe0305/DLP_Final_Project/tensor_temp/temp.pth')
            print('加載前段資料成功')
        
        for i in range(0, t):
            
            # print('//////',torch.min(feat_prop)) # 出現超大的負數跟正數
            # print('------',torch.max(feat_prop))

            if torch.isnan(feat_prop).any(): # 第14幀出現nan
                print('**********************',i)
            
            x_feat = feature[:, i, :, :, :]
            x_feat = self.lrelu(self.conv_range_limit1(x_feat))
            x_feat = self.lrelu(self.conv_range_limit2(x_feat))
            x_feat = self.conv_range_limit3(x_feat)
            x_feat = F.tanh(x_feat) # 把它限制在-1~1之間
            # fusion propagation
            feat_fusion = torch.cat([x_feat, feat_prop], dim=1)  # b 128 256 256
            feat_fusion = self.lrelu(self.conv1(feat_fusion))  # b 128 256 256
            feat_prop1, feat_prop2 = torch.split(feat_fusion, self.num_feat, dim=1)
            feat_prop1 = feat_prop1 * torch.sigmoid(self.conv2(feat_prop1))
            feat_prop2 = feat_prop2 * torch.sigmoid(self.conv3(feat_prop2))
            feat_prop = feat_prop1 + feat_prop2
            # dynamic conv
            feat_prop = self.kernel_conv_pixel(feat_prop)
            # resblock2D
            feat_prop = self.resblock_bcakward2d(feat_prop)
            forward_list.append(feat_prop)

        conv3d_feature = torch.stack(forward_list, dim=1)      # b 64 t 256 256
        
        torch.save(feat_prop, '/home/youzhe0305/DLP_Final_Project/tensor_temp/temp.pth')
        
        return conv3d_feature
