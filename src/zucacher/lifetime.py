class Lifetime:
    @staticmethod
    def permanent():
        return None

    @staticmethod
    def timed(seconds: int):
        return seconds

    @staticmethod
    def daily():
        return 86400
