import os
from typing import Optional, Tuple, List
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


class GeminiAssistant:

    # Klasse voor het beheren van een Gemini AI-assistent met 
    # model-fallbacks en Google Search Grounding.

    MODELS_PREFERRED = [
    "gemini-3.8-flash",
    "gemini-3.1-pro-preview",
        ]

    
    def __init__(
        self,
        api_key: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ):
        resolved_key = api_key or os.getenv("GOOGLE_API_KEY")

        if not resolved_key:
            raise ValueError(
                "GOOGLE_API_KEY is missing. Please add it to your .env file or pass it as an argument."
            )

        self.client = genai.Client(api_key=resolved_key)
        self.system_prompt = system_prompt or (
            "You are a highly intelligent AI assistant that provides "
            "accurate and concise answers "
            "based on the provided context. "
            "If the answer is not directly available, provide a cautious analysis based on the available information and clearly indicate"
             "that it is an estimate."
               )

        self.model = self._select_model() 


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
            print(f"Waarschuwing bij ophalen modellenlijst ({e}). Gebruikt standaardmodel.")

        return "gemini-3.8-flash"

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
            raise ValueError("Query cannot be empty.")

        if not prompt_text or not prompt_text.strip():
            raise ValueError("Prompt context cannot be empty.")

        # Compose the full prompt with context and question
        full_prompt = f"""Context:
        {prompt_text}

         Question:{query}
         Answer:"""


        # Build the configuration for content generation
        tools = [types.Tool(google_search=types.GoogleSearch())] if enable_serp else []
        
        config = types.GenerateContentConfig(
            system_instruction=self.system_prompt,
            tools=tools,
            temperature=0.3 if not enable_serp else 0.7,
        )

        # Prepare fallback models in case of errors or quota limits
        fallback_models = [self.model] + [
            m for m in self.MODELS_PREFERRED if m != self.model
        ]

        response = None
        last_exception = None

        # Try models one by one in case of errors or quota limits
        for current_model in fallback_models:
            try:
                response = self.client.models.generate_content(
                    model=current_model,
                    contents=full_prompt.strip(),
                    config=config,
                )
                self.model = current_model
                break
            except Exception as e:
                last_exception = e
                print(f"Error {current_model}: {e}. Trying next model...")

        if not response:
            raise RuntimeError(f"Cannot generate response via Gemini API: {last_exception}")

        answer = response.text or ""
        
        web_sources: List[str] = []

        # Extract grounding sources (SERP)
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

        return answer, web_sources
    

    def ask_with_context(
        self, 
        query: str, 
        context: str, 
        enable_serp: bool = True
    ) -> tuple[str, list[str]]:
        '''
        Simplified interface to ask a question with context.
         '''
        
        answer, sources = self.generate_response(query, context, enable_serp=enable_serp)
        
        return answer, sources

    def __str__(self) -> str:
        return f"GeminiAIAssistant(model={self.model})" 
    