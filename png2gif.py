import imageio
import os

def png_to_gif(root_path, save_path):
    
    frames = []
    assert os.path.exists(root_path), '路徑不存在'
    for img_name in sorted(os.listdir(root_path)):
        print(os.path.join(root_path,img_name))
        frames.append(imageio.imread(os.path.join(root_path,img_name)))
    imageio.mimwrite(save_path, frames, duration =0.5)
        
    
if __name__ == '__main__':
    
    
    png_to_gif('/home/youzhe0305/DLP_Final_Project/results/GOPRO/GOPR0854_11_00', '/home/youzhe0305/DLP_Final_Project/GIF_folder/GOPR0854_11_00_deblur.gif')
    png_to_gif('/home/youzhe0305/DLP_Final_Project/dataset/blur/GOPR0854_11_00', '/home/youzhe0305/DLP_Final_Project/GIF_folder/GOPR0854_11_00_blur.gif')

    
    
    