#!/usr/bin/env python3
from typing import Any, Union, List, Dict
import json
import weasyprint
from make_module import make_module

def load_questions_data() -> Dict[Any, Any]:
    """Load questions data from JSON file"""
    with open("questions.json", "r") as f:
        return json.load(f)


def write_html_header() -> str:
    """Read HTML header template"""
    with open("header.html", "r") as f:
        header_content = f.read()
    return header_content


def render_list_type_question(details: List[Dict[str, Any]]) -> str:
    """Render list-type question details"""
    html_content = ""
    det_0: Dict[str, Any] = details[0]

    if "body" in det_0:
        html_content += f'<div class="stimulus">{det_0["body"]}</div>'

    if "stem" in det_0:
        html_content += f'<div class="stem">{det_0["stem"]}</div>'

    if "prompt" in det_0:
        html_content += f'<div class="stem">{det_0["prompt"]}</div>'

    if "answer" in det_0:
        if det_0["answer"]["style"] in ("MCQ", "Multiple Choice"):
            html_content += '<ul class="options">'
            for k, v in det_0["answer"]["choices"].items():
                html_content += f'<li class="option"><span class="option-letter">{k.upper()}</span><span class="option-content">{v["body"]}</span></li>'
            html_content += '</ul>'

    return html_content


def render_dict_type_question(details: Dict[str, Any]) -> str:
    """Render dictionary-type question details"""
    html_content = ""

    if "stimulus" in details:
        html_content += f'<div class="stimulus">{details["stimulus"]}</div>'

    if "stem" in details:
        html_content += f'<div class="stem">{details["stem"]}</div>'

    if "answerOptions" in details:
        html_content += '<ul class="options">'
        for j, option in enumerate(details["answerOptions"]):
            option_letter: str = chr(65 + j)
            html_content += f'<li class="option"><span class="option-letter">{option_letter}</span><span class="option-content">{option["content"]}</span></li>'
        html_content += "</ul>"

    return html_content


def render_question(
    question_id: str, question_num: int, questions_dict: Dict[Any, Any]
) -> str:
    """Render a single question"""
    html_content = f'<div class="question"><div class="question-header">Question {question_num}</div>'

    details: Union[List[Dict[str, Any]], Dict[str, Any]] = questions_dict.get(
        question_id, {}
    ).get("details", {})

    if isinstance(details, list):
        html_content += render_list_type_question(details)
    else:
        html_content += render_dict_type_question(details)

    html_content += "</div>\n"
    return html_content


def generate_section_html(
    section: str, module: int, questions_dict: Dict[Any, Any]
) -> str:
    """Generate HTML content for a single section"""
    question_ids: List[str] = make_module(section, module)
    html_content = f"<h2>{section.capitalize()} Module {module}</h2>\n"

    for i, question_id in enumerate(question_ids):
        print(f"{section.capitalize()} section module {module} question {i + 1}: {question_id}")
        html_content += render_question(question_id, i + 1, questions_dict)

    return html_content


def generate_html_content(questions_dict: Dict[Any, Any]) -> str:
    """Generate complete HTML content"""
    html_content = write_html_header()

    for section in ["reading", "math"]:
        for module in [1, 2]:
            html_content += generate_section_html(section, module, questions_dict)

    html_content += "</body>\n</html>"
    return html_content


def write_html_file(html_content: str, filename: str = "questions.html") -> None:
    """Write HTML content to file"""
    with open(filename, "w", encoding="utf-8") as html_file:
        html_file.write(html_content)


def generate_pdf(
    html_filename: str = "questions.html", pdf_filename: str = "questions.pdf"
) -> None:
    """Generate PDF from HTML content"""
    weasyprint.HTML(html_filename).write_pdf(pdf_filename)


def main() -> None:
    """Main function to generate HTML and PDF files"""
    # Load questions data
    questions_dict: Dict[Any, Any] = load_questions_data()

    # Generate HTML content
    html_content: str = generate_html_content(questions_dict)

    # Write HTML file
    write_html_file(html_content)

    # Generate PDF
    generate_pdf()

    print("HTML and PDF files generated successfully!")


if __name__ == "__main__":
    main()
