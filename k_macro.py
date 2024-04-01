


class K_Macro():


    def __init__(self, name):

        self._name = name
        self._is_config = False

        if name.startswith("CONFIG_"):
            self._is_config = True

    def is_config(self):
        return self._is_config
