# Fil: prompts/logbook_analysis_prompt.py

def build_logbook_analysis_prompt(story_content: str) -> str:
    """
    Bygger en prompt, der instruerer AI'en i at analysere en historie
    og returnere strukturerede, narrative "guldkorn" som JSON.
    """
    prompt = f"""
SYSTEM INSTRUKTION:
Du er en specialiseret AI-assistent med dyb ekspertise i narrativ terapi for børn. Din opgave er at læse den vedlagte børnehistorie og identificere centrale terapeutiske elementer. Du skal eksternalisere problemet, finde "glimt" (unique outcomes), navngive den anvendte styrke, og identificere de værdier, barnet forsvarede.
Dit output SKAL være en valid JSON-formateret streng, der følger den specificerede struktur NØJAGTIGT.

HISTORIE TIL ANALYSE:
---
{story_content}
---

DIN OPGAVE:
Analysér historien ovenfor og udfyld følgende JSON-struktur. Vær præcis, brug et positivt og styrkende sprog, og formuler indsigterne fra barnets perspektiv.

JSON-STRUKTUR (udfyld værdierne):
{{
  "problem_name": "...",
  "problem_influence": "...",
  "unique_outcome": "...",
  "discovered_method_name": "...",
  "discovered_method_steps": "...",
  "child_values": ["...", "..."],
  "support_system": ["...", "..."]
}}

VEJLEDNING TIL UDFYLDNING AF JSON-FELTER:
1.  "problem_name": Identificer den eksternaliserede version af problemet i historien (f.eks. "Vrede-vulkanen", "Bekymrings-monsteret"). Værdien skal være en kort, navne-lignende streng.
2.  "problem_influence": Beskriv kort, hvordan problemet påvirkede hovedpersonen. Hvad gjorde problemet? (f.eks. "Fik maven til at boble og hænderne til at knytte sig.").
3.  "unique_outcome": Beskriv det specifikke vendepunkt, hvor hovedpersonen gjorde noget, der succesfuldt modstod problemet. Formuler det som en aktiv handling fra hovedpersonens side. (f.eks. "Da [Hovedperson] valgte at trække vejret dybt i stedet for at råbe, og mærkede at Vrede-vulkanen blev mindre.").
4.  "discovered_method_name": Giv et fængende og positivt navn til den strategi eller "superkraft", der blev brugt i "unique_outcome". (f.eks. "Pause-knappen", "Spørge-om-hjælp-kraften", "Vejrtræknings-skjoldet").
5.  "discovered_method_steps": Baseret på "discovered_method_name", skriv en kort, letforståelig trin-for-trin guide (2-3 trin) til, hvordan metoden kan bruges. Brug et handlingsorienteret sprog. Eksempel: "1. Stop op og mærk efter i maven. 2. Træk vejret dybt tre gange som en drage. 3. Pust al den varme luft ud og fortæl, hvad du har brug for.". Værdien skal være en enkelt streng, hvor du bruger '\\n' for linjeskift.
6.  "child_values": Analysér temaet i historien og identificer 2-3 centrale værdier, som hovedpersonens handling forsvarede. Værdier kunne være "Mod", "Venskab", "Retfærdighed", "Ærlighed", "Omsorg". Returner som en liste af strenge.
7.  "support_system": Identificer de karakterer (personer, dyr, magiske væsener), der hjalp eller støttede hovedpersonen. Returner som en liste af navne/beskrivelser.

Returner KUN den færdige JSON-streng, intet andet.
"""
    return prompt