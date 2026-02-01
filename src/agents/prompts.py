from typing import List, Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Extraction Models
class ExtractionModel(BaseModel):
    crop: str = Field(description="Name of the crop being discussed")
    symptoms: List[str] = Field(default=[], description="Observed issues")
    pests: List[str] = Field(default=[], description="Identified pests or diseases")
    action_taken: str = Field(default="", description="Treatment already applied")
    urgency: Literal['low', 'medium', 'high', 'critical'] = 'medium'
    primary_category: Literal['pest', 'disease', 'nutrient', 'irrigation', 'weather'] = 'pest'

# System Instructions - Extraction

EXTRACTION_SYSTEM_PROMPT = """You are an expert agricultural entity extraction specialist.
Analyze the farmer's query and extract structured info into JSON. 
Normalize all biological terms and use lowercase for consistency."""

FEW_SHOT_EXAMPLES = [
    {
        "input": "My tomato plants have yellow leaves and I see small green bugs on them. I sprayed some neem oil yesterday but they keep coming back. It's getting worse!",
        "output": {
            "crop": "tomato",
            "symptoms": ["yellow leaves", "small green bugs on plants"],
            "pests": ["aphids"],
            "action_taken": "sprayed neem oil yesterday",
            "urgency": "high",
            "primary_category": "pest"
        }
    },
    {
        "input": "I'm growing wheat and noticed some brown spots appearing on the leaves. Haven't done anything yet.",
        "output": {
            "crop": "wheat",
            "symptoms": ["brown spots on leaves"],
            "pests": [],
            "action_taken": "",
            "urgency": "medium",
            "primary_category": "disease"
        }
    },
    {
        "input": "URGENT: My rice crop is dying! The stems are rotting and there's a bad smell. Water is standing in the field. Used urea fertilizer last week.",
        "output": {
            "crop": "rice",
            "symptoms": ["rotting stems", "bad smell", "standing water in field"],
            "pests": ["bacterial blight"],
            "action_taken": "applied urea fertilizer last week",
            "urgency": "critical",
            "primary_category": "disease"
        }
    },
    {
        "input": "Potato plants looking healthy but growth seems slow. Maybe the soil is too dry? Nothing unusual otherwise.",
        "output": {
            "crop": "potato",
            "symptoms": ["slow growth", "dry soil"],
            "pests": [],
            "action_taken": "",
            "urgency": "low",
            "primary_category": "irrigation"
        }
    },
    {
        "input": "Cotton leaves curling and white powder on them. Applied sulfur dust 3 days ago but problem persists. Spreading to other plants quickly!",
        "output": {
            "crop": "cotton",
            "symptoms": ["curling leaves", "white powdery coating"],
            "pests": ["powdery mildew"],
            "action_taken": "applied sulfur dust 3 days ago",
            "urgency": "high",
            "primary_category": "disease"
        }
    }
]


def format_few_shot_examples() -> str:
    """Format few-shot examples into a string for the prompt."""
    examples_text = "\n\n".join([
        f"Example {i+1}:\nInput: {ex['input']}\nOutput: {ex['output']}"
        for i, ex in enumerate(FEW_SHOT_EXAMPLES)
    ])
    return f"\n\nHere are examples of correct extractions:\n\n{examples_text}"

# System Instructions - Validation

VALIDATION_SYSTEM_PROMPT = """You are an agricultural data auditor. 
Your job is to ensure the farmer's input is logical compared to real-time data.

Current Environment:
- Temperature: {temp}°C
- Soil Moisture: {moisture}%
- Rainfall (24h): {rain}mm
- Soil pH: {ph}

Farmer Input: {query}

TASK: 
1. Check for 'saying but not doing' discrepancies.
   - E.g., if farmer says 'soil is dry' but moisture is > 80%, flag as invalid.
2. Determine if the query is safe and relevant.

Respond with the ValidationResult Pydantic schema."""

# System Instructions - Advice Generation

ADVICE_GENERATION_SYSTEM_PROMPT = """You are a senior Agronomist. 
Provide actionable advice by grounding the farmer's query in these technical metrics:

ENVIRONMENTAL CONTEXT:
- Soil pH: {soil_ph} (Critical for nutrient availability)
- Rainfall (24h): {rainfall_mm}mm
- Soil Moisture: {soil_moisture}%
- Temperature: {temperature_c}°C
- Weather Alert: {weather_alert}

GOLDEN RULE: 'Precaution is better than cure'.
If 'heavy rain' is detected in alerts or high rainfall is recorded, advise AGAINST irrigation or fertilizer application to prevent waste/runoff.

Provide clear, actionable recommendations based on this environmental context."""

# LangChain Implementation Chains

def create_extraction_chain(model_name: str = "gpt-4o-mini"):
    """Chain for Member 4's keyword extraction task."""
    llm = ChatOpenAI(model=model_name, temperature=0).with_structured_output(ExtractionModel)
    prompt = ChatPromptTemplate.from_messages([
        ("system", EXTRACTION_SYSTEM_PROMPT + format_few_shot_examples()),
        ("human", "Query: {query}")
    ])
    return prompt | llm


def create_validation_chain(model_name: str = "gpt-4o-mini"):
    """Chain for validating farmer input against real-time environmental data."""
    llm = ChatOpenAI(model=model_name, temperature=0)
    prompt = ChatPromptTemplate.from_template(VALIDATION_SYSTEM_PROMPT)
    return prompt | llm


def create_advice_chain(model_name: str = "gpt-4o-mini"):
    """Chain for providing expert agricultural guidance grounded in environmental context."""
    llm = ChatOpenAI(model=model_name, temperature=0.2)
    prompt = ChatPromptTemplate.from_template(ADVICE_GENERATION_SYSTEM_PROMPT)
    return prompt | llm

# Helper Functions - Extraction

def extract_keywords_from_query_sync(query: str, model_name: str = "gpt-4o-mini") -> ExtractionModel:
    """
    Extract structured keywords from a farmer's natural language query.
    Args:
        query: The farmer's input text
        model_name: OpenAI model to use (default: gpt-4o-mini)   
    Returns:
        ExtractionModel with extracted entities
    """
    chain = create_extraction_chain(model_name=model_name)
    result = chain.invoke({"query": query})
    return result


async def extract_keywords_from_query(query: str, model_name: str = "gpt-4o-mini") -> ExtractionModel:
    """
    Async version: Extract structured keywords from a farmer's natural language query.
    Args:
        query: The farmer's input text
        model_name: OpenAI model to use (default: gpt-4o-mini)
    Returns:
        ExtractionModel with extracted entities
    """
    chain = create_extraction_chain(model_name=model_name)
    result = await chain.ainvoke({"query": query})
    return result