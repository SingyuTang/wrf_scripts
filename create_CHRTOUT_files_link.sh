#!/bin/bash
# 为wrf-hydro输出的CHRTOUT文件创建链接并剪切到指定文件夹，方便后续绘图
folder="/home/root123/coding/WRF_Hydro/wrf_hydro_nwm_public-5.2.0/trunk/NDHMS/Run(CA)/"
target_folder="/home/root123/coding/wrf_extra_scripts/CHRTOUT_files/"

files=$(find "$folder" -type f -name "*CHRTOUT*")

for file in $files;do
    filename=$(basename "$file")
    ln -s "$file" "link_$filename"
done

echo "created links successfully!"

mv link_* "$target_folder"

echo "moved links successfully!"

cd $target_folder
rename 's/link_//' *

echo "renamed files successfully!"

