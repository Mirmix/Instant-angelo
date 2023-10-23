
"""
This file is adapted from https://github.com/Fyusion/LLFF.
"""

import os
import sys
import argparse
import subprocess


def run_colmap(basedir, match_type):
    logfile_name = os.path.join(basedir, 'colmap_output.txt')
    logfile = open(logfile_name, 'w')
    
    feature_extractor_args = [
        'colmap', 'feature_extractor', 
            '--database_path', os.path.join(basedir, 'database.db'), 
            '--image_path', os.path.join(basedir, 'images'),
            '--ImageReader.single_camera', '1'
    ]
    feat_output = ( subprocess.check_output(feature_extractor_args, universal_newlines=True) )
    logfile.write(feat_output)
    print('Features extracted')

    exhaustive_matcher_args = [
        'colmap', match_type, 
            '--database_path', os.path.join(basedir, 'database.db'), 
    ]

    match_output = ( subprocess.check_output(exhaustive_matcher_args, universal_newlines=True) )
    logfile.write(match_output)
    print('Features matched')
    
    p = os.path.join(basedir, 'sparse', '0')
    if not os.path.exists(p):
        os.makedirs(p)
    p = os.path.join(basedir, 'model')
    if not os.path.exists(p):
        os.makedirs(p)

    mapper_args = [
        'colmap', 'mapper',
            '--database_path', os.path.join(basedir, 'database.db'),
            '--image_path', os.path.join(basedir, 'images'),
            '--output_path', os.path.join(basedir, 'model'),
            '--Mapper.num_threads', '16',
            '--Mapper.init_min_tri_angle', '4',
            '--Mapper.multiple_models', '0',
            '--Mapper.extract_colors', '0',
    ]

    map_output = ( subprocess.check_output(mapper_args, universal_newlines=True) )
    logfile.write(map_output)
    print('Sparse map created')
    
    # Run point_triangulator to recompute the 3D points with higher thresold
    re_triangulator_args = [
        'colmap', 'point_triangulator',
            '--database_path', os.path.join(basedir, 'database.db'),
            '--image_path', os.path.join(basedir, 'images'),
            '--input_path', os.path.join(basedir, 'model', '0'),
            '--output_path', os.path.join(basedir, 'sparse', '0'),
            '--Mapper.tri_min_angle', '10',
            '--Mapper.tri_merge_max_reproj_error', '1'
    ]

    re_triangulator_output = ( subprocess.check_output(re_triangulator_args, universal_newlines=True) )
    logfile.write(re_triangulator_output)
    logfile.close()
    print('Retriangulation done')
    
    print( 'Finished running COLMAP, see {} for logs'.format(logfile_name) )

    
def gen_poses(basedir, match_type):
    files_needed = ['{}.bin'.format(f) for f in ['cameras', 'images', 'points3D']]
    if os.path.exists(os.path.join(basedir, 'sparse/0')):
        files_had = os.listdir(os.path.join(basedir, 'sparse/0'))
    else:
        files_had = []
    if not all([f in files_had for f in files_needed]):
        print( 'Need to run COLMAP' )
        run_colmap(basedir, match_type)
    else:
        print('Don\'t need to run COLMAP')
    
    return True


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--match_type', type=str, 
                        default='exhaustive_matcher', help='type of matcher used.  Valid options: \
                        exhaustive_matcher sequential_matcher.  Other matchers not supported at this time')
    parser.add_argument('scenedir', type=str,
                        help='input scene directory')
    args = parser.parse_args()

    if args.match_type != 'exhaustive_matcher' and args.match_type != 'sequential_matcher':
        print('ERROR: matcher type ' + args.match_type + ' is not valid.  Aborting')
        sys.exit()    
    if os.path.exists(os.path.join(args.scenedir, 'sparse/0')):
        print('Sparse map ' + args.scenedir + ' exist.  Aborting')
        sys.exit()
    gen_poses(args.scenedir, args.match_type)
