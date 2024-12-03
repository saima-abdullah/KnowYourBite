import pickle
import pandas as pd
import streamlit as st
from PIL import Image, ImageEnhance
import pytesseract
import re
from code.recommender_for_food import preprocess_data, get_ingredient_vectors, recommend_healthier_alternate

# Title of the app
st.title('Know your Food')

# Upload image
uploaded_image = st.file_uploader("Upload a food label image", type=["png", "jpg", "jpeg"])

ingredients = []

if uploaded_image:
    # Display the uploaded image
    st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)

    with st.spinner("Extracting text from the image..."):
        try:
            # Open the image
            image = Image.open(uploaded_image)

            # Preprocess the image (convert to grayscale and enhance contrast)
            image = image.convert("L")
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2)

            # Use Tesseract to extract text
            extracted_text = pytesseract.image_to_string(image)

            if extracted_text.strip():
                st.subheader("Extracted Text:")
                st.text_area("OCR Output (Debugging)", extracted_text)

                # Extract the "Ingredients" section
                match = re.search(r"ingredients[:\s]*(.*?\.)(\s|$|contains|may contain)", extracted_text, re.IGNORECASE)
                if match:
                    ingredients_section = match.group(1)
                    ingredients = [i.strip() for i in ingredients_section.split(",")]
                    st.subheader("Extracted Ingredients:")
                    for ingredient in ingredients:
                        st.write(f"- {ingredient}")
                else:
                    st.warning("Could not find 'Ingredients' section in the text.")
            else:
                st.error("No text could be extracted. Please try another image.")

        except Exception as e:
            st.error(f"Error extracting text: {e}")

# Enter product name
product_name = st.text_input("Enter product name (optional):")

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

# Combine ingredients from OCR and product name
if product_name:
    name_based_ingredients = get_ingredients_by_product_name(product_name, df)
    if name_based_ingredients:
        ingredients.extend(name_based_ingredients)
        st.subheader("Combined Ingredients:")
        for ingredient in ingredients:
            st.write(f"- {ingredient}")

# Prediction
prediction_label = None
if ingredients:
    st.header("Prediction")
    
    ingredients_text = " ".join(ingredients)
    st.write(f"Ingredients for Prediction: {ingredients_text}")
    try:
        prediction = classifier.predict([ingredients_text])  # Assuming model takes a text input
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
