import os
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI

import tool1
import tool2
from prompts import SAFETY_PROMPT, METADATA_PROMPT, RESPONSE_GENERATION_PROMPT, QUERY_ENHANCEMENT_PROMPT, TOOL_SELECTION_PROMPT

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

def check_query_safety(user_input: str) -> Dict[str, Any]:
    response = client.responses.create(
        model="gpt-4-turbo",
        instructions=SAFETY_PROMPT,
        input=user_input
    )

    refined_text = response.output[0].content[0].text.strip()

    if not refined_text:
        return {
            "is_safe": False,
            "refined_query": None
        }
    else:
        return {
            "is_safe": True,
            "refined_query": refined_text
        }

def extract_query_metadata(user_query: str) -> Dict[str, Any]:
    response = client.responses.create(
        model="gpt-4-turbo",
        instructions=METADATA_PROMPT,
        input=user_query
    )

    output = response.output[0].content[0].text
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {}

def enhance_search_query(query: str, metadata: Dict[str, Any]) -> str:
    enhancement_input = f"""
    Original Query: {query}
    
    Metadata:
    Company: {metadata.get('company_name', 'Not specified')}
    Industry: {metadata.get('industry', 'Not specified')}
    Financial Metric: {metadata.get('financial_metric', 'Not specified')}
    Time Period: {metadata.get('time_period', 'Not specified')}
    Country: {metadata.get('country', 'Not specified')}
    """
    
    response = client.responses.create(
        model="gpt-4-turbo",
        instructions=QUERY_ENHANCEMENT_PROMPT,
        input=enhancement_input
    )
    
    enhanced_query = response.output[0].content[0].text.strip()
    return enhanced_query if enhanced_query else query

def select_tools(query: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    response = client.responses.create(
        model="gpt-4-turbo",
        instructions=TOOL_SELECTION_PROMPT,
        input=query
    )
    
    output = response.output[0].content[0].text
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {
            "vector_search": True,
            "web_search": True,
            "data_analysis": False,
            "report_generation": False,
            "primary_tool": "web_search"
        }

def retrieve_context_from_faiss(query: str, metadata: Dict[str, Any]) -> List[str]:
    persist_path = "data/output/faiss_index.index"
    doc_map_path = "data/output/doc_map.json"
    
    if not os.path.exists(persist_path) or not os.path.exists(doc_map_path):
        return []
    
    index, documents, ids = tool1.load_index(persist_path, doc_map_path)
    
    results = tool1.query_embeddings(index, query, documents, ids, top_k=3)
    
    context_passages = [doc for doc, _, _ in results if doc]
    
    return context_passages

def perform_web_search(query: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    enhanced_query = enhance_search_query(query, metadata)
    
    return tool2.web_search(enhanced_query)

def generate_response(query: str, context_passages: List[str], web_results: List[Dict[str, Any]]) -> str:
    combined_context = ""
    
    if context_passages:
        combined_context += "### Context from Knowledge Base:\n"
        for i, passage in enumerate(context_passages):
            combined_context += f"[{i+1}] {passage[:500]}...\n\n"
    
    if web_results:
        combined_context += "### Context from Web Search:\n"
        for i, result in enumerate(web_results[:3]):
            combined_context += f"[{i+1}] Title: {result.get('title', 'No title')}\n"
            combined_context += f"URL: {result.get('url', 'No URL')}\n"
            combined_context += f"Content: {result.get('content', 'No content')[:300]}...\n\n"
    
    if not combined_context:
        combined_context = "No relevant context found."
    
    response = client.responses.create(
        model="gpt-4-turbo",
        instructions=RESPONSE_GENERATION_PROMPT,
        input=f"User Query: {query}\n\nContext Information:\n{combined_context}"
    )
    
    return response.output[0].content[0].text.strip()

def process_user_query(user_input: str) -> Dict[str, Any]:
    safety_result = check_query_safety(user_input)
    
    if not safety_result["is_safe"]:
        return {
            "status": "error",
            "message": "Query contains harmful or inappropriate content",
            "response": None
        }
    
    refined_query = safety_result["refined_query"]
    
    metadata = extract_query_metadata(refined_query)
    
    tool_selection = select_tools(refined_query, metadata)
    
    context_passages = []
    web_results = []
    
    if tool_selection.get("vector_search", True):
        context_passages = retrieve_context_from_faiss(refined_query, metadata)
    
    if tool_selection.get("web_search", True):
        web_results = perform_web_search(refined_query, metadata)
    
    response = generate_response(refined_query, context_passages, web_results)
    
    return {
        "status": "success",
        "refined_query": refined_query,
        "metadata": metadata,
        "tool_selection": tool_selection,
        "response": response
    } 