"""
Post-call extraction: takes a full meeting transcript and uses GPT-4o to
return structured action items, summary, and participant info for the connectors.
"""

import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


async def extract_actions(transcript: list[dict]) -> dict:
    """
    Given a list of transcript segments (each with 'speaker' and 'transcript'),
    returns a dict with summary, action_items, participants, recipient_email, recipient_name.
    """
    if not transcript:
        return {}

    full_text = "\n".join(
        f"{seg.get('speaker', 'Unknown')}: {seg.get('transcript', '')}"
        for seg in transcript
    )

    participants = list({seg.get("speaker", "Unknown") for seg in transcript if seg.get("speaker")})

    prompt = f"""You are an AI assistant that analyzes meeting transcripts.

Given the transcript below, extract:
1. A 2-3 sentence summary of the meeting
2. A list of action items (things someone agreed to do)
3. The most appropriate recipient for a follow-up email (pick the main organizer or decision-maker)
4. If a company, client, project, or deal is mentioned, extract it as deal_name (otherwise use null)
5. The deal stage if determinable: one of "appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "decisionmakerboughtin", "contractsent", "closedwon", "closedlost" — or null if not a sales meeting

Return ONLY valid JSON in this exact format:
{{
  "summary": "string",
  "action_items": [
    {{"title": "string", "owner": "string", "due": "string or empty"}}
  ],
  "recipient_name": "string",
  "recipient_email": "",
  "deal_name": "string or null",
  "deal_stage": "string or null"
}}

Transcript:
{full_text}"""

    try:
        response = _get_client().chat.completions.create(
            model="gpt-4o",
            max_tokens=800,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You extract structured data from meeting transcripts. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
        )
        result = json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"[EXTRACTION] GPT-4o call failed: {e}")
        return {}

    result["participants"] = participants
    print(f"[EXTRACTION] Done — {len(result.get('action_items', []))} action items, summary: {result.get('summary', '')[:80]}...")
    return result
