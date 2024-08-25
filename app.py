import streamlit as st
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import os

# Function to initialize the Gemini API client
def initialize_gemini():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def generate_lesson_plan_gemini(input_query):
    # Initialize the model configuration
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 50,
        "max_output_tokens": 2000,
        "response_mime_type": "text/plain",
    }

    # Initialize the model with the specified configuration
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )

    # Start a new chat session
    chat_session = model.start_chat(history=[])

    # Prepare the prompt
    prompt = f"""You are an helpful assistant who's job is to:-
Generate a detailed lesson plan for the following syllabus details:
If the input contains just some message and doesn't contain any syllabus information reply accordingly.
Input:

{input_query}

Output format:

The output should have a structure like below. The structure below is just an example.And the number of sessions must be equal to number of hours from the query above:
Each session should have the following format : **Session 3: History of Artificial Intelligence (60 mins)**

| **Development of Lesson Plan**| **Teaching Aids** | **Time** |
|---|---|---|
| **Early AI Research and Developments** |  Projector - PPT presentation | 10 mins |
| **The Golden Age of AI and its Challenges** |  Projector - PPT presentation | 10 mins |
| **The AI Winter and its Aftermath** | Projector - PPT presentation | 10 mins |
| **The Rise of Modern AI: Machine Learning and Deep Learning** |  Projector - PPT presentation | 15 mins |
| **Summary and Evaluation** |  Board | 5 mins |
| **Home Assignment and Follow Up** |    | 5 mins |
| **Preparation for Next Lecture** |    |  |

TOTAL NUMBER OF SESSIONS FOR THIS UNIT: 07.
"""

    # Send the message and get a response
    response = chat_session.send_message(prompt)

    # Return the generated lesson plan
    return response.text.strip()

def save_to_pdf(text, filename):
    # Create a PDF document with ReportLab
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()

    # Define custom styles for headings, bold text, and lists
    heading_style = ParagraphStyle(
        'Heading1', parent=styles['Heading1'], fontSize=14, spaceAfter=12, textColor='#000000'
    )
    bold_style = ParagraphStyle(
        'Bold', parent=styles['BodyText'], fontName='Helvetica-Bold', fontSize=12
    )
    list_style = ParagraphStyle(
        'List', parent=styles['BodyText'], fontName='Helvetica', fontSize=12, leftIndent=20, bulletFontName='Helvetica', bulletFontSize=12
    )

    content = []
    table_mode = False
    table_data = []

    paragraphs = text.split('\n')
    for para in paragraphs:
        if para.startswith("|") and "---" not in para:
            # If the line starts with a pipe, it's part of a table
            table_data.append([cell.strip() for cell in para.split("|")[1:-1]])
            table_mode = True
        elif table_mode:
            # If table mode was active, add the table to the PDF content
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            content.append(table)
            content.append(Spacer(1, 12))
            table_data = []
            table_mode = False
        else:
            if para.startswith("* "):
                # Convert list items to a proper format
                para = para.replace('* ', '')  # Remove bullet indicator for ListFlowable
                content.append(Paragraph(f'• {para}', list_style))
            elif para.startswith("**"):
                # Handle bold text
                para = para.replace("**", "")
                para = f"<b>{para}</b>"
                content.append(Paragraph(para, bold_style))
            else:
                # Normal text
                content.append(Paragraph(para, styles['BodyText']))
            content.append(Spacer(1, 6))  # Add space between paragraphs

    # Build the PDF
    doc.build(content)

# Streamlit app UI
def main():
    st.title("Lesson Plan Generator made by AI and DS Department of DYPCOE Akurdi")
    st.write("Enter the syllabus details below and generate a lesson plan: Only enter syllabus of one unit")

    input_query = st.text_area("Syllabus Details:", height=200)
    if st.button("Generate Lesson Plan"):
        if input_query.strip() == "":
            st.error("Please enter some syllabus details.")
        else:
            with st.spinner("Generating lesson plan..."):
                initialize_gemini()
                lesson_plan = generate_lesson_plan_gemini(input_query)
                st.success("Lesson plan generated successfully!")

                st.subheader("Generated Lesson Plan:")
                st.code(lesson_plan)

                pdf_filename = "lesson_plan.pdf"
                save_to_pdf(lesson_plan, pdf_filename)

                # Provide download link for the PDF
                with open(pdf_filename, "rb") as file:
                    st.download_button(
                        label="Download Lesson Plan as PDF",
                        data=file,
                        file_name=pdf_filename,
                        mime="application/pdf"
                    )

if __name__ == "__main__":
    main()
