"""
Prompt builder for the AI Study Plan Generator.
Constructs system and user prompts from test result data.
"""

from app.engine.irt import get_theta_descriptor


SYSTEM_PROMPT = """You are an expert academic tutor specializing in GRE preparation.
Your task is to generate a structured 3-step study plan based on the student performance data below.

Constraints:
- Be specific, actionable, and reference the exact topics and difficulty levels shown.
- Respond ONLY in valid JSON with this exact structure:
{
  "step_1": {"focus": "...", "action": "...", "resource_type": "..."},
  "step_2": {"focus": "...", "action": "...", "resource_type": "..."},
  "step_3": {"focus": "...", "action": "...", "resource_type": "..."}
}
- Each step should target the student's weakest areas first, then build toward strengths.
- Resource types should be one of: "Practice Set", "Flashcard Deck", "Timed Mock Test", "Video Tutorial", "Study Guide".
- Do NOT include any text outside the JSON object."""


def build_user_prompt(result: dict) -> str:
    """
    Build the dynamic user prompt from test result data.

    Args:
        result: TestResult document containing performance data.

    Returns:
        Formatted user prompt string.
    """
    final_theta = result.get("final_theta", 0.0)
    theta_descriptor = get_theta_descriptor(final_theta)
    accuracy_rate = result.get("accuracy_rate", 0.0)
    correct_count = result.get("correct_count", 0)
    total_questions = result.get("total_questions", 0)
    topics_missed = result.get("topics_missed", [])
    topics_attempted = result.get("topics_attempted", [])
    difficulty_trajectory = result.get("difficulty_trajectory", [])

    # Compute topics mastered (attempted but not missed)
    topics_correct = [t for t in topics_attempted if t not in topics_missed]

    # Compute max difficulty reached
    max_difficulty = max(difficulty_trajectory) if difficulty_trajectory else 0.5

    # Determine difficulty trend
    if len(difficulty_trajectory) >= 2:
        first_half = sum(difficulty_trajectory[:len(difficulty_trajectory)//2])
        second_half = sum(difficulty_trajectory[len(difficulty_trajectory)//2:])
        if second_half > first_half * 1.1:
            difficulty_trend = "Increasing (student improved over time)"
        elif second_half < first_half * 0.9:
            difficulty_trend = "Decreasing (student struggled with harder content)"
        else:
            difficulty_trend = "Stable (consistent performance)"
    else:
        difficulty_trend = "Insufficient data"

    prompt = f"""Student Performance Summary:
- Ability Level: {theta_descriptor} (theta: {final_theta:.2f})
- Accuracy: {accuracy_rate:.0%} ({correct_count}/{total_questions} questions)
- Topics with errors: {', '.join(topics_missed) if topics_missed else 'None'}
- Topics mastered: {', '.join(topics_correct) if topics_correct else 'None'}
- Difficulty reached: {max_difficulty:.1f}/1.0
- Trajectory: {difficulty_trend}

Generate a 3-step personalized study plan targeting the student's weakest areas."""

    return prompt
