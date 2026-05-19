import os
import docx
from pypdf import PdfReader
from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)

# The Files module allows JARVIS to read, summarize, create, and open files.

class FilesSkill:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        print("[FILES] Files module initialized.")

    def read_text_file(self, file_path: str) -> str:
        """Reads a .txt file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading text file, sir: {e}"

    def read_pdf(self, file_path: str) -> str:
        """Reads a .pdf file using pypdf."""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text
        except Exception as e:
            return f"Error reading PDF file, sir: {e}"

    def read_docx(self, file_path: str) -> str:
        """Reads a .docx file using python-docx."""
        try:
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            return f"Error reading Word document, sir: {e}"

    def read_file(self, file_path: str) -> str:
        """Detects file type and reads its content."""
        if not os.path.exists(file_path):
            return f"I cannot find the file at {file_path}, sir."

        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.txt':
            return self.read_text_file(file_path)
        elif ext == '.pdf':
            return self.read_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return self.read_docx(file_path)
        else:
            return f"I am unable to read {ext} files currently, sir."

    def summarize_file(self, file_path: str) -> str:
        """Reads the file and generates a concise summary using Gemini."""
        print(f"[FILES] Summarizing {file_path}...")
        content = self.read_file(file_path)
        
        if content.startswith("Error") or content.startswith("I cannot find") or content.startswith("I am unable"):
            return content

        if not content.strip():
            return "The file appears to be empty, sir."

        try:
            system_instruction = (
                "You are JARVIS. Summarize the provided document text concisely and intelligently. "
                "Address the user as 'sir'. Do not overexplain."
            )
            
            # Truncate content to avoid exceeding token limits for extremely large files
            truncated_content = content[:100000]
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Please summarize the following document:\n\n{truncated_content}",
                config={"system_instruction": system_instruction, "temperature": 0.3}
            )
            return response.text.strip()
        except Exception as e:
            print(f"[FILES] Error summarizing file: {e}")
            return "I encountered an error while trying to summarize the document, sir."

    def create_file(self, file_path: str, content: str) -> str:
        """Creates a text file and writes content to it."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[FILES] Created file at {file_path}")
            return f"I have successfully created the file {os.path.basename(file_path)}, sir."
        except Exception as e:
            print(f"[FILES] Error creating file: {e}")
            return f"I encountered an error creating the file, sir: {e}"

    def open_file(self, file_path: str) -> str:
        """Opens a file using the default Windows application."""
        if not os.path.exists(file_path):
            return f"I cannot find the file {os.path.basename(file_path)}, sir."
            
        try:
            print(f"[FILES] Opening {file_path}...")
            os.startfile(file_path)
            return f"Opening {os.path.basename(file_path)} for you now, sir."
        except Exception as e:
            print(f"[FILES] Error opening file: {e}")
            return f"I was unable to open the file, sir: {e}"

if __name__ == "__main__":
    files_skill = FilesSkill()
    
    # Test file creation
    test_file = "test_jarvis_doc.txt"
    print(files_skill.create_file(test_file, "This is a test document created by JARVIS. It contains some basic information."))
    
    # Test file read
    print("\n--- Content ---")
    print(files_skill.read_file(test_file))
    
    # Test summarization
    print("\n--- Summary ---")
    print(files_skill.summarize_file(test_file))
    
    # Test open file
    print("\n--- Opening ---")
    print(files_skill.open_file(test_file))
