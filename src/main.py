

import os
import re
import argparse

import json
import logging

from k_file import K_File
from k_ifmacro import K_IfMacro

REPORT_PATH="../report"

def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError


def find_source_files(dir_path):
    source_files = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith(".h") or file.endswith(".c"):
                source_files.append(os.path.join(root, file))
    return source_files


def find_configs(config_file_path):
    configs = []
    with open(config_file_path, 'r') as file:
        for line in file:
            configs.append(line.strip())

    return configs


def parse_path_func(k_files, archive_path):
    path_func_res = {}
    func_path_res = {}
    for _k_file in k_files:
        file_path = _k_file.get_relative_path()
        func_list = _k_file.to_dict()["functions"]

        # add record to path func result
        path_func_res[file_path] = func_list
        # add record to func path result
        for _func in func_list:
            if _func not in func_path_res:
                func_path_res[_func] = set()
            func_path_res[_func].add(file_path)

    with open(os.path.join(archive_path, "path_func.json"), "w") as f:
        json.dump(path_func_res, f, indent=4, default=set_default)

    with open(os.path.join(archive_path, "func_path.json"), "w") as f:
        json.dump(func_path_res, f, indent=4, default=set_default)


def parse_config_func(k_files, archive_path):
    func_config_res = {}
    config_func_res = {}
    for _k_file in k_files:
        func_config_relevance = _k_file.get_func_config_relevance()

        # add record to func config result
        for _func in func_config_relevance:
            if _func not in func_config_res:
                func_config_res[_func] = set()

            # add record to config func result
            for _config in func_config_relevance[_func]:
                if _config not in config_func_res:
                    config_func_res[_config] = set()

                func_config_res[_func].add(_config)
                config_func_res[_config].add(_func)

    with open(os.path.join(archive_path, "func_config.json"), "w") as f:
        json.dump(func_config_res, f, indent=4, default=set_default)

    with open(os.path.join(archive_path, "config_func.json"), "w") as f:
        json.dump(config_func_res, f, indent=4, default=set_default)


def parse_config_code(k_files, archive_path):
    config_code_res = {}

    for _k_file in k_files:
        file_path = _k_file.get_relative_path()

        for _ifmacro in _k_file.get_ifmacro_list():
            # print(_ifmacro.get_name())
            for _config in _ifmacro.get_configs():
                if _config not in config_code_res:
                    config_code_res[_config] = []

                _code_block = {
                    "path": file_path,
                    "line_start": _ifmacro.get_if_line_start(),
                    "line_end": _ifmacro.get_endif_line()
                }

                config_code_res[_config].append(_code_block)

    with open(os.path.join(archive_path, "config_code.json"), "w") as f:
        json.dump(config_code_res, f, indent=4, default=set_default)


def parse_arch_related_config_code(k_files, archive_path, arch):
    config_code_res = []

    for _k_file in k_files:
        file_path = _k_file.get_relative_path()

        for _ifmacro in _k_file.get_arch_ifmacro_list():
            _code_block = {
                "path": file_path,
                "line_start": _ifmacro.get_if_line_start(),
                "line_end": _ifmacro.get_endif_line(),
                "arch_related_configs": _ifmacro.get_arch_related_configs()
            }
            config_code_res.append(_code_block)

    with open(os.path.join(archive_path, "{}_related_config_code.json".format(arch)), "w") as f:
        json.dump(config_code_res, f, indent=4, default=set_default)


def parse_arch_related_config_file(archive_path, arch, dir_path):
    config_file_res = {}
    kbuildparse = "../3rd/kbuildparser/kbuildparser"

    dir_path = os.path.relpath(dir_path, start="./")
    cmd = "python2 {} -a {} {}".format(kbuildparse, arch, dir_path)
    out = os.popen(cmd).readlines()

    for line in out:
        substrs = line.strip().split("<-")
        if len(substrs) <= 1:
            continue
        file_path = substrs[0]

        pattern = re.compile(r'CONFIG_[_A-Za-z0-9]+')
        configs = pattern.findall(substrs[1])

        for _config in configs:
            if _config not in config_file_res:
                config_file_res[_config] = set()
            config_file_res[_config].add(file_path.replace(dir_path, "").strip("/"))

    with open(os.path.join(archive_path, "{}_related_config_file.json".format(arch)), "w") as f:
        json.dump(config_file_res, f, indent=4, default=set_default)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--src-path", help="Path to the source dir")
    parser.add_argument("-n", "--src-name", help="Source version")
    parser.add_argument("-r", '--relate-arch', action='store_true', required=False, help="parse configs reletive to arch")
    parser.add_argument("-c", '--config-file', required=False, help="arch reletive configs")

    args = parser.parse_args()

    src_path = args.src_path
    src_version = args.src_name
    source_files = find_source_files(src_path)

    # source_files = ["/root/linux_6_6/arch/ia64/include/asm/pgtable.h"]
    # source_files = ["/root/linux_6_6/drivers/video/fbdev/aty/radeon_pm.c"]

    k_files = []
    for _file in source_files:
        _k_file = K_File(_file, src_path)
        _k_file.parse_func()
        _k_file.parse_ifmacro()
        _k_file.parse_func_config_relevance()

        k_files.append(_k_file)

    archive_path = os.path.join(REPORT_PATH, src_version)
    if not os.path.exists(archive_path):
        os.makedirs(archive_path)

    parse_path_func(k_files, archive_path)
    parse_config_func(k_files, archive_path)
    parse_config_code(k_files, archive_path)

    ## find code relative to arch
    if args.relate_arch:
        with open(args.config_file, "r") as config_file:
            arch_dicts = json.load(config_file)
            for arch in arch_dicts:
                # parse code block relative to arch
                arch_config_file_path = arch_dicts[arch]
                arch_configs = find_configs(arch_config_file_path)
                for _k_file in k_files:
                    _k_file.parse_code_arch_relevance(arch_configs)
                parse_arch_related_config_code(k_files, archive_path, arch)

                # parse file relative to arch
                parse_arch_related_config_file(archive_path, arch, src_path)

def init():
    logging.basicConfig(level=logging.DEBUG)


if __name__=="__main__":
    init()
    main()
