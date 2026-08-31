import unittest

from leaf_ai.datasets.common import safe_class_name
from leaf_ai.datasets.prepare_plantvillage_cls import split_items


class DatasetCommonTests(unittest.TestCase):
    def test_safe_class_name_normalizes_plantvillage_names(self):
        self.assertEqual(safe_class_name("Tomato___Late_blight"), "Tomato_Late_blight")
        self.assertEqual(safe_class_name(" pepper bell / bacterial spot "), "pepper_bell_bacterial_spot")

    def test_split_items_preserves_total_count(self):
        items = list(range(20))
        splits = split_items(items, val_ratio=0.15, test_ratio=0.05, seed=42)
        self.assertEqual(sum(len(value) for value in splits.values()), len(items))
        self.assertEqual(len(splits["train"]), 16)
        self.assertEqual(len(splits["val"]), 3)
        self.assertEqual(len(splits["test"]), 1)


if __name__ == "__main__":
    unittest.main()
