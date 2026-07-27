# VAČ — Virtualna Arhivska Čitalnica
## Znanje za virtualnega asistenta (chatbot)
> Vir: Uporabniška navodila + PZI + scraped podatki sistema
> Zadnja posodobitev: september 2025

---

# 1. SPLOŠNO O VAČ

VAČ (Virtualna Arhivska Čitalnica) je spletna aplikacija za dostop do arhivskega gradiva v Republiki Sloveniji. Omogoča iskanje, naročanje in ogled digitaliziranega arhivskega gradiva javnih arhivov.

**Dostop:** Aplikacija je dostopna prek spletnega brskalnika. Prijava poteka prek enotne točke SI-PASS.

**Arhivi v sistemu:** SI_AS, SI_PAM, SI_PAK, SI_PANG, SI_ZAC, SI_ZAL, SI_ZAP

---

# 2. REGISTRACIJA IN PRIJAVA

## Kako se registriram?

Za prijavo in registracijo v VAČ se uporablja enotna točka za preverjanje identitete SI-PASS.

**Postopek:**
1. Na glavni strani klikni gumb **Prijava**
2. Aplikacija te preusmeri na SI-PASS
3. Izberi način prijave (uporabniško ime + geslo, digitalno potrdilo...)
4. Ob prvi prijavi se odpre obrazec **Matični list**
5. Izpolni obvezna polja (označena z *)
6. Strinjaj se z **Izjavo o pogojih uporabe in dostopnosti arhivskega gradiva**
7. Klikni **Shrani spremembe**

**Obvezna polja pri registraciji:**
- Ime in priimek
- Naslov, poštna številka, kraj, država
- E-pošta
- Vrsta in številka osebnega dokumenta (samodejno izpolnjeno pri prijavi z dig. potrdilom)
- Državljanstvo, poklic
- Strinjanje s pogoji uporabe (kljukica)

**Opomba za organizacije:** Izberi ali gre za fizično osebo ali predstavnika pravne osebe — odpreta se različna obrazca.

## Statusi uporabnikov

| Status | Opis | Kaj lahko delam |
|---|---|---|
| Registriran | Prijavil se z user/pass | Branje, iskanje — NE morem naročati |
| Aktiven | Prijavil z dig. potrdilom ALI potrdil v Arhivu RS | Vse funkcije vključno z naročanjem |

Če imaš status **Registriran** in hočeš naročati gradivo, se moraš osebno oglasiti v Arhivu RS, kjer preverijo veljavnost osebnega dokumenta in ti dodelijo status Aktiven.

## Prijava in odjava

- **Prijava:** Klikni gumb Prijava v glavi → SI-PASS → vrne te v VAČ
- **Odjava:** Klikni na svoje ime v glavi → Odjava

## Urejanje podatkov profila

Dostop: Klikni na svoje **ime v glavi** → **Podatki o računu**

Sami lahko spremeniš:
- Telefon
- GSM številka
- Državljanstvo
- Poklic
- Naročanje na novice
- Dodajanje priponk/dokazil

**Ostale podatke** (ime, priimek, naslov...) lahko popravi samo Administrator VAČ v Arhivu RS.

### Dodajanje priponk k profilu
1. V profilu klikni gumb **Priponka / Priloga**
2. Klikni **Izberi** in poišči datoteko na računalniku
3. Dodaj opis in izberi vrsto priloge (Dokazilo za izjemni dostop / Dovoljenje za reprodukcije / Prilagojen dostop / Drugo)
4. Klikni **Dodaj prilogo**
5. **OBVEZNO:** klikni **Shrani spremembe** — brez tega se priloga ne shrani!

---

# 3. ISKANJE GRADIVA

**URL:** `/vac/search` — Zavihek **Iskanje** v glavni navigaciji

Na voljo so **4 načini iskanja:**

## 3.1 Iskanje po besedilu

Najpreprostejši način — eno iskalno polje za hitro iskanje.

**Kako:**
1. Klikni zavihek **Iskanje** → **Iskanje po besedilu**
2. Vnesi iskalni pojem
3. Klikni **Išči**

**Napredne možnosti** (klikni *Prikaži druge možnosti iskanja*):
- **Z vsemi besedami** — najde PE ki vsebujejo vse vnesene pojme
- **Z ustrezno besedno zvezo** — točno ujemanje besednega reda
- **S katerokoli besedo** — najde PE z vsaj enim pojmom
- **Brez besed** — izključi pojme
- **Soundex** — najde podobno zveneče besede (npr. "Greif" najde "Grajf")
- **Besedni koren** — upošteva pregibe (npr. "zveza" najde "zveze")
- **Časovno obdobje** — od/do datuma nastanka
- **Vrsta arhivskega gradiva**
- **Nivo popisa**

## 3.2 Iskanje po poljih

Iskanje po specifičnih lastnostih popisne enote. Priporočeno za natančno iskanje.

**Lastnosti po katerih iščeš:**
- Klasifikacijska oznaka, naslov, nivo popisa, signatura
- Signatura tektonike arhiva, stopnja urejenosti
- Vsebina, vsebuje tudi, zvrsti arhivskega gradiva

**Načini primerjave:** Začne z / Vsebuje / Zaključi z / Je enako

**Logično povezovanje:** IN / ALI / IN NE (za kombiniranje več polj)

## 3.3 Iskanje po tektoniki arhiva

Prikazuje strukturo arhivskega gradiva v obliki **drevesnega prikaza** (fondi in zbirke).

- Odpri/zapri veje z **+** / **-**
- **Prikaži podrobnosti** — podrobnosti označene PE
- **Omejitev pogleda** — omeji iskanje na izbrano PE
- **Preklic omejitve** — vrni se na celoten arhiv
- **Dodaj v delovno mapo** — samo za prijavljene uporabnike

## 3.4 Iskanje po deskriptorjih

Iskanje prek indeksov imen (občna, stvarna, osebna, zemljepisna imena).

**Postopek v 2 korakih:**
1. Vnesi deskriptor → klikni **Išči** → dobis seznam pojmov
2. S **+** prenesi želen pojem na desni seznam → klikni **Išči**

**Tip:** Pred pojmom napiši `%` za iskanje kateregakoli predhodnega zaporedja.

## 3.5 Rezultati iskanja

Tabela rezultatov prikazuje:
- Naslov/vsebuje tudi, Časovno obdobje, Nivo, Signatura, Ustreznost, Dostopnost

**Akcije z rezultati:**
- Klikni **košarico** 🛒 pri PE da jo dodaš v košarico
- **Prikaži samo dostopne PE** — filtrira samo naročljive
- **Prikaži seznam s slikami** — pokaže digitalizate
- **Iskanje znotraj zadetkov** — nadaljnje ožanje rezultatov

---

# 4. NAROČILO GRADIVA

## 4.1 Košarica

PE dodaš v košarico iz rezultatov iskanja s klikom na ikono košarice.

**URL košarice:** `/vac/cart/list`

V košarici pri vsaki PE izberi:
- **Naročilo uporabe** — ogled gradiva
- **Naročilo reprodukcije** — kopija gradiva

## 4.2 Vnos podatkov naročila

**Obvezna polja:**
- **Datum načrtovane uporabe** — kdaj hočeš priti
- **Namen naročanja:** drugo / znanstveno-raziskovalni / upravno-pravni
- **Način dostopa:** VAČ (privzeto) / ogled v čitalnici / e-pošta / osebni prevzem / pošta / SOVD

**Opcijsko:**
- Sporočilo čitalnici
- Vrsta reprodukcije (samo za naročila reprodukcije)
- Dokazila za izjemni dostop
- Dovoljenje za reprodukcije
- Prilagojen dostop

**Gumbi:**
- **Shrani** → status Shranjeno (ni še oddano)
- **Oddaj naročilo** → status Oddano (čaka na arhivista)
- **Izbriši** → briše naročilo
- **Nazaj** → seznam naročil

## 4.3 Naročilo z izjemnim dostopom

Nekatere PE zahtevajo **Dokazilo za izjemni dostop**.

**Postopek:**
1. Sistem te opozori da gre za omejeno gradivo
2. Izberi: imam dokazila / nimam dokazil
3. Priloži ustrezno dokazilo iz profila ali naloži novo
4. Šele potem lahko odda naročilo

**Izjema:** Če ima napredni uporabnik že potrjeno prilogo v tvojem profilu (z veljavnostjo in PE), ti dokazila ni treba prilagati ročno.

## 4.4 Statusi naročil

| Status | Pomen |
|---|---|
| Shranjeno | Shranjeno, ni oddano |
| Oddano | Oddano, čaka na prevzem arhivista |
| Sprejeto | Arhivist je prevzel naročilo |
| Potrjeno | Odobreno |
| Potrjeno – potrebno plačilo | Odobreno, čaka na plačilo |
| V pripravi | Arhivist pripravlja gradivo |
| Pripravljeno | Gradivo pripravljeno za ogled |
| Uporabljeno | Zaključeno |
| Stornirano | Preklicano |
| Zavrnjeno | Zavrnjeno s strani arhiva |
| Spremenjeno | Arhivist je spremenil naročilo, čaka na potrditev |

## 4.5 Pregled naročil

**URL:** `/vac/userprofile/orders`

Dostop: Klikni na ime → **Moja naročila**

Filter je na voljo za iskanje po: ID, datumu, arhivu, signaturi, namenu, uporabniku, statusu.

---

# 5. DELOVNE MAPE

Delovne mape so zbirke PE ki si jih shranjaš za poznejšo obdelavo.

- Dodaj PE v delovno mapo iz rezultatov iskanja ali tektonike
- Dostop: Zavihek **Delovne mape** v navigaciji
- Iskanje **Po delovnih mapah** je možno v iskalnih parametrih

---

# 6. E-OBRAZCI IN E-VLOGE

**URL:** `/vac/userprofile/documents`

Dostop: Klikni na ime → **E-obrazci in e-vloge**

Vrste e-obrazcev:
- **Vloga za izjemni dostop** — za dostop do omejenega gradiva
- **Vloga za uporabo reprodukcije AG** — dovoljenje za reprodukcije
- **Obrazec za reprodukcijo** — konkretni obrazec za reprodukcijo

---

# 7. KNJIGA PRITOŽB IN POHVAL

**URL:** `/vac/userprofile/complains`

Dostop: Klikni na ime → **Knjiga pritožb in pohval**

**Kako oddaš:**
1. Izberi **arhiv**
2. Izberi **tip** (pohvala ali pritožba)
3. Vnesi **povzetek**
4. Vnesi **vsebino**
5. Potrdi

---

# 8. PREGLED ZGODOVINE

**URL:** `/vac/userprofile/history`

Dostop: Klikni na ime → **Pregled zgodovine**

- Izberi tip zgodovine
- Vnesi datum od / datum do
- Klikni **Išči**

---

# 9. NOVICE

**URL:** `/vac/userhelp/vacNewsUsers`

Dostop: Zavihek **Pomoč** → Novice

Kot registriran uporabnik se lahko naročiš na kategorije novic v svojem profilu (Podatki o računu → Naročanje na novice).

---

# 10. POGOSTA VPRAŠANJA IN POMOČ

**URL:** `/vac/userhelp`

Dostop: Zavihek **Pomoč** v navigaciji

Na tej strani:
- Iskanje med vprašanji
- Kategorije vprašanj
- Možnost postavitve vprašanja strokovnjakom

### Zastavite vprašanje strokovnjakom
**URL:** `/vac/userhelp/QAForm`

1. Izberi **arhiv**
2. Izberi **kategorijo vprašanja**
3. Vnesi **vsebino vprašanja**
4. Vnesi **kraj** in **e-pošto**
5. Potrdi

---

# 11. PRIJAVA NAPAKE

**URL:** `/vac/reportError`

Dostop: Klikni **Prijava napake** v navigaciji

1. Vnesi **komentar** z opisom napake
2. Sistem samodejno priloži screenshot
3. Klikni **Pošlji**

---

# 12. DOSTOPNOST

VAČ podpira prilagoditve za uporabnike s posebnimi potrebami:

**Velikost pisave:** Privzeto / 125% / 150% / 200% / 14pt / 16pt / 18pt / 20pt

**Pisava:** Arial / Arial bold / Verdana / Verdana bold / Open Dyslexic / Open Dyslexic Alta / Didact Gothic

**Barvne sheme:** Privzeta / Črno na belem / Belo na črnem / Črno na bež / Modro na belem / Črno na zelenem / Črno na rumenem / Modro na rumenem / Rumeno na modrem / Turkizna na črnem / Črna na roza

Nastavitve dostopnosti so v orodni vrstici na vrhu vsake strani.

---

# 13. VIRTUALNE RAZSTAVE

**URL:** `/vac/virtualTourView`

Dostop: Prva stran → Virtualne razstave

**Obstoječe razstave:**
- Življenje v srednjeveškem mestu
- Računalništvo
- Ter ostale virtualne razstave

---

# 14. NAPREDNI UPORABNIK (NU) — DODATNE FUNKCIJE

## 14.1 Upravljanje uporabniških računov

**URL:** `/vac/userprofile/advanced/userAccounts`

- Pregled vseh registriranih uporabnikov
- Filter po: ID, ime, priimek, naslov, pošta, datum, status, arhiv
- Gumb **Prijave v VAČ** — pregled prijav uporabnika
- Dodelitev/odvzem statusa NU

## 14.2 Notifikacija prilog

NU potrjuje priložene dokumente uporabnikov:
1. Pojdi na profil uporabnika
2. Preveri priložene dokumente
3. Določi veljavnost (datum)
4. Izberi PE za katere velja dokazilo
5. Potrdi prilogo

Ko je priloga potrjena, uporabnik pri naročanju omejenega gradiva ni treba ročno prilagati dokazil.

## 14.3 Urejanje virtualnih razstav

Dostop: Nastavitve → Virtualne razstave

**Sprememba slik in videov:**
1. Pojdi na urednik razstave
2. Izberi element ki ga hočeš spremeniti
3. Naloži novo sliko/video
4. Shrani

## 14.4 Vnos novic

**URL:** `/vac/settings/vacNews`

**Kako dodaš novo novico:**
1. Nastavitve → Vnos novic
2. Klikni za novo novico → odpre se `/vac/settings/vacNewsEdit`
3. Izpolni: Naslov, Podnaslov, Avtor, Status
4. Vnesi vsebino v urejevalnik
5. Opcijsko: naslovna slika, barve, ključne besede, interesno področje
6. Klikni **Shrani**

**Statusi novice:** Osnutek / Objavljena

## 14.5 Prejete reklamacije, pritožbe in pohvale

**URL:** `/vac/userprofile/advanced/receivedComplains`

Tabela vseh prejetih pritožb/pohval z možnostjo pregleda podrobnosti in odgovora.

## 14.6 Prejeta vprašanja

**URL:** `/vac/userprofile/advanced/receivedUserQuestions`

Tabela vprašanj uporabnikov. Filtri po: neodgovorjeno / odgovorjeno / objavljeno / neobjavljeno.

## 14.7 Statistika in evidence

**URL:** `/vac/userprofile/advanced/statistics`

- Izberi **tip statistike**
- Izberi **časovni okvir:** leto / obdobje / kvartalno / mesečno / tedensko
- Izberi **arhiv**
- Klikni **Naprej**

**URL statistike registracij:** `/vac/userprofile/advanced/userRegistrationStatistics`

## 14.8 Stalni dostopni informacijski paketi (DIPP)

**URL:** `/vac/dip/dipp`

- Dodaj/uredi/briši DIPP zapise
- Filter po: ID, signatura, opis, lokacija, javnost

## 14.9 Odločbe arhivske komisije

**URL:** `/vac/userprofile/advanced/decisionList`

Pregled odločb za izjemni dostop.

## 14.10 Novice in obveščanja

**URL:** `/vac/userprofile/advanced/newsAndInformation`

Upravljanje naročnikov na novice z filtri po: ime, priimek, datum, kategorija novice.

---

# 15. NASTAVITVE SISTEMA (NU)

Dostop: Zavihek **Nastavitve** v navigaciji

| Stran | URL | Namen |
|---|---|---|
| Javni arhiv | `/vac/settings/regionalArchive` | Podatki o arhivih |
| Poštna številka | `/vac/settings/postNumber` | Šifrant poštnih številk |
| Cenik | `/vac/settings/priceList` | Cene storitev |
| Iskalna polja | `/vac/settings/searchField` | Konfiguracija iskalnih polj |
| Uporabniške pravice | `/vac/settings/userPermission` | Seznam pravic |
| Predloge pravic | `/vac/settings/userRole` | Vloge in dovoljenja |
| Elektronska pošta | `/vac/settings/email` | E-poštni naslovi |
| Geslovnik | `/vac/settings/thesaurus` | Predmetne oznake |
| Način dostopa | `/vac/settings/archMaterialAccessType` | Načini dostopa do gradiva |
| Nastavitve naročil | `/vac/settings/loanSettings` | Parametri naročil |
| Test e-pošte | `/vac/settings/emailTest` | Testiranje e-pošte |

---

# 16. NAVIGACIJA — PREGLED STRANI

## Glavna navigacija (vidna vsem prijavljenim)

| Element | URL | Namen |
|---|---|---|
| Prva stran | `/vac` | Domača stran |
| Nastavitve | `/vac/settings/...` | Sistemske nastavitve (NU) |
| Iskanje | `/vac/search` | Iskanje gradiva |
| Delovne mape | `/vac/workfolders` | Shranjene PE |
| Košarica | `/vac/cart/list` | Naročilna košarica |
| Naročila | `/vac/userprofile/orders` | Moja naročila |
| Pomoč | `/vac/userhelp` | FAQ, O VAČ, novice |
| Prijava napake | `/vac/reportError` | Prijava tehničnih napak |

## Profil (klik na ime)

| Element | URL |
|---|---|
| Podatki o računu | `/vac/register/editData` |
| Moja naročila | `/vac/userprofile/orders` |
| E-obrazci in e-vloge | `/vac/userprofile/documents` |
| Pregled zgodovine | `/vac/userprofile/history` |
| Knjiga pritožb in pohval | `/vac/userprofile/complains` |
| Odjava | — |

## Samo napredni uporabnik (NU)

| Element | URL |
|---|---|
| Uporabniški računi | `/vac/userprofile/advanced/userAccounts` |
| Stalni dostopni inf. paketi | `/vac/dip/dipp` |
| Evidence in statistike | `/vac/userprofile/advanced/statistics` |
| Prejete reklamacije | `/vac/userprofile/advanced/receivedComplains` |
| Prejeta vprašanja | `/vac/userprofile/advanced/receivedUserQuestions` |
| Pregled odločb | `/vac/userprofile/advanced/decisionList` |

---

# 17. POGOSTA VPRAŠANJA (FAQ)

**V: Kako se registriram v VAČ?**
O: Registracija poteka prek SI-PASS. Klikni Prijava → SI-PASS → ob prvi prijavi izpolni Matični list.

**V: Zakaj ne morem naročati gradiva?**
O: Verjetno imaš status Registriran namesto Aktiven. Moraš se osebno oglasiti v Arhivu RS z osebnim dokumentom.

**V: Kako dodam gradivo v košarico?**
O: V rezultatih iskanja klikni ikono košarice 🛒 pri željeni popisni enoti.

**V: Kako oddaim naročilo?**
O: V košarici izberi Naročilo uporabe ali Naročilo reprodukcije → izpolni podatke → klikni Oddaj naročilo.

**V: Kaj pomeni status Potrjeno – potrebno plačilo?**
O: Naročilo je odobreno, ampak moraš najprej plačati. Preveri podatke o plačilu v naročilu.

**V: Kako prijavim napako v sistemu?**
O: Klikni Prijava napake v navigaciji → vnesi opis → Pošlji.

**V: Kako spremenjem velikost pisave?**
O: V orodni vrstici za dostopnost na vrhu strani izberi željeno velikost (14pt, 16pt, 18pt, 20pt ali %).

**V: Kako iščem gradivo iz določenega leta?**
O: V iskanju po besedilu ali poljih uporabi parameter Časovno obdobje in nastavi datum od/do.

**V: Kje najdem virtualne razstave?**
O: Na prvi strani aplikacije ali prek URL `/vac/virtualTourView`.

**V: Kako oddaim pritožbo ali pohvalo?**
O: Klikni na ime → Knjiga pritožb in pohval → izberi arhiv in tip → vnesi besedilo.

---

*Dokument združuje: Uporabniška navodila VAČ + PZI Finalna verzija 1.2 + Scraped podatki sistema*
