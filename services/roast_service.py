from openai import OpenAI

client = OpenAI()


def generate_roast(
    *,
    username: str,
    total_seconds: float,
    top_game: str,
) -> str:
    hours = total_seconds / 3600

    prompt = f"""
Username: {username}
Gaming today: {hours:.1f} hours
Most played game: {top_game}

Write ONE short Discord roast, maximum 2 sentences.

Style:
- funny, savage, absurd friend-group banter
- jokes can reference being jobless, living in a basement,
  avoiding sunlight, drinking beer, questionable life choices,
  unemployment-office energy, etc.
- these are fictional jokes only; do not claim the person
  actually has alcoholism, addiction, or is actually unemployed
- no slurs
- no protected-class jokes
- don't explain the joke
- don't mention AI
"""

    response = client.responses.create(
        model="gpt-5.6",
        input=prompt,
    )

    return response.output_text.strip()