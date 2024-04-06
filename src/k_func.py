


class K_Func():


    def __init__(self, path, name, line_sta, line_end):
        self._path = path
        self._name = name
        self._line_sta = int(line_sta)
        self._line_end = int(line_end)

    def get_name(self):
        return self._name

    def get_path(self):
        return self._path

    def get_line_start(self):
        return self._line_sta

    def get_line_end(self):
        return self._line_end
