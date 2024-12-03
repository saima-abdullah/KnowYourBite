import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# preprocess data
def preprocess_data(data):
    data['product_name'] = data['product_name'].str.lower().str.strip()
    data['food_groups'] = data['food_groups'].str.replace('en:', '').str.lower().str.strip()
    return data

# convert ingredients to vector representation
def get_ingredient_vectors(data):
    tf_idf_vec = TfidfVectorizer()
    ingredient_vectors = tf_idf_vec.fit_transform(data['processed_ingredients'])
    return ingredient_vectors, tf_idf_vec

# recommend healthier alternatives
def recommend_healthier_alternate(product_name, data, ingredient_vectors, top_n=5):
    try:
        # find product
        matches = data[data['product_name'].str.contains(product_name.lower(), case=False, na=False)]
        if matches.empty:
            return f"Product '{product_name}' not found in the dataset."
        
        product_idx = matches.index[0]

        # heck if product is healthy
        if data.iloc[product_idx]['health_label'] == 'healthy':
            return f"Product '{product_name}' is already labeled as healthy."

        # Get category and vector of input product
        category = data.iloc[product_idx]['food_groups']
        product_vector = ingredient_vectors[product_idx]

        # Filter healthier products in the same category
        healthier_products = data[(data['food_groups'] == category) & 
                                  (data['health_label'] == "healthy")]
        if healthier_products.empty:
            return f"No healthier alternatives found for '{product_name}'."

        # Calculate similarity
        healthier_indices = healthier_products.index
        healthier_vectors = ingredient_vectors[healthier_indices]
        similarity_scores = cosine_similarity(product_vector, healthier_vectors).flatten()

        # Sort by similarity
        sorted_indices = similarity_scores.argsort()[::-1]

        # Generate unique recommendations
        seen = set()  # To track duplicates
        recommendations = []
        for i in sorted_indices:
            rec_product = healthier_products.iloc[i]['product_name']
            rec_score = similarity_scores[i]
            if rec_product not in seen:  # Add only if not already seen
                recommendations.append((rec_product, rec_score))
                seen.add(rec_product)
            if len(recommendations) == top_n:  # Stop when top_n is reached
                break

        return recommendations if recommendations else f"No suitable alternatives found for '{product_name}'."
    except Exception as e:
        return f"An error occurred: {e}"

