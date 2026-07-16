import unittest

from ao_save_editor import (
    EXPECTED_SIZE,
    RECIPE_BOOK_ITEMS,
    RECIPE_BOOK_MASK,
    RECIPE_BOOK_OFFSETS,
    SaveData,
    ui_text,
)


class RecipeBookTests(unittest.TestCase):
    def setUp(self):
        self.save = SaveData()
        self.save.data = bytearray(EXPECTED_SIZE)

    def test_recipe_items_follow_t_cook_indexes(self):
        self.assertEqual(len(RECIPE_BOOK_ITEMS), 24)
        self.assertEqual(RECIPE_BOOK_ITEMS[0], 0x0191)
        self.assertEqual(RECIPE_BOOK_ITEMS[15], 0x01BE)
        self.assertEqual(RECIPE_BOOK_ITEMS[-1], 0x01D6)

    def test_read_recipes_merges_mirrors(self):
        self.save.write_u32(RECIPE_BOOK_OFFSETS[0], 1 << 2)
        self.save.write_u32(RECIPE_BOOK_OFFSETS[1], 1 << 3)
        self.save.write_u32(RECIPE_BOOK_OFFSETS[2], 1 << 24)

        selected = self.save.read_recipes()

        self.assertEqual([index + 1 for index, value in enumerate(selected) if value], [2, 3, 24])

    def test_write_recipes_syncs_mirrors_and_preserves_reserved_bits(self):
        reserved = (0x80000001, 0x40000000, 0x20000001)
        for offset, value in zip(RECIPE_BOOK_OFFSETS, reserved):
            self.save.write_u32(offset, value | (1 << 8))

        selected = [False] * 24
        selected[0] = True
        selected[-1] = True
        self.save.write_recipes(selected)

        expected_recipes = (1 << 1) | (1 << 24)
        for offset, old_value in zip(RECIPE_BOOK_OFFSETS, reserved):
            value = self.save.read_u32(offset)
            self.assertEqual(value & RECIPE_BOOK_MASK, expected_recipes)
            self.assertEqual(value & ~RECIPE_BOOK_MASK, old_value & ~RECIPE_BOOK_MASK)

    def test_write_recipes_rejects_wrong_length(self):
        with self.assertRaises(ValueError):
            self.save.write_recipes([True])

    def test_recipe_ui_labels_are_global_translations(self):
        self.assertEqual(ui_text("料理手册", "en"), "Recipe Book")
        self.assertEqual(ui_text("料理手册", "ja"), "料理手帳")
        self.assertEqual(ui_text("全不选", "en"), "Clear All")


if __name__ == "__main__":
    unittest.main()
