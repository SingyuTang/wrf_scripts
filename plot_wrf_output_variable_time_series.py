"""
introduce:
    绘制WRF输出文件wrfout_d0*的各类型图和数据提取
    (1) 提取单一变量并保存为csv文件，默认提取变量名为'RAINNC'，默认保存路径为"./Results/wrfout_singlevar_output.csv"
    (2) 提取降雨并绘制时序图
parameters:
    dirpath: str
        WRF的多个输出文件wrfout_d0*的存放目录
    SHAPEFILEPATH: str,
        自定义研究区域的shapefile文件存放路径
    type: int
        1:  实现introduce中的功能（1）
        2： 实现introduce中的功能（2）,default
    varname: str
        type=1时需要提供的变量名，默认为"RAINNC"

usage:
    main(type=2)

备注：暂时没有wrfout数据用以验证，如有错误等后续对该脚本再进行更正
"""

import netCDF4 as nc
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime
import csv
import wrf
from GPM_draw import read_shapefile_boundaries, round_to_5_with_2_decimals, find_first_last_indices

dirpath = r"./Data/wrfout_files/"
varname = 'RAINNC'
SHAPEFILEPATH = r'./USA_shp/jiazhou_merge.shp'


def wrfout_time_series_singlevar_savecsv(wrfout_dirpath, varname='RAINNC', savepath='./Results/wrfout_singlevar_output.csv'):
    """
    读取所有wrf-hydro输出CHRTOUT文件中的lon，lat、streamflow数据和对应的时间，并输出为csv文件
    :param CHRTOUT_dirpath:WRF的多个输出文件wrfout_d0*的存放目录
    :param savepath: csv文件保存路径
    :return: None
        输出csv文件格式
        每一行代表一个时间点的streamflow数据，文件第一行为经度，第二行为纬度，第一列为时间，中间为数据
    """
    folder = Path(wrfout_dirpath)
    file_paths = sorted([file.absolute() for file in folder.iterdir() if file.is_file()])
    n_file = len(file_paths)
    count = 0
    wrfoutlist = []

    # 读取变量并保存为二维数组，一行代表一个时间点，并读取时间，保存为lons，lats，vars，t
    for filename in file_paths:
        dataset = nc.Dataset(filename)
        wrfoutlist.append(dataset)

        YYYY, MM, DD, HH, mm, ss = filename.stem[11:15], filename.stem[16:18], filename.stem[19:21], filename.stem[22:24], filename.stem[25:27], filename.stem[28:]
        time_str = f'{YYYY}-{MM}-{DD} {HH}:{mm}:{ss}'
        time = np.atleast_2d(datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S'))
        if count == 0:
            t = time
            count = count + 1
        else:
            t = np.vstack((t, time))
            count = count + 1
    var_cat = wrf.to_np(wrf.getvar(wrfoutlist, varname, timeidx=wrf.ALL_TIMES, method='cat'))
    XLONG = wrf.to_np(wrf.getvar(dataset, 'XLONG'))
    XLAT = wrf.to_np(wrf.getvar(dataset, 'XLAT'))

    # 将经度格网XLONG和纬度格网XLAT二维转换为一维列向量lon_arr\lat_arr,并将变量数组var_cat由三维转为二维var_cat_arr,每一行代表一个时间点的变量数据，与降维后的经纬度向量lon_arr\lat_arr中的元素一一对应,可用于后续利用经纬度和对应点变量数据绘图
    time_dim, lon_dim, lat_dim = var_cat.shape
    lon_arr = XLONG.reshape(lon_dim * lat_dim, 1)
    lat_arr = XLAT.reshape(lon_dim * lat_dim, 1)
    var_cat_arr = var_cat.reshape(time_dim, lon_dim * lat_dim)
    output_data = np.hstack((t, var_cat_arr))
    output_data = np.vstack((np.hstack((np.atleast_2d('lat'), lat_arr.T)), output_data))
    output_data = np.vstack((np.hstack((np.atleast_2d('lon'), lon_arr.T)), output_data))

    with open(savepath, 'w', newline="") as f:
        writer = csv.writer(f)
        writer.writerows(output_data)
    print('finished!')

def wrfout_precip_time_series_plot(dirpath:str, shapefile_path:str, variables=['RAINC', 'RAINNC', 'RAINSH']):
    """
    读取wrfout中的降雨量和指定区域的shapefile文件绘制时序图
    :param dirpath: str
        wrfout folder
    :parm shapefile_path: str
        指定区域的shapefile文件路径
    :return:
    """
    # 读取所有文件路径
    folder = Path(dirpath)
    file_paths = sorted([file.absolute() for file in folder.iterdir() if file.is_file()])
    n_file = len(file_paths)
    # 读取经纬度,时间和变量并合并变量,保存为XLONG, XLAT, t, var_sum
    count, count_var = 0, 0
    wrfoutlist = []
    for filename in file_paths:
        dataset = nc.Dataset(filename)
        wrfoutlist.append(dataset)
        YYYY, MM, DD, HH, mm, ss = filename.stem[11:15], filename.stem[16:18], filename.stem[19:21], filename.stem[22:24], filename.stem[25:27], filename.stem[28:]
        time_str = f'{YYYY}-{MM}-{DD} {HH}:{mm}:{ss}'
        time = np.atleast_2d(datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S'))
        if count == 0:
            t = time
            count += 1
        else:
            t = np.vstack((t, time))
            count += 1

    XLONG = wrf.to_np(wrf.getvar(dataset, 'XLONG'))
    XLAT = wrf.to_np(wrf.getvar(dataset, 'XLAT'))


    # 提取变量并合并为var_data_sum: 3-d ndarray
    ex_vars = {}
    count = 0
    for varname in variables:
        var_cat = wrf.to_np(wrf.getvar(wrfoutlist, varname, timeidx=wrf.ALL_TIMES, method='cat'))
        ''' 使用wrf.getvar()函数读取wrfout中的变量数据分布与panoply默认打开一致（西经：东经；南纬：北纬） '''
        """
        var_cat格网格式
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
        ex_vars[varname] = var_cat
        if count == 0:
            ## all_var_cat: 4-d ndarray, 存放根据variables提取的所有文件的所有变量，第一维：变量名，第二维：时间，第三维：经度，第四维：纬度
            all_var_cat = var_cat.reshape(1, var_cat.shape[0], var_cat.shape[1], var_cat.shape[2])
            count += 1
        else:
            var_cat_2 = var_cat.reshape(1, var_cat.shape[0], var_cat.shape[1], var_cat.shape[2])
            all_var_cat = np.concatenate((all_var_cat, var_cat_2), axis=0)
            count += 1

    var_data_sum = np.sum(all_var_cat, axis=0)

    ## 提取shapefile文件内的数据, 制作shapefile_path对应的掩膜文件area_mask2，ndarray
    outline, polygon = read_shapefile_boundaries(shapefile_path)
    round_XLONG = round_to_5_with_2_decimals(XLONG)
    round_XLAT = round_to_5_with_2_decimals(XLAT)
    outline_dec2 = round_to_5_with_2_decimals(outline)
    unique_outline_dec2 = np.unique(outline_dec2, axis=0)
    unique_lon, unique_lat = unique_outline_dec2[:, 0], unique_outline_dec2[:, 1]

    min_rlat, max_rlat = round_XLAT.min(), round_XLAT.max()
    min_rlon, max_rlon = round_XLONG.min(), round_XLONG.max()
    area_mask = np.zeros_like(var_data_sum[0])

    pcol_index = (10 * (- min_rlon + unique_lon)).astype(int)
    prow_index = (10 * (- min_rlat + unique_lat)).astype(int)
    area_mask[prow_index, pcol_index] = 1
    area_mask2 = np.zeros_like(area_mask)

    for row in range(area_mask.shape[0]):
        row_mask = area_mask[row, :]
        first_index, last_index = find_first_last_indices(row_mask, number=1)
        if first_index != 0:
            row_mask[first_index:last_index] = 1
            area_mask2[row, :] = row_mask

    # 计算研究区域均值，生成时序data_time_series_arr
    data_time_series = []
    len_mask_point = np.sum(area_mask2[area_mask2 == 1])
    for index in range(len(file_paths)):
        data = var_data_sum[index]
        mask_data = data * area_mask2
        mask_data[np.isnan(mask_data)] = 0
        inshp_mean_data = np.sum(mask_data) / len_mask_point
        data_time_series.append(inshp_mean_data)

    # 绘制区域降雨时序图
    data_time_series_arr = np.array(data_time_series)
    plt.plot(t, data_time_series_arr)
    plt.show()


def main(type=2):

    if type == 1:
        wrfout_time_series_singlevar_savecsv(dirpath)
    elif type == 2:
        wrfout_precip_time_series_plot(dirpath, SHAPEFILEPATH)
    else:
        raise ValueError("type is wrong.")


if __name__ == "__main__":
    main(type=2)