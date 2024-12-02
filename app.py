import pickle
import pandas as pd
import streamlit as st



#create a title
st.title('Know your Food')

#enter product name 
product_name = st.text_input("Enter product name:")

#load the food products database
df =pd.read_csv('data/final_data.csv')

#load the bad ingredients database
df_add = pd.read_csv('data/addtitives_processed.csv')

#get the ingredients of the input product
def get_ingredients_by_product_name(product_name,df):
    match = df[df["product_name"].str.contains(product_name, case=False, na=False)]
    if not match.empty:
        return match.iloc[0]["processed_ingredients"]
    else:
        return "Product not found in the database."
    
#load the classifier
def load_classifier_model(model_path="data/classifier_model.pkl"):
    with open('models/foodclassifier.pkl','rb') as f:
        return pickle.load(f)

classifier = load_classifier_model()
ingredients = []
if product_name:
    ingredients = get_ingredients_by_product_name(product_name, df)
    st.subheader("Ingredients for Product Name:")
    st.write(ingredients)

if ingredients:
    st.header("Prediction")
    # Preprocess ingredients into a format suitable for the classifier
    ingredients_text = " ".join(ingredients)  # Example preprocessing
    prediction = classifier.predict([ingredients_text])  # Assuming model takes a text input
    prediction_label = "Healthy" if prediction[0] == 1 else "Not Healthy"
    st.write(f"Prediction: **{prediction_label}**")
    
if prediction_label == "Not Healthy":
    st.header("Recommendations")
    st.write("Here are some healthy alternatives for you:")
        # Call recommender system here
    st.write("Example: Suggest alternatives based on your recommender logic.")
 

        