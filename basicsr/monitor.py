import os
import cv2
import logging
from os import path as osp
import time
import torch
from basicsr.data import build_dataloader, build_dataset
from basicsr.models import build_model
from basicsr.utils.options import dict2str, parse_options
from basicsr.utils import get_env_info, get_root_logger, get_time_str, make_exp_dirs

def img_process(frame_idx, model, opt):
    
    test_loaders = []
    for phase, dataset_opt in sorted(opt['datasets'].items()):
        test_set = build_dataset(dataset_opt)
        test_loader = build_dataloader(
            test_set, dataset_opt, num_gpu=opt['num_gpu'], dist=opt['dist'], sampler=None, seed=opt['manual_seed'])
        test_loaders.append(test_loader)
        
    for test_loader in test_loaders:
        model.validation(test_loader, current_iter=opt['name'], tb_logger=None, save_img=opt['val']['save_img'])

    while True:
        img = cv2.imread('/home/youzhe0305/DLP_Final_Project/results/GOPRO_test/visualization/GOPRO/video 1-000/00000000_GOPRO_test.png')            
        if img is not None:
            print('圖片存在')
            break    

    os.rename('/home/youzhe0305/DLP_Final_Project/results/GOPRO_test/visualization/GOPRO/video 1-000/00000000_GOPRO_test.png',
              f'/home/youzhe0305/DLP_Final_Project/results/GOPRO_test/visualization/GOPRO/video 1-000/{frame_idx:06d}.png')

if __name__ == '__main__':

    root_path = osp.abspath(osp.join(__file__, osp.pardir, osp.pardir))
    opt = parse_options(root_path, is_train=False)
    torch.backends.cudnn.benchmark = True

    model = build_model(opt)

    frame_idx = 0
    print('運行中...')
    while True:

        if os.path.exists(f'/home/youzhe0305/DLP_Final_Project/stream_img/blur/video 1/{frame_idx:06d}.png'):
            if os.path.exists(f'/home/youzhe0305/DLP_Final_Project/stream_img/blur/video 1/{frame_idx-1:06d}.png'):
                os.remove(f'/home/youzhe0305/DLP_Final_Project/stream_img/blur/video 1/{frame_idx-1:06d}.png')
            if os.path.exists(f'/home/youzhe0305/DLP_Final_Project/results/GOPRO_test/visualization/GOPRO/video 1-000/{frame_idx-1:06d}.png'):
                os.remove(f'/home/youzhe0305/DLP_Final_Project/results/GOPRO_test/visualization/GOPRO/video 1-000/{frame_idx-1:06d}.png')
            
            while True:  # 確認img有被寫入完全
                img = cv2.imread(f'/home/youzhe0305/DLP_Final_Project/stream_img/blur/video 1/{frame_idx:06d}.png')
                print('寫入中...')
                if img is not None:
                    break    
            
            img_process(frame_idx, model, opt)
        
            os.remove(f'/home/youzhe0305/DLP_Final_Project/stream_img/blur/video 1/{frame_idx:06d}.png')
            print(f'處理frame {frame_idx}')

            frame_idx += 1

# python basicsr/monitor.py -opt options/test/Deblur/test_Deblur_GOPRO_demo.yml