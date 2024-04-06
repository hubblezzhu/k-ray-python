import re
import json
import sys
import logging


def replace_whole_word(text, old_word, new_word):
    pattern = r'\b{}\b'.format(re.escape(old_word))
    return re.sub(pattern, new_word, text)


class K_IfMacro():

    def __init__(self, macro_str, l_if_sta, l_if_end, l_endif):
        self._str = macro_str

        self._l_if_sta = l_if_sta
        self._l_if_end = l_if_end
        self._l_endif = l_endif

        self._macros = []
        self._configs = []

        # macro relative with arch
        self._is_arch_relative = False
        self._arch_related_configs = []

    def get_name(self):
        return self._str

    def get_if_line_start(self):
        return self._l_if_sta

    def get_if_line_end(self):
        return self._l_if_end

    def get_endif_line(self):
        return self._l_endif

    def get_configs(self):
        return self._configs

    def get_arch_related_configs(self):
        return self._arch_related_configs

    def is_arch_relative(self):
        return self._is_arch_relative

    def set_line_end(self, line_end):
        self._l_endif = line_end

    def set_macro_str(self, macro_str):
        self._str = macro_str

    def display(self):
        print(json.dumps({
                    "macro_str": self._str,
                    "line_if_sta": self._l_if_sta,
                    "line_if_end": self._l_if_end,
                    "line_endif": self._l_endif
                },
                indent=4, separators=(',', ':')
            )
        )

    def parse_config(self):
        pattern = re.compile(r'CONFIG_[_A-Za-z0-9]+')
        self._configs = pattern.findall(self._str)

    def parse_arch_relevance(self, arch_configs):
        # if macro not contain any configs, it's not related with architecture
        # if macro not contain arch configs, it's not related with architecture
        contain_arch_config = False
        for _config in self._configs:
            if _config in arch_configs:
                contain_arch_config = True
        if not contain_arch_config:
            return False

        macro_str = self._str
        # negtive string
        negtive_symbols = [
            "#ifndef",
        ]
        for _symbol in negtive_symbols:
            macro_str = macro_str.replace(_symbol, "!")

        # postive string
        positive_symbols = [
            "#if",
            "# if",
            "#  if",
            "#else",
            "# else",
            "#  else",
            "#elif",
            "# elif",
            "#  elif",
            "#endif",
            "# endif",
            "#  endif",

            "defined",
            "def",
            "IS_ENABLED",
            "IS_BUILTIN",
            "IS_MODULE",
            "IS_REACHABLE",
            "__HAS_BUILT_IN",
            "__has_attribute",
            "\t",
            "\n",
        ]
        for _symbol in positive_symbols:
            macro_str = macro_str.replace(_symbol, "")

        # get symbols
        pattern = re.compile(r'[_A-Za-z0-9]+')
        macro_symbols = pattern.findall(macro_str)

        # symbol value replace
        for _symbol in macro_symbols:
            if _symbol in arch_configs:
                macro_str = replace_whole_word(macro_str, _symbol, "1")
                if macro_str not in self._arch_related_configs:
                    self._arch_related_configs.append(_symbol)
            else:
                macro_str = replace_whole_word(macro_str, _symbol, "0")

        # operator
        macro_str = macro_str.replace("&&", "and")
        macro_str = macro_str.replace("||", "or")
        macro_str = macro_str.replace("!", " not ")
        macro_str = macro_str.replace("==", "or")

        # erase string between /* and */
        macro_str = re.sub(r'/\*.*?\*/', '', macro_str)
        # erase string after //
        macro_str = re.sub(r'//.*', '', macro_str)

        try:
            _value = eval(macro_str)
            # logging.debug("Macro Str: {}".format(self._str))
            # logging.debug("Value: {}".format(_value))
            if _value:
                self._is_arch_relative = True
        except Exception as e:
            logging.error("==============")
            logging.error("Original string:")
            logging.error(self._str)
            logging.error("Macro string: ")
            logging.error(macro_str)
            logging.error(f"Error evaluating macro string: {e}")
            sys.exit()

    def get_pos_config_list(self):
        return self._postive_configs

    def get_neg_config_list(self):
        return self._negtive_configs


# Unit Test
if __name__=="__main__":

    macro_str = '''
    #if defined(CONFIG_X86) || defined(CONFIG_ALPHA) ||\
    defined(CONFIG_MIPS) || defined(CONFIG_PPC) || defined(CONFIG_SPARC) ||\
    defined(CONFIG_PARISC) || defined(CONFIG_SUPERH) ||\
    (defined(CONFIG_ARM) && defined(CONFIG_KEYBOARD_ATKBD) && !defined(CONFIG_ARCH_RPC))
    '''

    macro = K_IfMacro(macro_str, 0, 0, 0)
    macro.parse_config()
    print(macro.get_configs())
