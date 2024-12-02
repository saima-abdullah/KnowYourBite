import pickle
import pandas as pd
import streamlit as st

from code.recommender_for_food import preprocess_data, get_ingredient_vectors, recommend_healthier_alternate

st.title('Know your Food')

# Enter product name
product_name = st.text_input("Enter product name:")

# Food products database
df = pd.read_csv('data/final_data.csv')
df = preprocess_data(df)  # Use preprocess_data to standardize the dataset

# Bad ingredients database
df_add = pd.read_csv('data/addtitives_processed.csv')

# Get the ingredient vectors for the dataset
def ingredients_vectors(df):
    return get_ingredient_vectors(df)


ingredient_vectors, tf_idf_vec = ingredients_vectors(df)

# Load classifier

def load_classifier_model(model_path="models/foodclassifier.pkl"):
    with open(model_path, 'rb') as f:
        return pickle.load(f)

classifier = load_classifier_model()

# Helper function: Get the ingredients of the input product
def get_ingredients_by_product_name(product_name, df):
    match = df[df["product_name"].str.contains(product_name, case=False, na=False)]
    if not match.empty:
        return match.iloc[0]["processed_ingredients"].split(", ")  # Return as a list
    else:
        return None

ingredients = []
prediction_label = None

# Check if product name is provided
if product_name:
    ingredients = get_ingredients_by_product_name(product_name, df)
    if ingredients is None:
        st.error("Product not found in the database.")
    else:
        st.subheader("Ingredients for Product Name:")
        st.write(ingredients)

# Prediction
if ingredients:
    st.header("Prediction")
    
    ingredients_text = " ".join(ingredients)
    st.write(f"Check1: {ingredients_text}")
    try:
        prediction = classifier.predict([ingredients_text])  # Assuming model takes a text input
        st.write(f"Check2: Raw Prediction Value - {prediction[0]}")
        prediction_label = "Healthy" if prediction[0] == 0 else "Not Healthy"
        st.write(f"Prediction: **{prediction_label}**")
    except Exception as e:
        st.error(f"Error during prediction: {e}")

# Highlight unhealthy ingredients
if prediction_label == "Not Healthy" and ingredients:
    st.header("Unhealthy Ingredients Highlight")
    unhealthy_matches = []
    for ingredient in ingredients:
        match = df_add[
            df_add['bad_ingredients_preprocessed'].str.contains(ingredient, case=False, na=False)
        ]
        if not match.empty:
            unhealthy_matches.append({
                "ingredient": ingredient,
                "health_concern": match.iloc[0]['health_concern']
            })

    # Display unhealthy ingredients and their health concerns
    if unhealthy_matches:
        for match in unhealthy_matches:
            st.markdown(f"### **{match['ingredient']}**")
            st.write(f"- **Health Concerns:** {match['health_concern']}")
    else:
        st.write("No unhealthy ingredients found.")

# Recommendations Section
if prediction_label == "Not Healthy":
    st.header("Recommendations")
    st.write("Here are some healthy alternatives for you:")

    try:
        # Use the recommendation logic
        recommendations = recommend_healthier_alternate(
            product_name=product_name, 
            data=df, 
            ingredient_vectors=ingredient_vectors, 
            top_n=5
        )
        
        if isinstance(recommendations, str):  # If no recommendations or product not found
            st.write(recommendations)
        else:
            for rec, score in recommendations:
                st.write(f"- **{rec}** (Similarity Score: {score:.2f})")
    except Exception as e:
        st.error(f"Error during recommendations: {e}")
