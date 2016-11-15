import unittest
from app import create_app, db, brew_controller
from app.models import Recipe, Step
from app.brewcontroller import BrewControllerException


class RecipeControllerTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

        # add recipe data
        recipe = Recipe(
            name='Testrecipe',
            comment='testcommment'
        )
        db.session.add(recipe)
        db.session.commit()

        # add steps
        steps = [
            Step(name='Einmaischen', setpoint=60),
            Step(name='Eiweißrast', setpoint=54, duration=5),
            Step(name='Maltoserast', setpoint=63, duration=30),
            Step(name='Verzuckerungsrast', setpoint=72, duration=30),
            Step(name='Abmaischen', setpoint=78, duration=15)
        ]
        for step in steps:
            step.receipe = recipe

        db.session.add_all(steps)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_load_recipe(self):
        # get first recipe
        recipe = Recipe.query.first()

        # assign new recipe
        with self.assertRaises(BrewControllerException):
            brew_controller.load_recipe(-1)
        brew_controller.load_recipe(recipe.id)

        # test recipe id
        self.assertEqual(recipe.id, brew_controller._loaded_recipe_id)

        # start recipe
        brew_controller.start()
        self.assertTrue(brew_controller.running)

        # trying to load recipe should raise Exception
        with self.assertRaises(BrewControllerException):
            brew_controller.load_recipe(1)

        # trying to restart should raise Exception
        with self.assertRaises(BrewControllerException):
            brew_controller.start()


if __name__ == '__main__':
    unittest.main()
