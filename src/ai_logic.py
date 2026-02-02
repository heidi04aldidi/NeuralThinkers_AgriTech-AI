from typing import Dict, Any, List
import os
import random
import json

from src.agents.prompts import (
    generate_agricultural_advice, 
    extract_keywords_from_query_sync,
    generate_advice_with_environment,
    verify_farmer_claim
)
from src.agents.state import WeatherData, SoilData

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    try:
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
    except ImportError:
        from langchain.schema import SystemMessage, HumanMessage, AIMessage
    AI_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI dependencies missing ({e}). Using mock AI logic.")
    AI_AVAILABLE = False

def get_simulated_analysis(weather: Dict[str, Any], soil: Dict[str, Any]) -> Dict[str, Any]:
    temp = weather.get('temperature_c', 25)
    ph = soil.get('soil_ph', 7.0)
    
    if ph < 6.0:
        crops = ["Blueberries", "Potatoes", "Sweet Potatoes"]
        soil_note = "Your soil is acidic. These crops thrive in lower pH levels."
        actions = ["Apply agricultural lime to raise pH", "Monitor for nutrient deficiencies", "Add organic matter"]
    elif ph > 7.5:
        crops = ["Asparagus", "Beets", "Cabbage"]
        soil_note = "Your soil is alkaline. Selecting salt-tolerant crops is recommended."
        actions = ["Apply elemental sulfur", "Use acidifying fertilizers", "Ensure deep irrigation"]
    else:
        crops = ["Rice", "Wheat", "Maize", "Tomatoes"]
        soil_note = "Your soil pH is optimal (Neutral). Most major crops will thrive here."
        actions = ["Maintain current fertilization", "Monitor moisture during bloom", "Check for pests weekly"]

    return {
        "suggested_crops": crops,
        "soil_analysis": f"(Simulated) {soil_note}",
        "action_plan": actions
    }

def get_simulated_chat(prompt: str, context: Dict[str, Any]) -> str:
    prompt_lower = prompt.lower()
    crop = context.get('crop_type', 'crop')
    ph = context.get('ph_level', 7.0)
    moisture = context.get('soil_moisture', 50.0)
    temp = context.get('temperature_c', 25.0)
    
    header = f"### Senior Agronomist Advice (Simulated)\n\n"
    
    if "water" in prompt_lower or "irrigation" in prompt_lower:
        advice = f"""**Subject: Irrigation Management for {crop}**

#### ROOT CAUSE ANALYSIS
Based on your current soil moisture ({moisture}%) and temperature ({temp}°C), your {crop} is currently in a metabolic state that requires precise water management. Over-irrigation can lead to root rot, while under-irrigation causes nutrient lockout.

#### IMMEDIATE ACTIONS (Next 48h)
- **Moisture Check:** Verify the top 3 inches of soil. If it feels dusty, provide a deep soak.
- **Timing:** Irrigate specifically between 5:00 AM and 8:00 AM to minimize fungal development and evaporation.
- **Monitoring:** If rainfall is expected, delay any manual irrigation to prevent nitrogen leaching.

#### LONG-TERM PREVENTION
Consider installing a drip irrigation system to deliver water directly to the root zone. Mulching with organic matter can also help retain {moisture}% moisture levels more consistently.

#### SAFETY WARNING
Avoid overhead sprinkling during hot afternoon hours, as this can cause leaf scald and increase the risk of disease."""
    
    elif "pest" in prompt_lower or "bug" in prompt_lower or "insect" in prompt_lower:
        advice = f"""**Subject: Integrated Pest Management (IPM) for {crop}**

#### ROOT CAUSE ANALYSIS
Rising temperatures ({temp}°C) often accelerate the life cycle of common pests. Your {crop} may be vulnerable to attackers if the plant is stressed by moisture fluctuations or pH imbalances.

#### IMMEDIATE ACTIONS (Next 48h)
- **Manual Scouting:** Inspect the undersides of leaves for eggs or small larvae.
- **Organic Intervention:** Apply a 2% Neem Oil solution or a mild insecticidal soap if infestation is visible.
- **Biological Control:** Encourage natural predators like ladybugs or lacewings in your field.

#### LONG-TERM PREVENTION
Implement crop rotation in the next season to break pest cycles. Maintain strong plant immunity by keeping soil pH near {ph}.

#### SAFETY WARNING
Wear protective gear when applying any treatment, even organic ones. Avoid spraying during the presence of bees or other pollinators."""

    elif "fertilizer" in prompt_lower or "nutrient" in prompt_lower or "urea" in prompt_lower:
        advice = f"""**Subject: Nutrient and Soil Health for {crop}**

#### ROOT CAUSE ANALYSIS
Soil pH is the primary governor of nutrient availability. At pH {ph}, your {crop} may have specific needs. If the pH is outside the 6.0-7.0 range, some essential minerals like Phosphorus or Iron might be "locked" in the soil.

#### IMMEDIATE ACTIONS (Next 48h)
- **Soil Testing:** If you haven't recently, conduct a professional N-P-K test.
- **Targeted Feeding:** Use a balanced, slow-release fertilizer if growth appears stunted.
- **pH Adjustment:** If pH is too high, consider adding elemental sulfur; if too low, add agricultural lime.

#### LONG-TERM PREVENTION
Incorporate well-rotted compost annually to build soil structure and buffer pH levels over time.

#### SAFETY WARNING
Do not over-apply Nitrogen fertilizers, as this can lead to excessive leaf growth at the expense of fruit/grain production and can contaminate local groundwater."""

    elif "hindi" in prompt_lower:
         advice = f"""नमस्ते! आपकी **{crop}** की फसल के लिए यहां कुछ विशेषज्ञ सुझाव दिए गए हैं:

1. **सिंचाई:** मिट्टी की नमी ({moisture}%) की जांच करें। सुबह जल्दी पानी देना सबसे अच्छा है।
2. **मिट्टी का स्वास्थ्य:** आपका pH {ph} है। इसे संतुलित रखने के लिए जैविक खाद का प्रयोग करें।
3. **तापमान:** अभी तापमान {temp}°C है, इसलिए फसल को लू या अधिक गर्मी से बचाएं।

यह एक सिम्युलेटेड (Simulated) उत्तर है क्योंकि अभी AI सर्विस उपलब्ध नहीं है। पूर्ण विवरण के लिए कृपया थोड़ी देर बाद फिर से प्रयास करें।"""

    else:
        advice = f"""**Subject: General Agronomy Assessment for {crop}**

#### ROOT CAUSE ANALYSIS
The query "{prompt[:30]}..." indicates an interest in optimizing your {crop} production. Your current environmental parameters (pH: {ph}, Temp: {temp}°C) provide a solid baseline for analysis.

#### IMMEDIATE ACTIONS (Next 48h)
- **Routine Inspection:** Walk your fields to check for any visible stress signals in the leaves or stems.
- **Data Monitoring:** Keep an eye on the weather alerts for any sudden changes in humidity or rainfall.
- **Soil Balance:** Maintain the soil pH and moisture at optimal levels for {crop}.

#### LONG-TERM PREVENTION
Keep a detailed farm journal to track how your {crop} responds to different weather patterns and interventions.

#### SAFETY WARNING
Always prioritize environmental safety and personal protection when performing any field operations."""

    return header + advice

def get_expert_analysis(weather_data: Dict[str, Any], soil_data: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip().strip('"').strip("'")
    
    if AI_AVAILABLE and api_key and "sk-" in api_key:
        try:
            llm = ChatOpenAI(temperature=0.7, model_name="gpt-4o-mini", openai_api_key=api_key)
            json_prompt = ChatPromptTemplate.from_template(
                """
                Analyze environmental data: Weather: {weather_data}, Soil: {soil_data}.
                Return JSON with keys: suggested_crops (list), soil_analysis (string), action_plan (list of 3).
                """
            )
            chain = json_prompt | llm
            result = chain.invoke({"weather_data": str(weather_data), "soil_data": str(soil_data)})
            clean_content = result.content.strip().replace("```json", "").replace("```", "")
            return json.loads(clean_content)
        except Exception as e:
            print(f"AI API failed, switching to Smart Simulator: {e}")

    return get_simulated_analysis(weather_data, soil_data)

def get_chat_response(messages: List[Dict[str, str]], context: Dict[str, Any]) -> str:
    """
    Get chat response using the advanced logic from src.agents.prompts.
    Priority: OpenAI → Gemini → Smart Simulator
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip().strip('"').strip("'")
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    
    user_prompt = messages[-1]["content"] if messages else ""
    
    print(f"\n{'='*60}")
    print(f"AI ADVISOR DEBUG:")
    print(f"  AI_AVAILABLE: {AI_AVAILABLE}")
    print(f"  OpenAI Key Present: {bool(api_key and 'sk-' in api_key)}")
    print(f"  Gemini Key Present: {bool(gemini_key)}")
    print(f"  User Query: {user_prompt[:50]}...")
    print(f"{'='*60}\n")
    
    # Extract historical context from messages
    history = ""
    if len(messages) > 1:
        history = "\n".join([f"{m['role']}: {m['content']}" for m in messages[:-1]])
    
    # Try OpenAI first (more generous rate limits)
    if AI_AVAILABLE and api_key and "sk-" in api_key:
        try:
            print("  → Trying OpenAI GPT-4o-mini...")
            
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.2,
                openai_api_key=api_key
            )
            
            prompt_template = """You are a Senior Agronomist providing expert agricultural advice.

FARMER'S QUESTION: {query}

ENVIRONMENTAL CONTEXT:
- Soil pH: {soil_ph}
- Soil Moisture: {soil_moisture}%
- Temperature: {temperature_c}°C
- Recent Rainfall: {rainfall_mm}mm
- Weather Alert: {weather_alert}
- Conversation History: {history}

Provide practical, science-backed advice. Be specific and actionable."""

            prompt = ChatPromptTemplate.from_template(prompt_template)
            chain = prompt | llm
            
            result = chain.invoke({
                "query": user_prompt,
                "soil_ph": context.get('ph_level', 7.0),
                "soil_moisture": context.get('soil_moisture', 50.0),
                "temperature_c": context.get('temperature_c', 25.0),
                "rainfall_mm": context.get('rainfall_mm', 0.0),
                "weather_alert": context.get('weather_alert', 'None'),
                "history": history or "No previous conversation"
            })
            
            advice = result.content if hasattr(result, 'content') else str(result)
            print(f"  ✓ OpenAI Response received ({len(advice)} chars)")
            return advice
            
        except Exception as e:
            print(f"  ✗ OpenAI FAILED: {str(e)[:100]}")
            print(f"  → Trying Gemini as fallback...")
    
    # Try Gemini as fallback
    if AI_AVAILABLE and gemini_key:
        try:
            advice = generate_agricultural_advice(
                farmer_query=user_prompt,
                soil_ph=context.get('ph_level', 7.0),
                soil_moisture=context.get('soil_moisture', 50.0),
                rainfall_mm=context.get('rainfall_mm', 0.0),
                temperature_c=context.get('temperature_c', 25.0),
                weather_alert=context.get('weather_alert', 'None'),
                history=history,
                model_name="gemini-1.5-flash-latest"  # Correct model name for free tier
            )
            print(f"  ✓ Gemini Response received ({len(advice)} chars)")
            return advice
        except Exception as e:
            error_msg = str(e)
            if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
                print(f"  ✗ Gemini rate limit hit (20/day limit)")
                print(f"  → Quota resets in 24 hours")
            else:
                print(f"  ✗ Gemini FAILED: {error_msg[:100]}")
            print(f"  → Falling back to Smart Simulator")
    else:
        print("  → Using Smart Simulator (No API keys found)")
    
    return get_simulated_chat(user_prompt, context)


