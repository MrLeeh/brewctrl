import unittest
from app.recipe_control import RecipeController, RecipeControllerException


class RecipeControllerTestCase(unittest.TestCase):

    def setUp(self):
        self.recipe_controller = RecipeController()

    def test_load_recipe(self):
        # assign new recipe
        self.recipe_controller.load_recipe(0)

        # test recipe id
        self.assertEqual(0, self.recipe_controller.recipe_id)

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
