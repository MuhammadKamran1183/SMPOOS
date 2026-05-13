class _NoOpComm:
    def send(self, *args, **kwargs):
        return None

    def close(self, *args, **kwargs):
        return None


def create_comm(*args, **kwargs):
    return _NoOpComm()

