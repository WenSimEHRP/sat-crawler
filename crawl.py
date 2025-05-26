#!/usr/bin/env python3
# import beautifulsoup4
import requests
from typing import Final, List, Dict, Any, Optional
from dataclasses import dataclass
import tqdm
# enum

headers: Final = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:138.0) Gecko/20100101 Firefox/138.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    # 'Accept-Encoding': 'gzip, deflate, br, zstd',
    "Content-Type": "application/json",
    "Origin": "https://satsuitequestionbank.collegeboard.org",
    "Connection": "keep-alive",
    "Referer": "https://satsuitequestionbank.collegeboard.org/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    # Requests doesn't support trailers
    # 'TE': 'trailers',
}


@dataclass
class Question:
    update_date: Optional[int]
    p_pcc: Optional[str]
    question_id: Optional[str]
    skill_cd: Optional[str]
    score_band_range_cd: Optional[int]
    u_id: Optional[str]
    skill_desc: Optional[str]
    create_date: Optional[int]
    program: Optional[str]
    primary_class_cd_desc: Optional[str]
    ibn: Optional[str]
    external_id: Optional[str]
    primary_class_cd: Optional[str]
    difficulty: Optional[str]
    rationale: Optional[str] = None
    stem: Optional[str] = None
    stimulus: Optional[str] = None
    answer_options: Optional[List[Dict[str, Any]]] = None
    correct_answer: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Question":
        c = cls(
            update_date=data.get("updateDate"),
            p_pcc=data.get("pPcc"),
            question_id=data.get("questionId"),
            skill_cd=data.get("skill_cd"),
            score_band_range_cd=data.get("score_band_range_cd"),
            u_id=data.get("uId"),
            skill_desc=data.get("skill_desc"),
            create_date=data.get("createDate"),
            program=data.get("program"),
            primary_class_cd_desc=data.get("primary_class_cd_desc"),
            ibn=data.get("ibn"),
            external_id=data.get("external_id"),
            primary_class_cd=data.get("primary_class_cd"),
            difficulty=data.get("difficulty"),
        )

        # complete the rest of the fields
        if "external_id" in data:
            response = requests.post(
                "https://qbank-api.collegeboard.org/msreportingquestionbank-prod/questionbank/digital/get-question",
                headers=headers,
                json={"external_id": data["external_id"]},
            )
            # print(response.status_code)
            # print(response.text)
            json_data = response.json()
            c.rationale = json_data.get("rationale")
            c.stem = json_data.get("stem")
            c.stimulus = json_data.get("stimulus")
            c.answer_options = json_data.get("answerOptions")
            c.correct_answer = json_data.get("correct_answer")

        return c


json_data: Dict[str, Any] = {
    "asmtEventId": 99,
    "test": 1,
    "domain": "INI,CAS,EOI,SEC",
}

response = requests.post(
    "https://qbank-api.collegeboard.org/msreportingquestionbank-prod/questionbank/digital/get-questions",
    headers=headers,
    json=json_data,
)

# print(response.status_code)
# convert response to dict
data: List[Dict[str, Any]] = response.json()
# create a new file named index.json
questions_list: List[Dict[Any, Any]] = []

for item in tqdm.tqdm(data, desc="Processing Questions"):
    question = Question.from_dict(item)
    questions_list.append(question.__dict__)

print("Fetched all questions, saving to files...")

with open("questions.cbor", "wb") as f:
    import cbor2

    cbor2.dump(questions_list, f)

print(
    "Saved questions to questions.cbor. CBOR format is more compact than JSON and is faster to read/write."
)

with open("questions.json", "w+") as f:
    import json

    json.dump(questions_list, f, indent=4)

print("Saved questions to questions.json")
print("Done!")
