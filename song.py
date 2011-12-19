class Note:
    def __init__(self, time):
        self.time=time

class Touch(Note):
    def __init__(self, time, pos):
        Note.__init__(self, time)
        self.pos = pos
    pass

        



