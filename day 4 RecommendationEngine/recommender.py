import csv
from pathlib import Path


def read_purchases(path: Path) -> tuple[list[dict], list[dict]]:
    valid_rows = []
    rejected_rows = []
    seen_purchase_ids = set()

    required_fields = [
        "purchase_id",
        "customer_id",
        "customer_name",
        "product_id",
        "product_name",
        "category",
        "quantity"
                    
    ]

    with Path(path).open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
       

        for line_number, row in enumerate(reader, start=2):
            row = {
                key: (value or "").strip()
                for key, value in row.items()

            }

            for field in ("purchase_id", "customer_id", "product_id"):
                if field in row:
                    row[field] = row[field].upper()  
                
            missing_fields = [
                field
                for field in required_fields
                if not row.get(field)
            ]

            if missing_fields:
                row["source_line"] = line_number
                row["rejection_reason"] = (
                    "Missing required fields: " + ", ".join(missing_fields))
                rejected_rows.append(row)
                continue
                


            purchase_id = row["purchase_id"]

            if purchase_id in seen_purchase_ids:
                row["source_line"] = line_number
                row["rejection_reason"] = (f"Duplicate purchase_id: {purchase_id}")
                rejected_rows.append(row)
                continue



            seen_purchase_ids.add(purchase_id)
            try:
                quantity = int(row["quantity"])
            except ValueError:
                quantity = 0

            if quantity <= 0:
                row["source_line"] = line_number
                row["rejection_reason"] = ("Quantity must be a positive number")

                rejected_rows.append(row)
                continue

            row["quantity"] = quantity

        
            valid_rows.append(row)

        return valid_rows, rejected_rows



    

def jaccard(a: set, b: set) -> float:
    union = a | b
    if not union:
        return 1.0
    
    intersection = a & b
    return len(intersection) / len(union)




class RecommendationEngine:
    def __init__(
        self,
        purchases: list[dict],
        min_similarity: float = 0.0,
    ) -> None:
        
        
        self.min_similarity = min_similarity

        self.customer_products: dict[str, set[str]] = {}
        self.customer_names: dict[str, str] = {}
        self.product_details: dict[str, dict] = {}
        self.product_popularity: dict[str, int] = {}

        for row in purchases:
            customer_id = row["customer_id"]
            customer_name = row["customer_name"]
            product_id = row["product_id"]

            self.customer_names[customer_id] = customer_name

            if customer_id not in self.customer_products:
                self.customer_products[customer_id] = set()

            self.customer_products[customer_id].add(product_id)

            self.product_details[product_id] = {
                "product_name": row["product_name"],
                "category": row["category"],
            }

        for products in self.customer_products.values():
            for product_id in products:
                self.product_popularity[product_id] = (
                    self.product_popularity.get(product_id, 0) + 1
                )


    def history(self, customer_id: str) -> set[str]:

        if customer_id not in self.customer_products:
            raise KeyError(f"Unknown customer ID: {customer_id}")

        return self.customer_products[customer_id]

    
    def similarity(
        self,
        customer_a: str,
        customer_b: str,
    ) -> float:
        
        products_a = self.history(customer_a)
        products_b = self.history(customer_b)

        return jaccard(products_a, products_b)


    
    def similar_customers(
        self,
        customer_id: str,
        k: int = 5,
    ) -> list[tuple[str, float]]:
      

        self.history(customer_id)

        similar = []

       
        for other_id in self.customer_products:
            if other_id == customer_id:
                continue

            score = self.similarity(customer_id, other_id)

            if score >= self.min_similarity:
                similar.append((other_id, score))

        
        similar.sort(key=lambda item: (-item[1], item[0]))

        return similar[:k]


    
    def candidate_products(
        self,
        customer_id: str,
        k: int = 5,
    ) -> dict[str, list[tuple[str, float]]]:
       
        purchased = self.history(customer_id)
        neighbors = self.similar_customers(customer_id, k)
        candidates = {}

        for neighbor_id, similarity_score in neighbors:
            neighbor_products = self.history(neighbor_id)

            for product_id in neighbor_products:
                if product_id in purchased:
                    continue

                if product_id not in candidates:
                    candidates[product_id] = []

                candidates[product_id].append(
                    (neighbor_id, similarity_score)
                )

        return candidates

    
    
    def score(
        self,
        product_id: str,
        evidence: list[tuple[str, float]],
    ) -> float:
        similarity_score = sum(
        similarity for _, similarity in evidence
    )

        popularity = self.product_popularity.get(product_id, 0)

        popularity_weight = 0.05

        return similarity_score + (
            popularity_weight * popularity
    )


    
    def recommend(
        self,
        customer_id: str,
        n: int = 3,
    ) -> list[dict]:

        purchased = self.history(customer_id)
        candidates = self.candidate_products(customer_id)

        recommendations = []

        for product_id, evidence in candidates.items():
            
            recommendations.append({
                "customer_id": customer_id,
                "customer_name": self.customer_names[customer_id],
                "product_id": product_id,
                "product_name": self.product_details[product_id]["product_name"],
                "category": self.product_details[product_id]["category"],
                "score": self.score(product_id, evidence),
                "supporting_customers": [
                    neighbor_id for neighbor_id, _ in evidence
                ],
            })

        
        recommendations.sort(
            key=lambda item: (-item["score"], item["product_id"])
        )

        if len(recommendations) < n:
            recommended_ids = {
                item["product_id"] for item in recommendations
            }


            popular_products = sorted(
                self.product_popularity.items(),
                key=lambda item: (-item[1], item[0]),
            )


            for product_id, popularity in popular_products:
                if product_id in purchased:
                    continue

                if product_id in recommended_ids:
                    continue

                details = self.product_details[product_id]

                recommendations.append({
                    "customer_id": customer_id,
                    "customer_name": self.customer_names[customer_id],
                    "product_id": product_id,
                    "product_name": details["product_name"],
                    "category": details["category"],
                    "score": self.score(product_id, []),
                    "supporting_customers": [],
                })

                recommended_ids.add(product_id)

                if len(recommendations) >= n:
                    break

        recommendations.sort(
            key=lambda item: (-item["score"], item["product_id"])
        )
        return recommendations[:n]

    
    
    def recommend_all(self, n: int = 3) -> list[dict]:

        all_recommendations = []

        for customer_id in sorted(self.customer_products):
            recommendations = self.recommend(customer_id, n)
            all_recommendations.extend(recommendations)

        return all_recommendations




    
def export_csv(
    engine: RecommendationEngine,
    rows: list[dict],
    path: Path,
) -> None:
    

    fieldnames = [
        "customer_id",
        "customer_name",
        "rank",
        "product_id",
        "product_name",
        "category",
        "score",
        "supporting_customers",
    ]

    recommendations_by_customer = {}

    for row in rows:
        customer_id = row["customer_id"]
        recommendations_by_customer.setdefault(
            customer_id, []
        ).append(row)


    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

       
        for customer_id in sorted(engine.customer_products):
            customer_recommendations = recommendations_by_customer.get(
                customer_id, []
            )

            if not customer_recommendations:
                writer.writerow({
                    "customer_id": customer_id,
                    "customer_name": engine.customer_names[customer_id],
                    "rank": "",
                    "product_id": "",
                    "product_name": "",
                    "category": "",
                    "score": "",
                    "supporting_customers": "",
                })
                continue

            for rank, recommendation in enumerate(
                customer_recommendations, start=1
            ):
                writer.writerow({
                    "customer_id": customer_id,
                    "customer_name": engine.customer_names[customer_id],
                    "rank": rank,
                    "product_id": recommendation["product_id"],
                    "product_name": recommendation["product_name"],
                    "category": recommendation["category"],
                    "score": recommendation["score"],
                    "supporting_customers": "; ".join(
                        recommendation["supporting_customers"]
                    ),
                })


