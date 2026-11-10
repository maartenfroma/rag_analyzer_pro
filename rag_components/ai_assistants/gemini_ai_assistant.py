import os
from typing import Optional, Tuple, List
from dotenv import load_dotenv
from google import genai
from google.genai import types
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


from rag_components.exceptions.gemini_exceptions import (
    GeminiError,
    GeminiAuthenticationError,
    GeminiModelError,
    GeminiContextError,
    GeminiRateLimitError,
    GeminiResponseError,
    GeminiConnectionError
)

# Load environment variables from .env file for API key configuration
load_dotenv()

# GeminiAssistant class for managing Gemini AI assistant 
# with model selection and context handling.

class GeminiAssistant:

    # Klasse voor het beheren van een Gemini AI-assistent met 
    # model-fallbacks en Google Search Grounding.

    # Default model to use if no preferred or flash model is available
    MODELS_PREFERRED = [
    "gemini-3.8-flash",
    "gemini-3.1-pro-preview",
        ]


    # Initialize the GeminiAssistant with API key and system prompt.
    def __init__(
        self,
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ):

        # Resolve the API key from the argument or environment variable
        resolved_key = api_key or os.getenv("GOOGLE_API_KEY")

        # Raise an error if the API key is not resolved
        if not resolved_key:
            raise GeminiAuthenticationError(
                "GOOGLE_API_KEY is missing. Please add it to your .env file or pass it as an argument."
            )

        # Store the resolved API key and initialize 
        # the Gemini client with it
        self.api_key = resolved_key

        try:
            self.client = genai.Client(api_key=resolved_key)
        except Exception as e:
            logger.exception(f"Failed to initialize Gemini client: {e}")
            raise GeminiConnectionError(
                "Failed to initialize Gemini client.") from e

        # Define the response formatting rules for the Gemini assistant 
        response_formatting=str(

            "IMPORTANT FORMATTING RULES:\n\n"

            "- Respond using Markdown only.\n"
            "- Never generate HTML.\n"
            "- Never use tags such as:\n"
            "  <ul>, <ol>, <li>, <strong>, <em>, <p>, <div>, <span>.\n"
            "- Use Markdown bullet points (-).\n"
            "- Use Markdown numbered lists (1. 2. 3.).\n"
            "- Use **bold** for emphasis.\n"
            "- Use *italic* for emphasis.\n"
            "- Always complete your answer.\n"
            "- Never stop in the middle of a sentence or list item.\n"
            "- If the answer is long, finish all sections before ending.\n"
            "- Do not include any XML, HTML or CSS.\n"
        )


        # Store the system prompt, using the default if not 
        # provided
        self.system_prompt = system_prompt or (response_formatting + "\n\n" + (

            "You are an expert document analysis assistant. "

            "Answer only using the provided context. "

            "Use all supplied context and combine information from all "
            "retrieved passages before answering. "

            "When information about a person, event, concept or topic appears "
            "in multiple passages, merge that information into one coherent answer. "

            "Provide detailed and comprehensive answers when sufficient "
            "context is available. "

            "Do not repeat the same information unnecessarily. "

            "If the answer is not directly available in the context, "
            "provide a cautious analysis based on the available information "
            "and clearly state that it is an estimate. "

            "Only say information is unavailable if it truly cannot be "
            "derived from the supplied context."
        ))
                    
        # Select the model to use for the Gemini 
        # client based on availability and preferences
        self.model = self._select_model() 
        

    # Select the best available model based on preferred models 
    # and flash models
    def _select_model(self) -> str:

        #Select the best available model based on preferred models and flash models
        try:
            #Get the list of available models from the Gemini API
            models_list = self.client.models.list()

            # Extract model names from the API response
            available_models={m.name.replace("models/", "") for m in models_list}

            # Check if any preferred model is available
            # Iterate over preferred models and return the first available one

            for preferred_model in self.MODELS_PREFERRED:
            
                if preferred_model in available_models:
                    return preferred_model

            
            # If no preferred model is available, check for flash models
            flash_models = sorted([m for m in available_models 
                                   if "flash" in m.lower()], reverse=True)
            
            # Return the first available flash model if any
            if flash_models:
                return flash_models[0]
            
            # If no flash model is available, return any available model
            if available_models:
                return next(iter(available_models))

        except Exception as e:
            raise GeminiConnectionError(f"Failed to fetch models list: {e}")
        
        #Return the default model if no other model is available
        return "gemini-3.8-flash"

    # Default model to use if no preferred or flash model is available
    def generate_response(
        self, 
        query: str, 
        prompt_text: str, 
        enable_serp: bool = True
    ) -> Tuple[str, List[str]]:
        #
        # Validate input parameters
        # Check if query and prompt_text are not empty
        if not query or not query.strip():
            raise GeminiContextError("Query cannot be empty.")
        
        # Strip leading and trailing whitespace from query and prompt_text
        if not prompt_text or not prompt_text.strip():
            raise GeminiContextError("Prompt context cannot be empty.")

        # Compose the full prompt with context and question
        full_prompt = f"""Context:
        {prompt_text}

         Question:{query}
         Answer:"""


        # Build the configuration for content generation
        tools = [types.Tool(google_search=types.GoogleSearch())] if enable_serp else []

        # Build the configuration for content generation 
        # based on system prompt, tools, and temperature settings
        config = types.GenerateContentConfig(
            system_instruction=self.system_prompt,
            tools=tools,
            temperature=0.3 if not enable_serp else 0.7,
            max_output_tokens=2000,
        )

        # Prepare fallback models in case of errors or quota limits
        fallback_models = [self.model] + [
            m for m in self.MODELS_PREFERRED if m != self.model
        ]
        # Ensure the fallback models list is not empty
        response = None
        last_exception = None

        # Try models one by one in case of errors or quota limits
        for current_model in fallback_models:

            # Attempt to generate content using the current model
            try:
                response = self.client.models.generate_content(
                    model=current_model,
                    contents=full_prompt.strip(),
                    config=config,
                )
                self.model = current_model

                logger.info(f"Successfully generated response "
                            f"using model: {current_model}")
                break

            except Exception as e:
                last_exception = e
                logger.warning(f"Error {current_model}: {e}. "
                            "Trying next model...")
        if not response:
            raise GeminiModelError(f"Cannot generate response "
                                   f"via Gemini API: {last_exception}")   

        # Log the final answer and web sources for debugging purposes
        answer = response.text or ""
        logger.info(f"Final answer: {answer}")  
        
        
        web_sources: List[str] = []

        # Extract grounding sources (SERP)
        # Serp grounding is used to extract web sources from 
        # the response if available
        if enable_serp and response.candidates:
            grounding_meta = getattr(response.candidates[0], "grounding_metadata", None)
            if grounding_meta and getattr(grounding_meta, "grounding_chunks", None):
                sources_set = set()
                for chunk in grounding_meta.grounding_chunks:
                    web = getattr(chunk, "web", None)
                    if web:
                        uri = getattr(web, "uri", None)
                        title = getattr(web, "title", None) or uri
                        if uri:
                            sources_set.add(f"[{title}]({uri})")
                web_sources = list(sources_set)

        # Return the final answer and web sources
        return answer, web_sources
    

    #METHOD: Ask a question with context using the GeminiAssistant
    def ask_with_context(
        self, 
        query: str, 
        context: str, 
        enable_serp: bool = True
    ) -> tuple[str, list[str]]:
        '''
        Simplified interface to ask a question with context.
         '''
        # Attempt to generate a response using the GeminiAssistant 
        # with the provided context    
        try:
            answer, sources = self.generate_response(query, context, enable_serp=enable_serp)
        except (GeminiModelError, GeminiContextError, GeminiAuthenticationError,
                GeminiConnectionError) as e:
      
            logger.exception(f"Error in ask_with_context: {e}")
            raise 
        
        #Return the answer and sources retrieved from the GeminiAssistant
        return answer, sources

    # String representation of the GeminiAIAssistant    
    def __str__(self) -> str:
        return f"GeminiAIAssistant(model={self.model})" 
    