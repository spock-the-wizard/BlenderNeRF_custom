#!/usr/bash

blend_root="/home/spock-the-wizard/uss_enterprise/2025_viewopt/Dataset/blender_files"
outpath_root="/home/spock-the-wizard/uss_enterprise/2025_viewopt/DatasetVDSF"
blend_root="/path/to/blender/files"
outpath_root="/path/to/dataset/root"
num_views=25
num_views_test=300
num_views_eval=200

scene_list=(
    "record-player"
    # "steamtrain" 
)

for scene in "${scene_list[@]}" 
do
    dataset_name=$scene

    # # even mode
    echo "Even Mode"
    blender -b ${blend_root}/$dataset_name/scene.blend --background --python generate.py -- \
        --mode even --num_views ${num_views} --outpath_root $outpath_root --dataset_name ${dataset_name}_trainview$num_views \
        # --debug

done