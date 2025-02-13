import streamlit as st
import json
import requests
import os
from datetime import datetime
import openai
import folium
from streamlit_folium import st_folium
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load API Keys
YELP_API_KEY = os.getenv("YELP_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
openai.api_key = OPENAI_API_KEY

def get_yelp_data(query, location="San Juan, PR", category="hotels"):
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {"term": query, "location": location, "limit": 5, "categories": category}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        results = []
        for business in data.get("businesses", []):
            name = business["name"]
            rating = business.get("rating", "N/A")
            review_count = business.get("review_count", "N/A")
            price = business.get("price", "N/A")
            lat = business["coordinates"].get("latitude", None)
            lon = business["coordinates"].get("longitude", None)
            results.append({"name": name, "rating": rating, "reviews": review_count, "price": price, "lat": lat, "lon": lon})
        return results
    return []

def get_weather_forecast(location, units="imperial"):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={OPENWEATHER_API_KEY}&units={units}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        weather_desc = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        humidity = data["main"].get("humidity", "N/A")
        wind_speed = data["wind"].get("speed", "N/A")
        return f"Current weather in {location}: {weather_desc}, {temp}°F\nHumidity: {humidity}% | Wind Speed: {wind_speed} mph"
    return "Weather data not available."

def travel_chatbot(user_query, location="San Juan, PR"):
    categories = {"hotels": "hotels", "attractions": "landmarks,hiking,arts,parks", "outdoor activities": "hiking,surfing,tours,boating", "restaurants": "restaurants"}
    
    for keyword, category in categories.items():
        if keyword in user_query.lower():
            results = get_yelp_data(keyword, location, category)
            if not results:
                return "No results found."
            return results
    
    if "weather" in user_query.lower() or "forecast" in user_query.lower():
        return get_weather_forecast(location)
    
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a friendly Puerto Rico travel assistant helping a user plan their trip."}, {"role": "user", "content": user_query}]
    )
    return response.choices[0].message.content

# Streamlit UI Setup
st.title("🌴 Puerto Rico Travel Planner")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Chatbot", "Itinerary", "Weather", "Map View"])

if page == "Chatbot":
    st.header("💬 Travel Chatbot")
    user_query = st.text_input("Ask me about hotels, attractions, restaurants, or activities!")
    if st.button("Ask", key="chatbot_button"): 
        response = travel_chatbot(user_query)
        if isinstance(response, list):
            for res in response:
                st.write(f"**{res['name']}** - Rating: {res['rating']} ({res['reviews']} reviews) - Price: {res['price']}")
        else:
            st.write(response)

elif page == "Itinerary":
    st.header("🗺️ Plan Your Trip")
    itinerary = st.text_area("Enter places you want to visit:")
    if st.button("Save Itinerary", key="itinerary_button"):
        with open("itinerary.json", "w") as f:
            json.dump({"itinerary": itinerary.split('\n')}, f)
        st.success("Itinerary saved!")
    
    try:
        with open("itinerary.json", "r") as f:
            saved_itinerary = json.load(f)
            st.subheader("Your Saved Itinerary:")
            for place in saved_itinerary["itinerary"]:
                st.write(f"- {place}")
    except FileNotFoundError:
        st.write("No itinerary saved yet.")

elif page == "Weather":
    st.header("🌦️ Weather Forecast")
    location = st.text_input("Enter a location:", key="weather_input")
    if st.button("Check Weather", key="weather_button"):
        weather_info = get_weather_forecast(location)
        st.write(weather_info)

elif page == "Map View":
    st.header("🗺️ Interactive Map")
    location = st.text_input("Enter a location for recommendations:", key="map_input")
    category = st.selectbox("Choose category", ["hotels", "restaurants", "attractions", "outdoor activities"], key="map_category")
    
    if st.button("Show on Map", key="map_button"):
        results = get_yelp_data(category, location, category)
        
        if results:
            map_center = [18.2208, -66.5901]
            m = folium.Map(location=map_center, zoom_start=10)
            
            for res in results:
                if res["lat"] and res["lon"]:
                    folium.Marker(
                        [res["lat"], res["lon"]],
                        popup=f"{res['name']} - Rating: {res['rating']}"
                    ).add_to(m)
            
            st_folium(m, width=700, height=500)
        else:
            st.write("No locations found.")


