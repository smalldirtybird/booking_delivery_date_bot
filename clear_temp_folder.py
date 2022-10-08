import platform
import os
import shutil


def clear_temp_folder():
    pathname_templates = ['rust_mozprofile', 'tmp']
    if platform.system() == 'Linux':
        tempfolder = '/tmp'
    tempfolder_content = os.listdir(tempfolder)
    for element in tempfolder_content:
        element_path = os.path.join(tempfolder, element)
        for template in pathname_templates:
            if os.path.isdir(element_path) and template in element:
                shutil.rmtree(element_path)
    print(tempfolder, 'clear.')


if __name__ == '__main__':
    clear_temp_folder()
