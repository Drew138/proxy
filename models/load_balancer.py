from models.target import Target


class LoadBalancer:

    def __init__(self, targets: list[Target]) -> None:
        self.targets: list[Target] = targets
        self.index: int = 0

    def next(self) -> Target:
        target: Target = self.targets[self.index]
        self.index = (self.index + 1) % len(self.targets)
        return target
