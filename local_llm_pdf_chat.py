import gradio as gr
import pdfplumber
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import fitz  # PyMuPDF

# 🧠 Load local LLM
llm = Llama(model_path="models/llm.gguf", n_ctx=2048)

# # 🔍 Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# 🗃️ FAISS Index
dimension = embedding_model.get_sentence_embedding_dimension()
faiss_index = faiss.IndexFlatL2(dimension)
document_chunks = []  # Holds original text chunks, same order as FAISS vectors

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
dimension = embedding_model.get_sentence_embedding_dimension()
index = faiss.IndexFlatL2(dimension)

stored_chunks = []

def extract_and_chunk(pdf_file, chunk_size=500):
    # pdf_file is expected to be a filepath string from gr.File with type="filepath"
    with fitz.open(pdf_file) as doc:
        full_text = "\n".join([page.get_text() for page in doc])

    if not full_text.strip():
        print("⚠️ No text extracted from PDF.")
    else:
        print("✅ Extracted PDF text preview:")
        print(full_text[:1000])  # Print first 1000 characters

    chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
    return chunks





def index_pdf(pdf_file):
    chunks = extract_and_chunk(pdf_file)
    if not chunks:
        return "❌ No valid chunks to index."

    embeddings = embedding_model.encode(chunks)
    index.reset()  # Clear old index
    index.add(np.array(embeddings))
    stored_chunks.clear()
    stored_chunks.extend(chunks)

    print(f"✅ Indexed {len(chunks)} chunks in FAISS.")
    return "✅ PDF indexed. You can now ask questions."


def answer_question(question, history):
    if len(stored_chunks) == 0:
        answer = "⚠️ No data indexed yet. Please upload and index a PDF."
    else:
        query_vector = embedding_model.encode([question])
        D, I = index.search(np.array(query_vector), k=5)

        context_chunks = [stored_chunks[i] for i in I[0] if i < len(stored_chunks)]

        if not context_chunks:
            answer = "No relevant content found in the PDF."
        else:
            context = "\n".join(context_chunks)
            prompt = build_prompt(context, question)
            response = llm(prompt, max_tokens=512, stop=["\n", "Question:"], echo=False)
            try:
                answer = response["choices"][0]["text"].strip()
                if not answer:
                    answer = "⚠️ The model could not generate a valid answer."
            except Exception as e:
                answer = f"⚠️ Error from model: {str(e)}"

            # answer = response["choices"][0]["text"].strip()

    if history is None:
        history = []

    print("Question: ", question)
    print("Answer: ", answer)

    history.append((question, answer))
    return history, history  # First for chatbot, second for state

def build_prompt(context, question):
    base = f"""
You are a helpful assistant that answers user questions using ONLY the following PDF content. Be accurate, concise, and do not hallucinate information.

--- BEGIN PDF CONTENT ---
{context}
--- END PDF CONTENT ---

User Question: {question}

Answer:"""

    # Light formatting suggestion for list-type questions
    if "list" in question.lower() or "important" in question.lower():
        base += "\n\nIf possible, format the answer as a numbered list."

    return base.strip()



# 🖼️ Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("## 📄 Ask Questions About Your Confidential PDF (100% Local with FAISS)")

    chatbot = gr.Chatbot()
    pdf_input = gr.File(label="Upload PDF", type="filepath")
    index_btn = gr.Button("Index PDF")

    user_question = gr.Textbox(label="Ask a Question")
    ask_btn = gr.Button("Ask")
    state = gr.State([])

    index_btn.click(fn=index_pdf, inputs=[pdf_input], outputs=[])
    ask_btn.click(fn=answer_question, inputs=[user_question, state], outputs=[chatbot, state])

demo.launch()
