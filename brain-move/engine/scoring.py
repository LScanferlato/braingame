class Scoring:
    def __init__(self):
        self.total_score = 0
        self.game_scores = {}

    def add_score(self, game_name, points):
        self.total_score += points
        if game_name not in self.game_scores:
            self.game_scores[game_name] = 0
        self.game_scores[game_name] += points

    def get_total(self):
        return self.total_score

    def get_game_score(self, game_name):
        return self.game_scores.get(game_name, 0)

    def reset(self):
        self.total_score = 0
        self.game_scores = {}
