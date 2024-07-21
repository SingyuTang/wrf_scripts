# 替换dstGridName，将NLDAS数据重新网格化，并替换NLDAS_regird输出文件（如2024020100.LDASIN_DOMAIN1）中全部变量中的NAN值为0
ncl 'interp_opt="bilinear"' 'srcGridName="input_files/NLDAS_FORA0125_H.A20240201.0000.002.grb"' 'dstGridName="geo_em.d01.nc"' NLDAS2WRFHydro_generate_weights.ncl
ncl 'srcFileName="NLDAS_FORA0125_H.*"' 'dstGridName="geo_em.d01.nc"' NLDAS2WRFHydro_regrid.ncl
python NLDAS_regrid_data_replaceNAN.py
