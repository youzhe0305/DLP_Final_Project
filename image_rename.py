import os



root_to_rename = 'train_dataset/blur' # xxxx/video/frames 拿xxx

folder_names = sorted(os.listdir(root_to_rename))

for folder_name in folder_names:
    idx = 0
    file_names = sorted(os.listdir(f'{root_to_rename}/{folder_name}'))
    for file_name in file_names:
        print(f'before: {root_to_rename}/{folder_name}/{file_name}')
        os.rename(f'{root_to_rename}/{folder_name}/{file_name}', f'{root_to_rename}/{folder_name}/{idx:06d}.png')
        print(f'after: {root_to_rename}/{folder_name}/{idx:06d}.png')
        idx += 1

