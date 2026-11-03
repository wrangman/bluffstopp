# Bluffstopp

Kortspelet Bluffstopp i terminalen: en människa mot en datorspelare. Skolprojekt i Programmering 2 (Python).

## Köra

```
pip install pygame-ce     # en gång, behövs bara för grafiken
python3 main.py           # grafik (eller terminalen om pygame-ce saknas)
python3 main.py terminal  # alltid terminalen
```

`USE_GRAPHICS` högst upp i `main.py` väljer vad som startar som standard. Terminalversionen använder bara standardbiblioteket. Det finns inga tester.

## Testa

- **Kör inga tester eller simuleringar (t.ex. skripten i `sim/`) innan användaren själv har provspelat.** Bottarna spelar inte som en människa och missar regelbrott och buggar som syns direkt när man spelar. De slösar bara användarens usage.
- Användaren provspelar själv med `python3 main.py`. Efter en ändring: berätta vad som ändrats och vad man ska titta efter, och vänta på hur det kändes.
- Säg aldrig att något fungerar för att en simulering gick bra.

## Filer

- `main.py` – väljer grafik eller terminal och startar spelet. Terminalen frågar efter namn med `TerminalUI.ask_name()`, grafiken i fönstret. Båda visar en lista med de 5 som spelat senast plus "Ny spelare". Finns ingen i `scores.json` frågar de bara efter namnet.
- `card.py` – `Card` (färg + valör) och `card_ranks` (J=11, Q=12, K=13, A=14). `can_follow()` innehåller regeln för vilka kort som får läggas. `Card.from_code("hk")` tolkar koderna man skriver (används av båda gränssnitten).
- `deck.py` – `Deck`. `make_deck()` och `shuffle_deck()` (egen Fisher–Yates) är statiska. `deal()` kastar fel om korten inte räcker, `draw()` tar så många som finns.
- `player.py` – `Player` med handen och hjälpmetoder.
- `ai_player.py` – `AIPlayer(Player)`.
  - **Minne:** kort han vet är spelade (`seen_cards`) och vad människan har sagt utan att han sa bluffstopp (`claimed_cards`). Har han fler än 10 kort i minnet totalt glömmer han 1–3 av de äldsta (`forget_some`), slumpat från båda listorna. Det sista kortet i en lista glöms aldrig. Han kommer också ihåg vilka kort människan har passat på (`passed_on`). Högre kort i den färgen räknas då som halvt så troliga i `stop_value`, så han säger gärna den färgen igen. Det glöms när människan får straffkort.
  - **Drag (`choose_move`):** han listar alla möjliga drag (pass, ärliga kort och bluffar) och ger varje drag poäng (`score_move` / `score_pass`). Sedan väljer han det bästa, med lite slump. Poängen bygger på flera saker: att bli av med kort, att låga kort är svåra att bli av med senare, serier, hur svårt påståendet är att följa (`stop_value`) och risken att bli synad (`call_risk`). Undvik att lägga in specialfall med `if`. Ändra hellre poängen.
  - **Bluffar:** samma valör i en annan färg, eller samma färg 1–5 steg upp. På tomt bord kan han säga vilket högre kort som helst ("lägg lågt, säg högt"). Han får säga kort han själv har eller som redan spelats, för det är spelarens sak att komma ihåg. I risken räknar han med chansen att motståndaren *vet* att det är bluff (`opponent_knows`): 0 för hans egna kort, 0,2 för spelade kort och annars chansen att kortet ligger på motståndarens hand. Därför säger han gärna sina egna höga kort. Att slänga ett högt kort, ett kort som passar eller ett kort i en serie som bluff kostar poäng (`waste_value`), så han bluffar nästan alltid med låga, ensamma kort.
  - **Väntetid:** `think_time` slumpas *innan* draget. Efter lång väntan (> 2,0 s) är han nervösare (`nerves`) och bluffar mer sällan, utom med 1–2 kort kvar.
  - **Bluffstopp (`wants_to_call_bluff`):** säkra regler först (han har kortet, kortet är spelat, människans sista kort), sedan sannolikheter. Har människan redan sagt samma kort vet han att en av gångerna var bluff, men inte vilken. Chansen blir då `chance / (chance + 0.3)`, så på tomt bord synar han sällan. Varje gång han synar ett ärligt kort halveras chansen (`wrong_calls`). Det nollställs när han har rätt eller en ny omgång börjar. De säkra reglerna gäller alltid.
- `game.py` – `Game`: all spellogik och allt tillstånd. Ingen `print` eller `input` här. `record_result()` ger vinnaren 1 poäng när omgången är slut och lämnar tillbaka en text om rekordet slogs. `score_text()` och `streak_text()` ger ställningen och vinstsviten som text.
- `scoreboard.py` – `Scoreboard`: människans vunna och förlorade omgångar mot datorn, per namn, plus vinster i rad (`streak`) och rekordet (`best_streak`) att slå. `last_played` (sekunder sedan 1970) sätts när en omgång räknas, och `recent_players()` ger namnen med den senaste först. Sparas i `scores.json` i spelmappen efter varje omgång. Datorns poäng är samma sak som människans förluster. Ingen `print` eller `input` här heller, så grafikversionen kan använda samma klass.
- `terminal_ui.py` – `TerminalUI`: ritar bordet, läser in val och kör spelloopen (`run()`). `SHOW_AI_MEMORY` och `SHOW_AI_HAND` högst upp visar datorns minne och hand ovanför bordet för felsökning. Sätt dem till `False` när spelet är klart.
- `graphic_ui.py` – `GraphicUI` (pygame-ce): fönster 1280×800 som går att skala. Turordningen i `next_step()` följer `TerminalUI.run()` exakt. Datorns väntan är en tidpunkt (`wait_until`), inte `time.sleep`, så fönstret fryser inte. Lägen i `self.state`: `name`, `human`, `ai_bluff_wait`, `ai_wait`, `reveal`, `round_over`.
  - **Animationer:** `sync_sprites()` jämför korten på skärmen med `Game` efter varje drag. Kort som bytt plats flyger dit, nya kort kommer från leken och kort som försvunnit sopas ut till vänster. `Game` behöver inte veta något om animationer.
  - **Handen:** solfjäder (`fan()`), sorterad efter färg och valör. Mellanrummet krymper med fler kort. Valt kort lyfts 40 px, kortet under musen 16 px.
  - **Bluffpanel:** när ett kort är valt visas det riktiga kortet först (grön ram = ärligt), sedan förslag (`suggested_claims`) och knappen "Alla…" med alla 52 kort (otillåtna gråa). Man kan också skriva en kod som i terminalen. Klick på samma kort igen eller Enter = ärligt.
  - **Startskärmen:** flera användare som i Windows, men i spelets egen design (`draw_player_list()`): en vit panel med en rad per spelare, en rund bricka med första bokstaven, mörk ram på vald rad och grå rad under musen. Vald "Ny spelare" blir samma namnruta som när ingen spelat. Pilarna eller klick väljer, klick på valt namn igen eller Enter spelar. Skriver man något hoppar man till "Ny spelare".
  - **Layout (Johans design):** ingen egen titelrad, fönstrets rad räcker. Leken till vänster om mittkortet. Mittkortet ligger alltid med baksidan upp och rakt (lite huller om buller men aldrig snett), med "?" i hörnet och "Datorn sa: …" under. Till höger: poängrutan ("Johan vs Datorn", "Visa" = topplistan från `scores.json`, "Starta om") och händelserna.
  - **Vems tur:** datorns hand blir större och tydlig på hans tur, mindre och genomskinlig på din (`AI_SCALE`, `ALPHA`). Din hand ändrar aldrig storlek eller genomskinlighet.
  - **Klicka på bordet:** mittkortet = syna (bara på datorns kort), leken = pass. Musen över dem gör kortet större, tonar ned det och visar "Syna kort" / "Pass – dra kort" ovanför. Kortet som synas blir större när det vänds.
  - **Händelser:** chevronen stänger listan så bara det senaste syns ("hard mode"). Öppen lista går att scrolla.
  - `SHOW_AI_HAND` högst upp, eller F1 under spelet, visar datorns kort.
- `card_sprite.py` – `CardSprite`: ett kort på skärmen. Glider mot sitt mål (`target_x` osv.) varje bild och vänds genom att tryckas ihop på bredden. Laddar bilderna en gång (`load_images()`).
- `assets/cards/` – kortbilderna (public domain, från github.com/hayeah/playing-cards-assets, se `LICENSE.txt`). Baksidan ritas med kod i `CardSprite.make_back()`.

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

## Inmatning i grafiken

- Klicka på ett kort för att välja det, och klicka igen (eller Enter) för att lägga det ärligt. Bluffa genom att klicka i panelen, under "Alla…" eller genom att skriva en kod + Enter. Esc ångrar.
- Tangenter när inget kort är valt: `1`–`9` väljer kort, `P` = pass, `B` = bluffstopp.
- Lägger datorn sitt sista kort kan man bara välja Bluffstopp! eller Godta.

## Inmatning i terminalen

- `1`–`n` = välj kort. Sedan Enter för att säga kortets riktiga namn, eller en kod för att bluffa: färgbokstav + valör, t.ex. `hk`, `s10`, `r2`.
  - Färgkoder: `s` = ♠ spader, `h` = ♥ hjärter, `k` = ♣ klöver, `r` = ♦ ruter.
- `b` (eller `s`) = bluffstopp, `p` = pass, `a` (eller `q`) = avsluta.

## Kodstil

Projektet är skrivet på en nivå som passar kursen. Följ samma stil:

- Kommentarer och all text som visas är på **svenska**. Namn på variabler, metoder och klasser är på engelska.
- Enkel och tydlig Python: vanliga `for`-loopar och `if`/`else`, inga list comprehensions, lambdas, dataclasses, type hints eller andra avancerade konstruktioner om användaren inte ber om det.
- Korta kommentarer som förklarar *varför*, i samma ton som den befintliga koden.
- Inga externa bibliotek, utom pygame-ce i grafikversionen (`graphic_ui.py`, `card_sprite.py`). Resten av spelet ska fungera utan det.
- Färgerna på korten lagras som Unicode-symboler (`"♠"`, `"♥"`, `"♣"`, `"♦"`), och valören som `int` (2–10) eller `str` (`"J"`, `"Q"`, `"K"`, `"A"`). Jämför kort med `same_as()`, inte `==`.

## Att provspela (datorspelaren)

Ställs in efter provspel. Siffrorna kommer från en simulering mot den gamla datorn (800 spel, slumpen är ungefär ±2 %).

- **Blockering när motståndaren närmar sig vinst:** i `score_move` är bonusen stoppvärdet × 2,5 / motståndarens kort. Den ersatte en `if` som bara gällde vid 1 kort. Effekten är knappt mätbar: vid 1–2 kort säger han dam, kung eller ess i ~40 % av dragen, både före och efter. Känns han för snäll mot en spelare som snart går ut kan vikten höjas, t.ex. till × 5.
- **Tvekan:** efter lång väntan passar han i ~74 % av fallen när inget kort passar (önskat var ~66 %), och annars i ~16 % (önskat ~20 %). Styrs av `nerves` och grundrisken i `call_risk`.
- **Lägg lågt, säg högt på tomt bord:** händer i ~3 % av dragen där. Det var 5–6 % innan `opponent_knows` lades till. Styrs av avdraget för tomt bord i `call_risk`.
- Varje ändring av vikterna påverkar de andra siffrorna, så ändra en sak i taget och provspela.
