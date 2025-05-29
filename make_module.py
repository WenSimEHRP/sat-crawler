from collections import defaultdict
import pandas as pd
from typing import Dict, Any, List, Tuple

def load_csv_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load CSV data files"""
    reading: pd.DataFrame = pd.read_csv("reading.csv", encoding="utf-8")
    math: pd.DataFrame = pd.read_csv("math.csv", encoding="utf-8")
    return reading, math


def get_module_config(section: str, module: int) -> Dict[str, Any]:
    """Get module configuration"""
    configs: Dict[Tuple[str, int], Dict[str, Any]] = {
        ("reading", 1): {
            "total_questions": 27,
            "difficulty_ratios": {"E": 11, "M": 11, "H": 5},
            "max_skill_count": 3
        },
        ("reading", 2): {
            "total_questions": 27,
            "difficulty_ratios": {"E": 7, "M": 10, "H": 10},
            "max_skill_count": 3
        },
        ("math", 1): {
            "total_questions": 22,
            "difficulty_ratios": {"E": 9, "M": 9, "H": 4},
            "max_skill_count": 1
        },
        ("math", 2): {
            "total_questions": 22,
            "difficulty_ratios": {"E": 4, "M": 9, "H": 9},
            "max_skill_count": 1
        }
    }
    return configs[(section, module)]


def validate_inputs(section: str, module: int) -> None:
    """Validate input parameters"""
    if section not in ["math", "reading"]:
        raise ValueError("Please input either math or reading")
    if module not in [1, 2]:
        raise ValueError("Please input either 1 or 2")


def select_math_questions_by_skill(
    df: pd.DataFrame,
    difficulty_ratios: Dict[str, int],
    draw_counts: defaultdict[str, int]
) -> List[str]:
    """Select questions for each skill in math module"""
    q_list: List[str] = []
    unique_skills_count: int = len(df["Skill"].unique())

    while len(q_list) < unique_skills_count:
        temp: pd.DataFrame = df.sample(n=1)
        difficulty: str = temp.iloc[0, 1]
        skill: str = temp.iloc[0, 3]
        question_id: str = temp.iloc[0, 0]

        if (
            draw_counts[difficulty] <= difficulty_ratios[difficulty]
            and draw_counts[skill] < 1
        ):
            draw_counts[difficulty] += 1
            draw_counts[skill] += 1
            q_list.append(question_id)

    return q_list


def select_additional_math_questions(
    df: pd.DataFrame,
    difficulty_ratios: Dict[str, int],
    draw_counts: defaultdict[str, int],
    current_count: int,
    target_count: int
) -> List[str]:
    """Select additional math questions to reach target count"""
    q_list: List[str] = []

    while current_count + len(q_list) < target_count:
        temp: pd.DataFrame = df.sample(n=1)
        difficulty: str = temp.iloc[0, 1]
        skill: str = temp.iloc[0, 3]
        question_id: str = temp.iloc[0, 0]

        if draw_counts[difficulty] <= difficulty_ratios[difficulty]:
            draw_counts[difficulty] += 1
            draw_counts[skill] += 1
            q_list.append(question_id)

    return q_list


def select_reading_questions(
    df: pd.DataFrame,
    difficulty_ratios: Dict[str, int],
    target_count: int,
    max_skill_count: int
) -> List[str]:
    """Select reading questions"""
    draw_counts: defaultdict[str, int] = defaultdict(int)
    q_list: List[str] = []

    while len(q_list) < target_count:
        temp: pd.DataFrame = df.sample(n=1)
        difficulty: str = temp.iloc[0, 1]
        skill: str = temp.iloc[0, 3]
        question_id: str = temp.iloc[0, 0]

        if (
            draw_counts[difficulty] <= difficulty_ratios[difficulty]
            and draw_counts[skill] < max_skill_count
        ):
            draw_counts[difficulty] += 1
            draw_counts[skill] += 1
            q_list.append(question_id)

    return q_list


def select_math_questions(df: pd.DataFrame, config: Dict[str, Any]) -> List[str]:
    """Select math questions"""
    difficulty_ratios: Dict[str, int] = config["difficulty_ratios"]
    target_count: int = config["total_questions"]
    draw_counts: defaultdict[str, int] = defaultdict(int)

    # First select one question for each skill
    q_list: List[str] = select_math_questions_by_skill(df, difficulty_ratios, draw_counts)

    # Select remaining questions
    additional_questions: List[str] = select_additional_math_questions(
        df, difficulty_ratios, draw_counts, len(q_list), target_count
    )

    q_list.extend(additional_questions)
    return q_list


def make_module(section: str, module: int) -> List[str]:
    """Generate module question list"""
    # Validate input
    validate_inputs(section, module)

    # Load data
    reading_df, math_df = load_csv_data()

    # Get configuration
    config: Dict[str, Any] = get_module_config(section, module)

    # Select appropriate questions based on section
    if section == "math":
        return select_math_questions(math_df, config)
    else:  # reading
        return select_reading_questions(
            reading_df,
            config["difficulty_ratios"],
            config["total_questions"],
            config["max_skill_count"]
        )
