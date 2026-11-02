# Bluffstopp

Kortspelet Bluffstopp i terminalen: en människa mot en datorspelare. Skolprojekt i Programmering 2 (Python).

## Köra

```
python3 main.py
```

Inga externa beroenden, bara standardbiblioteket. Det finns inga tester.

## Filer

- `main.py` – frågar efter namn, skapar `Game` och `TerminalUI`, startar spelet.
- `card.py` – `Card` (färg + valör) och `card_ranks` (J=11, Q=12, K=13, A=14). `can_follow()` innehåller regeln för vilka kort som får läggas.
- `deck.py` – `Deck`. `make_deck()` och `shuffle_deck()` (egen Fisher–Yates) är statiska. `deal()` kastar fel om korten inte räcker, `draw()` tar så många som finns.
- `player.py` – `Player` med handen och hjälpmetoder.
- `ai_player.py` – `AIPlayer(Player)`.
  - **Minne:** kort han vet är spelade (`seen_cards`) och vad människan har sagt utan att han sa bluffstopp (`claimed_cards`). Har han fler än 10 kort i minnet totalt glömmer han 1–3 slumpade (`forget_some`), så att han går att lura.
  - **Drag (`choose_move`):** han listar alla möjliga drag (pass, ärliga kort och bluffar) och ger varje drag poäng (`score_move` / `score_pass`). Sedan väljer han det bästa, med lite slump. Poängen bygger på flera saker: att bli av med kort, att låga kort är svåra att bli av med senare, serier, hur svårt påståendet är att följa (`stop_value`) och risken att bli synad (`call_risk`). Undvik att lägga in specialfall med `if`. Ändra hellre poängen.
  - **Bluffar:** samma valör i en annan färg, eller samma färg 1–5 steg upp. På tomt bord kan han säga vilket högre kort som helst ("lägg lågt, säg högt"). Han får säga kort han själv har eller som redan spelats, för det är spelarens sak att komma ihåg. Att slänga ett högt kort, ett kort som passar eller ett kort i en serie som bluff kostar poäng (`waste_value`), så han bluffar nästan alltid med låga, ensamma kort.
  - **Väntetid:** `think_time` slumpas *innan* draget. Efter lång väntan (> 2,0 s) är han nervösare (`nerves`) och bluffar mer sällan, utom med 1–2 kort kvar.
  - **Bluffstopp (`wants_to_call_bluff`):** säkra regler först, sedan sannolikheter.
- `game.py` – `Game`: all spellogik och allt tillstånd. Ingen `print` eller `input` här.
- `terminal_ui.py` – `TerminalUI`: ritar bordet, läser in val och kör spelloopen (`run()`).

## Arkitektur

- **Logik och UI är separerade.** `Game` skriver aldrig ut något. Metoderna lämnar tillbaka svenska meddelandesträngar (eller tupler som `(var_bluff, text)`), och `TerminalUI` visar dem. Håll det så.
- Även väntetid hör till UI: `AIPlayer.think_time()` räknar bara ut sekunderna, och `time.sleep` görs i `TerminalUI.ai_move()`.
- Viktigt tillstånd i `Game`:
  - `claim` – kortet man *säger* att man lade (det som syns på bordet)
  - `last_card` – kortet som faktiskt ligger där
  - `last_player` – vem som lade det. `None` betyder att kortet kom från leken
  - `bluff_called` – man får säga bluffstopp högst en gång per tur
  - `current` – vems tur det är
- `claim is None` betyder att bordet är tomt (ny sekvens).

## Spelregler (så som de är implementerade)

- 52 kort, 6 var. Översta kortet i leken vänds upp och läggs på bordet. Det kortet ser alla, så man kan inte säga bluffstopp på det.
- Man får lägga ett kort av samma färg med högre valör, eller ett kort med samma valör i en annan färg (`Card.can_follow`).
- Kortet läggs med baksidan upp och man säger vilket kort det är. Man får bluffa, men det man säger måste vara ett tillåtet kort.
- **Pass:** man drar 1 kort om det finns några kvar, och motståndaren börjar en ny sekvens med valfritt kort. Man kan inte passa när bordet är tomt.
- **Bluffstopp:** man får bara säga det på motståndarens senaste kort.
  - Ärligt kort: den som sa bluffstopp får straff, och den som lade kortet börjar en ny sekvens.
  - Bluff: bluffaren får straff, och den som sa bluffstopp börjar en ny sekvens.
- **Straff:** dra 3 kort. Är leken slut tar man i stället 1 slumpat kort från motståndarens hand.
- **Vinst:** den som blir av med alla kort vinner omgången. Det kollas först *efter* att motståndaren har fått chansen att säga bluffstopp på det sista kortet. Vinnaren börjar nästa omgång. Första omgången slumpas vem som börjar.

## Inmatning i terminalen

- `1`–`n` = välj kort. Sedan Enter för att säga kortets riktiga namn, eller en kod för att bluffa: färgbokstav + valör, t.ex. `hk`, `s10`, `r2`.
  - Färgkoder: `s` = ♠ spader, `h` = ♥ hjärter, `k` = ♣ klöver, `r` = ♦ ruter.
- `b` (eller `s`) = bluffstopp, `p` = pass, `a` (eller `q`) = avsluta.

## Kodstil

Projektet är skrivet på en nivå som passar kursen. Följ samma stil:

- Kommentarer och all text som visas är på **svenska**. Namn på variabler, metoder och klasser är på engelska.
- Enkel och tydlig Python: vanliga `for`-loopar och `if`/`else`, inga list comprehensions, lambdas, dataclasses, type hints eller andra avancerade konstruktioner om användaren inte ber om det.
- Korta kommentarer som förklarar *varför*, i samma ton som den befintliga koden.
- Inga externa bibliotek.
- Färgerna på korten lagras som Unicode-symboler (`"♠"`, `"♥"`, `"♣"`, `"♦"`), och valören som `int` (2–10) eller `str` (`"J"`, `"Q"`, `"K"`, `"A"`). Jämför kort med `same_as()`, inte `==`.
