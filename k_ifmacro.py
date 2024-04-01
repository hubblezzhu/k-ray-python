import re
import json

class K_IfMacro():

    def __init__(self, macro_str, l_if_sta, l_if_end, l_endif):
        self._str = macro_str

        self._l_if_sta = l_if_sta
        self._l_if_end = l_if_end
        self._l_endif = l_endif

        self._macros = []
        self._configs = []


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
