"""
Parse NBS exam questions from PDF and export to JSON.
Usage: python3 scripts/parse_questions.py
"""
from __future__ import annotations
import re
import json
from pypdf import PdfReader

PDF_PATH = "/Users/petropuneiko/Downloads/otazky-2025-12-18.pdf"
OUTPUT_PATH = "scripts/questions.json"

SECTION_RE = re.compile(
    r"^(Všeobecná časť|Sektor [^\n]+?)(?:\s*\n|$)", re.MULTILINE
)
# Question starts: number followed by dot and space
Q_START_RE = re.compile(r"^(\d{1,4})\.\s+(.+)", re.MULTILINE)
# Answer line: a-e followed by dot/period and space
ANS_RE = re.compile(r"^([a-e])\.\s+(.+)")


def extract_full_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "\n".join(parts)


def determine_level(section_name: str) -> str:
    name = section_name.lower()
    if "vyšší stupeň" in name or "vyšší" in name:
        return "vyssi"
    if "stredný stupeň" in name or "stredný" in name:
        return "stredny"
    return "zakladny"


def determine_sector(section_name: str) -> str:
    name = section_name.lower()
    # strip level suffixes
    name = re.sub(r"otázky pre (stredný|vyšší) stupeň", "", name).strip()
    name = re.sub(r"\s+", " ", name)
    return name


def parse(text: str) -> list[dict]:
    lines = text.splitlines()

    questions: list[dict] = []
    current_section = "Všeobecná časť"
    current_q: dict | None = None
    current_ans_key: str | None = None
    buffer: list[str] = []

    def flush_answer():
        nonlocal current_ans_key, buffer
        if current_q and current_ans_key and buffer:
            ans_text = " ".join(buffer).strip()
            # Remove hyphenation artifacts
            ans_text = re.sub(r"-\s+", "", ans_text)
            current_q["options"][current_ans_key] = ans_text
        current_ans_key = None
        buffer = []

    def flush_question():
        nonlocal current_q
        flush_answer()
        if current_q and current_q.get("text") and len(current_q.get("options", {})) >= 2:
            questions.append(current_q)
        current_q = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        # Section header detection
        sec_m = SECTION_RE.match(line)
        if sec_m:
            flush_question()
            current_section = sec_m.group(1).strip()
            continue

        # Skip page numbers (lone digit(s))
        if re.fullmatch(r"\d{1,3}", line):
            continue

        # New question
        q_m = Q_START_RE.match(line)
        if q_m:
            flush_question()
            q_num = int(q_m.group(1))
            q_text = q_m.group(2).strip()
            current_q = {
                "number": q_num,
                "section": current_section,
                "sector": determine_sector(current_section),
                "level": determine_level(current_section),
                "text": q_text,
                "options": {},
                "correct": None,
            }
            current_ans_key = None
            buffer = []
            continue

        if current_q is None:
            continue

        # Answer option line
        ans_m = ANS_RE.match(line)
        if ans_m:
            flush_answer()
            current_ans_key = ans_m.group(1)
            ans_text = ans_m.group(2).strip()
            # Bold answer detection heuristic: PDF extracts correct answer
            # with leading bold marker — we rely on position (first option
            # that appears with a "?" suffix or capital letter at start is NOT
            # reliable). Instead we mark correct via bold font later.
            # For now store as-is; correct answer is the FIRST option listed
            # whose line in raw PDF had bold styling. pypdf doesn't preserve bold,
            # so we use a known convention: the PDF spec says "Správna odpoveď je
            # vyznačená tučným písmom" — bold = correct.
            # We can detect it heuristically: correct answer text tends to start
            # with uppercase or have punctuation. We'll mark all as None and fix
            # via secondary pass.
            buffer = [ans_text]
            continue

        # Continuation of question text or answer text
        if current_ans_key:
            buffer.append(line)
        else:
            # continuation of question text
            current_q["text"] += " " + line

    flush_question()

    # Post-process: remove hyphenation in question texts
    for q in questions:
        q["text"] = re.sub(r"-\s+", "", q["text"]).strip()

    return questions


def detect_correct_answers(text: str, questions: list[dict]) -> None:
    """
    Bold text in PDF: pypdf sometimes outputs bold text differently.
    Strategy: for each question block in raw text, find which answer option
    appears to be 'tučné' (bold). Since pypdf flattens bold, we use a
    secondary heuristic: the NBS PDF places the correct answer FIRST among
    options in alphabetical order — actually, answers are always a-e in order.
    
    Better approach: re-extract using pdfplumber char-level font info.
    But as a fast approximation: the correct answer for many questions can be
    inferred because the PDF has the correct marked with a special character
    or capitalization. Without font info, we skip and mark correct=None.
    
    We will try to detect via pdfplumber font weight if available.
    """
    try:
        import pdfplumber  # type: ignore

        q_by_num = {q["number"]: q for q in questions}
        current_q_num: int | None = None
        current_ans_key: str | None = None
        bold_threshold = 700  # font weight

        with pdfplumber.open(PDF_PATH) as pdf:
            for page in pdf.pages:
                words = page.extract_words(extra_attrs=["fontname", "size"])
                line_text = ""
                line_bold = False
                prev_y = None

                for word in words:
                    y = round(word["top"])
                    is_bold = "Bold" in word.get("fontname", "") or "bold" in word.get("fontname", "").lower()

                    if prev_y is not None and abs(y - prev_y) > 3:
                        # process previous line
                        _process_line(line_text.strip(), line_bold, q_by_num,
                                      current_q_num, current_ans_key)
                        line_text = ""
                        line_bold = False

                    line_text += " " + word["text"]
                    if is_bold:
                        line_bold = True
                    prev_y = y

        print("pdfplumber bold detection done")
    except Exception as e:
        print(f"pdfplumber not available or failed: {e}. correct=None for all questions.")


def _process_line(line: str, is_bold: bool, q_by_num: dict,
                  current_q_num, current_ans_key):
    pass  # placeholder — bold detection complex, skip for MVP


def main():
    print("Reading PDF...")
    text = extract_full_text(PDF_PATH)
    print(f"Text length: {len(text)} chars")

    print("Parsing questions...")
    questions = parse(text)
    print(f"Parsed {len(questions)} questions")

    # Stats
    sectors = {}
    for q in questions:
        s = q["sector"]
        sectors[s] = sectors.get(s, 0) + 1
    print("\nBy sector:")
    for s, c in sorted(sectors.items(), key=lambda x: -x[1]):
        print(f"  {c:4d}  {s}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
