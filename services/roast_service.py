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
Nume: {username}
Gaming azi: {hours:.1f} ore
Cel mai jucat joc: {top_game}

Scrie UN SINGUR roast scurt în LIMBA ROMÂNĂ,
maximum 2 propoziții.

Vreau să sune ca o replică foarte nesimțită între prieteni
pe Discord, nu ca o glumă corporatistă sau generată de AI.

STIL:
- foarte răutăcios
- obraznic
- sarcastic
- absurd
- limbaj natural românesc
- poți folosi înjurături moderate
- vorbește direct cu persoana
- roast-ul trebuie să aibă legătură cu numărul de ore jucate
  și/sau jocul jucat

TEME PE CARE LE POȚI FOLOSI:
- "fă ceva cu viața ta"
- "alcoolicule"
- "du-te la dezalcoolizare"
- șomer / agenția de șomaj
- maică-sa îl dă afară din casă
- trăiește în beci
- n-a mai văzut soarele
- bere ieftină
- doarme până la prânz
- n-are ocupație
- alegeri proaste în viață
- familia se întreabă unde a greșit
- CV-ul lui are mai puține ore decât Steam

EXEMPLE DE ENERGIE, NU LE COPIA EXACT:
- "Fă ceva cu viața ta, alcoolicule."
- "Te-o dat mă-ta afară din casă și tu tot ai găsit Wi-Fi să bagi 8 ore de PUBG."
- "Du-te la dezalcoolizare lmao, că Steam-ul tău deja cere ajutor."
- "La câte ore ai băgat azi, mâine te sună direct agenția de șomaj să vadă dacă mai trăiești."
- "Fratele meu, soarele nu e DLC, poți să ieși și afară."

IMPORTANT:
- acestea sunt glume fictive între prieteni
- nu afirma ca fapt că persoana este alcoolică, dependentă,
  șomeră sau are alte probleme reale
- fără glume despre clase protejate
- fără amenințări
- fără explicații
- nu spune că ești AI
- răspunde DOAR cu roast-ul
"""

    response = client.responses.create(
        model="gpt-5.6",
        input=prompt,
    )

    return response.output_text.strip()


def generate_everyone_roast(
    *,
    username: str,
    message_content: str,
) -> str:
    prompt = f"""
Utilizator Discord: {username}

Mesajul trimis:
{message_content}

Persoana tocmai a folosit @everyone într-un canal Discord.

Scrie UN SINGUR roast scurt în LIMBA ROMÂNĂ,
maximum 2 propoziții.

Fă mișto în primul rând de faptul că omul a considerat
mesajul suficient de important încât să deranjeze TOT serverul
cu @everyone.

Dacă mesajul lui îți oferă material pentru roast,
folosește și conținutul mesajului.

STIL:
- foarte răutăcios
- obraznic
- sarcastic
- absurd
- friend-group banter
- limbaj natural românesc
- poți folosi înjurături moderate
- vorbește direct cu persoana

TEME PE CARE LE POȚI FOLOSI:
- n-are ocupație
- prea mult timp liber
- șomaj
- alcool
- stat în beci
- n-a văzut soarele
- maică-sa se întreabă unde a greșit
- comportament de administrator de bloc
- ANAF
- convocarea serverului pentru ceva complet inutil

EXEMPLE DE ENERGIE, NU LE COPIA EXACT:
- "Ai dat @everyone pentru asta? Fă ceva cu viața ta."
- "Fratele meu a convocat tot serverul de parcă îl caută ANAF-ul."
- "Șomajul chiar îți lasă prea mult timp liber dacă dai @everyone pentru asta."
- "Ai deranjat tot serverul doar ca să confirmi că n-ai ocupație."
- "Ăsta a dat @everyone de parcă urma să anunțe demisia președintelui."

IMPORTANT:
- glumele sunt fictive între prieteni
- nu afirma ca fapt că persoana este alcoolică,
  dependentă sau șomeră
- fără glume despre clase protejate
- fără amenințări
- fără explicații
- nu spune că ești AI
- răspunde DOAR cu roast-ul
"""

    response = client.responses.create(
        model="gpt-5.6",
        input=prompt,
    )

    return response.output_text.strip()

def generate_group_session_roast(
    *,
    sessions: list[dict],
) -> str:
    session_lines = "\n".join(
        (
            f"- {session['username']}: "
            f"{session['game_name']} "
            f"({session['duration_seconds'] / 3600:.1f}h)"
        )
        for session in sessions
    )

    prompt = f"""
Următorii oameni tocmai și-au terminat sesiunile de gaming:

{session_lines}

Scrie UN SINGUR roast scurt în română,
maximum 2-3 propoziții, adresat grupului.

Stil:
- foarte răutăcios, sarcastic și absurd
- friend-group banter
- fă mișto de timpul pierdut împreună
- poți sugera că puteau face ceva util cu timpul lor
- glume despre șomaj, lipsă de ocupație, stat în beci,
  bautura, alcolemie, lipsă de soare etc.
- dacă au jucat multe ore, folosește asta
- dacă au jucat același joc, fă mișto și de asta
- vorbește despre ei ca despre o gașcă de idioți

Energie aproximativă:
- "Ia uite-i pe idioții ăștia..."
- "În timpul ăsta puteați face literalmente orice util..."
- "Ați transformat șomajul într-un sport de echipă."

IMPORTANT:
- toate sunt glume fictive între prieteni
- nu afirma drept fapt probleme reale cu alcoolul,
  dependența sau șomajul
- fără clase protejate
- fără amenințări
- răspunde DOAR cu roast-ul
"""

    response = client.responses.create(
        model="gpt-5.6",
        input=prompt,
    )

    return response.output_text.strip()