#!/usr/bin/env python3
import requests
from typing import Final, List, Dict, Any, Optional, Tuple, Union
import tqdm
import concurrent.futures
import json
import csv
import argparse

# Strong type definitions
HeadersType = Dict[str, str]
QuestionDataType = Dict[str, Any]
QuestionsDict = Dict[str, Dict[str, Any]]
ExternalIdTaskResult = Tuple[str, Dict[str, Any]]
IBNTaskResult = Optional[requests.Response]

headers: Final[HeadersType] = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:138.0) Gecko/20100101 Firefox/138.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Content-Type": "application/json",
    "Origin": "https://satsuitequestionbank.collegeboard.org",
    "Connection": "keep-alive",
    "Referer": "https://satsuitequestionbank.collegeboard.org/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}

# Create a global session object
session: requests.Session = requests.Session()
session.headers.update(headers)


def get_question_details(external_id: str) -> ExternalIdTaskResult:
    """Get detailed information for a single question"""
    response: requests.Response = session.post(
        "https://qbank-api.collegeboard.org/msreportingquestionbank-prod/questionbank/digital/get-question",
        json={"external_id": external_id},
    )
    return external_id, response.json()


def get_question_details_ibn(ibn: str) -> IBNTaskResult:
    """Get detailed information for ibn type questions"""
    if ibn:
        response: requests.Response = session.get(
            f"https://saic.collegeboard.org/disclosed/{ibn}.json"
        )
        return response
    return None


def process_data(data: List[QuestionDataType], debug: bool = False) -> QuestionsDict:
    """Process data in parallel"""
    # If in debug mode, only process the first 100 questions
    if debug:
        data = data[:100]
        print(f"Debug mode: Processing only {len(data)} questions")

    # Collect two types of tasks separately
    external_id_tasks: List[str] = []
    ibn_tasks: List[str] = []

    for item in data:
        ibn: Optional[str] = item.get("ibn")
        external_id: Optional[str] = item.get("external_id")

        if (ibn is None or ibn == "") and external_id:
            external_id_tasks.append(external_id)
        elif ibn and ibn != "":
            ibn_tasks.append(ibn)

    details_dict: Dict[str, Dict[str, Any]] = {}
    questions_dict: QuestionsDict = {}

    # Use thread pool to fetch details in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures: Dict[concurrent.futures.Future[Any], Tuple[str, str]] = {}

        # Submit external_id tasks
        for external_id in external_id_tasks:
            future: concurrent.futures.Future[ExternalIdTaskResult] = executor.submit(get_question_details, external_id)
            futures[future] = ("external_id", external_id)

        # Submit ibn tasks
        for ibn in ibn_tasks:
            future_ibn: concurrent.futures.Future[IBNTaskResult] = executor.submit(get_question_details_ibn, ibn)
            futures[future_ibn] = ("ibn", ibn)

        # Show progress bar
        for future in tqdm.tqdm(
            concurrent.futures.as_completed(futures),
            total=len(futures),
            desc="Fetching details",
        ):
            try:
                task_type: str
                task_id: str
                task_type, task_id = futures[future]

                if task_type == "external_id":
                    result: ExternalIdTaskResult = future.result()
                    external_id_result: str
                    details: Dict[str, Any]
                    external_id_result, details = result
                    details_dict[external_id_result] = details
                elif task_type == "ibn":
                    response: Union[IBNTaskResult, Any] = future.result()
                    if response and response.status_code == 200:
                        details_dict[task_id] = response.json()
                    else:
                        print(f"Failed to fetch ibn details for {task_id}")

            except Exception as e:
                print(f"Error fetching details for {futures[future]}: {e}")

    # Process all questions - simple merge of raw JSON
    for item in data:
        external_id: Optional[str] = item.get("external_id")
        ibn: Optional[str] = item.get("ibn")
        question_id: Optional[str] = item.get("questionId")

        if not question_id:
            continue

        # Create complete question data
        full_question: Dict[str, Any] = {
            "basic_info": item,  # Raw basic information
            "details": None      # Detailed information
        }

        # Get corresponding details based on type
        if (ibn is None or len(ibn) == 0) and external_id:
            full_question["details"] = details_dict.get(external_id)
        elif ibn:
            full_question["details"] = details_dict.get(ibn)

        questions_dict[question_id] = full_question

    return questions_dict


def main(debug: bool = False) -> None:
    """Main function"""
    # Get reading section questions
    print("Fetching reading questions...")
    response: requests.Response = session.post(
        "https://qbank-api.collegeboard.org/msreportingquestionbank-prod/questionbank/digital/get-questions",
        json={
            "asmtEventId": 99,
            "test": 1,
            "domain": "INI,CAS,EOI,SEC",
        },
    )

    print(f"Reading API response status: {response.status_code}")
    data: List[QuestionDataType] = response.json()
    questions_dict: QuestionsDict = process_data(data, debug)

    print("Fetched reading questions, saving to CSV...")

    # Save reading section CSV
    filename_suffix: str = "_debug" if debug else ""
    with open(f"reading{filename_suffix}.csv", "w+", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Difficulty", "Domain", "Skill"])
        for question in questions_dict.values():
            basic_info = question["basic_info"]
            writer.writerow(
                [
                    basic_info.get("questionId"),
                    basic_info.get("difficulty"),
                    basic_info.get("primary_class_cd_desc"),
                    basic_info.get("skill_desc"),
                ]
            )

    # Get math section questions
    print("Fetching math questions...")
    response = session.post(
        "https://qbank-api.collegeboard.org/msreportingquestionbank-prod/questionbank/digital/get-questions",
        json={
            "asmtEventId": 99,
            "test": 2,
            "domain": "H,P,Q,S",
        },
    )

    print(f"Math API response status: {response.status_code}")
    data = response.json()
    math_questions: QuestionsDict = process_data(data, debug)

    # Merge both sections
    questions_dict.update(math_questions)

    print("Fetched math questions, saving to CSV...")

    # Save math section CSV
    with open(f"math{filename_suffix}.csv", "w+", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Difficulty", "Domain", "Skill"])
        for question in math_questions.values():
            basic_info = question["basic_info"]
            writer.writerow(
                [
                    basic_info.get("questionId"),
                    basic_info.get("difficulty"),
                    basic_info.get("primary_class_cd_desc"),
                    basic_info.get("skill_desc"),
                ]
            )

    # Save all questions to JSON
    print("Saving all questions to JSON...")
    with open(f"questions{filename_suffix}.json", "w+", encoding="utf-8") as f:
        json.dump(questions_dict, f, indent=4, ensure_ascii=False)

    print(f"Saved questions to questions{filename_suffix}.json")
    print(f"Total questions processed: {len(questions_dict)}")
    print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SAT Question Crawler")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug mode: only fetch 100 questions per section"
    )

    args = parser.parse_args()
    main(debug=args.debug)
