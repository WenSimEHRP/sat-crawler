#!/usr/bin/env python3
from typing import Any, Union, List, Dict, Optional
import json
import argparse
from make_module import make_module
from string import Template


def load_questions_data() -> Dict[Any, Any]:
    """Load questions data from JSON file"""
    with open("questions.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_template() -> Template:
    """Load the main HTML template"""
    with open("template.html", "r", encoding="utf-8") as f:
        return Template(f.read())


def get_correct_answer(details: Union[List[Dict[str, Any]], Dict[str, Any]]) -> str:
    """Extract the correct answer from question details"""
    if isinstance(details, list) and details:
        det_0 = details[0]
        if "answer" in det_0 and "correct" in det_0["answer"]:
            return det_0["answer"]["correct"]
    elif isinstance(details, dict):
        if "correctAnswerOption" in details:
            return chr(65 + details["correctAnswerOption"])
        elif "correctAnswer" in details:
            return details["correctAnswer"]
        elif "correct_answer" in details:
            return ", ".join(details["correct_answer"])

    return "<em>N/A; check explanation for more info</em>"


def get_answer_explanation(details: Union[List[Dict[str, Any]], Dict[str, Any]]) -> str:
    """Extract the answer explanation from question details"""
    if isinstance(details, list) and details:
        det_0 = details[0]
        if "rationale" in det_0:
            return det_0["rationale"]
        elif "answer" in det_0 and "rationale" in det_0["answer"]:
            return det_0["answer"]["rationale"]
    elif isinstance(details, dict):
        if "rationale" in details:
            return details["rationale"]
        elif "explanation" in details:
            return details["explanation"]

    return "No explanation available."


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
            html_content += "</ul>"

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


def render_answer_key_question(
    question_id: str, question_num: int, questions_dict: Dict[Any, Any]
) -> str:
    """Render a single question with answer and explanation"""
    question_data = questions_dict.get(question_id, {})
    details: Union[List[Dict[str, Any]], Dict[str, Any]] = question_data.get(
        "details", {}
    )

    html_content = f'<div class="question"><div class="question-header">Question {question_num}</div>'

    # Render the question content
    if isinstance(details, list):
        html_content += render_list_type_question(details)
    else:
        html_content += render_dict_type_question(details)

    # Add correct answer
    correct_answer = get_correct_answer(details)
    html_content += f'<div class="answer-key"><strong>Correct Answer: {correct_answer}</strong></div>'

    # Add explanation
    explanation = get_answer_explanation(details)
    html_content += (
        f'<div class="rationale"><strong>Explanation:</strong> {explanation}</div>'
    )

    html_content += "</div>\n"
    return html_content


def generate_section_html(
    section: str, module: int, questions_dict: Dict[Any, Any], question_ids: List[str]
) -> str:
    """Generate HTML content for a single section using provided question IDs"""
    html_content = f"<h2>{section.capitalize()} Module {module}</h2>\n"

    for i, question_id in enumerate(question_ids):
        print(
            f"{section.capitalize()} section module {module} question {i + 1}: {question_id}"
        )
        html_content += render_question(question_id, i + 1, questions_dict)

    return html_content


def generate_answer_key_section_html(
    section: str, module: int, questions_dict: Dict[Any, Any], question_ids: List[str]
) -> str:
    """Generate answer key HTML content for a single section using provided question IDs"""
    html_content = f"<h2>{section.capitalize()} Module {module} - Answer Key</h2>\n"

    for i, question_id in enumerate(question_ids):
        print(
            f"Answer key: {section.capitalize()} section module {module} question {i + 1}: {question_id}"
        )
        html_content += render_answer_key_question(question_id, i + 1, questions_dict)

    return html_content


def generate_questions_and_keys(
    questions_dict: Dict[Any, Any],
) -> Dict[str, Dict[int, List[str]]]:
    """Generate and cache question IDs for each section and module"""
    cached_questions: Dict[str, Dict[int, List[str]]] = {}

    for section in ["reading", "math"]:
        cached_questions[section] = {}
        for module in [1, 2]:
            question_ids = make_module(section, module)
            cached_questions[section][module] = question_ids

    return cached_questions


def generate_html_content(
    questions_dict: Dict[Any, Any],
    cached_questions: Dict[str, Dict[int, List[str]]],
) -> str:
    """Generate complete HTML content for questions only"""
    template = load_template()

    content = ""
    for section in ["reading", "math"]:
        for module in [1, 2]:
            question_ids = cached_questions[section][module]
            content += generate_section_html(
                section, module, questions_dict, question_ids
            )

    html_content = template.substitute(
        document_title="SAT Questions",
        content=content,
    )

    return html_content


def generate_answer_key_html_content(
    questions_dict: Dict[Any, Any],
    cached_questions: Dict[str, Dict[int, List[str]]],
) -> str:
    """Generate complete HTML content for answer key with explanations using cached question IDs"""
    template = load_template()

    content = ""
    for section in ["reading", "math"]:
        for module in [1, 2]:
            question_ids = cached_questions[section][module]
            content += generate_answer_key_section_html(
                section, module, questions_dict, question_ids
            )

    html_content = template.substitute(
        document_title="SAT Questions - Answer Key & Explanations",
        content=content,
    )

    return html_content


def write_html_file(html_content: str, filename: str = "questions.html") -> None:
    """Write HTML content to file"""
    with open(filename, "w", encoding="utf-8") as html_file:
        html_file.write(html_content)


def main(
    paper_size: str = "us-letter",
    output: str = "questions",
    answers_only: bool = False,
    no_answers: bool = False,
    questions: Optional[Dict[str, Dict[int, List[str]]]] = None,
) -> None:
    """Main function to generate HTML file"""

    # Generate filenames
    questions_html_filename = f"{output}.html"
    answers_html_filename = f"{output}_answers.html"

    # Load questions data
    questions_dict: Dict[Any, Any] = load_questions_data()

    # Generate and cache question IDs
    if questions is None:
        cached_questions = generate_questions_and_keys(questions_dict)
    else:
        cached_questions = questions

    if not answers_only:
        # Generate questions HTML
        print(
            f"Generating questions: {questions_html_filename}"
        )

        questions_html_content = generate_html_content(
            questions_dict, cached_questions
        )
        write_html_file(questions_html_content, questions_html_filename)

        print("Questions HTML generated successfully!")

    if not no_answers:
        # Generate answer key HTML using the same question IDs
        print(f"Generating answer key: {answers_html_filename}")

        answers_html_content = generate_answer_key_html_content(
            questions_dict, cached_questions
        )
        write_html_file(answers_html_content, answers_html_filename)

        print("Answer key HTML generated successfully!")

    print("All files generated successfully!")


def cli_main() -> None:
    """CLI entry point that parses arguments and calls main()"""
    parser = argparse.ArgumentParser(description="Generate SAT Questions HTML")
    parser.add_argument(
        "--output",
        type=str,
        default="questions",
        help="Output filename prefix (default: questions)",
    )
    parser.add_argument(
        "--answers-only", action="store_true", help="Generate only the answer key HTML"
    )
    parser.add_argument(
        "--no-answers",
        action="store_true",
        help="Generate only the questions HTML (no answer key)",
    )

    args = parser.parse_args()

    # Call main with parsed arguments
    main(
        paper_size=args.paper_size,
        output=args.output,
        answers_only=args.answers_only,
        no_answers=args.no_answers,
    )


if __name__ == "__main__":
    cli_main()
