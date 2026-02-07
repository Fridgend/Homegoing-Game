class Flags:
    DEFINED: dict[str, bool] = {}

    @classmethod
    def is_set(cls, flag: str) -> bool:
        return cls.DEFINED.get(flag, False)

    @classmethod
    def set(cls, flag: str) -> None:
        cls.DEFINED[flag] = True

    @classmethod
    def clear(cls, flag: str) -> None:
        cls.DEFINED[flag] = False

    @classmethod
    def toggle(cls, flag: str) -> None:
        cls.DEFINED[flag] = not cls.DEFINED.get(flag, False)

    @classmethod
    def modify(cls, flag: str, how: str) -> None:
        match how:
            case "add":
                cls.set(flag)
            case "remove":
                cls.clear(flag)
            case "toggle":
                cls.toggle(flag)
            case _:
                return

class Conditions:
    def __init__(self, all_flags: list[str], any_flags: list[str], not_flags: list[str]):
        self.all_flags: list[str] = all_flags
        self.any_flags: list[str] = any_flags
        self.not_flags: list[str] = not_flags

    def satisfied(self) -> bool:
        for flag in self.all_flags:
            if not Flags.is_set(flag):
                return False

        found: bool = len(self.any_flags) == 0
        for flag in self.any_flags:
            if Flags.is_set(flag):
                found = True
                break

        if not found:
            return False

        for flag in self.not_flags:
            if Flags.is_set(flag):
                return False

        return True