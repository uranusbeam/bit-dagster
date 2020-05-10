import copy
import os
import zipfile

import six

from dagster import check
from dagster.utils import file_relative_path


def subset_environment_dict(environment_dict, solid_name):
    '''Drops solid config for solids other than solid_name; this subsetting is required when
    executing a single solid on EMR to pass config validation.
    '''
    check.dict_param(environment_dict, 'environment_dict')
    check.str_param(solid_name, 'solid_name')

    subset = copy.deepcopy(environment_dict)
    if 'solids' in subset:
        solid_config_keys = list(subset['solids'].keys())
        for key in solid_config_keys:
            if key != solid_name:
                del subset['solids'][key]
    return subset


def build_main_file(
    main_file, mode_name, pipeline_file, solid_name, environment_dict, pipeline_fn_name
):
    with open(file_relative_path(__file__, 'main.py.template'), 'rb') as f:
        main_template_str = six.ensure_str(f.read())

    with open(main_file, 'wb') as f:
        f.write(
            six.ensure_binary(
                main_template_str.format(
                    mode_name=mode_name,
                    pipeline_file=os.path.splitext(os.path.basename(pipeline_file))[0],
                    solid_name=solid_name,
                    environment_dict=subset_environment_dict(environment_dict, solid_name),
                    pipeline_fn_name=pipeline_fn_name,
                )
            )
        )


def build_pyspark_zip(zip_file, path):
    '''Archives the current path into a file named `zip_file`
    '''
    check.str_param(zip_file, 'zip_file')
    check.str_param(path, 'path')

    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(path):
            for fname in files:
                abs_fname = os.path.join(root, fname)

                # Skip various artifacts
                if 'pytest' in abs_fname or '__pycache__' in abs_fname or 'pyc' in abs_fname:
                    continue

                zf.write(abs_fname, os.path.relpath(os.path.join(root, fname), path))
