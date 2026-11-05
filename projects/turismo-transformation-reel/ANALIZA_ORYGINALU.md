# Dogłębna analiza oryginału (VANTA, 0:00–0:18): budowa, montaż, technologia

Źródło: `source/ref_vanta_clean_512x850.mp4`. Wszystkie liczby pochodzą z pomiarów:
- klatki unikalne (mpdecimate),
- przepływ optyczny w strefach kadru (droga osobno, całość osobno),
- dopasowanie zoomu/obrotu,
- pasma audio (sub-bas 30–150 Hz, środek 300–2500 Hz, „powietrze” 5–11 kHz),
- spektrogram,
- palety k-means,
- kadry w natywnej rozdzielczości.

Klatki referencyjne: `analysis/deep_*.jpg`, spektrogram: `analysis/deep_spectrogram.png`.

## 1. Czym jest ten film

To **w pełni komputerowa (CGI) reklama typu „build / transformation”** firmy tuningowej, w pionie 9:16. Ma 18 s i 30 kl./s.

Konstrukcja:
- **Jeden ciągły lot kamery od 1,04 do 13,30 s.** Nie ma w nim ani jednego twardego cięcia. Świat zmienia się w środku ujęcia przez ukryte cięcie, czyli przelot „przez lakier”.
- **Cztery statyczne ujęcia produktu (packshoty).**
- **Pętla:** ostatnia klatka przechodzi w pierwszą.

W filmie nie ma żadnego tekstu, przenikań, błysków, glitchy ani efektów „z montażu”. Wszystko dzieje się w kamerze i w animacji 3D.

Główny produkt to **pakiet przemiany auta**: maska z wlotami, nowy lakier i aktywny spoiler. Felga z intro i outro wraca na aucie po przemianie.

## 2. Parametry techniczne (delivery)

| Parametr | Wartość |
|---|---|
| Format | 9:16, H.264 High, BT.709, AAC 48 kHz stereo |
| Klatkaż treści | **30 kl./s** (nagranie z telefonu ma 60–120 kl./s, ale obraz zmienia się co ok. 0,033 s) |
| Migawka / motion blur | Mocne rozmycie ruchu, odpowiadające migawce ok. 180–270°. W szybkich ujęciach tło rozmazuje się w smugi, w obróconych kadrach widać rozmycie obrotowe |
| Głębia ostrości | Płytka w zbliżeniach (maska, szyba, koła); tło miękkie |
| Obiektyw | Szeroki (ok. 14–20 mm FF) w lotach FPV, z lekką beczką; w packshotach normalny, ok. 35–50 mm, nisko przy ziemi |
| Ostrość ogólna | Miękka: Laplacian 2,5–3,5 w ruchu (u nas 6–8), bez wyostrzania |
| Ekspozycja | High-key: mediana luminancji 0,74 (świat 1), 0,84 (świat 2), szczyty ok. 0,98 |
| Napisy / logo | Brak |

## 3. Dramaturgia: 7 aktów

| Akt | Czas (s) | Klatki @30 | Funkcja |
|---|---|---|---|
| 0. Hook | 0,00–1,04 | 0–31 | Produkt w próżni: felga leży płasko, centrum osiada, koło się kręci |
| I. Przed | 1,04–3,00 | 31–90 | Żółte GT3 w czasie rzeczywistym: szybki lot FPV, obrót 90° → 0°, stara maska otwiera się i odlatuje |
| II. Metamorfoza | 3,00–6,80 | 90–204 | **Mocne zwolnione tempo.** Nowa maska wlatuje i ląduje |
| III. Przejście | 6,80–9,40 | 204–282 | Ramp-up do czasu rzeczywistego, najazd w lakier, kadr = sam lakier (0,5 s), wyjście w nowym świecie |
| IV. Po | 9,40–13,30 | 282–399 | Nowe auto (błękitne GT3 RS) w śniegu: przelot wzdłuż boku, spoiler się rozkłada, auto odjeżdża |
| V. Packshoty | 13,30–17,07 | 399–512 | 3 statyczne ujęcia produktu, cięcia na beat |
| VI. Pętla | 17,07–18,00 | 512–540 | Felga: ramiona opadają do obręczy, czyli wejście w klatkę 0 |

## 4. Rozpiska ujęć (beat po beacie)

| Czas (s) | Obraz | Kamera | Czas akcji | Efekt | Dźwięk |
|---|---|---|---|---|---|
| 0,00–0,20 | Felga leży płasko na czarnym lustrze; końcówki ramion jeszcze wystają nad obręcz | Nieruchoma, nisko (ok. 20° nad podłogą) | 1× | Ramiona osiadają (koniec animacji z 17 s) | 0–0,2 s cisza; intro bez basu |
| 0,20–1,04 | Koło się kręci, ramiona rozmyte ruchem | Nieruchoma | 1× | Rozmycie ruchu obrotowego | Intro: pad i lead 1,46 kHz, bez basu |
| **1,04** | **Cięcie dopasowane kształtem (match cut):** felga z czarnego tła → przednie koło żółtego auta w tym samym miejscu i rozmiarze | | | | **Drop basu dokładnie na cięciu** (sub-bas −6 → +30 dB) |
| 1,04–1,75 | Nad przednim lewym kołem, błotnik u dołu, niebo z palmami z lewej | FPV, obrót ok. 90°, szeroki obiektyw; przelot nad błotnikiem i reflektorem | 1×; droga 0–8 px/kl. | Rozmycie obrotowe | Groove + szum powietrza (whoosh) 1,6–2,1 |
| 1,75–2,25 | Przód auta z lewej, koło na dole | Obrót ok. 45°, szczyt prędkości (droga 7–9 px/kl.) | 1× | Smugi tła | |
| 2,20–2,60 | **Fabryczna maska otwiera się na zawiasie jak klapa** (widać brązowe wnętrze), odrywa się i odlatuje w górę i w lewo, z obrotem | Kamera omija narożnik auta, obrót → 0° | 1×, potem **ramp-down** | Animacja części z rozmyciem ruchu | Whoosh (pasmo 5–11 kHz) 2,7–3,0 |
| 2,60–3,00 | Nisko z przodu, auto bez maski (otwarty bagażnik) | Wyhamowanie do niemal bezruchu | **Ramp-down: droga 7,5 → 0,1 px/kl. (ok. 1/40)** | | |
| 3,05–3,40 | **Nowa maska wlatuje z góry, ustawiona PIONOWO jak tarcza.** Najpierw jest mała (daleko), potem rośnie | Prawie nieruchoma, centralna, nisko z przodu | **Slow-motion** (droga 0,1–0,3 px/kl.) | | |
| 3,40–6,30 | Maska unosi się nad przodem auta i powoli **obraca z pionu do poziomu**, łagodnie się kołysząc | Powolny najazd (0,02–0,1 %/kl.) | **Slow-motion** | | Groove trwa |
| 6,30–6,80 | **Maska ląduje** i osiada równo z nadwoziem | Kamera schodzi lekko w lewo (przód 3/4) | Slow-mo → zaczyna się ramp-up | | |
| 6,80–7,60 | Przód 3/4 z lewej: żółte auto z błękitną maską z wlotami (karbonowe żaluzje) | Najazd, przyspieszenie | **Ramp-up: droga 0,6 → 2,5 px/kl.** | Płytka głębia ostrości | |
| 7,60–8,30 | Kamera leci nisko wzdłuż maski w prawy wlot | Wykładnicze przyspieszenie, zoom do 4,3 %/kl., obrót ok. 10° | 1× (droga ok. 9 px/kl.) | Rozmycie ruchu i głębi | **Break: bas i lead całkowicie wycięte (7,6–8,3)** |
| 8,30–8,45 | Krawędź wlotu, potem już tylko lakier | Kamera „wchodzi w powierzchnię” | | | Uderzenia basu 8,4 / 8,8 |
| **8,45–8,95** | **Kadr = jednolity jasnobłękitny lakier z miękkim gradientem.** To kolor *nowego* auta | Stop (energia ruchu 0) | | **Ukryte cięcie przez powierzchnię (push-through / matched-material)**: tu podmienia się świat i auto | **Stutter:** lead szatkowany w rytm uderzeń (8,4–9,3) |
| 8,95–9,40 | Z lakieru wyłania się krawędź szyby bocznej (przyciemniane szkło z odbiciami drzew), uszczelka; obrót ok. 35° | Odjazd od powierzchni | Ramp-up | Odbicia w szkle | Whoosh 8,7–9,3 |
| **9,40** | | | | | **Pełny drop** (groove wraca) |
| 9,40–10,40 | Bok błękitnego GT3 RS w śniegu: szyba, lusterko, drzwi, białe koła | Wybuchowy odjazd w bok i do tyłu (zoom −4,3 %/kl., szczyt 9,6), obrót → 0° | 1× | Mocne smugi, płytka głębia | |
| 10,40–10,90 | Bok i tył 3/4: **spoiler na łabędzich szyjach wysuwa się i ustawia pod kątem** | Wyhamowanie, kamera nisko z boku | 1× | Animacja mechaniczna części | |
| 10,90–13,30 | Auto odjeżdża mokrą drogą: odbicia tylnych świateł w kałużach, pas śniegu, nagie drzewa, mgła | Kamera praktycznie stoi na drodze, lekki ruch | 1× | Mokra nawierzchnia, mgła, mgiełka spod kół | |
| **13,30** | **Twarde cięcie na beat** | | | | Uderzenie 13,36 |
| 13,30–15,30 | Auto zaparkowane, przód 3/4 nisko, koła skręcone; śnieg, drzewa, góry, mokre lustro drogi | Statyczna, mikro-najazd 0,07 %/kl. | | | |
| **15,30** | Cięcie na beat → nisko przy przednim kole i poszerzonym nadkolu | Statyczna, mikro-najazd | | | |
| **16,22** | Cięcie → tylne koło + spoiler (niebieskie płetwy) | Statyczna, lekki obrót | | | |
| **17,07** | Cięcie → felga na czarnym tle: **ramiona unoszą się nad obręczą („rozstrzelony” widok)** i opadają | Statyczna | | Animacja montażu felgi | **Muzyka ucięta twardo w 17,0**, zostaje tylko pogłos |

## 5. Czas: zwolnione tempo (time remapping)

Pomiar prędkości drogi w dolnych 28% kadru, przy kamerze jadącej z autem:

```
czas (s)    1,75  2,0  2,25  2,5  2,75  3,0 ... 6,0  6,5  7,0  7,5  7,75  8,25
droga px/kl 7,7   8,6  7,5   5,4  1,1   0,1 ... 0,4  0,6  0,9  1,6  2,5   9,4
            czas rzeczywisty   RAMP-DOWN    SLOW-MOTION        RAMP-UP → czas rzeczywisty
```

- Metamorfoza (3,0–6,6 s) to **slow-motion rzędu 1/20–1/40**: auto „jedzie”, ale droga prawie stoi, a maska unosi się bardzo wolno.
- Zejście do slow-mo trwa ok. 0,5 s (2,5–3,0). Powrót do czasu rzeczywistego trwa ok. 1,7 s (6,5–8,25) i płynnie łączy się z najazdem w maskę.
- To typowy „time dilation” z silnika 3D (cała scena zwalnia, łącznie z obrotem kół i chmurami), a nie spowolnienie gotowego materiału.

## 6. Kamera

- **Wirtualny dron FPV:** szerokie szkło, przechył (roll) do 90°, przeloty kilka centymetrów nad karoserią.
- **Krzywe prędkości (zmierzone):**
  - lot FPV: ease-in-out, szczyt 1,8–2,2 s;
  - wyhamowanie do slow-mo;
  - pełzający najazd;
  - wykładniczy ramp-in (szczyt 8,25);
  - stop na lakierze;
  - lustrzany ramp-out (szczyt 9,6), wyhamowanie;
  - spokojne podążanie.
  Ruch nigdy nie jest liniowy.
- **Obrót kamery:** 90° → 45° → 0° w akcie I; ok. 35° → 0° przy wyjściu ze szkła. Obrót zawsze wraca do poziomu, zanim kamera się zatrzyma.
- **Packshoty:** statyczny statyw z mikro-najazdem, nisko przy ziemi, auto i koła wypełniają kadr.

## 7. Efekty: pełna lista

1. Rozmycie ruchu (kamera i obiekty), w tym rozmycie obrotowe przy przechyle.
2. Płytka głębia ostrości w zbliżeniach (maska, wloty, szyba, koła).
3. **Otwarcie i oderwanie starej maski:** obrót na zawiasie, potem wylot z obrotem.
4. **Wlot nowej maski:** z góry, pionowo, z obrotem do poziomu i miękkim lądowaniem; w slow-motion.
5. **Przejście przez powierzchnię lakieru** z 0,5 s jednolitego koloru nowego auta. Kolor mostkuje oba światy.
6. **Zmiana auta i świata** schowana w tym kolorze: żółte GT3 w lecie zmienia się w błękitne GT3 RS w zimie.
7. **Rozkładanie aktywnego spoilera** (mechanika).
8. **Mokra droga:** lustrzane odbicia, kałuże, mgiełka spod kół, mgła, chmury wolumetryczne.
9. **Animacja felgi:** ramiona unoszą się nad obręczą i osiadają (intro i outro, pętla).
10. Zero efektów montażowych: brak przenikań, błysków, glitchy, napisów i dodawanych wstrząsów.

## 8. Światło, kolor, materiały

| Świat | Paleta (k-means, udział) | Charakter |
|---|---|---|
| Próżnia 0–1 | #000000 79%, #b1b4b2 9% | Czarne lustro, jedno miękkie światło z góry |
| Świat 1, FPV | #fbf7f1 31%, #625e53 18%, **#b89028 16% (żółty)**, #e0d5ca 13% | Pochmurne białe niebo, ciepło-neutralny, high-key, niski kontrast |
| Metamorfoza | #4b4a46 34% (asfalt), #faf5f2 32% (niebo), #9ba8a9 8% (maska), #b7902f 7% | Jak wyżej, spokojny |
| Lakier (przejście) | #6c9bba / #adc7d4 / #7eb1cb / #9ac4d5 | Jasnobłękitny satynowy lakier z gradientem: **kolor-most** |
| Świat 2, zima | #eaf4f9 29%, #78939e 19%, #cddde4 16%, #445d6c 11% | Chłodny, stalowo-błękitny, jasny, mokry |
| Packshoty | #abc0c8 29%, #68818d 19%, #8ba6b2 19% | Chłodny, miękki, pochmurny |

- **Kontrast światów:** ciepły żółty zmienia się w chłodny błękit. Zmiana koloru auta jest główną „przemianą”.
- **Materiały:** żółty lakier z połyskiem; satynowy jasnobłękitny lakier; karbon z widocznym splotem (żaluzje); białe felgi; przyciemniane szkło z odbiciami.
- **Światło:** wyłącznie miękkie, pochmurne (HDRI z zachmurzonym niebem). Nie ma twardych słońc ani flar.

## 9. Dźwięk i synchronizacja (montaż pod muzykę)

| Czas (s) | Zdarzenie |
|---|---|
| 0,0–0,2 | Cisza |
| 0,2–1,1 | Intro bez basu (pad + lead ok. 1,46 kHz) |
| **1,04–1,2** | **Drop basu na pierwszym cięciu** |
| 1,2–7,5 | Groove ok. 120 BPM; stały lead 1,46 kHz; uderzenia co 0,5 s |
| 1,6–2,1 i 2,7–3,0 | Szum „powietrza” (5–11 kHz) pod szybkim FPV i odlot maski: whoosh |
| **7,6–8,3** | **Break:** bas i lead wycięte do zera dokładnie podczas najazdu w maskę (napięcie) |
| **8,4–9,3** | **Stutter:** pocięte uderzenia i lead na przejściu przez lakier; whoosh 8,7–9,3 |
| **9,4** | **Pełny drop:** świat zimowy wjeżdża z całym groove'em |
| 13,36 / 15,36 / 16,36 | Uderzenia pod cięciami do packshotów |
| **17,0** | **Twarde ucięcie muzyki** pod cięcie do felgi; zostaje pogłos (pętla) |

## 10. Technologia (wnioski z obrazu)

- **Silnik:** rendering w czasie rzeczywistym lub path tracing, w stylu Unreal Engine 5. Za tym przemawiają:
  - miękkie globalne oświetlenie,
  - chmury wolumetryczne,
  - skany drzew i skał,
  - mokre nawierzchnie z odbiciami,
  - fizyczny motion blur i głębia ostrości z renderu.
- **Modele aut** pochodzą z bibliotek (992 GT3, 992 GT3 RS); części (maska, spoiler) są osobnymi obiektami animowanymi kluczowo.
- **Kamera** jest animowana w sekwencerze (rig FPV z przechyłem i krzywymi ease). Zwolnione tempo to globalne spowolnienie czasu sceny, ustawiane krzywą.
- **Podmiana auta i lokacji** dzieje się w ukrytym cięciu w lakierze. W praktyce to dwie sekwencje 3D połączone klatką jednolitego koloru.
- **Montaż:** muzyka jest zmontowana pod obraz (break, stutter, drop), cięcia leżą na beat. Wyjście w 1080×1920 przy 30 kl./s.

## 11. Różnice v6 względem oryginału (lista do poprawy)

| # | Oryginał | v6 |
|---|---|---|
| 1 | Metamorfoza w **slow-mo 1/20–1/40** z ramp-down (2,5–3,0) i ramp-up (6,5–8,25) | Metamorfoza ok. 1×; brak ramp-down i ramp-up |
| 2 | Stara maska **otwiera się na zawiasie i odlatuje** | Brak |
| 3 | Nowa maska wlatuje **pionowo jak tarcza**, obraca się do poziomu przez ok. 3 s | Maska unosi się poziomo i opada |
| 4 | Najazd w maskę **przez prawdziwy przelot kamery** wzdłuż maski w wlot, z obrotem ok. 10° | Cyfrowy zoom 2D w środek kadru |
| 5 | Kadr lakieru = **kolor nowego auta** (u nas biały); 0,5 s | Biały 0,5 s ✓ |
| 6 | Wyjście **ze szkła bocznego / dachu** (ten sam materiał co lakier), z obrotem 35° → 0° | Wyjście ze zbliżenia złotej felgi |
| 7 | **Spoiler się rozkłada** (10,4–10,9) | Brak |
| 8 | Świat 1 pochmurny, high-key | Lot FPV z zachodu słońca po korekcji (nadal ciepły) |
| 9 | Auto „przed” w obu światach: inne auto, inny kolor (żółte 992 GT3 → błękitne GT3 RS) | Żółte GT3 → białe GT3 RS ✓ (zgodnie z decyzją) |
| 10 | Muzyka: break 7,6–8,3, **stutter 8,4–9,3**, drop 9,4, twarde ucięcie w 17,0 | Breakdown i uderzenie w 9,0; brak stuttera i twardego ucięcia |
| 11 | Brak tekstu i logo | Logo Turismo na końcu (świadoma decyzja) |
| 12 | Szerokie szkło FPV (14–20 mm) z beczką, płytka głębia w zbliżeniach | Kadry z AI, różne ogniskowe |

## 12. Wnioski do produkcji (do decyzji)

Z analizy wynika, że oryginał to **jedna zaplanowana sekwencja 3D**, a nie seria osobnych ujęć. Najwierniejsza droga to film w całości z naszego modelu 3D (GT3 RS z MSP02):
1. Ta sama kamera i krzywe czasu co w oryginale. Kamera i krzywe są już zmierzone i są w szkicu `cgi/guide.py`.
2. Fotorealizm w jednym przebiegu `video_edit` na całym ciągłym ujęciu 1,04–13,3 s, a nie w kawałkach.

Do szkicu trzeba dodać:
- slow-mo z rampami;
- otwarcie maski na zawiasie;
- pionowy wlot nowej maski;
- wyjście ze szkła;
- rozkładający się spoiler.

Muzykę trzeba dociąć pod break 7,6, stutter 8,4–9,3, drop 9,4 i ucięcie w 17,0.
