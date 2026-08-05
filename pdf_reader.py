from pypdf import PdfReader


def extract_pdf_text(file_path):

    text = ""

    try:

        reader = PdfReader(file_path)

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"


        return text


    except Exception as e:

        return f"Error reading PDF: {str(e)}"