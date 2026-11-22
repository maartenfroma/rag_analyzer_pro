from rag_components.ai_assistants.gemini_ai_assistant import GeminiAssistant


# Service for generating research reports using GeminiAIAssistant
class ResearchReportService:
   
    # Maximum number of chapters to generate for the research report
    MAX_CHAPTERS = 6
   
    # Initialize the research report service with a GeminiAssistant instance
    def __init__(self, assistant: GeminiAssistant):
        
        self.assistant = assistant  
    

    # Generate an outline for the research report based on the question and context
    def generate_outline(self, question: str, context:str, status=None)->list[str]:
        
        prompt = f"""
                Maak een inhoudsopgave voor een professioneel onderzoeksrapport.

                Geef exact tien hoofdstuktitels terug.
                
                Vraag:

                {question}

                Gebruik uitsluitend informatie uit de context.

                Geef alleen hoofdstuktitels terug.
                """

        
        if status:
            status.write("Generating outline...")
        answer, _ = self.assistant.ask_with_context(
            query=prompt,
            context=context
        )

        return [
            line.strip("-•1234567890. ").strip()
            for line in answer.splitlines()
            if line.strip()
        ]

    
    # Generate a chapter for the research report based on the title and context
    def generate_chapter(self, title: str, context: str, status=None)->str:
        
    
            prompt = f"""
            Maak hoofdstuk:

            {title}

            Gebruik uitsluitend informatie uit de context.

            Schrijf professioneel.
            Gebruik meerdere paragrafen.
            Werk het hoofdstuk volledig uit.
            
            BELANGRIJK:
            - Voeg geen hoofdstuktitel toe.
            - Voeg geen markdown heading toe.
            - Begin direct met de inhoud.
            - Schrijf alleen de tekst van het hoofdstuk.
            """
                
            answer, _ = self.assistant.ask_with_context(
                query=prompt,
                context=context
            )

            return answer
        
    # Generate the full research report based on the question and context
    def generate_report(self, question: str, context: str, status=None) -> str:
        
        if status:
            status.write(f"📖 Generating outline ...")
        
        outline = self.generate_outline(question, context, status=status)
        
        print("Generated outline:", outline)
        
        if not outline:
            return "No outline generated"   
        
        # Initialize the list to hold the content of each chapter
        sections=[]
        
        # Iterate over each chapter title in the outline to generate its content
        for chapter in outline:
            
            # Display the status message for the current chapter being generated
            if status:
                
                # Update the status message to indicate which chapter is being generated
                status.write(f"Generating chapter for: {chapter}")
            
            # Generate the content for the current chapter using the title and context
            chapter_content = self.generate_chapter(title=chapter, context=context, status=status)
            
            # Append the generated chapter content to the sections list
            sections.append(f"# {chapter}\n\n{chapter_content}"
            )

        if not sections:
            return "No chapters generated"
          
        # Combine all sections into the final report
        return "\n\n".join(sections)