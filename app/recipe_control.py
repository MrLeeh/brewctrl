class RecipeControllerException(Exception):
    pass


class RecipeController:
    """
    Controller class for receipe progress

    """
    def __init__(self):
        self.recipe_id = -1
        self.running = False

    def load_recipe(self, recipe_id):
        if self.running:
            raise RecipeControllerException(
                'Can not load recipe. Another recipe is currently beeing '
                'progressed.'
            )
        else:
            self.recipe_id = recipe_id

    def start(self):
        if self.running:
            raise RecipeControllerException(
                'Recipe already in progress.'
            )
        else:
            self.running = True