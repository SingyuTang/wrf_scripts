"""
introduce:
    脚本用于绘制GPM时序图
    GPM数据来源：GPM IMERG Early Precipitation L3 Half Hourly 0.1 degree x 0.1 degree V06 (GPM_3IMERGHHE) at GES DISC
    https://search.earthdata.nasa.gov/search/granules?p=C1598621094-GES_DISC&pg[0][v]=f&pg[0][gsk]=-start_date&q=GPM&tl=1721559804.175!3!!

    所有用户都必须在 Earthdata 登录系统上注册才能访问 GES DISC 数据，可通过下面链接注册
        [earthdata login](https://urs.earthdata.nasa.gov/oauth/authorize?response_type=code&redirect_uri=http%3A%2F%2Fdisc.gsfc.nasa.gov%2Flogin%2Fcallback&client_id=C_kKX7TXHiCUqzt352ZwTQ)
    其它关于Earthdata数据访问问题及流程可查看下面链接
        https://disc.gsfc.nasa.gov/information/documents?title=Data%20Access
parameters:
        dirname: str,  GPM数据存放目录
        SHAPEFILEPATH: str, 自定义研究区域的shapefile文件存放路径
        main()函数提供1个参数(type)
            type = 1: 绘制时序图
            type = 2: 绘制降雨空间分布图
usage：
    main(type=1)
    无输出
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path, PosixPath
import h5py, shapely
import shapefile
from shapely.ops import cascaded_union, unary_union
from shapely.geometry import Point, Polygon
from datetime import datetime, timedelta

from mpl_toolkits.basemap import Basemap
import geopandas as gpd
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

dirname = r'./Data/GPM'
SHAPEFILEPATH = r'./Data/USA_shp/jiazhou_merge.shp'

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

def GPM_readdata(dirname:str, variable='precipitationCal'):
    """
        批量读取GPM文件的单个变量
    :param dirname:
    :param variable: 变量名
    :return:
        data: np.ndarray
        lon: np.ndarray
        lat: np.ndarray
        time_arr np.ndarray
    """
    filenames, fullabspaths = get_filenames(dirname, suffix='.HDF5')
    count = 0
    time_list = []
    since_time = datetime.strptime('1970-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    for filepath in fullabspaths:
        with h5py.File(filepath, 'r') as f:
            if count == 0:
                data = f['Grid'][variable][:]
                lon = f['Grid']['lon'][:]
                lat = f['Grid']['lat'][:]
                interval_seconds = float(f['Grid']['time'][:][0])
                time = timedelta(seconds=interval_seconds) + since_time
                time_list.append(time)
                count += 1
            else:
                data_1 = f['Grid'][variable][:]
                data = np.concatenate((data, data_1), 0)
                interval_seconds = float(f['Grid']['time'][:][0])
                time = timedelta(seconds=interval_seconds) + since_time
                time_list.append(time)
                count += 1
    time_arr = np.array(time_list)
    # # 替换-9999
    data[data < 0] = np.nan
    return data, lon, lat, time_arr

def read_shapefile_boundaries(shapefile_path:str):
    """
    读取shapefile文件（line），并输出边界点的经纬度，分为两种类型，POLYGON 和 np.ndarray
    :param shapefile_path:
    :return:
        边界点的经纬度
        poly: POLYGON
        outline: np.ndarray
    """
    gdf = gpd.read_file(shapefile_path)
    shp = shapefile.Reader(shapefile_path)
    rec = shp.shapeRecords()
    polygon = []
    for r in rec:
        polygon.append(Polygon(r.shape.points))
    poly = unary_union(polygon)  #POLYGON
    outline = np.array(list(poly.exterior.coords))  # ndarray

    # longitudes = outline[:, 0]
    # latitudes = outline[:, 1]
    # #
    # lon = longitudes[::20]
    # lat = latitudes[::20]
    return outline, poly

def round_to_5_with_2_decimals(arr):
    """
    numpy数组保留两位小数，根据第二位小数决定向5靠近
    :param arr:
    :return:
    """
    # 保留两位小数
    arr = np.round(arr, 2)
    arr = np.floor(arr * 10) / 10 + 0.05
    return arr

def find_first_last_indices(arr, number):
    """
    找到一维数组中第一个为number和最后一个为number的元素的索引
    :param arr: ndarray
    :param number: int | float
    :return:
        int, int
        数组中第一个为number和最后一个为number的元素的索引
    """
    if len(arr) == 1:
        if arr[0] == number:
            first_index, last_index = 0, 0
        else:
            first_index, last_index = np.nan, np.nan
    elif len(arr) == 2:
        if arr[0] == number & arr[1] == number:
            first_index, last_index = 0, 1
        elif arr[0] == number & arr[1] != number:
            first_index, last_index = 0, 0
        elif arr[0] != number & arr[1] == number:
            first_index, last_index = 1, 1
        else:
            first_index, last_index = np.nan, np.nan
    else:
        is_exist = number in arr
        if is_exist == False:
            first_index, last_index = 0, 0
        else:
            first_index = int(np.argmax(arr == number))
            last_index = int(len(arr) - np.argmax(arr[::-1] == number) - 1)
    return first_index, last_index

def get_in_shape_time_series(dirname:str, shapefile_path:str):
    """
    读取GPM中的降雨量和指定区域的shapefile文件并返回时序
    :param dirname:
    :param shapefile_path:
    :return:
        time_arr: np.ndarray(1-D)

        precip_time_series_arr: np.ndarray(1-D)

    """
    # read precipitation data
    precip, lon, lat, time_arr = GPM_readdata(dirname)

    # 制作shapefile_path对应的掩膜文件global_mask2，ndarray
    outline, polygon = read_shapefile_boundaries(shapefile_path)
    ## 保留两位小数，并使最后一位小数为5
    outline_dec2 = round_to_5_with_2_decimals(outline)
    unique_outline_dec2 = np.unique(outline_dec2, axis=0)
    unique_lon, unique_lat = unique_outline_dec2[:, 0], unique_outline_dec2[:, 1]
    ## plt.scatter(unique_lon, unique_lat)
    global_mask = np.zeros_like(precip[0].T)
    pcol_index = (10 * (179.95 + unique_lon)).astype(int)
    prow_index = (10 * (89.95 + unique_lat)).astype(int)
    global_mask[prow_index, pcol_index] = 1
    global_mask2 = np.zeros_like(global_mask)
    """
    global_mask, global_mask2格网格式
                -179.95 -179.85 ......179.85 179.95     -----longitude
        -89.95      *       *      *    *       *
        -89.85      *       *      *    *       *
           .        *       *      *    *       *
           .        *       *      *    *       *
           .        *       *      *    *       *
        89.85       *       *      *    *       *
        89.95       *       *      *    *       *
          |
          |
          |
        latitude        
    """
    # 绘制区域降雨时序图
    precip_time_series = []
    for i in range(len(time_arr)):
        data = precip[i].T
        """
        data = precip[0].T格网格式
                -179.95 -179.85 ......179.85 179.95     -----longitude
        -89.95      *       *      *    *       *
        -89.85      *       *      *    *       *
           .        *       *      *    *       *
           .        *       *      *    *       *
           .        *       *      *    *       *
        89.85       *       *      *    *       *
        89.95       *       *      *    *       *
          |
          |
          |
        latitude
        """



        for row in range(len(lat)):
            row_mask = global_mask[row, :]
            first_index, last_index = find_first_last_indices(row_mask, number=1)
            if first_index != 0:
                row_mask[first_index:last_index] = 1
                global_mask2[row, :] = row_mask
        len_mask_point = np.sum(global_mask2[global_mask2 == 1])
        mask_data = data * global_mask2
        mask_data[np.isnan(mask_data)] = 0
        inshp_mean_data = np.sum(mask_data) / len_mask_point
        precip_time_series.append(inshp_mean_data)
    precip_time_series_arr = np.array(precip_time_series)
    return time_arr, precip_time_series_arr

def plot_precip_map(dirname:str, count=1):
    """
        绘制GPM文件的降雨分布图（单个文件）
    :param dirname:  str
        GPM 文件夹路径
    :param count:   int
        第count个文件
    :return:
    """
    precip, lon, lat, time_list = GPM_readdata(dirname)
    fig, ax = plt.subplots(figsize=(12, 8))

    m = Basemap(projection="cyl", llcrnrlat=min(lat), urcrnrlat=max(lat),
                llcrnrlon=min(lon), urcrnrlon=max(lon), resolution='i')
    m.drawparallels(np.arange(-90, 91, 30), labels=[1,0,0,0], linewidth=0)
    m.drawmeridians(np.arange(-180, 181, 60), labels=[0,0,0,1], linewidth=0)
    m.drawcoastlines()
    m.drawcountries()
    # m.drawrivers(color='blue')

    mlon, mlat = np.meshgrid(lon, lat)
    x, y = m(lon, lat)

    cmap = plt.get_cmap('jet')
    cs = m.pcolormesh(x, y, precip[count-1].T, cmap=cmap, shading='auto')


    cbar = m.colorbar(cs, location='bottom', pad='10%')
    cbar.set_label('PreciptationCal(mm/hr)')
    plt.title('PrecipitaionCal')
    plt.show()

def plot_GPM_time_series(dirname:str, shapefile_path=SHAPEFILEPATH):

    time_arr, precip_time_series_arr = get_in_shape_time_series(dirname, shapefile_path)
    plt.plot(time_arr, precip_time_series_arr)
    plt.show()

def main(type=1):

    if type == 1:
        # 绘制时序图
        plot_GPM_time_series(dirname)
    elif type == 2:
        # 绘制单个GPM文件降雨分布图, ubuntu
        plot_precip_map(dirname)

if __name__ == "__main__":
    main(type=2)
