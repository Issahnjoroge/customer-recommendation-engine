
from pathlib import Path

from recommender import (
    RecommendationEngine,
    export_csv,
    jaccard,
    read_purchases,
)


DATA_PATH = Path("data") / "purchases.csv"
OUTPUT_PATH = Path("output") / "recommendations.csv"


def main() -> None:
    # Reading and validating the purchase data.
    valid, rejected = read_purchases(DATA_PATH)

    print("Rows accepted:", len(valid))
    print("Rows rejected:", len(rejected))

    # Test Jaccard similarity examples.
    print("Jaccard partial overlap:", jaccard({1, 2}, {2, 3}))
    print("Jaccard identical:", jaccard({1, 2}, {1, 2}))
    print("Jaccard no overlap:", jaccard({1}, {2}))
    print("Jaccard both empty:", jaccard(set(), set()))

    # Create the recommendation engine.
    engine = RecommendationEngine(valid)

    print("Customers:", len(engine.customer_products))
    print("Customer IDs:", sorted(engine.customer_products))
    print("Products:", len(engine.product_details))

    customer_ids = sorted(engine.customer_products)

    # Show an example of customer similarity.
    if len(customer_ids) >= 2:
        customer_a = customer_ids[0]
        customer_b = customer_ids[1]

        print(
            f"Similarity {customer_a} vs {customer_b}:",
            engine.similarity(customer_a, customer_b),
        )

    #  Print the similarity matrix for the first five customers.
    first_five = customer_ids[:5]

    print("\nSimilarity matrix:")
    print("Customer", *first_five, sep="\t")

    for customer_a in first_five:
        scores = [
            f"{engine.similarity(customer_a, customer_b):.2f}"
            for customer_b in first_five
        ]
        print(customer_a, *scores, sep="\t")

    
    
    #  Display a complete recommendation example for one customer.
    if customer_ids:
        example_customer = customer_ids[0]

        print("\n--- Customer Recommendation Example ---")
        print("Customer:", example_customer)
        print("Name:", engine.customer_names[example_customer])
        print("Products bought:", engine.history(example_customer))

        print("\nMost similar customers:")
        similar = engine.similar_customers(example_customer, k=5)

        if similar:
            for neighbor_id, similarity_score in similar:
                print(
                    f"  {neighbor_id} "
                    f"({engine.customer_names[neighbor_id]}): "
                    f"{similarity_score:.3f}"
                )
        else:
            print("  No similar customers found.")

        print("\nRecommended products:")
        customer_recommendations = engine.recommend(
            example_customer,
            n=3,
        )

        if customer_recommendations:
            for rank, recommendation in enumerate(
                customer_recommendations,
                start=1,
            ):
                print(
                    f"  Rank {rank}: "
                    f"{recommendation['product_name']} "
                    f"({recommendation['product_id']})"
                )
                print(f"    Category: {recommendation['category']}")
                print(f"    Score: {recommendation['score']:.3f}")

                supporters = recommendation["supporting_customers"]
                print(
                    "    Supporting customers:",
                    ", ".join(supporters) if supporters else "Popularity fallback",
                )
        else:
            print("  No recommendations available.")


    # Generate and export recommendations.
    all_recommendations = engine.recommend_all(n=3)

    export_csv(engine, all_recommendations, OUTPUT_PATH)

    # Print the required run summary.
    print("\n--- Run Summary ---")
    print("Purchases read:", len(valid) + len(rejected))
    print("Purchases used:", len(valid))
    print("Purchases rejected:", len(rejected))
    print("Customers:", len(engine.customer_products))
    print("Products:", len(engine.product_details))
    print("Recommendations written:", len(all_recommendations))
    print("Output file:", OUTPUT_PATH)
    print("Total recommendations:", len(all_recommendations))
    print("First recommendation:", all_recommendations[:1])


if __name__ == "__main__":
    main()
