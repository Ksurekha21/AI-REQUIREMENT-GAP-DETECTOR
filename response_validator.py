import json
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ValidationError as PydanticValidationError


class AmbiguityItem(BaseModel):
    """Represents a single detected ambiguity."""
    issue: str
    explanation: str
    suggested_clarification: str


class RequirementAnalysis(BaseModel):
    """
    Pydantic model validating the full 9-category AI response structure.
    All list fields default to empty to handle graceful partial responses.
    """
    high_priority_gaps: List[str] = Field(default_factory=list)
    medium_priority_gaps: List[str] = Field(default_factory=list)
    low_priority_gaps: List[str] = Field(default_factory=list)
    missing_details: List[str] = Field(default_factory=list)
    ambiguity_detection: List[AmbiguityItem] = Field(default_factory=list)
    edge_cases: List[str] = Field(default_factory=list)
    clarification_questions: List[str] = Field(default_factory=list)
    improved_requirement: str = ""
    recommendations: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "high_priority_gaps": self.high_priority_gaps,
            "medium_priority_gaps": self.medium_priority_gaps,
            "low_priority_gaps": self.low_priority_gaps,
            "missing_details": self.missing_details,
            "ambiguity_detection": [a.model_dump() for a in self.ambiguity_detection],
            "edge_cases": self.edge_cases,
            "clarification_questions": self.clarification_questions,
            "improved_requirement": self.improved_requirement,
            "recommendations": self.recommendations,
        }


class ResponseValidationError(Exception):
    """Raised when the AI response cannot be parsed or validated."""
    pass


def _extract_json(raw_text: str) -> str:
    """Strip markdown code fences if accidentally included by the model."""
    cleaned = raw_text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if match:
        return match.group(1).strip()
    return cleaned


def validate_ai_response(raw_text: str) -> RequirementAnalysis:
    """
    Validates and parses the raw AI text into a RequirementAnalysis object.

    Raises:
        ResponseValidationError: If parsing or schema validation fails.
    """
    if not raw_text or not raw_text.strip():
        raise ResponseValidationError("The AI returned an empty response.")

    json_str = _extract_json(raw_text)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ResponseValidationError("AI response could not be parsed as valid JSON.") from e

    if not isinstance(data, dict):
        raise ResponseValidationError("AI response is not a valid JSON object.")

    # Sanitize all simple string list fields
    string_list_fields = [
        "high_priority_gaps", "medium_priority_gaps", "low_priority_gaps",
        "missing_details", "edge_cases", "clarification_questions", "recommendations"
    ]
    for field in string_list_fields:
        raw_val = data.get(field)
        if not isinstance(raw_val, list):
            data[field] = []
        else:
            data[field] = [str(item).strip() for item in raw_val if str(item).strip()]

    # Sanitize improved_requirement
    data["improved_requirement"] = str(data.get("improved_requirement", "")).strip()

    # Parse ambiguity_detection flat strings into structured dicts
    cleaned_ambiguities = []
    for item in data.get("ambiguity_detection", []) or []:
        item_str = str(item).strip()
        if not item_str:
            continue
        # Try to parse structured string: [Issue: ...] [Explanation: ...] [Clarification: ...]
        issue_match = re.search(r"\[Issue:\s*(.*?)\]", item_str, re.IGNORECASE)
        explanation_match = re.search(r"\[Explanation:\s*(.*?)\]", item_str, re.IGNORECASE)
        clarification_match = re.search(r"\[Clarification:\s*(.*?)\]", item_str, re.IGNORECASE)
        if issue_match and explanation_match and clarification_match:
            cleaned_ambiguities.append({
                "issue": issue_match.group(1).strip(),
                "explanation": explanation_match.group(1).strip(),
                "suggested_clarification": clarification_match.group(1).strip(),
            })
        elif isinstance(item, dict) and all(k in item for k in ("issue", "explanation", "suggested_clarification")):
            # Fallback: model returned an object despite schema change
            cleaned_ambiguities.append({
                "issue": str(item["issue"]).strip(),
                "explanation": str(item["explanation"]).strip(),
                "suggested_clarification": str(item["suggested_clarification"]).strip(),
            })
        else:
            # Fallback: treat the whole string as the issue
            cleaned_ambiguities.append({
                "issue": item_str,
                "explanation": "",
                "suggested_clarification": "",
            })
    data["ambiguity_detection"] = cleaned_ambiguities

    try:
        return RequirementAnalysis(**data)
    except PydanticValidationError as e:
        raise ResponseValidationError("Data validation error in AI response.") from e
