import fitz


def debug_extract_text(pdf_path):
    with fitz.open(pdf_path) as doc:
        for i, page in enumerate(doc):
            text = page.get_text()
            print(f"--- Page {i+1} text ---")
            print(repr(text[:500]))  # print first 500 chars with escapes shown
            print(f"Length: {len(text)}\n")

# Call it with your PDF path (replace with your actual file path)
pdf_path = "/mnt/c/Users/mohammedusama/Downloads/agent_cut.pdf"


with fitz.open(pdf_path) as doc:
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        print(f"--- Page {page_num+1} text ---")
        print(repr(text))
        print(f"Length: {len(text)}")

        # Check if page contains images
        img_list = page.get_images()
        print(f"Images on page: {len(img_list)}")


#debug_extract_text("/mnt/c/Users/mohammedusama/Downloads/agent_cut.pdf")
