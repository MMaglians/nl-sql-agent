import json
import re
from pathlib import Path

from nl_sql_agent.agent import PROMPT_V0, PROMPT_V1, PROMPTS, SYSTEM_PROMPT
from test_agent import FakeLLM, run, text_response

QUESTIONS = Path(__file__).resolve().parents[1] / "eval" / "questions.json"


def test_default_prompt_is_v1_and_v0_is_kept():
    assert SYSTEM_PROMPT == PROMPT_V1 and PROMPTS == {"v0": PROMPT_V0, "v1": PROMPT_V1}


def test_chosen_prompt_reaches_the_model(db_path):
    llm = FakeLLM(responses=[text_response("ciao")])
    run(db_path, llm, lambda sql: True, system_prompt=PROMPT_V1)
    assert llm.models.last_config.system_instruction == PROMPT_V1


def test_v1_does_not_leak_the_impossible_questions():
    """Il prompt non deve nominare i dati delle domande impossibili del test set."""
    items = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    leaked = {"chiama", "reddito", "etnia", "assicurazione", "indirizzo"}
    words = lambda text: set(re.findall(r"\w+", text.lower()))     # parole intere
    impossible = words(" ".join(i["question"] for i in items if i["gold_sql"] is None))
    assert leaked <= impossible                 # le parole vengono davvero dal test set
    assert not leaked & words(PROMPT_V1)        # e non compaiono nel prompt