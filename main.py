

import os
import argparse

import json
import logging

from k_file import K_File
from k_ifmacro import K_IfMacro

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


def parse_path_func(k_files, src_version):
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

    with open(os.path.join(src_version, "path_func.json"), "w") as f:
        json.dump(path_func_res, f, indent=4, default=set_default)

    with open(os.path.join(src_version, "func_path.json"), "w") as f:
        json.dump(func_path_res, f, indent=4, default=set_default)


def parse_config_func(k_files, src_version):
    func_config_res = {}
    config_func_res = {}
    for _k_file in k_files:
        file_path = _k_file.get_relative_path()
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


    with open(os.path.join(src_version, "func_config.json"), "w") as f:
        json.dump(func_config_res, f, indent=4, default=set_default)

    with open(os.path.join(src_version, "config_func.json"), "w") as f:
        json.dump(config_func_res, f, indent=4, default=set_default)



def parse_config_code(k_files, src_version):
    pass



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dir_path", help="Path to the source dir")
    parser.add_argument("src_version", help="Dir to save result")
    args = parser.parse_args()

    dir_path = args.dir_path
    src_version = args.src_version
    source_files = find_source_files(dir_path)

    # source_files = ["/root/linux_6_6/net/ipv4/tcp.c"]
    # source_files = ["/root/linux_6_6/lib/zstd/decompress/zstd_decompress_internal.h"]

    k_files = []
    for _file in source_files:
        _k_file = K_File(_file, dir_path)
        _k_file.parse_func()
        _k_file.parse_ifmacro()
        _k_file.parse_func_config_relevance()
        # print(_k_file.to_json_detail())

        k_files.append(_k_file)

    if not os.path.exists(src_version):
        os.makedirs(src_version)

    parse_path_func(k_files, src_version)
    parse_config_func(k_files, src_version)
    parse_config_code(k_files, src_version)


def init():
    logging.basicConfig(level=logging.DEBUG)

if __name__=="__main__":
    init()
    main()
