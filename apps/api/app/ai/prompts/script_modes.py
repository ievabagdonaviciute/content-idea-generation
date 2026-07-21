"""Per-script-mode Lithuanian structural guidance, threaded into the script
prompt so each mode produces a differently shaped script rather than one
generic template with a label slapped on. See
docs/LITHUANIAN_GENERATION_GUIDE.md "Format-specific guidance".
"""

from __future__ import annotations

SCRIPT_MODES = (
    "polished_explainer",
    "casual_talking_head",
    "grwm_story",
    "news_recap",
    "comment_response",
    "personal_story",
)

_GUIDANCE_LT: dict[str, str] = {
    "polished_explainer": (
        "Kabliukas -- klausimas arba netikėtas teiginys. Aiški vientisa mintis, "
        "po vieną idėją kiekviename etape, be sukrautų retorinių klausimų."
    ),
    "casual_talking_head": (
        "Laisvas, pokalbio tonas, tarsi kalbėtum draugui. Trumpi sakiniai, "
        "natūralios pauzės, be scenarinio griežtumo."
    ),
    "grwm_story": (
        "Esamasis laikas, pirmas asmuo, kasdienis veiksmas persipynęs su "
        "istorijos etapais. Retkarčiais natūralios šnekamosios dalelytės "
        '("na", "tai va"), bet ne per dažnai.'
    ),
    "news_recap": (
        "Pirmiausia -- kas nutiko, tada -- kodėl tai svarbu, pabaigoje -- viena "
        'nuomonės eilutė. Ne bendras "parašyk, ką manai" uždarymas.'
    ),
    "comment_response": (
        "Trumpai pacituok arba perfrazuok komentarą, tada atsakyk tiesiogiai ir "
        "konkrečiai."
    ),
    "personal_story": (
        "Pirmas asmuo, konkretu ir tikslu. Jei trūksta asmeninės detalės, kurios "
        "modelis negali žinoti, aiškiai pažymėk vietą rezervuota žyma, "
        "pvz. [ĮRAŠYK: kurso pavadinimas] -- niekada neišgalvok tokios detalės."
    ),
}

_GUIDANCE_EN: dict[str, str] = {
    "polished_explainer": (
        "Hook as a question or surprising claim. One clear throughline, one idea "
        "per beat, no stacked rhetorical questions."
    ),
    "casual_talking_head": (
        "Loose, conversational tone as if talking to a friend. Short sentences, "
        "natural pauses, no scripted stiffness."
    ),
    "grwm_story": (
        "Present tense, first person, routine actions interleaved with the story "
        "beats. Sparse use of casual spoken filler, not overused."
    ),
    "news_recap": (
        'Lead with what happened, then why it matters, end with one opinion line '
        '-- not a generic "let me know what you think" close.'
    ),
    "comment_response": "Briefly quote or paraphrase the comment, then answer directly.",
    "personal_story": (
        "First person, concrete and specific. If a personal detail is needed that "
        "the model cannot know, mark it explicitly with a placeholder, e.g. "
        "[FILL IN: course name] -- never invent one."
    ),
}


def script_mode_guidance(mode: str, output_language: str) -> str:
    guidance = _GUIDANCE_LT if output_language == "lt" else _GUIDANCE_EN
    return guidance.get(mode, guidance["polished_explainer"])
