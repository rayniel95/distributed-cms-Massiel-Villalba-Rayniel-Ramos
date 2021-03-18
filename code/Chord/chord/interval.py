
class Interval():

    def __init__(self, start: int, end: int, lexclude=False, rexclude=False):
        self.start = start
        self.end = end
        self.lexclude = lexclude
        self.rexclude = rexclude

    def __contains__(self, value: int):
        if self.lexclude and self.rexclude:  # ()
            if self.start == self.end:
                res = value != self.start

            elif self.start < self.end:
                res = self.start < value and value < self.end

            else:
                res = value > self.start or value < self.end

        elif not self.lexclude and not self.rexclude:  # [] devolver true siempre
            if self.start == self.end:
                res = True
            elif self.start < self.end:
                res = self.start <= value and value <= self.end
            else:
                res = value >= self.start or value <= self.end

        elif self.lexclude and not self.rexclude:  # (] devolver true aqui si los extremos son iguales
            if self.start == self.end:
                res = True
            elif self.start < self.end:
                res = self.start < value and value <= self.end
            else:
                res = value > self.start or value <= self.end

        else:  # [) si los extremos son iguales aqui que hacemos, falso para todas las llaves, probado por alejandro
            if self.start == self.end:
                res = False
            elif self.start < self.end:
                res = self.start <= value and value < self.end
            else:
                res = value >= self.start or value < self.end

        return res

    def __str__(self):
        opar = '(' if self.lexclude else '['
        cpar = ')' if self.rexclude else ']'

        return opar + str(self.start) + ',' + str(self.end) + cpar

