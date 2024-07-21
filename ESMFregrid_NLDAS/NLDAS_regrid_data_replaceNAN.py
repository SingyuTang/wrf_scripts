"""
introduce:
    脚本用于替换NLDAS_regird输出文件（如2024020100.LDASIN_DOMAIN1）中全部变量中的NAN值为0
    数据来源：ESMFregrid_NLDAS脚本重新网格化后的数据（如2024020100.LDASIN_DOMAIN1）
        ESMFregrid_NLDAS脚本包括:   (1) NLDAS2WRFHydro_generate_weights.ncl
                                  (2) NLDAS2WRFHydro_regrid.ncl
        ESMFregrid_NLDAS下载链接：https://ral.ucar.edu/sites/default/files/public/ESMFregrid_NLDAS.tar_.gz

parameters:
    dirname: str
        NLDAS_regird data(如2024020100.LDASIN_DOMAIN1) 的存放目录
usage:
    main()
    无输出
"""
import os
import netCDF4 as nc
import numpy as np
from pathlib import Path
import tqdm


dirname = r'./Data/NLDAS_regrid'
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

def replace_nan_with_zero(filepath):
    '''
    替换NLDAS_regird输出文件中全部变量中的NAN值为0
    :param filepath:
    :return:
    '''
    with nc.Dataset(filepath, 'r+') as dataset:

        variables_data = dataset.variables
        for varname in variables_data:
            variable = variables_data[varname]

            if variable.dtype.kind in {'f'}:
                data = variable[:]
                if isinstance(data, np.ma.MaskedArray):
                    data = np.ma.filled(data, 0)
                else:
                    data[np.isnan(data)] = 0
                variable[:] = data
    print(f"{filepath}中的所有NAN值已替换为0")

def delete_variable(nc_file, varname):
    """
    删除文件中的某个变量，如'lon','lat'等
    :param nc_file:
    :param varname:
    :return:
    """
    src_ds = nc.Dataset(nc_file, 'r')
    tmp_file = nc_file + '.tmp'
    dst_ds = nc.Dataset(tmp_file, 'w')

    for name in src_ds.ncattrs():
        dst_ds.setncattr(name, src_ds.getncattr(name))

    for name, dimension in src_ds.dimensions.items():
        dst_ds.createDimension(name, (len(dimension) if not dimension.isunlimited() else None))

    for name, variable in src_ds.variables.items():
        if name != varname:
            dst_var = dst_ds.createVariable(name, variable.datatype, variable.dimensions)
            dst_var.setncatts({k: variable.getncattr(k) for k in variable.ncattrs()})
            dst_var[:] = variable[:]

    src_ds.close()
    dst_ds.close()

    os.remove(nc_file)
    os.rename(tmp_file, nc_file)

    print(f"{nc_file}中的{varname}变量已删除")


def main():
    filepaths, fullabspaths = get_filenames(dirname, suffix='.LDASIN_DOMAIN1')
    print(f'{dirname}目录下的所有xxxxxxx.LDASIN_DOMAIN1文件正在替换变量中的nan值...')
    for filepath in tqdm.tqdm(filepaths, ncols=80, desc="replace progress"):
        # delete_variable(str(filepath), 'lat')
        # delete_variable(str(filepath), 'lon')
        replace_nan_with_zero(filepath)

if __name__ == "__main__":
    main()


