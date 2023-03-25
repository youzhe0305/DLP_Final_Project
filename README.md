# DSTNet

[![LICENSE](https://img.shields.io/badge/license-MIT-green)](https://github.com/xuboming8/CDVD-TSPNL/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/pytorch-1.10.1-%237732a8)](https://pytorch.org/)

### Deep Discriminative Spatial and Temporal Network for Efficient Video Deblurring
By [Jinshan Pan*](https://jspan.github.io/), Boming Xu*, Jiangxin Dong,  Jianjun Ge and Jinhui Tang

<hr />

> **Abstract**: *How to effectively explore spatial and temporal information is important for video deblurring. In contrast to existing methods that directly align adjacent frames without discrimination, we develop a deep discriminative spatial and temporal network to facilitate the spatial and temporal feature exploration for better video deblurring. We first develop a channel-wise gated dynamic network to adaptively explore the spatial information. As adjacent frames usually contain different contents, directly stacking features of adjacent frames without discrimination may affect the latent clear frame restoration. Therefore, we develop a simple yet effective discriminative temporal feature fusion module to obtain useful temporal features for latent frame restoration. Moreover, to utilize the information from long-range frames, we develop a wavelet-based feature propagation method that takes the discriminative temporal feature fusion module as the basic unit to effectively propagate main structures from long-range frames for better video deblurring. We show that the proposed method does not require additional alignment methods and performs favorably against state-of-the-art ones on benchmark datasets in terms of accuracy and model complexity*
<hr />


This repository is the official PyTorch implementation of "Deep Discriminative Spatial and Temporal Network for Efficient Video Deblurring"

## Network Architecture
[![Architecture](https://s1.ax1x.com/2023/03/25/ppDnq0A.png)](https://imgse.com/i/ppDnq0A)

## Updates
[2022-02-28] Paper has been accepted by CVPR2023\
[2023-03-25] Training & Testing code is available!

## Experimental Results
Quantitative evaluations on the GoPro dataset. “Ours-L” denotes a large model, where we use 96 features and 30 ResBlocks in the DTFF module
[![GOPRO](https://s1.ax1x.com/2023/03/25/ppDu8tx.png)](https://imgse.com/i/ppDu8tx)

Quantitative evaluations on the DVD dataset in terms of PSNR and SSIM
[![DVD](https://s1.ax1x.com/2023/03/25/ppDuGh6.png)](https://imgse.com/i/ppDuGh6)

Quantitative evaluations on the BSD deblurring dataset in terms of PSNR and SSIM.
[![BSD](https://s1.ax1x.com/2023/03/25/ppDut1O.png)](https://imgse.com/i/ppDut1O)

## Dependencies
- Linux (Tested on Ubuntu 18.04)
- Python 3 (Recommend to use [Anaconda](https://www.anaconda.com/download/#linux))
- [PyTorch 1.10.1](https://pytorch.org/): `conda install pytorch==1.10.1 torchvision==0.11.2 torchaudio==0.10.1 cudatoolkit=11.3 -c pytorch -c conda-forge`
- Install dependent packages :`pip install -r requirements.txt`
- Install CDVD-TSPNL :`python setup.py develop`

## Get Started

### Pretrained models
- Models are available in  `'./experiments'`

### Dataset Organization Form
If you prepare your own dataset, please follow the following form like GOPRO/DVD:
```
|--dataset  
    |--blur  
        |--video 1
            |--frame 1
            |--frame 2
                ：  
        |--video 2
            :
        |--video n
    |--gt
        |--video 1
            |--frame 1
            |--frame 2
                ：  
        |--video 2
        	:
        |--video n
```
 
