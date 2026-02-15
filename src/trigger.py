from src.event import CatchEvent, DispatchEvent, DispatchChain

class Trigger:
    def __init__(self, disabled: bool, once: bool, catch: list[CatchEvent], dispatch: list[DispatchEvent]):
        self.disabled: bool = disabled
        self.once: bool = once
        self.catches: list[CatchEvent] = catch
        self.dispatch_chain: DispatchChain = DispatchChain(dispatch)

        self.dispatch_index: int = 0
        self.wait_time: float = 0

    def catch(self, scene) -> bool:
        if self.disabled:
            return False
        if scene.dialogue is not None:
            return False

        for event in self.catches:
            if event.conditions is not None and not event.conditions.satisfied():
                continue
            if event.catch(scene):
                return True
        return False

    def dispatch(self, manager, scene) -> None:
        if self.disabled:
            return

        if self.once:
            self.disabled = True
        scene.add_dispatch_chain(manager, self.dispatch_chain)
