from pathlib import Path


def get_rockets_frames():
    rocket_frames = []
    for file_name in ['rocket_frame_1.txt', 'rocket_frame_2.txt']:
        with open(f'animations/{file_name}', "r", encoding="UTF-8") as rocket_frame_file:
            rocket_frames.append(rocket_frame_file.read())
    return rocket_frames


def get_garbage_frames():
    garbage_frames = []
    garbage_file_names = ['duck.txt',
                          'hubble.txt',
                          'lamp.txt',
                          'trash_large.txt',
                          'trash_small.txt',
                          'trash_xl.txt']
    for garbage_file_name in garbage_file_names:
        with open(f'animations/{garbage_file_name}', "r", encoding="UTF-8") \
                as trash_frame_file:
            garbage_frames.append(trash_frame_file.read())

    return garbage_frames
