from . import db
from .models import Receipe as Recipe


class RecipeControllerException(Exception):
    pass


class RecipeController:
    """
    Controller class for recipe progress

    """
    def __init__(self, app):
        self._app = app
        self.recipe_id = -1
        self.running = False

    def load_recipe(self, recipe_id):
        if self.running:
            raise RecipeControllerException(
                'Can not load recipe. Another recipe is currently beeing '
                'progressed.'
            )

        with self._app.app_context():
            self.recipe = Recipe.query.get(recipe_id)
            if self.recipe is None:
                raise ValueError(
                   'There is no recipe with id {}.'.format(recipe_id)
                )

        self.recipe_id = recipe_id

    def start(self):
        if self.running:
            raise RecipeControllerException(
                'Recipe already in progress.'
            )
        else:
            self.running = True

    def process(self):
        pass
