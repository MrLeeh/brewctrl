import unittest
from app import create_app, db
from app.models import Receipe, Step
from app.hardware import temperature_controller
from app.recipe import RecipeController, RecipeControllerException


class RecipeControllerTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

        # create test database
        db.create_all()

        # add recipe data
        recipe = Receipe(
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

        self.recipe_controller = RecipeController(
            self.app, temperature_controller
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_load_recipe(self):
        # get first recipe
        recipe = Receipe.query.first()

        # assign new recipe
        self.recipe_controller.load_recipe(recipe.id)

        # test recipe id
        self.assertEqual(recipe.id, self.recipe_controller.recipe_id)

        # start recipe
        self.recipe_controller.start()
        self.assertTrue(self.recipe_controller.running)

        # trying to load recipe should raise Exception
        with self.assertRaises(RecipeControllerException):
            self.recipe_controller.load_recipe(1)

        # trying to restart should raise Exception
        with self.assertRaises(RecipeControllerException):
            self.recipe_controller.start()


if __name__ == '__main__':
    unittest.main()
