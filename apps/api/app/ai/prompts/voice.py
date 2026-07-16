"""Shared voice-contract prompt fragments. See docs/LITHUANIAN_GENERATION_GUIDE.md
for the full rationale -- every prompt that generates creator-facing Lithuanian text
must include ``LT_VOICE_GUIDE``."""

from __future__ import annotations

LT_VOICE_GUIDE = """\
Rašyk taip, kaip kalbėtų jauna lietuvė technologijų kūrėja į kamerą -- ne kaip \
rinkodaros skyrius. Naudok teisingus lietuviškus diakritinius ženklus (ą č ę ė į š ų \
ū ž) visur. Rink natūralią lietuvišką sakinio tvarką, ne pažodinį vertimą iš anglų \
kalbos. Palik anglų kalbos technologijų terminus tokius, kokius jauni lietuviai \
technologijų kūrėjai iš tiesų vartoja (pvz. "AI", "startup", "prompt", "open \
source"), bet visa kita rašyk lietuviškai -- nemaišyk kalbų atsitiktinai. Venk \
korporatyvinės kalbos ("pasinerkite į", "atraskite naujus horizontus") ir \
nesistenk per daug skambėti jaunatviškai/slengiškai. Keisk sakinių ilgį -- derink \
trumpus, ryškius sakinius su ilgesniais paaiškinančiais."""

EN_VOICE_GUIDE = """\
Write in a natural, conversational voice for a young technology creator talking to \
camera -- not corporate marketing copy. Vary sentence length. Avoid stacking \
rhetorical questions. Keep technical terms creators actually use as-is."""


def voice_guide(output_language: str) -> str:
    return LT_VOICE_GUIDE if output_language == "lt" else EN_VOICE_GUIDE
