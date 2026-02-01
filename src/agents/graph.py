from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from src.agents.state import FarmerState
from src.agents.prompts import SYSTEM_PROMPT
from src.tools.weather_api import get_weather_alert
from src.tools.soil_service import get_soil_advice
from src.database.memory import get_memory

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3
)

def weather_node(state: FarmerState) -> FarmerState:
    alert = get_weather_alert(state.rainfall)
    state.weather_alert = alert
    state.reasoning_steps.append("Weather conditions evaluated")
    return state

def soil_node(state: FarmerState) -> FarmerState:
    advice = get_soil_advice(state.soil_type, state.crop)
    state.soil_advice = advice
    state.reasoning_steps.append("Soil suitability analyzed")
    return state

def decision_node(state: FarmerState) -> FarmerState:
    prompt = f"""
    {SYSTEM_PROMPT}

    Farmer Details:
    - Crop: {state.crop}
    - Crop Stage: {state.crop_stage}
    - Soil Type: {state.soil_type}
    - Weather Alert: {state.weather_alert}
    - Soil Advice: {state.soil_advice}
    - Observed Problems: {state.problems}

    Task:
    Provide 3–5 clear, stage-specific farming recommendations.
    """

    response = llm.invoke(prompt)
    state.final_advice = response.content
    state.reasoning_steps.append("Final recommendation generated")
    return state

def build_graph():
    graph = StateGraph(FarmerState)

    graph.add_node("weather_analysis", weather_node)
    graph.add_node("soil_analysis", soil_node)
    graph.add_node("decision", decision_node)

<<<<<<< Updated upstream
    graph.set_entry_point("weather_analysis")
    graph.add_edge("weather_analysis", "soil_analysis")
    graph.add_edge("soil_analysis", "decision")
    graph.add_edge("decision", END)
=======
    graph.set_entry_point("validate_input")

    graph.add_edge("validate_input", "extract_keywords")
    graph.add_edge("extract_keywords", "weather_analysis")
    graph.add_conditional_edges(
        "weather_analysis",
        route_after_weather,
        {
            "soil_analysis": "soil_analysis",
            "generate_advice": "generate_advice",
        }
    )
    graph.add_edge("soil_analysis", "generate_advice")
    graph.add_edge("generate_advice", END)
>>>>>>> Stashed changes

    return graph.compile(
        checkpointer=get_memory()
    )
<<<<<<< Updated upstream
=======

def route_after_weather(state: AgentState) -> str:
    farmer_input = state["farmer_input"]

    if farmer_input.soil_type == "unknown":
        return "generate_advice"

    return "soil_analysis"              
>>>>>>> Stashed changes
