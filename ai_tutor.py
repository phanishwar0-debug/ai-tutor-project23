import openai
import os
from config import Config

class AITutor:
    def __init__(self):
        openai.api_key = Config.OPENAI_API_KEY
        self.system_prompt = """You are an AI tutor for rural students. You should:
        1. Explain concepts in simple, easy-to-understand language
        2. Use examples from daily life that rural students can relate to
        3. Break down complex topics into smaller steps
        4. Be patient and encouraging
        5. Ask questions to check understanding
        6. Provide practice problems when appropriate
        
        Subjects you can help with: Mathematics, Science, English, Social Studies, Computer Basics."""
    
    def get_response(self, question, subject="general"):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"{self.system_prompt}\n\nCurrent subject: {subject}"},
                    {"role": "user", "content": question}
                ],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI Error: {e}")
            return "I apologize, but I'm having trouble connecting right now. Please try again later or ask your teacher for help with: " + question