
#https://www.geeksforgeeks.org/introduction-to-python-pytesseract-package/
import pickle
import time
import pandas as pd
import streamlit as st
from PIL import Image
import pytesseract
import re
import os
import sys

sys.path.append(os.path.abspath("code"))
from recommender_for_food import preprocess_data, get_ingredient_vectors, recommend_healthier_alternate

#fonts and css
st.markdown(
    """
    <style>
    /* Title and Header Styling */
    .title { 
        font-size: 42px; 
        color: #6C63FF; 
        font-weight: bold; 
        font-family: 'Arial', sans-serif; 
    }

    /* Highlighting Prediction */
    .prediction { 
        font-size: 24px; 
        font-weight: bold; 
        color: #6C63FF; 
    }
    /* General Styling */
    body { 
   
    font-family: 'Arial', sans-serif;
    background-color: #f7f9fc;


        background-color: #FAFAFA; 
    }
    .stButton>button { 
        font-size: 18px; 
        font-weight: bold; 
        color: white; 
        background-color: #6C63FF; 
        border-radius: 8px; 
        padding: 10px 20px; 
    }
    </style>
    """, unsafe_allow_html=True
)


st.title('🍎 Know Your Bite')

st.markdown("### 🌟 Discover whether your food is healthy or not!", unsafe_allow_html=True)

#  food products database
# Get the absolute path of the CSV file
# Construct the correct path to the CSV file inside 'data/clean_data/'
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "cleaned_data", "final_data.csv")  # Replace with actual file name
CSV_PATH_1 = os.path.join(os.path.dirname(__file__), "data", "cleaned_data", "addtitives_processed.csv") 
# Check if the file exists before loading
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"❌ CSV file not found at: {CSV_PATH}")

# Load the CSV file
df = pd.read_csv(CSV_PATH)

# Display first few rows to verify
print("✅ CSV file loaded successfully!")
print(df.head())
# Load the CSV file
#df = pd.read_csv(CSV_PATH)
#df = pd.read_csv('data/cleaned_data/final_data.csv')

# bad ingredients database
df_add = pd.read_csv(CSV_PATH_1)

#  ingredient vectors from the recommender
def ingredients_vectors(df):
    return get_ingredient_vectors(df)
ingredient_vectors, tf_idf_vec = ingredients_vectors(df)

#  classifier
# Get the absolute path of the model
BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "models", "foodclassifier.pkl")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Make sure it's uploaded.")

def load_classifier_model():
    model_path = os.path.join(os.path.dirname(__file__), "models", "classifier.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"❌ Model file not found at: {model_path}")

    with open(model_path, "rb") as f:
        return pickle.load(f)
    
classifier = load_classifier_model()

# ingredients of the input product
def get_ingredients_by_product_name(product_name, df):
    match = df[df["product_name"].str.contains(product_name, case=False, na=False)]
    if not match.empty:
        return match.iloc[0]["processed_ingredients"].split(", ")  # Return as a list
    else:
        return None
    
#ingredients of the input image
def extract_ingredients_from_image(image_data):
    try:
        image = Image.open(image_data)
        extracted_text = pytesseract.image_to_string(image)  # use OCR to extract text
        # extract text to match 
        extracted_text = extracted_text.replace('\n', ' ').replace('\r', '')
        extracted_text = re.sub(r'\s+', ' ', extracted_text).strip() 
    # Using regex to find 'Ingredients' 
        match = re.search(
    r"(?i)\bingredients\b\s*[:\-]?\s*(.+?)(?:\.|\n|contains|may contain)",  # Extract up to a stopping condition
    extracted_text,
    re.IGNORECASE | re.DOTALL  # Case-insensitive and allows matching across multiple lines
)
        if match:
           
        # getting everything after 'ingredients' keyword
            ingredients_text = match.group(1)
        # cleaning white spaces
            ingredients_list = ingredients_text.strip().split(',')
            return [ingredient.strip() for ingredient in ingredients_list if ingredient.strip()]
        else:
            return []  # empty if 'ingredients' keyword not found
    except Exception as e:
        st.error(f"Failed to extract ingredients: {str(e)}")
        return []

col1, col2 = st.columns(2)
with col1:
    product_name = st.text_input("Enter product name:", help="Type the name of the product (e.g., Oreo, Coca Cola)")
  
with col2:
    uploaded_image = st.file_uploader("Or upload an image of the food ingredients:", type=['jpg', 'png'])


ingredients = []
prediction_label = None


# Check if product name is provided

if product_name:
    with st.spinner("Analyzing ingredients..."):
        time.sleep(1)  #  delay


    ingredients = get_ingredients_by_product_name(product_name, df)
 
    
    if not ingredients:  #  if ingredients list is empty or None
        st.error("Product not found in the database.")
    else:
        st.success("Analysis complete!")
        st.markdown("### 🥗 Ingredients List:")
        for ingredient in ingredients:
            st.markdown(f"- {ingredient}")
if uploaded_image:
    # get ingredients from uploaded image
    st.image(uploaded_image, caption="Uploaded Image of Ingredients", use_column_width=True)

    ingredients = extract_ingredients_from_image(uploaded_image)
    with st.spinner("Analyzing ingredients..."):
        time.sleep(0.1)  
    st.success("Analysis complete!")
    st.markdown("### 🥗  Ingredients List:")
    for ingredient in ingredients:
        st.markdown(f"- {ingredient}")
    if not ingredients:
        st.error("No ingredients could be extracted from the image.")
    

st.markdown("---")

# Prediction
if ingredients:
    st.header("Prediction")
    
    ingredients_text = " ".join(ingredients)
   #st.write(f"Check1: {ingredients_text}")
    try:
        prediction = classifier.predict([ingredients_text])  
        #st.write(f"Check2: Raw Prediction Value - {prediction[0]}")
        prediction_label = "Healthy" if prediction[0] == 0 else "Not Healthy"
       
        st.markdown(f'<p class="prediction">Prediction: {prediction_label}</p>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error during prediction: {e}")
st.markdown("---")
#  unhealthy ingredients
if prediction_label == "Not Healthy" and ingredients:
    st.write("### Unhealthy Ingredients Highlight")
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

    #  unhealthy ingredients and their health concerns
 
    if unhealthy_matches:
        for match in unhealthy_matches:
            st.markdown(f"### **{match['ingredient']}**")
            st.write(f"- **Health Concern:** {match['health_concern']}")
    else:
        st.write("No unhealthy ingredients found.")
st.markdown("---")
# recommendations Section
if prediction_label == "Not Healthy":
    st.write("### **Recommendations**")
    st.write("Here are some healthy alternatives for you:")

    try:
        # from the recommendation.py file
        recommendations = recommend_healthier_alternate(
            product_name=product_name, 
            data=df, 
            ingredient_vectors=ingredient_vectors, 
            top_n=5	
        )
        
        if isinstance(recommendations, str):  # if no recommendations found
            st.write(recommendations)
        else:
            for rec, score in recommendations:
                 st.markdown(f"✅ {rec} ")
    except Exception as e:
        st.error(f"Error during recommendations: {e}")


 
