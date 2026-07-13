class Difficulty:
    def __init__(self, initial_level=1, min_level=1, max_level=5):
        self.level = initial_level
        self.min_level = min_level
        self.max_level = max_level
        self.history = []

    def increase(self):
        if self.level < self.max_level:
            self.level += 1
        self.history.append(("up", self.level))

    def decrease(self):
        if self.level > self.min_level:
            self.level -= 1
        self.history.append(("down", self.level))

    def keep(self):
        self.history.append(("keep", self.level))

    def adapt(self, accuracy, fatigue_level="bassa"):
        if accuracy > 0.8 and fatigue_level == "bassa":
            self.increase()
        elif accuracy < 0.5 or fatigue_level == "alta":
            self.decrease()
        else:
            self.keep()

    def get_level(self):
        return self.level
