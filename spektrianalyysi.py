"""
Spektrianalyysi
@author Jimi Käyrä

Ikkunasto-kirjastoa hyödyntävä työkalu, jolla voidaan ladata mittausdataa
ja piirtää siitä kuvaaja.
Työkalu sisältää yksinkertaisen graafisen käyttöliittymän, jonka avulla
käyttäjä voi suorittaa toimintoja.
Dataa voidaan muokata poistamalla siitä lineaarinen tausta.
Työkalu mahdollistaa myös datan analyysin laskemalla kuvaajalta löytyvien piikkien pinta-alat
numeerisella integroinnilla.
Kuvaaja voidaan tallentaa png-tiedostoksi.

Ikkunastoon on tehty joitakin muutoksia, jotta se soveltuisi paremmin
tähän ohjelmaan; ks. ikkunasto.py.
"""

import os # Hyödynnetään kansioiden ja tiedostojen "haravoinnissa".
from re import search # RegExiä hyödynnetään tutkittaessa, onko tiedostonimet haluttua muotoa.
from enum import Enum
import locale
import numpy as np
import ikkunasto as ik

locale.setlocale(locale.LC_ALL, "FI")
# Asetetaan locale, jotta saadaan käytettyä oikeaoppisesti desimaalipilkkua.

class Odottaa(Enum):
    """
    Määrittelee tilamuuttujan arvot:
    mitä varten pisteiden valintaa odotetaan?
    """

    POISTA = 0
    LASKE = 1
    LEPO = 2

data = { # Määritellään datasanakirja, jotta ladattuja arvoja voidaan käyttää eri funktioissa.
    "energiat": [], # Sisältää mittausdatasta ladatut energia-arvot.
    "summaintensiteetit": [], # Saadaan laskemalla tiedostojen intensiteetit yhteen.
    "summaintensiteetit_taustaton": [], # Lopputulos, kun käyttäjä on poistanut lineaarisen taustan.
    "lkm": 0, # Ladattujen tiedostojen lukumäärä.
    "piste_a": (), # Kuvaajalta voidaan valita kerralla vain kaksi pistettä.
                   # Määritellään siksi selkeyden vuoksi omina muuttujinaan.
    "piste_b": (), # Tulevat sisältämään monikon (x, y), joka sisältää pisteen koordinaatit.
    "tila": Odottaa.LEPO # Alussa ohjelma on lepotilassa.
}

# Asetetaan nappien nimet, jotta niihin voidaan viitata muualla poistettaessa nappi käytöstä.
napit = {
    "LATAA": None,
    "PIIRRA": None,
    "POISTA": None,
    "LASKE": None,
    "TALLENNA": None
}

elementit = { # Määritellään muiden ulkoasuelementtien nimet.
    "tekstilaatikko": None,
    "piirto": None, # matplotlibin subplot
    "alue": None, # matplotlibin kuvaaja
    "graafi": None,
    "kuvaaja": None,
    "merkit": [] # Sisältää kuvaajalle piirrettävät merkit valittujen pisteiden kohdille.
}

TIEDOSTO_REGEX = r"^measurement_\d+.txt$"
# Määrittää, minkä nimisistä tiedostoista etsitään mittausdataa (RegEx).
TOLERANSSI = 1
# Toleranssi valittaessa pistettä kuvaajalta (picker): "kuinka lähelle" on osuttava,
# jotta klikkaus rekisteröidään kuvaajan pisteeksi.
KUVAAJAN_KOKO = [940, 950] # Määrittää kuvaajan koon (leveys, korkeus).
LAATIKON_KOKO = [980, 950] # Määrittää tekstilaatikon koon (leveys, korkeus).
# Edelliset määräävät nappien koon.

# Määritellään tässä ohjelmassa käytetyt tekstit ym.,
# jotta niitä voidaan muuttaa helposti esim. kääntämistä varten.

X_AKSELI = "Sidosenergia (eV)"
Y_AKSELI = "Intensiteetti (mielivaltainen yksikkö)"

OTSIKKO = "Spektrianalyysi"
NAPPI_LATAA = "Lataa mittausdata"
NAPPI_PIIRRA = "Piirrä kuvaaja"
NAPPI_POISTA = "Poista lineaarinen tausta"
NAPPI_LASKE = "Laske piikin intensiteetti"
NAPPI_TALLENNA = "Tallenna kuvaaja"

LADATTIIN_TIEDOSTOJA = "Ladattiin {} mittaustiedostoa."
PIIKIN_INTENSITEETTI = "Valitun piikin intensiteetti on {}."

INFO = "Tervetuloa spektrityökaluun.\n"  \
"Aloita lataamalla mittaustulokset.\n" \
"Uusien tulosten lataaminen korvaa aiemmat tulokset ja kuvaajan.\n" \
"Kuvaaja tallennetaan png-tiedostona.\n\n"

DATAA_EI_LADATTU = "Dataa ei ole ladattu. Lataa mittausdata \"Lataa mittausdata\"-painikkeesta."
TAUSTA_POISTETTU = "Lineaarinen tausta poistettiin."
VALITSE_PISTEET = "Valitse kuvaajalta kaksi pistettä hiiren vasemmalla painikkeella."
KUVAAJA_EI_PIIRRETTY = "Kuvaajaa ei ole piirretty. Piirrä kuvaaja \"Piirrä kuvaaja\"-painikkeesta."
TAUSTA_EI_POISTETTU = "Poista lineaarinen tausta ennen intensiteettien laskemista."
VALITSE_ERI_PISTEET = "Valitse kaksi eri pistettä."

TALLENNUS_EI = "Tallentaminen epäonnistui."
TALLENNUS_OK = "Tallentaminen onnistui."

def laske_parametrit(x_1, y_1, x_2, y_2):
    """
    Laskee suoran (joka ei ole muotoa x = a) kulmakertoimen ja vakiotermin, kun
    on annettu kaksi suoran pistettä (x_1, y_1) ja (x_2, y_2).
    """

    k = (y_2 - y_1) / (x_2 - x_1)
    b = (x_2 * y_1 - x_1 * y_2) / (x_2 - x_1)

    return k, b

def laske_pisteet_suoralla(k, b, kohdat):
    """
    Tuottaa joukon pisteitä, jotka ovat annetulla kulmakertoimella ja vakiotermillä
    määritetyn suoran arvoja annetuissa x-akselin pisteissä.
    """

    pisteet = []

    for kohta in kohdat:
        pisteet.append(k * kohta + b)

    return pisteet

def etsi_indeksit(mittausdata, minimi, maksimi):
    """
    Etsii annetusta numeerista dataa sisältävästä listasta alku- ja päätepisteet
    siten, että alueen arvot ovat annettujen minimi- ja maksimiarvojen välissä.
    Palauttaa näiden pisteiden indeksit.
    """

    alku = -1
    loppu = -1
    i = None

    for i, luku in enumerate(mittausdata):
        if luku >= minimi and alku == -1:
            # Jos löydettiin minimiä suurempi luku ja alkuindeksiä ei ole vielä asetettu,
            # asetetaan se.
            alku = i

        if luku > maksimi and loppu == -1:
            # Jos löydettiin maksimia suurempi luku ja loppuindeksiä ei ole vielä asetettu,
            # asetetaan se.
            loppu = i

        if alku > -1 and loppu > -1:
            # Jos alku- ja päätepisteet löydettiin, palautetaan ne.
            return alku, loppu

    if alku > -1 and loppu == -1:
        # Tutkitaan, löydettiinkö alku ja loppu ja palautetaan sen mukaan oikeat arvot.
        return alku, i + 1

    return i + 1, i + 1

def onko_data_ladattu():
    """
    Tarkistaa, onko käyttäjä ladannut mittausdatan ja ilmoittaa siitä käyttäjälle.
    Palauttaa totuusarvon.
    Muista onko_... -funktioista poiketen tämä ei sisällä tulosta_virhe -parametria, sillä
    ohje on tarpeen tulostaa aina.
    """

    if (not data["energiat"] or
            all(summaintensiteetti == 0 for summaintensiteetti in data["summaintensiteetit"])):
        # Jos energialista on tyhjä tai kaikki summaintensiteetit ovat nollia, dataa ei ole ladattu.
        ik.kirjoita_tekstilaatikkoon(elementit["tekstilaatikko"], DATAA_EI_LADATTU)
        # Ilmoitetaan tästä käyttäjälle.
        return False

    return True

def onko_pisteet_valittu(tulosta_virhe):
    """
    Tarkistaa, onko käyttäjä valinnut kaksi pistettä.
    Parametri määrää, tulostetaanko käyttäjälle ohje pisteiden valitsemisesta.
    Palauttaa totuusarvon.
    """

    if data["piste_a"] and data["piste_b"]: # Jos molemmat pisteet on valittu...
        return True

    if tulosta_virhe:
        ik.kirjoita_tekstilaatikkoon(elementit["tekstilaatikko"], VALITSE_PISTEET)
        # Muuten tulostetaan virhe, jos niin on pyydetty.

    return False

def onko_kuvaaja_piirretty(tulosta_virhe):
    """
    Tarkistaa, onko käyttäjä piirtänyt datasta kuvaajan.
    Parametri määrää, tulostetaanko käyttäjälle ohje kuvaajan piirtämisestä.
    Palauttaa totuusarvon.
    """

    if elementit["graafi"]: # Jos kuvaaja on piirretty...
        return True

    if tulosta_virhe:
        ik.kirjoita_tekstilaatikkoon(elementit["tekstilaatikko"], KUVAAJA_EI_PIIRRETTY)
        # Muuten tulostetaan virhe, jos niin on pyydetty.

    return False

def onko_tausta_poistettu(tulosta_virhe):
    """
    Tarkistaa, onko käyttäjä poistanut mittausdatasta lineaarisen taustan.
    Parametri määrää, tulostetaanko käyttäjälle ohje taustan poistamisesta.
    Palauttaa totuusarvon.
    """

    if data["summaintensiteetit_taustaton"]: # Jos tausta on poistettu...
        return True

    if tulosta_virhe:
        ik.kirjoita_tekstilaatikkoon(elementit["tekstilaatikko"], TAUSTA_EI_POISTETTU)
        # Muuten tulostetaan virhe, jos niin on pyydetty.

    return False

def lue_tiedosto(polku):
    """"
    Lukee mittausdatatiedoston.
    Palauttaa löydetyt energiat ja intensiteetit, jos tiedoston "muotoseikat" ovat kunnossa:
    sen tulee sisältää rivejä, joilla on kullakin kaksi liukulukua välilyönnillä erotettuna.
    (Muista vaatimuksista huolehditaan lue_data -funktiossa.)
    Muuten palautetaan monikko, joka sisältää kaksi totuusarvoa.
    """

    energiat = []
    intensiteetit = []

    try:
        with open(polku) as lahde:
            for rivi in lahde.readlines():
                tiedot = rivi.rstrip().split()
                # Poistetaan lopusta rivinvaihtomerkki ja yritetään jakaa rivi välilyönnin kohdalta.

                if not len(tiedot) == 2:
                    # Tiedosto hylätään saman tien, jos rivillä ei ole oikeaa määrää tietoja.
                    return False, False

                energiat.append(float(tiedot[0]))
                # Lisätään energiat ja intensiteetit listaan, jota käydään läpi funktion sisällä.
                intensiteetit.append(float(tiedot[1]))
    except (ValueError, IOError, IndexError):
        # tietoja ei voitu muuttaa liukuluvuiksi; tiedostoa ei voitu lukea;
        # rivillä oli vähemmän kuin kaksi arvoa
        return False, False
        # Jos tapahtui virhe, tiedosto ei ole kelvollinen ja se hylätään saman tien.
    else:
        return energiat, intensiteetit

def lue_data(polku):
    """
    Käy läpi polun sisältämät tiedostot alikansioita myöten.
    Lukee muotoa measurement_X.txt olevista tiedostoista mittausdatan ja
    tallettaa energiat sekä summaintensiteetit ohjelman muistiin.
    Tiedosto hylätään, jos sen "muotoseikat" eivät ole kunnossa
    tai se ei sisällä samoja energiatietoja/saman verran datarivejä.
    """

    ensimmainen = True
    # Kyseessä on ensimmäinen iteraatio;
    # tällöin täytyy tallettaa energiat ja luoda oikean pituinen intensiteettilista.
    lkm = 0 # Kelvollisten tiedostojen lukumäärä.
    summaintensiteetit = [0]
    # Täytetään summaintensiteetit nollilla siltä varalta, että tiedostoja ei saatu ladattua.
    # Listan pituus on tällöin merkityksetön.

    for kansiopolku, _, tiedostot in os.walk(polku):
        # os.walkista saadaan kansiopolku, alikansion nimi ja tiedostonimi.
        for tiedosto in tiedostot:
            hakemistopolku = os.path.join(kansiopolku, tiedosto) # Muodostetaan koko polku.

            if search(TIEDOSTO_REGEX, tiedosto):
                # Tutkitaan RegExillä, onko tiedostonimi haluttua muotoa
                # (määrätty tiedoston alussa).
                energiat, intensiteetit = lue_tiedosto(hakemistopolku)

                if energiat and intensiteetit: # Itse tiedosto oli kelvollinen.
                    if ensimmainen: # Jos kyseessä on ensimmäinen tiedosto...
                        summaintensiteetit = [0] * len(intensiteetit)
                        # luodaan oikean pituinen summaintensiteettilista ja täytetään se nollilla.
                        data["energiat"] = energiat # Sijoitetaan energiatiedot datasanakirjaan.
                        ensimmainen = False
                        # Tämän jälkeen kyseessä ei tietenkään ole ensimmäinen iteraatio...
                    else: # Jos kyseessä ei ole ensimmäinen tiedosto...
                        if data["energiat"] != energiat:
                            # ...verrataan, ovatko tiedostojen sisältämät energiatiedot samat ja
                            # tarvittaessa hylätään tiedosto.
                            continue

                    summaintensiteetit = np.array(summaintensiteetit) + np.array(intensiteetit)
                    # Käytetään numpyä listojen summamiseen (element-wise addition).
                    summaintensiteetit = summaintensiteetit.tolist()
                    # Muutetaan array vielä tavalliseksi listaksi.
                    lkm += 1 # Jos tiedosto oli kelvollinen, lisätään se lukumäärään.

    data["summaintensiteetit"] = summaintensiteetit
    data["lkm"] = lkm # Lopuksi asetetaan saadut tiedot koko ohjelman käyttöön (datasanakirjaan).

def nollaa_pisteet():
    """
    Kun kasittele_pistevalinta() -funktion tuottama pistedata on käsitelty, tätä funktiota
    kutsutaan, jotta pistevalinnat saadaan nollattua muita toimintoja varten.
    """

    data["piste_a"] = ()
    data["piste_b"] = () # Pistekoordinaatit tyhjennetään.

    for merkki in elementit["merkit"][:]: # Poistetaan pistemerkit kuvaajalta.
        merkki.remove()
        elementit["merkit"].remove(merkki)

    elementit["alue"].draw() # Uudelleenpiirto, jotta tilanne päivittyy.

def kasittele_pistevalinta(tapahtuma):
    """
    Funktiota kutsutaan pick-eventissä, kun käyttäjä klikkaa hiirtä
    kuvaajan kohdalla. Pisteiden valinta aloitetaan, jos ja vain jos ohjelma
    odottaa käyttäjän syötettä (=pisteiden valintaa) taustan poistoa tai
    intensiteetin laskemista varten.

    Käyttäjä valitsee kaksi pistettä ja niiden kohdalle piirretään markkerit.
    Tallettaa valitut pisteet ohjelman muistiin.
    Onnistuneen pistevalinnan jälkeen kutsuu pisteiden käsittelystä vastaavia
    funktioita tilamuuttujan arvon mukaan.
    """

    artisti = tapahtuma.artist # Artist on nyt kuvaaja.
    x_lista = artisti.get_xdata()
    y_lista = artisti.get_ydata() # Hankitaan x- ja y-tiedot listoiksi.
    indeksi = tapahtuma.ind
    # Talletetaan indeksi, jotta tiedot osataan lukea oikeasta kohdasta x- ja y-arvojen listasta.

    x = x_lista[indeksi][0]
    y = y_lista[indeksi][0]

    if data["tila"] == Odottaa.POISTA or data["tila"] == Odottaa.LASKE:
        # Ei sallita pisteiden valintaa huvin vuoksi...
        elementit["merkit"].extend(elementit["piirto"].plot(x, y, "kx")) # Lisätään merkki.
        elementit["alue"].draw()

        if data["piste_a"] and not data["piste_b"]: # Onko piste A jo valittu ja B valitsematta?
            data["piste_b"] = (x, y)

            if data["piste_a"] == data["piste_b"]: # Pisteet eivät saa olla samat.
                ik.kirjoita_tekstilaatikkoon(elementit["tekstilaatikko"], VALITSE_ERI_PISTEET)
                # Jos näin kuitenkin on, kehotetaan käyttäjää valitsemaan eri pisteet...
                nollaa_pisteet() # ...ja nollataan valinnat.
            else: # Jos pisteet ovat OK, suoritetaan valittu toiminto.
                if data["tila"] == Odottaa.POISTA:
                    poista_tausta()
                elif data["tila"] == Odottaa.LASKE:
                    laske_intensiteetit()
        else: # Jos A on kuitenkin vielä valitsematta...
            data["piste_a"] = (x, y)

def avaa_kansio():
    """
    Napinkäsittelijä, joka pyytää käyttäjää valitsemaan kansion avaamalla
    kansioselaimen. Lataa datan valitusta kansiosta ja ilmoittaa käyttöliittymän
    tekstilaatikkoon montako tiedostoa luettiin.
    """

    lue_data(ik.avaa_hakemistoikkuna("Valitse kansio"))
    ik.kirjoita_tekstilaatikkoon(elementit["tekstilaatikko"], INFO, tyhjaa=True)
    # Tyhjennetään laatikko ja kirjoitetaan info.
    ik.kirjoita_tekstilaatikkoon(elementit["tekstilaatikko"],
                                 LADATTIIN_TIEDOSTOJA.format(data["lkm"]))
    # Ilmoitetaan käyttäjälle ladattujen tiedostojen lukumäärä.

    napit["PIIRRA"].config(state="normal")
    napit["POISTA"].config(state="normal")
    # Asetetaan painikkeet klikattaviksi siltä varalta, että nyt tuodaan uutta mittausdataa.

    if elementit["graafi"]: # Jos kuvaaja on jo olemassa...
        elementit["graafi"].remove() # ...poistetaan vanha kuvaaja...
        elementit["graafi"] = None
        nollaa_pisteet() # ...ja nollataan mahdolliset pistevalinnat.

def piirra_data():
    """
    Piirtää kuvaajan subplotiin ohjelman muistissa olevista tiedoista.
    """

    if onko_data_ladattu():
        # Vaatimuksena luonnollisesti on, että mittausdata on ladattu.
        # Käyttäjälle tulostetaan ohje, jos näin ei ole.
        elementit["piirto"].clear()
        elementit["piirto"].set_xlabel(X_AKSELI)
        elementit["piirto"].set_ylabel(Y_AKSELI)
        # Tyhjennetään piirtoalue varalta ja asetetaan akseleiden nimet.
        elementit["graafi"], = elementit["piirto"].plot(data["energiat"],
                                                        data["summaintensiteetit"],
                                                        picker=TOLERANSSI)
        # picker on valinnan toleranssi, ks. alussa määritelty vakio.
        elementit["alue"].draw()

        napit["PIIRRA"].config(state="disabled")
        # Poistetaan nappi käytöstä, jotta samasta datasta ei voida piirtää uutta kuvaajaa.
        # Käsitellään nyt siis vain yhtä kuvaajaa kerrallaan, jotta ohjelman toiminta ei
        # monimutkaistu liikaa.

def poista_tausta():
    """
    Poistaa spektristä lineaarisen taustan käyttäjän valitsemien pisteiden perusteella.
    Ensin ohjataan käyttäjää valitsemaan pisteet ja tarvittaessa suorittamaan muitakin
    "esitehtäviä".
    """

    if onko_data_ladattu() and onko_kuvaaja_piirretty(True) and onko_pisteet_valittu(True):
        # Tarkistetaan, täyttyvätkö edellytykset:
        # data on ladattu, käyttäjä on valinnut pisteet ja kuvaaja on piirretty.
        # Ei tulosteta pisteohjetta useaan kertaan (False).
        kulmakerroin, vakiotermi = laske_parametrit(data["piste_a"][0], data["piste_a"][1],
                                                    data["piste_b"][0], data["piste_b"][1])
        # Lasketaan pisteitä vastaavan suoran parametrit.

        pisteet = laske_pisteet_suoralla(kulmakerroin, vakiotermi, data["energiat"])
        intensiteetit_erotus = np.array(data["summaintensiteetit"]) - np.array(pisteet)
        # Vähennetään summaintensiteeteistä suoran pisteet...
        data["summaintensiteetit_taustaton"] = intensiteetit_erotus.tolist()
        # ...ja sijoitetaan listaksi muutettu tulos datasanakirjaan.

        elementit["graafi"].remove() # Poistetaan alkuperäinen kuvaaja.
        elementit["piirto"].clear() # Palautetaan akselit, jotta niiden skaalaus toimii oikein.
        nollaa_pisteet() # Nollataan käyttäjän valitsemat pisteet.

        elementit["piirto"].set_xlabel(X_AKSELI)
        elementit["piirto"].set_ylabel(Y_AKSELI) # Asetetaan akseleiden nimet uudelleen.

        elementit["graafi"], = elementit["piirto"].plot(data["energiat"],
                                                        data["summaintensiteetit_taustaton"],
                                                        picker=TOLERANSSI)
        # Uusi kuvaaja paikalleen.
        elementit["alue"].draw()

        napit["POISTA"].config(state="disabled") # Poistetaan nappi käytöstä.
        data["tila"] = Odottaa.LEPO # Toiminnon suorituksen jälkeen voidaan levätä.

        ik.kirjoita_tekstilaatikkoon(elementit["tekstilaatikko"], TAUSTA_POISTETTU)
        # Ilmoitetaan onnistuneesta poistosta käyttäjälle.
    elif onko_kuvaaja_piirretty(False) and not onko_pisteet_valittu(False):
        # Jos kuvaaja on piirretty (tällöin datakin on ladattu) mutta pisteitä ei ole vielä valittu,
        # tulostetaan ilmoitus ja asetetaan tilamuuttujalle sopiva arvo
        # (jäädään "odottamaan" pisteiden valintaa).
        data["tila"] = Odottaa.POISTA

def laske_intensiteetit():
    """
    Laskee spektrin piikin intensiteetin (pinta-ala) käyttäjän valitsemien pisteiden perusteella.
    Ensin ohjataan käyttäjää valitsemaan pisteet ja tarvittaessa suorittamaan edelleen muitakin
    "esitehtäviä".
    """
    if (onko_data_ladattu() and onko_kuvaaja_piirretty(True) and onko_tausta_poistettu(True)
            and onko_pisteet_valittu(True)):
        # Tarkistetaan, täyttyvätkö edellytykset:
        # data on ladattu, käyttäjä on valinnut pisteet, kuvaaja on piirretty
        a, b = etsi_indeksit(data["energiat"], data["piste_a"][0], data["piste_b"][0])
        # Etsitään, mille indeksivälille käyttäjän valitsema energiaväli osuu.

        intensiteetti = np.trapz(data["summaintensiteetit_taustaton"][a:b], x=data["energiat"][a:b])
        lukuarvo = locale.format_string("%.2f", intensiteetti, True)
        # Lasketaan puolisuunnikassäännön avulla energiaväliä vastaava intensiteetti...
        ik.kirjoita_tekstilaatikkoon(elementit["tekstilaatikko"],
                                     PIIKIN_INTENSITEETTI.format(lukuarvo))
        # ...ja ilmoitetaan se käyttäjälle.
        # Hyödynnetään localea, jotta desimaalierottimeksi saadaan pilkku.

        data["tila"] = Odottaa.LEPO
        nollaa_pisteet()
    elif (onko_kuvaaja_piirretty(False) and onko_tausta_poistettu(False)
          and not onko_pisteet_valittu(False)):
        # Jos vain pisteet ovat valitsematta, jäädään odottamaan sitä.
        data["tila"] = Odottaa.LASKE

def tallenna_kuvaaja():
    """
    Tallentaa kuvaajan png-tiedostona käyttäjän valitsemaan paikkaan (tallennusikkunassa).
    Tallennus suoritetaan vain, jos data on ladattu ja kuvaaja piirretty.
    Tarvittaessa käyttäjää pyydetään suorittamaan "esitehtävät".
    Mahdollisesta virheestä ilmoitetaan.
    """

    if onko_data_ladattu() and onko_kuvaaja_piirretty(True):
        # Tarkistetaan, täyttyvätkö edellytykset: data on ladattu ja kuvaaja on piirretty.
        try:
            elementit["kuvaaja"].savefig(ik.avaa_tallennusikkuna("Tallenna kuvaaja", paate=".png"),
                                         format="png")
            # Yritetään tallennusta.
        except (FileNotFoundError, IOError):
            ik.kirjoita_tekstilaatikkoon(elementit["tekstilaatikko"], TALLENNUS_EI)
            # Tallennus ei onnistunut.
        else:
            ik.kirjoita_tekstilaatikkoon(elementit["tekstilaatikko"], TALLENNUS_OK)
            # Tallennus onnistui.

def main():
    """
    Luo käyttöliittymäikkunan, joka sisältää käyttöliittymän napit eri toimintoihin,
    kuvaajan ja tekstilaatikon. Oletuksena sovellus avataan koko näytölle.
    Käyttöliittymäelementtien koot voidaan määrätä vakioiden avulla.
    """

    ikkuna = ik.luo_ikkuna(OTSIKKO)
    ikkuna.state("zoomed") # Avataan oletuksena koko näytölle.
    nappikehys = ik.luo_kehys(ikkuna, ik.VASEN)

    napit["LATAA"] = ik.luo_nappi(nappikehys, NAPPI_LATAA, avaa_kansio)
    napit["PIIRRA"] = ik.luo_nappi(nappikehys, NAPPI_PIIRRA, piirra_data)
    napit["POISTA"] = ik.luo_nappi(nappikehys, NAPPI_POISTA, poista_tausta)
    napit["LASKE"] = ik.luo_nappi(nappikehys, NAPPI_LASKE, laske_intensiteetit)
    napit["TALLENNA"] = ik.luo_nappi(nappikehys, NAPPI_TALLENNA, tallenna_kuvaaja)
    # Määritellään napit ja asetetaan niille käsittelijät.

    laatikkokehys = ik.luo_kehys(ikkuna, ik.VASEN) # Luodaan kehys tekstilaatikolle.

    elementit["alue"], elementit["kuvaaja"] = ik.luo_kuvaaja(nappikehys, kasittele_pistevalinta,
                                                             KUVAAJAN_KOKO[0], KUVAAJAN_KOKO[1])
    elementit["piirto"] = elementit["kuvaaja"].add_subplot(1, 1, 1)
    # Luodaan kuvaaja ja sille subplot.

    elementit["piirto"].set_xlabel(X_AKSELI)
    elementit["piirto"].set_ylabel(Y_AKSELI) # Asetetaan akseleille nimet.

    elementit["tekstilaatikko"] = ik.luo_tekstilaatikko(laatikkokehys, leveys=LAATIKON_KOKO[0],
                                                        korkeus=LAATIKON_KOKO[1])
    # Luodaan tekstilaatikko.
    ik.kirjoita_tekstilaatikkoon(elementit["tekstilaatikko"], INFO) # Kirjoitetaan infoteksti.

    ik.kaynnista() # Käyntiin!

if __name__ == "__main__":
    main()
