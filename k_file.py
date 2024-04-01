
import os
import json
import logging

from k_ifmacro import K_IfMacro
from k_func import K_Func


class K_File():

    def __init__(self, path, dir_path):
        self._path = path
        self._dir_path = dir_path

        self._func_list = []
        self._ifmacro_list = []
        self._func_config_relevance = {}


    def parse_func(self):
        _cmd = "/usr/bin/ctags --fields=ne --c-types=f -o - {}".format(self._path)
        logging.debug("[Run CMD] {}".format(_cmd))
        _out = os.popen(_cmd).readlines()
        for _line in _out:

            # example:
            # tcp_read_skb	/root/linux/net/ipv4/tcp.c	/^int tcp_read_skb(struct sock *sk, skb_read_actor_t recv_actor)$/;"	line:1628	end:1655
            # tcp_read_sock	/root/linux/net/ipv4/tcp.c	/^int tcp_read_sock(struct sock *sk, read_descriptor_t *desc,$/;"	line:1554	end:1625
            # tcp_recv_skb	/root/linux/net/ipv4/tcp.c	/^struct sk_buff *tcp_recv_skb(struct sock *sk, u32 seq, u32 *off)$/;"	line:1518	end:1540
            _strs = _line.strip().split("\t")

            _func_name = _strs[0]
            _line_sta  = _strs[-2].strip("line:")
            _line_end  = _strs[-1].strip("end:")

            _func = K_Func(self._path, _func_name, _line_sta, _line_end)
            self._func_list.append(_func)


    def parse_ifmacro(self):
        line_number = 1
        backslash_flag = False
        ifdef_flag = False

        ifdef_stack = []
        with open(self._path, 'r', encoding="UTF-8") as file:
            l_if_sta = 0
            l_if_end = 0
            l_endif = 0

            for line in file:
                # logging.debug("CODE: {}".format(line.strip()))

                # skip #ifdef, #endf in code generate, like "tools/bpf/bpftool/gen.c"
                # 	codegen("\
                #        \n\
                #        #ifdef __cplusplus					    \n\
                #        #undef _Static_assert					    \n\
                #        #endif							    \n\
                #        }							    \n\
                #        ");
                #
                if "\\n\\" in line:
                    line_number += 1
                    continue

                if backslash_flag and ifdef_flag:
                    ifmacro = ifdef_stack.pop()
                    ifmacro.set_macro_str("{} {}".format(ifmacro.get_name()), line.strip().strip("\\"))
                    ifmacro.set_line_end(line_number)
                    ifdef_stack.append(ifmacro)

                if line.strip().startswith("#if") or \
                    line.strip().startswith("# if") or \
                    line.strip().startswith("#  if"):
                    # logging.debug("#if line: {}".format(line.strip()))
                    ifdef_flag = True
                    l_if_sta = line_number
                    l_if_end = line_number
                    l_endif = line_number
                    ifmacro_str = line.strip().strip("\\")
                    ifmacro = K_IfMacro(ifmacro_str, l_if_sta, l_if_end, l_endif)
                    ifdef_stack.append(ifmacro)

                elif line.strip().startswith("#endif") or \
                    line.strip().startswith("# endif") or \
                    line.strip().startswith("#  endif"):
                    ifmacro = ifdef_stack.pop()
                    ifmacro.set_line_end(line_number)
                    ifmacro.parse_config()
                    self._ifmacro_list.append(ifmacro)
                    ifdef_flag = False

                elif line.strip().startswith("#else") or \
                    line.strip().startswith("# else") or \
                    line.strip().startswith("#  else") or \
                    line.strip().startswith("#elif") or \
                    line.strip().startswith("# elif") or \
                    line.strip().startswith("#  elif"):
                    # end last #if macro
                    ifmacro = ifdef_stack.pop()
                    ifmacro.set_line_end(line_number)
                    ifmacro.parse_config()
                    self._ifmacro_list.append(ifmacro)

                    # start a new #if macro
                    l_if_sta = line_number
                    l_if_end = line_number
                    l_endif = line_number
                    ifmacro_str = "{} {}".format(ifmacro.get_name(), line.strip().strip("\\"))
                    ifmacro = K_IfMacro(ifmacro_str, l_if_sta, l_if_end, l_endif)
                    ifdef_stack.append(ifmacro)

                if line.strip().endswith("\\"):
                    backslash_flag = True
                else:
                    backslash_flag = False
                    ifdef_flag = False

                line_number += 1

        if ifdef_stack:
            logging.fatal("Unexpected ifdef stack error for path {}".format(self._path))

    def _is_relevant(self, k_func, k_ifmacro):
        k_func_sta = k_func.get_line_start()
        k_func_end = k_func.get_line_end()

        k_ifmacro_sta = k_ifmacro.get_if_line_start()
        k_ifmacro_end = k_ifmacro.get_endif_line()

        if (max(k_func_sta, k_ifmacro_sta) < min(k_func_end, k_ifmacro_end)):
            return True
        return False

    def parse_func_config_relevance(self):
        for _func in self._func_list:
            _func_name = _func.get_name()
            if _func_name not in self._func_config_relevance:
                self._func_config_relevance[_func_name] = set()

            for _ifmacro in self._ifmacro_list:
                if self._is_relevant(_func, _ifmacro):
                    for _config in _ifmacro.get_configs():
                        self._func_config_relevance[_func_name].add(_config)

    def get_relative_path(self):
        return self._path.replace(self._dir_path, '', 1).strip("/")

    def get_ifmacro_list(self):
        return self._ifmacro_list

    def get_func_list(self):
        return self._func_list

    def get_func_config_relevance(self):
        return self._func_config_relevance

    def to_dict(self):
        res = {}

        func_list = []
        for _func in self._func_list:
            func_list.append(_func.get_name())


        macro_list = []
        for _ifmacro in self._ifmacro_list:
            macro_list.append(_ifmacro.get_name())

        res["functions"] = func_list
        res["ifmacros"] = macro_list

        return res

    def to_dict_detail(self):
        res = {}

        res["functions"] = []
        res["ifmacros"] = []

        for _func in self._func_list:
            _func_dict = {}
            _func_dict["name"] = _func.get_name()
            _func_dict["line_sta"] = _func.get_line_start()
            _func_dict["line_end"] = _func.get_line_end()

            res["functions"].append(_func_dict)

        for _ifmacro in self._ifmacro_list:
            _ifmacro_dict = {}
            _ifmacro_dict["name"] = _ifmacro.get_name()
            _ifmacro_dict["if_line_sta"] = _ifmacro.get_if_line_start()
            _ifmacro_dict["if_line_end"] = _ifmacro.get_if_line_end()
            _ifmacro_dict["endif_line"] = _ifmacro.get_endif_line()
            res["ifmacros"].append(_ifmacro_dict)

        return res

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)

    def to_json_detail(self):
        return json.dumps(self.to_dict_detail(), indent=4)
