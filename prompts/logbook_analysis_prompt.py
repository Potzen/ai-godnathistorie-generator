# Fil: prompts/logbook_analysis_prompt.py

def build_logbook_analysis_prompt(story_content: str) -> str:
    """
    Bygger en prompt, der instruerer AI'en i at analysere en historie
    og returnere strukturerede, narrative "guldkorn" samt en pædagogisk analyse som JSON.
    """
    prompt = f"""
SYSTEM INSTRUKTION:
Du er en specialiseret AI-assistent med dyb ekspertise i narrativ terapi for børn. Din opgave er at læse den vedlagte børnehistorie og identificere centrale terapeutiske elementer.
Dit output SKAL være en valid JSON-formateret streng, der følger den specificerede struktur NØJAGTIGT.

HISTORIE TIL ANALYSE:
---
{story_content}
---

DIN OPGAVE:
Analysér historien ovenfor og udfyld følgende JSON-struktur. Vær præcis, brug et positivt og styrkende sprog.

JSON-STRUKTUR (udfyld værdierne):
{{
  "ai_summary": "...",
  "problem_name": "...",
  "problem_category": "Følelse",
  "problem_influence": "...",
  "unique_outcome": "...",
  "discovered_method_name": "...",
  "strength_type": "Mod",
  "discovered_method_steps": "...",
  "child_values": ["...", "..."],
  "support_system": ["...", "..."]
}}

VEJLEDNING TIL UDFYLDNING AF JSON-FELTER:
**KRITISK REGEL: Hvis du ikke kan finde information til et specifikt felt i historien, skal du returnere strengen "Ikke specificeret i historien" som feltets værdi.**

1.  "ai_summary": Skriv en kort pædagogisk analyse/opsummering (2-3 sætninger), der beskriver, hvordan historien adresserer udfordringen.
2.  "problem_name": Identificer den eksternaliserede version af problemet (f.eks. "Vrede-vulkanen").
3.  "problem_category": **VIGTIGT - Udfyld dette felt:** Kategoriser problemet med et enkelt eller få ord (f.eks. "Følelse", "Social Udfordring", "Vane", "Angst").
4.  "problem_influence": Beskriv kort, hvordan problemet påvirkede hovedpersonen.
5.  "unique_outcome": Beskriv det specifikke vendepunkt, hvor helten handlede anderledes og succesfuldt.
6.  "discovered_method_name": Giv et fængende navn til den strategi/superkraft, der blev brugt.
7.  "strength_type": **VIGTIGT - Udfyld dette felt:** Kategoriser den type styrke, der blev brugt (f.eks. "Kreativitet", "Empati", "Logik", "Mod", "Social styrke").
8.  "discovered_method_steps": Skriv en kort, letforståelig trin-for-trin guide til metoden (2-3 trin adskilt af '\\n').
9.  "child_values": Identificer 2-3 centrale værdier, som heltens handling forsvarede (f.eks. "Mod", "Venskab"). Returner som en liste af strenge.
10. "support_system": Identificer de karakterer, der hjalp eller støttede helten. Returner som en liste af navne/beskrivelser.

Returner KUN den færdige JSON-streng, intet andet.
"""
    return prompt