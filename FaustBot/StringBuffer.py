class StringBuffer:
    def __init__(self):
        self._buffer = str()

    def append(self, to_append):
        self._buffer = self._buffer + to_append
        return self.get()

    def get(self):
        ready = set()
        idx = self._buffer.find('\n')
        while idx is not -1:
            idx = self._buffer.find('\n')
            data = self._buffer[0:idx]  #
            data = data.strip()
            if len(data) >= 1:
                ready.add(data)
            self._buffer = self._buffer[idx + 1:]
        return ready

    @property
    def buffer(self):
        return self._buffer

    @buffer.getter
    def set_buffer(self, new_value):
        self._buffer = new_value
