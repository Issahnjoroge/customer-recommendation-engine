
import unittest

from pathlib import Path
from tempfile import TemporaryDirectory
import csv

from recommender import (
    RecommendationEngine, 
    export_csv,
    jaccard, 
    read_purchases,
)     


class TestJaccard(unittest.TestCase):

    def test_partial_overlap(self):
        self.assertAlmostEqual(
            jaccard({"P01", "P02"}, {"P02", "P03"}),
            1 / 3,
        )

    def test_identical_sets(self):
        self.assertEqual(
            jaccard({"P01", "P02"}, {"P01", "P02"}),
            1.0,
        )

    def test_no_overlap(self):
        self.assertEqual(
            jaccard({"P01"}, {"P02"}),
            0.0,
        )

    def test_both_sets_empty(self):
        self.assertEqual(jaccard(set(), set()), 1.0)


class TestRecommendationEngine(unittest.TestCase):

    def setUp(self):
        self.purchases = [
            {
                "customer_id": "C101",
                "customer_name": "Wanjiru",
                "product_id": "P01",
                "product_name": "Milk",
                "category": "Dairy",
            },
            {
                "customer_id": "C101",
                "customer_name": "Wanjiru",
                "product_id": "P02",
                "product_name": "Bread",
                "category": "Bakery",
            },
            {
                "customer_id": "C102",
                "customer_name": "Otieno",
                "product_id": "P01",
                "product_name": "Milk",
                "category": "Dairy",
            },
            {
                "customer_id": "C102",
                "customer_name": "Otieno",
                "product_id": "P03",
                "product_name": "Eggs",
                "category": "Fresh",
            },
        ]

        self.engine = RecommendationEngine(self.purchases)

    def test_history_returns_products(self):
        self.assertEqual(
            self.engine.history("C101"),
            {"P01", "P02"},
        )

    def test_unknown_customer_raises_error(self):
        with self.assertRaises(KeyError):
            self.engine.history("C999")

    def test_similarity_and_popularity_both_affect_score(self):
        evidence = [("C102", 0.5)]

        
        self.assertAlmostEqual(
            self.engine.score("P01", evidence),
            0.6,
        )

    def test_recommendations_exclude_already_purchased_products(self):
        recommendations = self.engine.recommend("C101", n=3)

        recommended_ids = {
            item["product_id"] for item in recommendations
        }

        self.assertNotIn("P01", recommended_ids)
        self.assertNotIn("P02", recommended_ids)

    def test_recommendation_count_does_not_exceed_requested_limit(self):
        recommendations = self.engine.recommend("C101", n=2)

        self.assertLessEqual(len(recommendations), 2)



class TestReadPurchases(unittest.TestCase):

    def write_csv(self, folder, rows):
        path = Path(folder) / "test_purchases.csv"

        fieldnames = [
            "purchase_id",
            "customer_id",
            "customer_name",
            "product_id",
            "product_name",
            "category",
            "quantity",
        ]

        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return path

    def test_valid_purchase_is_accepted_and_ids_are_normalized(self):
        row = {
            "purchase_id": "t001",
            "customer_id": "c101",
            "customer_name": "Wanjiru",
            "product_id": "p01",
            "product_name": "Milk",
            "category": "Dairy",
            "quantity": "2",
        }

        with TemporaryDirectory() as folder:
            path = self.write_csv(folder, [row])
            valid, rejected = read_purchases(path)

        self.assertEqual(len(valid), 1)
        self.assertEqual(len(rejected), 0)
        self.assertEqual(valid[0]["purchase_id"], "T001")
        self.assertEqual(valid[0]["customer_id"], "C101")
        self.assertEqual(valid[0]["product_id"], "P01")
        self.assertEqual(valid[0]["quantity"], 2)

    def test_duplicate_purchase_id_is_rejected(self):
        first = {
            "purchase_id": "T001",
            "customer_id": "C101",
            "customer_name": "Wanjiru",
            "product_id": "P01",
            "product_name": "Milk",
            "category": "Dairy",
            "quantity": "1",
        }
        duplicate = {**first, "customer_id": "C102"}

        with TemporaryDirectory() as folder:
            path = self.write_csv(folder, [first, duplicate])
            valid, rejected = read_purchases(path)

        self.assertEqual(len(valid), 1)
        self.assertEqual(len(rejected), 1)
        self.assertIn("Duplicate purchase_id", rejected[0]["rejection_reason"])

    def test_missing_required_field_is_rejected(self):
        row = {
            "purchase_id": "T001",
            "customer_id": "C101",
            "customer_name": "Wanjiru",
            "product_id": "",
            "product_name": "Milk",
            "category": "Dairy",
            "quantity": "1",
        }

        with TemporaryDirectory() as folder:
            path = self.write_csv(folder, [row])
            valid, rejected = read_purchases(path)

        self.assertEqual(len(valid), 0)
        self.assertEqual(len(rejected), 1)
        self.assertIn("product_id", rejected[0]["rejection_reason"])

    def test_zero_quantity_is_rejected(self):
        row = {
            "purchase_id": "T001",
            "customer_id": "C101",
            "customer_name": "Wanjiru",
            "product_id": "P01",
            "product_name": "Milk",
            "category": "Dairy",
            "quantity": "0",
        }

        with TemporaryDirectory() as folder:
            path = self.write_csv(folder, [row])
            valid, rejected = read_purchases(path)

        self.assertEqual(len(valid), 0)
        self.assertEqual(len(rejected), 1)
        self.assertIn("Quantity", rejected[0]["rejection_reason"])

    def test_non_numeric_quantity_is_rejected(self):
        row = {
            "purchase_id": "T001",
            "customer_id": "C101",
            "customer_name": "Wanjiru",
            "product_id": "P01",
            "product_name": "Milk",
            "category": "Dairy",
            "quantity": "many",
        }

        with TemporaryDirectory() as folder:
            path = self.write_csv(folder, [row])
            valid, rejected = read_purchases(path)

        self.assertEqual(len(valid), 0)
        self.assertEqual(len(rejected), 1)


class TestExportCSV(unittest.TestCase):

    def setUp(self):
        self.purchases = [
            {
                "customer_id": "C101",
                "customer_name": "Wanjiru",
                "product_id": "P01",
                "product_name": "Milk",
                "category": "Dairy",
            },
            {
                "customer_id": "C102",
                "customer_name": "Otieno",
                "product_id": "P02",
                "product_name": "Bread",
                "category": "Bakery",
            },
        ]

        self.engine = RecommendationEngine(self.purchases)

    def test_csv_has_required_columns_and_rank(self):
        rows = [
            {
                "customer_id": "C101",
                "customer_name": "Wanjiru",
                "product_id": "P03",
                "product_name": "Eggs",
                "category": "Fresh",
                "score": 0.75,
                "supporting_customers": ["C102", "C103"],
            }
        ]

        with TemporaryDirectory() as folder:
            path = Path(folder) / "output" / "recommendations.csv"
            export_csv(self.engine, rows, path)

            with path.open("r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                output_rows = list(reader)
                columns = reader.fieldnames

        self.assertEqual(
            columns,
            [
                "customer_id",
                "customer_name",
                "rank",
                "product_id",
                "product_name",
                "category",
                "score",
                "supporting_customers",
            ],
        )

        c101_row = next(
            row for row in output_rows
            if row["customer_id"] == "C101"
        )

        self.assertEqual(c101_row["rank"], "1")
        self.assertEqual(c101_row["product_id"], "P03")
        self.assertEqual(
            c101_row["supporting_customers"],
            "C102; C103",
        )

    def test_customer_without_recommendations_is_exported(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "output" / "recommendations.csv"
            export_csv(self.engine, [], path)

            with path.open("r", newline="", encoding="utf-8") as file:
                output_rows = list(csv.DictReader(file))

        self.assertEqual(len(output_rows), 2)

        for row in output_rows:
            self.assertEqual(row["rank"], "")
            self.assertEqual(row["product_id"], "")
            self.assertEqual(row["product_name"], "")
            self.assertEqual(row["category"], "")
            self.assertEqual(row["score"], "")
            self.assertEqual(row["supporting_customers"], "")

    def test_ranks_start_at_one_for_each_customer(self):
        rows = [
            {
                "customer_id": "C101",
                "customer_name": "Wanjiru",
                "product_id": "P03",
                "product_name": "Eggs",
                "category": "Fresh",
                "score": 0.9,
                "supporting_customers": ["C102"],
            },
            {
                "customer_id": "C101",
                "customer_name": "Wanjiru",
                "product_id": "P04",
                "product_name": "Tea",
                "category": "Beverages",
                "score": 0.5,
                "supporting_customers": ["C102"],
            },
        ]

        with TemporaryDirectory() as folder:
            path = Path(folder) / "recommendations.csv"
            export_csv(self.engine, rows, path)

            with path.open("r", newline="", encoding="utf-8") as file:
                output_rows = list(csv.DictReader(file))

        c101_rows = [
            row for row in output_rows
            if row["customer_id"] == "C101"
        ]

        self.assertEqual(
            [row["rank"] for row in c101_rows],
            ["1", "2"],
        )



if __name__ == "__main__":
    unittest.main()
