import json
from rapidfuzz import process, fuzz

# ---------- Load Files ----------
def load_raw_skills():
    with open("data/user_skills.json", "r") as f:
        return json.load(f).get("raw_skills", [])


def load_master_skills():
    with open("data/skills_master.json", "r") as f:
        return json.load(f).get("skills", [])


# ---------- Alias Dictionary ----------
ALIASES = {
    "py": "Python",
    "python3": "Python",
    "python2": "Python",
    "reactjs": "React",
    "js": "JavaScript",
    "node": "Node.js",
    "ml": "Machine Learning",
    "ai": "Artificial Intelligence"
}


# ---------- Normalize Skills ----------
def normalize_skills(threshold=85):
    raw_skills = load_raw_skills()
    master_skills = load_master_skills()

    normalized = set()

    for skill in raw_skills:
        skill_lower = skill.lower()

        # 1️⃣ Alias check
        if skill_lower in ALIASES:
            normalized.add(ALIASES[skill_lower])
            continue

        # 2️⃣ Fuzzy match against master skills
        match, score, _ = process.extractOne(
            skill_lower,
            [s.lower() for s in master_skills],
            scorer=fuzz.partial_ratio
        )

        if score >= threshold:
            for s in master_skills:
                if s.lower() == match:
                    normalized.add(s)
                    break

    return sorted(list(normalized))


# ---------- Save Output ----------
def save_normalized_skills():
    normalized_skills = normalize_skills()

    output = {
        "normalized_skills": normalized_skills
    }

    with open("data/normalized_skills.json", "w") as f:
        json.dump(output, f, indent=4)

    return output


# ---------- Standalone Run ----------
if __name__ == "__main__":
    result = save_normalized_skills()
    print("Normalized skills saved:")
    print(result)
