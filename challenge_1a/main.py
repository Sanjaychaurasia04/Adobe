import fitz  # PyMuPDF
import os
import json

def rgb_from_int(color_int):
    # PyMuPDF color is 0xRRGGBB
    r = (color_int >> 16) & 255
    g = (color_int >> 8) & 255
    b = color_int & 255
    return (r, g, b)

def is_bold(flags):
    return (flags & 4) != 0

def is_colored(color_int):
    r, g, b = rgb_from_int(color_int)
    # Consider something as "colored" if not close to grayscale
    return not (abs(r - g) < 10 and abs(r - b) < 10 and abs(g - b) < 10 and r < 60)

def is_form_like(page):
    """
    Heuristic to detect form-like pages by counting field labels and short lines.
    """
    block_texts = []
    block_lengths = []
    form_phrase_count = 0

    field_keywords = [
        "name", "date", "designation", "s.no", "serial no", "relationship", 
        "amount", "advance", "pay", "service", "age", "town", "fare","goals"
    ]

    for block in page.get_text("dict")["blocks"]:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip().lower()
                    if not text:
                        continue
                    block_texts.append(text)
                    block_lengths.append(len(text))
                    if any(text.startswith(k) or k in text for k in field_keywords):
                        form_phrase_count += 1

    if not block_texts:
        return False

    short_line_fraction = sum(1 for l in block_lengths if l <= 30) / len(block_lengths)
    return len(block_texts) > 15 and short_line_fraction > 0.4 and form_phrase_count >= 4

def extract_title(page):
    """Single-pass version with multi-line title support."""
    largest_size = 0
    title_parts = []
    current_group = []
    
    for block in page.get_text("dict")["blocks"]:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            line_text = []
            line_size = 0
            for span in line["spans"]:
                span_size = span["size"]
                if span_size >= line_size:  # Get dominant size in line
                    line_size = span_size
                line_text.append(span["text"].strip())
            
            if line_size > largest_size:
                # Found larger text - reset everything
                largest_size = line_size
                title_parts = [" ".join(line_text)]
            elif line_size == largest_size:
                # Same size as current title - add to parts
                title_parts.append(" ".join(line_text))
    
    return " ".join(title_parts).strip()

def extract_outline(pdf_path):
    doc = fitz.open(pdf_path)
    all_blocks = []

    if is_form_like(doc[0]):
        title = extract_title(doc[0])
        return {"title": title, "outline": []}

    for page_number, page in enumerate(doc, start=0):
        for block in page.get_text("dict")["blocks"]:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    size = span["size"]
                    font = span["font"]
                    flags = span["flags"]
                    color = span["color"]
                    all_blocks.append({
                        "text": text,
                        "size": size,
                        "font": font,
                        "flags": flags,
                        "color": color,
                        "page": page_number,
                        "is_bold": is_bold(flags),
                        "is_colored": is_colored(color)
                    })
    if not all_blocks:
        return {"title": "", "outline": []}

    # Build composite score: size + 2*bold + 1.5*colored
    for block in all_blocks:
        block["score"] = block["size"] + (2 if block["is_bold"] else 0) + (1.5 if block["is_colored"] else 0)

    # Get unique scores and use as levels heuristically
    unique_scores = sorted({b["score"] for b in all_blocks}, reverse=True)
    level_map = {}
    if unique_scores:
        level_map[unique_scores[0]] = "Title"
    if len(unique_scores) > 1:
        level_map[unique_scores[1]] = "H1"
    if len(unique_scores) > 2:
        level_map[unique_scores[2]] = "H2"
    if len(unique_scores) > 3:
        level_map[unique_scores[3]] = "H3"

    outline = []
    title = ""
    for block in all_blocks:
        level = level_map.get(block["score"])
        if level == "Title" and not title:
            title = extract_title(doc[0])
        if level in {"H1", "H2", "H3"}:
            outline.append({
                "level": level,
                "text": block["text"],
                "page": block["page"]
            })

    return {
        "title": title,
        "outline": outline
    }

def process_all_pdfs(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename.replace(".pdf", ".json"))
            result = extract_outline(input_path)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    process_all_pdfs("sanjay/Hackthon-main/src/input", "sanjay/Hackthon-main/src/output")
