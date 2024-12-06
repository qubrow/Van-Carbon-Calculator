import streamlit as st
import openrouteservice

# Initialize OpenRouteService client
API_KEY = "5b3ce3597851110001cf6248a897a61867d9463189200028fa430a67"  # Replace with your ORS API key
client = openrouteservice.Client(key=API_KEY)

EMISSION_FACTORS = {
    "gasoline": 8.88,      # kg CO₂ per gallon of gasoline, from https://www.epa.gov/greenvehicles/greenhouse-gas-emissions-typical-passenger-vehicle#driving
    "diesel": 10.19,        # kg CO₂ per gallon of diesel, from https://www.epa.gov/greenvehicles/greenhouse-gas-emissions-typical-passenger-vehicle#driving
}

# Function to get distance between two locations
def get_distance_ors(start_city, end_city):
    try:
        # Geocode the start and end locations
        start_result = client.pelias_search(text=start_city)
        end_result = client.pelias_search(text=end_city)
        
        # Extract coordinates from results
        start_coords = start_result["features"][0]["geometry"]["coordinates"]
        end_coords = end_result["features"][0]["geometry"]["coordinates"]

        # Calculate the route and distance
        route = client.directions(coordinates=[tuple(start_coords), tuple(end_coords)], profile="driving-car")
        distance_meters = route["routes"][0]["summary"]["distance"]  # Distance in meters
        distance_miles = distance_meters / 1609.34  # Convert to miles
        return distance_miles, f"{distance_miles:.2f} miles"
    except Exception as e:
        return None, f"Error: {e}"


def calculate_emissions(fuel_type, distance, fuel_efficiency, added_weight, has_cartop_carrier):
    weight_penalty = (added_weight / 100) * 1.5
    adjusted_fuel_efficiency = fuel_efficiency * (1 - weight_penalty / 100)
    if has_cartop_carrier:
        adjusted_fuel_efficiency *= 0.95
    if fuel_type in ["gasoline", "diesel"]:
        fuel_used = distance / adjusted_fuel_efficiency
        emissions = fuel_used * EMISSION_FACTORS[fuel_type]
    return emissions, adjusted_fuel_efficiency

def main():
    st.title("Van Carbon Calculator :minibus:")
    st.write("Calculate the carbon emissions for your trips.")

    # Input for cities
    start_city = st.text_input("Enter Starting City, or the Closest City to your Destination", help="Type the name of the city you're starting from.")
    end_city = st.text_input("Enter Destination City, or the Closest City to your Destination", help="Type your destination city")

    # Ensure distance persistence
    if "distance" not in st.session_state:
        st.session_state.distance = None

    # Distance calculation
    if st.button("Calculate Distance"):
        if start_city and end_city:
            distance, distance_text = get_distance_ors(start_city, end_city)
            if distance:
                st.session_state.distance = distance
                st.success(f"The distance between {start_city} and {end_city} is {distance_text}.")
            else:
                st.error(distance_text)
        else:
            st.error("Please enter both starting and ending cities.")

    # Emissions calculation
    fuel_type = st.selectbox("Select Fuel Type", ["Gasoline", "Diesel"])
    fuel_efficiency = st.number_input("Enter Fuel Efficiency (MPG)", min_value=10.0, step=1.0)
    st.info("An average van will get 17.8 mpg according to the US Department of Energy, although this will depend on brand, wear, and maintenance.")
    has_cartop_carrier = st.checkbox("Do you have a cartop carrier?")
    
    weight_help_text = """
    -Bed frame and mattress: 80–150 lbs (mattress: ~50 lbs; frame: 30–100 lbs)  
    -Cabinets and storage units: 50–150 lbs  
    -Table and seating: 40–100 lbs  
    -Refrigerator: 40–60 lbs  
    -Cooktop or portable stove: 5–15 lbs  
    -Solar power system (panels, batteries, inverter): 100–300 lbs  
    -Heater/air conditioning unit: 30–60 lbs  
    -Water tank (filled): 8.3 lbs per gallon (20-gallon tank = ~170 lbs)   
    -Gray water tank: Similar weight, depending on size  
    -Clothing/Toiletries/Entertainment: 40–120 lbs  
    -Food supplies: 20–60 lbs  
    -Outdoor gear, such as climbing gear: 20-100+ lbs  
    -Insulation materials: 50–150 lbs  
    """
    
    added_weight = st.number_input("Enter Additional Weight (in pounds)", help=weight_help_text, min_value=0, step=10)
    st.info("For some common things that might add weight in your van: \nhover over the ? icon next to additional weight")
    st.info("CAT scales, typically found at truck stops, can tell you exactly how much your van weighs. Going over your van's GVWR (Gross Vehicle Weight Rating) can result in vehicle damage")
    st.info("A minimalist setup might add around 500–800 lbs.")
    st.info("A larger build out could add 1500 to 2500+ lbs.")
    


    if st.button("Calculate Emissions"):
        if st.session_state.distance:
            emissions, adjusted_efficiency = calculate_emissions(
                fuel_type.lower(), st.session_state.distance, fuel_efficiency, added_weight, has_cartop_carrier
            )
            st.success(f"Total Emissions: {emissions:.2f} kg CO₂")
            st.info(f"Adjusted Fuel Efficiency from inputs: {adjusted_efficiency:.2f} MPG")
            avg_emission_per_mile = 0.404  # Average for gasoline cars in kg CO₂ per mile. From https://www.epa.gov/greenvehicles/greenhouse-gas-emissions-typical-passenger-vehicle#driving
            user_emission_per_mile = emissions / st.session_state.distance if st.session_state.distance else None
            if user_emission_per_mile:
                st.markdown("### How your Emissions Compare")
                st.info(f"Your trip emits **{user_emission_per_mile:.2f} kg CO₂ per mile**, "
                        f"compared to the average of **{avg_emission_per_mile:.2f} kg CO₂ per mile** for passenger gasoline cars.")
        else:
            st.error("Please calculate the distance first.")

    if st.session_state.distance:
        st.markdown("### Suggestions to Reduce Your Carbon Footprint")
        if has_cartop_carrier:
            st.info("Removing the cartop carrier when not in use can improve fuel efficiency by about 5%.")
        if added_weight > 0:
            st.info(f"Reducing the added weight of {added_weight:.0f} lbs can increase fuel efficiency by up to {1.5 * (added_weight / 100):.1f}%.")
        st.info("Proper maintenance, such as getting your oil changed regularly, can significantly increase mpg")
        st.info("Reducing your emmissions in other ways is important to consider, such as by installing solar panels and implementing cost-saving and environmentally friendly vehicle modifications.")
if __name__ == "__main__":
    main()
