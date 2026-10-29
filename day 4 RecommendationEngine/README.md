
# Mama Mboga Online — Customer Recommendation Engine

## Project Overview

This project builds a customer recommendation engine for Mama Mboga Online using purchase history. It recommends products that a customer has not purchased, using the purchase behavior of similar customers and product popularity.

## Features

- Reads and validates purchase records from a CSV file.
- Normalizes purchase, customer, and product IDs to uppercase.
- Rejects records with missing required fields, duplicate purchase IDs, or invalid quantities.
- Represents each customer's purchase history as a set of product IDs.
- Calculates customer similarity using Jaccard similarity.
- Identifies similar customers and candidate products.
- Scores recommendations using similarity evidence and product popularity.
- Uses popular products as a fallback when collaborative recommendations are insufficient.
- Exports ranked recommendations to a CSV file.
- Includes automated tests using Python's built-in `unittest` framework.


## Requirements

- Python 3.9 or later

## How to Run

Run these commands from the project root.

### Generate recommendations

```bash
python3 main.py
```

The program reads the purchase data, builds the recommendation engine, prints a similarity matrix for the first five customers, generates recommendations, and writes the results to:

`output/recommendations.csv`

### Run automated tests

```bash
python3 -m unittest discover -s tests -v
```

The tests cover Jaccard similarity, purchase validation, customer history, scoring, recommendation limits, and CSV export.

## Data Cleaning Rules

The input file is `data/purchases.csv`.

The current implementation:

- Removes leading and trailing whitespace from field values.
- Converts purchase IDs, customer IDs, and product IDs to uppercase.
- Rejects records with missing required fields.
- Rejects duplicate purchase IDs.
- Rejects quantities that are not positive integers.
- Returns valid and rejected records separately.

## Recommendation Method

### Jaccard Similarity

Customer similarity is calculated from their sets of purchased products:

Jaccard similarity = size of intersection / size of union

If both sets are empty, this implementation returns `1.0`.

### Recommendation Score

The current scoring formula is:

Score = sum of supporting-customer similarity scores + (0.05 × product popularity)

Product popularity is the number of distinct customers who purchased the product.

Products already purchased by the target customer are excluded from recommendations. When collaborative recommendations are insufficient, popular unseen products are used as fallback candidates. Recommendations are sorted by descending score, with product ID used to break ties.

## Output Format

The output CSV contains these columns:

- `customer_id`
- `customer_name`
- `rank`
- `product_id`
- `product_name`
- `category`
- `score`
- `supporting_customers`

Supporting customer IDs are separated by semicolons. Customers without recommendations are represented by a row with blank recommendation fields.

## Current Dataset Run

The current dataset run reports:

- Purchases read: 63
- Purchases used: 60
- Purchases rejected: 3
- Customers: 20
- Products: 15
- Recommendations written: 60

## Testing Status

The current automated test suite contains 17 tests, all of which passed in the last recorded run.

## Limitations

Recommendations depend on the available purchase history. Customers with little overlapping purchase behavior may have low similarity scores, so product popularity can help provide fallback recommendations.


