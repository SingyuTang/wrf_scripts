"""

introduce:
    （1）读取WRF-Hydro的输出文件（如202402010000.CHRTOUT_DOMAIN1）绘制河道流量专题地图
        无输出文件
     (2) 批量读取WRF-Hydro的多个输出文件（如202402010000.CHRTOUT_DOMAIN1）的存放目录绘制河道流量专题地图，并另外输出一张全部专题地图的拼接图
        输出存放目录默认为 "./Results/CHRTOUT_output_figs/"
    （3）读取WRF-Hydro的多个输出文件（如202402010000.CHRTOUT_DOMAIN1）并提取streamflow变量到csv文件中
        输出文件路径默认为 "./Results/CHRTOUT streamflow output time series.csv"

parameter:
    dirpath: str
        WRF-Hydro的多个输出文件的存放目录
    filepath: str
        WRF-Hydro的输出文件的文件路径
    type: int
        1:  实现introduce中的功能（1）
        2： 实现introduce中的功能（2）,default
        3： 实现introduce中的功能（2）
    SHAPEFILEPATH: str,
        自定义研究区域的shapefile文件存放路径

usage:
    main(type=2)
"""
import os, sys, platform
import pathlib
import shutil
import netCDF4 as nc
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
import shapefile
from pathlib import Path, PosixPath
from datetime import datetime
import csv
from PIL import Image
import math
import tqdm

type = 3
SHAPEFILEPATH = r"./Data/USA_shp/jiazhou_merge.shp"
dirpath = r"./Data/CHRTOUT_files"
filepath = r'./Data/CHRTOUT_files/202402010100.CHRTOUT_DOMAIN1'

def get_platform_name():
    """
    获取当前操作系统名
    :return:
    """
    if sys.platform.startswith('linux'):
        return "linux"
    elif sys.platform.startswith('win'):
        return "windows"
    elif sys.platform.startswith('darwin'):
        return "macos"
    else:
        print('无法识别当前系统')
        sys.exit()

CURRENT_PLATFORM = get_platform_name()

def get_filenames(dirname:str, suffix):
    '''
    根据文件夹路径和后缀获取文件夹下的文件名
    :param dirname: str
    :param suffix: str
    :return:
        文件夹下的文件名
        filepaths: list[PosixPath]
        fullabspaths:list[PosixPath]
    '''
    dir_path = Path(dirname)
    filepaths = sorted([f for f in dir_path.glob(f'*{suffix}')])
    # 按照文件名排序并返回绝对路径
    fullabspaths = [filepath.resolve() for filepath in filepaths]
    return filepaths, fullabspaths

def concat_images_grid(image_paths, ncols):
    """
    拼接多张图片为一张图片
    :param image_paths: list[str] | list[PosixPath]
        图片路径列表，后缀必须一样
    :param ncols: int
        拼接后的图片每行的张数
    :return:
    """
    # Open all images and store them in a list
    images = [Image.open(img_path) for img_path in image_paths]

    # Get the dimensions of each image
    widths, heights = zip(*(i.size for i in images))

    # Calculate the dimensions of the grid
    max_width = max(widths)
    max_height = max(heights)
    num_images = len(images)

    num_rows = math.ceil(num_images / ncols)
    grid_width = ncols * max_width
    grid_height = num_rows * max_height

    # Create a new blank image with the size of the grid
    new_im = Image.new('RGB', (grid_width, grid_height))

    # Paste each image into the new image grid
    for index, im in enumerate(images):
        row = index // ncols
        col = index % ncols
        x_offset = col * max_width
        y_offset = row * max_height
        new_im.paste(im, (x_offset, y_offset))

    return new_im

def plot_streamflow_map(filepath, output_type='show'):
    """
    读取文件中的longitude, latitude, streamflow三个变量并绘制河道流量专题地图，
    数据来源WRF-Hydro输出文件，如"202402092200.CHRTOUT_DOMAIN1"
    :param filepath: str | PosixPath
        CHRTOUT_DOMAIN1文件路径
    :param output_type: str
        'show'：仅显示不保存
        'save'：保存但不显示
    :return: None
    """

    dataset = nc.Dataset(filepath)
    longitude = dataset.variables['longitude'][:]
    latitude = dataset.variables['latitude'][:]
    streamflow = dataset.variables['streamflow'][:]

    fig, ax = plt.subplots(figsize=(8, 6))

    m = Basemap(projection="cyl", llcrnrlat=min(latitude), urcrnrlat=max(latitude),
                llcrnrlon=min(longitude), urcrnrlon=max(longitude), resolution='i')

    m.drawcoastlines()
    m.drawcountries()
    m.drawrivers(color='blue')

    x, y = m(longitude, latitude)
    size = np.array(streamflow) / max(streamflow) * 100
    scatter = m.scatter(x, y, s=size, c=streamflow, cmap='jet', linewidth=0.5, alpha=0.5, edgecolors='k')
    cbar = m.colorbar(scatter, location='right', pad='5%')
    cbar.set_label('Stramflow')

    shpfile_path = SHAPEFILEPATH
    sf = shapefile.Reader(shpfile_path)

    for shape_rec in sf.shapeRecords():
        shape = shape_rec.shape
        points = shape.points
        parts = list(shape.parts) + [len(points)]
        for i in range(len(parts) - 1):
            segment = points[parts[i]:parts[i + 1]]
            lngs, lats = zip(*segment)
            x, y = m(lngs, lats)
            m.plot(x, y, marker=None, color='red')


    if CURRENT_PLATFORM == "linux":
        Date = PosixPath(filepath).resolve().parts[-1].split('.')[0]
    elif CURRENT_PLATFORM == 'windows':
        abspath = os.path.abspath(filepath)
        Date = abspath.split("\\")[-1].split(".")[0]
    plt.title(f'{Date} Streamflow Map(WGS84 Coordinate System)')

    if output_type == 'show':
        plt.show()
    elif output_type == "save":
        if CURRENT_PLATFORM == "linux":
            fig_savedir = PosixPath(r"./Results").joinpath('CHRTOUT_output_figs')
            filename = Date + '_CHRTOUT' + '.png'
            fig_savepath = fig_savedir.joinpath(PosixPath(filename))
        elif CURRENT_PLATFORM == 'windows':
            fig_savedir = os.path.join(os.path.abspath(r"./Results"), 'CHRTOUT_output_figs')
            filename = Date + '_CHRTOUT' + '.png'
            fig_savepath = os.path.join(fig_savedir, filename)
        plt.savefig(fig_savepath)
        plt.clf()

def read_CHRTOUT_streamflow_save_multi_fig(data_dir:str):

    filepaths, _ = get_filenames(data_dir, suffix='.CHRTOUT_DOMAIN1')
    if CURRENT_PLATFORM == "linux":
        fig_savedir = str(PosixPath(r"./Results").joinpath('CHRTOUT_output_figs')    )         # PosixPath -> str
    elif CURRENT_PLATFORM == 'windows':
        fig_savedir = os.path.join(os.path.abspath(r"./Results"), 'CHRTOUT_output_figs')  # str
    if os.path.exists(fig_savedir):
        shutil.rmtree(fig_savedir)
    os.mkdir(fig_savedir)
    for filepath in tqdm.tqdm(filepaths, ncols=80, desc="plot streamflow progress"):
        plot_streamflow_map(filepath, output_type='save')

    image_paths, _ = get_filenames(fig_savedir, '.png')
    imagepath_list = [str(imagepath) for imagepath in image_paths]
    result_image = concat_images_grid(imagepath_list, 12)
    result_image.save(fig_savedir + '/concat_image.jpg')

def time_series_CHRTOUT_streamflow_to_csv(CHRTOUT_dirpath:str):
    """
    读取所有wrf-hydro输出CHRTOUT文件中的lon，lat、streamflow数据和对应的时间，并输出为csv文件
    :param CHRTOUT_dirpath:
    :return: 输出csv文件格式
    每一行代表一个时间点的streamflow数据，文件第一行为经度，第二行为纬度，第一列为时间，中间为数据
    """
    file_paths, _ = get_filenames(CHRTOUT_dirpath, suffix='.CHRTOUT_DOMAIN1')
    n_file = len(file_paths)
    count = 0
    # 读取变量并保存为二维数组，一行代表一个时间点，并读取时间，保存为lons，lats，stfs，t
    for filename in file_paths:
        dataset = nc.Dataset(filename)
        longitude = np.atleast_2d(dataset.variables['longitude'][:])
        latitude = np.atleast_2d(dataset.variables['latitude'][:])
        streamflow = np.atleast_2d(dataset.variables['streamflow'][:])
        YYYY, MM, DD, HH, mm, ss = filename.stem[0:4], filename.stem[4:6], filename.stem[6:8], filename.stem[8:10], filename.stem[10:], '00'
        time_str = f'{YYYY}-{MM}-{DD} {HH}:{mm}:{ss}'
        time = np.atleast_2d(datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S'))
        if count == 0:
            lons = longitude
            lats = latitude
            stfs = streamflow
            t = time
            count = count + 1
        else:
            lons = np.vstack((lons, longitude))
            lats = np.vstack((lats, latitude))
            stfs = np.vstack((stfs, streamflow))
            t = np.vstack((t, time))
            count = count + 1
    output_data = np.hstack((t, stfs))
    output_data = np.vstack((np.hstack((np.atleast_2d('lat'), latitude)), output_data))
    output_data = np.vstack((np.hstack((np.atleast_2d('lon'), longitude)), output_data))
    if CURRENT_PLATFORM == "linux":
        savepath = PosixPath(r"./Results").resolve().joinpath('CHRTOUT streamflow output time series.csv')
    elif CURRENT_PLATFORM == 'windows':
        savepath = os.path.join(os.path.abspath(r"./Results"), 'CHRTOUT streamflow output time series.csv')  # str
    with open(savepath, 'w', newline="") as f:
        writer = csv.writer(f)
        writer.writerows(output_data)
    print('save finished! CHRTOUT streamflow output time series.csv ---> ./Results')


def main(type=2):
    if type == 1:
        plot_streamflow_map(filepath, output_type='show')
    elif type == 2:
        read_CHRTOUT_streamflow_save_multi_fig(dirpath)
    elif type == 3:
        time_series_CHRTOUT_streamflow_to_csv(dirpath)
    else:
        raise ValueError("type is wrong.")

if __name__ == "__main__":
    main(type=type)
