"""
ikkunasto - yksinkertainen käyttöliittymäkirjasto

@author Mika Oja, Oulun yliopisto

Tämä kirjasto sisältää nipun funktioita, joilla opiskelijat voivat toteuttaa
yksinkertaisen käyttöliittymän, jossa hyödynnetään matplotlib-kirjastoa
kuvaajien piirtämiseen. Kirjasto sisältää paljon oletusratkaisuja, jotta
opiskelijoiden ei tarvitse opetella kokonaista käyttöliittymäkirjastoa, eikä
paneutua sellaisen yksityiskohtiin. Tästä syystä käyttöliittymien toteutuksessa
voi kuitenkin tulla rajoja vastaan.

Kirjasto on rakennettu Pythonin mukana tulevan TkInterin päälle. Lisätietoa
löytyy mm. täältä:

https://docs.python.org/3/library/tk.html

Erityisen huomattavaa on, että Tk hoitaa pääasiassa automaattiseti elementtien
sijoittelun (perustuen siihen missä kehyksissä ne ovat), mutta kuvaaja- ja
tekstilaatikoiden koko määritetään staattisesti - niiden ulottuvuudet siis
sanelevat aika pitkälti miltä käyttöliittymä näyttää. Jos siis haluat
siistimmän näköisen käyttöliittymän, kannattaa kokeilla säätää näiden kokoja.

Kirjaston pääohjelmasta löydät pienen esimerkkikoodin, josta saat jonkinlaisen
käsityksen siitä miten tätä kirjastoa käyttämällä luodaan käyttöliittymän
peruselementtejä.

***

Muokkaus (Jimi Käyrä):
* Funktiossa luo_kuvaaja asetetaan pick-event, jotta piste saadaan valittua
  juuri kuvaajalta.
* Funktioon avaa_tallennusikkuna on lisätty lisäparametri paate, joka määrittelee
  tiedostopäätteen.

"""

import tkinter as tk
from tkinter.ttk import Separator
from tkinter import messagebox, filedialog

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib
matplotlib.use("TkAgg")

VASEN = tk.LEFT
OIKEA = tk.RIGHT
YLA = tk.TOP
ALA = tk.BOTTOM

def luo_ikkuna(otsikko):
    """
    Luo ikkunan käyttöliittymää varten. Ikkuna toimii kaiken pohjana, joten
    tätä funktiota pitää kutsua ennen kuin muita voidaan käyttää.

    :param str otsikko: ikkunan otsikko
    :return: palauttaa luodun ikkunaobjektin
    """

    # käytetään globaalia muuttujaa jotta kaynnista- ja lopeta-funktiot
    # toimivat ilman parametreja
    global ikkuna
    ikkuna = tk.Tk()
    ikkuna.wm_title(otsikko)
    return ikkuna

def luo_kehys(isanta, puoli=VASEN):
    """
    Luo kehyksen, johon voidaan asetella muita elementtejä. Kehyksillä voidaan
    jakaa käyttöliittymä helpommin käsiteltäviin alueisiin. Niitä tarvitaan
    myös, jos halutaan asetella komponentteja muutenkin kuin yhden akselin
    suuntaisesti.

    Kehykset voivat sijaita itse ikkunassa, tai toisten kehysten sisällä.
    Funktion ensimmäinen parametri on siis joko ikkunaobjekti tai kehysobjekti.
    Toinen parametri vaikuttaa siihen, mihin kehys sijoitetaan. Elementit
    pakataan aina jotain seinää vasten - ne siis muodostavat pinon. Jos esim.
    pakataan kaksi kehystä ylälaitaa vasten, ensimmäisenä pakattu kehys on
    ylimpänä ja toisena pakattu kehys sen alla.

    :param widget isanta: kehys tai ikkuna, jonka sisälle kehys sijoitetaan
    :param str puoli: mitä isäntäelementin reunaa vasten kehys pakataan
    :return: palauttaa luodun kehysobjektin
    """

    kehys = tk.Frame(isanta)
    kehys.pack(side=puoli, anchor="n")
    return kehys

def luo_nappi(kehys, teksti, kasittelija):
    """
    Luo napin, jota käyttäjä voi painaa. Napit toimivat käsittelijäfunktioiden
    kautta. Koodissasi tulee siis olla määriteltynä funktio, jota kutsutaan
    aina kun käyttäjä painaa nappia. Tämä funktio ei saa lainkaan argumentteja.
    Funktio annetaan tälle funktiokutsulle kasittelija-argumenttina. Esim.

    def aasi_nappi_kasittelija():
        # jotain tapahtuu

    luo_nappi(kehys, "aasi", aasi_nappi_kasittelija)

    Napit pakataan aina kehyksensä ylälaitaa vasten, joten ne tulevat näkyviin
    käyttöliittymään alekkain. Jos haluat asetella napit jotenkin muuten, voit
    katsoa tämän funktion koodista mallia ja toteuttaa vastaavan
    toiminnallisuuden omassa koodissasi. Jos laajenna-argumentiksi annetaan
    True, nappi käyttää kaiken jäljellä olevan tyhjän tilan kehyksestään.

    :param widget kehys: kehys, jonka sisälle nappi sijoitetaan
    :param str teksti: napissa näkyvä teksti
    :param function kasittelija: funktio, jota kutsutaan kun nappia painetaan
    :return: palauttaa luodun nappiobjektin
    """

    nappi = tk.Button(kehys, text=teksti, command=kasittelija)
    nappi.pack(side=tk.TOP, fill=tk.BOTH)
    return nappi

def luo_kuvaaja(kehys, hiiri_kasittelija, leveys, korkeus):
    """
    Luo kuvaajan sekä piirtoalueen johon se sijoitetaan. Tämän funktion avulla
    voidaan kytkeä matplotlib ja tällä kirjastolla luotu graafinen
    käyttöliittymä toisiinsa - erillisen piirtoikkunan sijaan kuvaaja tulee
    näkyviin yhtenä paneelina käyttöliittymässä. Kuvaajan käsittelystä löydät
    lisätietoja matplotlibin dokumentaatiosta:

    http://matplotlib.org/api/figure_api.html

    Funktiolle määritellään lisäksi käsittelijäfunktio, jota kutsutaan aina kun
    käyttäjä klikkaa hiirellä kuvaajaa. Tämä toimii samalla tavalla kuin
    nappien käsittelijät, mutta funktiolla on oltava yksi parametri. Tämä
    parametri saa arvoksi matplotlibiltä objektin, jossa on tiedot
    klikkauksesta. Hyödyllisiä ominaisuuksia tämän ohjelman kannalta ovat
    ainakin xdata ja ydata, jotka kertovat kuvaajan arvot klikatussa kohdassa,
    sekä button, joka kertoo mitä hiiren nappia klikattiin (1 = vasen, 2 =
    keski, 3 = oikea). Lisätietoja

    http://matplotlib.org/api/backend_bases_api.html#matplotlib.backend_bases.MouseEvent

    Kuvaajalle määritetään leveys ja korkeus pikseleinä.

    :param widget kehys: kehys, jonka sisälle kuvaaja sijoitetaan
    :param function hiiri_kasittelija: funktio, jota kutsutaan klikatessa
    :param int leveys: kuvaajan leveys pikseleinä
    :param int korkeus: kuvaajan korkeus pikseleinä
    :return: piirtoalueobjekti, kuvaajaobjekti
    """

    kuvaaja = Figure(figsize=(leveys / 100, korkeus / 100), dpi=100)
    piirtoalue = FigureCanvasTkAgg(kuvaaja, master=kehys)
    piirtoalue.get_tk_widget().pack(side=tk.TOP)
    piirtoalue.mpl_connect("pick_event", hiiri_kasittelija)
    # Muutos: valitaan pick-event, jotta piste tulee kuvaajalta.
    return piirtoalue, kuvaaja

def luo_tekstilaatikko(kehys, leveys=80, korkeus=20):
    """
    Luo tekstilaatikon, johon voidaan kirjoittaa viestejä samaan tapaan kuin
    printillä komentoriviohjelmissa. Oletuksena tekstilaatikko täyttää kaiken
    vapaana olevan tilan kehyksestään. Tarkalleen ottaen luo kehyksen, jossa
    on sekä tekstilaatikko että siihen liitetty pystysuuntainen vierityspalkki.
    Kehystä ja vierityspalkkia ei kuitenkaan palauteta, ainoastaan itse
    laatikko.

    :param widget kehys: kehys, jonka sisälle tekstilaatikko sijoitetaan
    :param int leveys: laatikon leveys merkkeinä
    :param int korkeus: laatikon korkeus riveinä
    :return: tekstilaatikko-objekti
    """

    laatikkokehys = luo_kehys(kehys, tk.TOP)
    vieritin = tk.Scrollbar(laatikkokehys)
    laatikko = tk.Text(laatikkokehys, height=korkeus, width=leveys, yscrollcommand=vieritin.set)
    laatikko.configure(state="disabled")
    laatikko.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
    vieritin.pack(side=tk.RIGHT, fill=tk.Y)
    vieritin.configure(command=laatikko.yview)
    return laatikko

def kirjoita_tekstilaatikkoon(laatikko, sisalto, tyhjaa=False):
    """
    Kirjoittaa rivin tekstiä valittuun tekstilaatikkoon. Tarvittaessa laatikko
    voidaan myös tyhjentää ennen kirjoitusta asettamalla tyhjaa-argumentin
    arvoksi True.

    :param widget laatikko: tekstilaatikko-objekti johon kirjoitetaan
    :param str sisalto: kirjoitettava teksti
    :param bool tyhjaa: tyhjätäänkö laatikko ensin
    """

    laatikko.configure(state="normal")
    if tyhjaa:
        try:
            laatikko.delete(1.0, tk.END)
        except tk.TclError:
            pass
    laatikko.insert(tk.INSERT, sisalto + "\n")
    laatikko.configure(state="disabled")

def luo_listalaatikko(kehys, leveys=80, korkeus=20):
    """
    Luo listalaatikon. Erona tekstilaatikkoon, listalaatikon rivit ovat
    yksittäisiä objekteja. Niitä voidaan siis valita hiirellä sekä poistaa ja
    lisätä yksitellen.

    :param widget kehys: kehys, jonka sisälle listalaatikko sijoitetaan
    :param int leveys: laatikon leveys merkkeinä
    :param int korkeus: laatikon korkeus riveinä
    :return: listalaatikko-objekti
    """

    laatikkokehys = luo_kehys(kehys, tk.TOP)
    vieritin = tk.Scrollbar(laatikkokehys)
    laatikko = tk.Listbox(laatikkokehys,
        height=korkeus,
        width=leveys,
        yscrollcommand=vieritin.set
    )
    laatikko.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
    vieritin.pack(side=tk.RIGHT, fill=tk.Y)
    vieritin.configure(command=laatikko.yview)
    return laatikko

def lisaa_rivi_laatikkoon(laatikko, sisalto, paikka=tk.END):
    """
    Lisää tekstirivin listalaatikkoon. Paikka voidaan antaa valinnaisena
    argumenttina, jolloin lisäys tapahtuu määritettyyn väliin. Jos parametria
    ei anneta, lisäys tehdään loppuun.

    :param widget laatikko: listalaatikko-objekti johon lisätään
    :param str sisalto: rivin sisältö
    :param int paikka: paikka johon rivi lisätään (valinnainen)
    """

    laatikko.insert(paikka, sisalto)

def poista_rivi_laatikosta(laatikko, indeksi):
    """
    Poistaa määritetyn rivin listalaatikosta. Rivi määritetään indeksillä.

    :param widget laatikko: listalaatikko-objekti josta poistetaan
    :param int indeksi: poistettavan rivin indeksi
    """

    laatikko.delete(indeksi)

def lue_valittu_rivi(laatikko):
    """
    Lukee listalaatikosta, mikä riveistä on valittu hiirellä. Palauttaa valitun
    rivin indeksin sekä sisällön. Jos mitään riviä ei ole valittu, palauttaa
    kaksi Nonea.

    :param widget laatikko: listalaatikko-objekti josta luetaan
    """

    valittu = laatikko.curselection()
    if valittu:
        sisalto = laatikko.get(valittu)
        return valittu[0], sisalto
    return None, None

def luo_tekstirivi(kehys, teksti):
    """
    Luo pienen tekstipätkän, jota voi käyttää tilatietojen esittämiseen, tai
    antamaan otsikoita käyttöliittymän eri osille.

    :param widget kehys: kehys, jonka sisälle tekstilaatikko sijoitetaan
    :param str teksti: näytettävä teksti
    :return: tekstiriviobjekti
    """

    rivi = tk.Label(kehys, text=teksti)
    rivi.pack(side=tk.TOP, fill=tk.BOTH)
    return rivi

def paivita_tekstirivi(rivi, teksti):
    """
    Päivittää tekstirivin sisällön.

    :param widget rivi: tekstiriviobjekti
    :param str teksti: uusi sisältö
    """

    rivi.configure(text=teksti)

def luo_tekstikentta(kehys):
    """
    Luo tekstikentän, johon käyttäjä voi syöttää tekstiä. Tekstikentän arvo
    voidaan lukea kutsumalla lue_kentan_sisalto-funktiota.

    :param widget kehys: kehys, jonka sisälle tekstikenttä sijoitetaan
    :return: tekstikenttäobjekti
    """

    kentta = tk.Entry(kehys)
    kentta.pack(side=tk.TOP, fill=tk.BOTH)
    return kentta

def lue_kentan_sisalto(kentta):
    """
    Lukee määritetyn syötekentän sisällön ja palauttaa sen.

    :param widget kentta: syötekenttä, jonka sisältö halutaan lukea
    :return: syötekentän sisältö merkkijonona
    """

    return kentta.get()

def tyhjaa_kentan_sisalto(kentta):
    """
    Tyhjentää määritetyn syötekentän sisällön.

    :param widget kentta: syötekenttä, jonka sisältö halutaan lukea
    """

    kentta.delete(0, len(kentta.get()))

def kirjoita_tekstikenttaan(kentta, sisalto):
    """
    Kirjoittaa määritettyyn syötekenttään sisältöä.

    :param widget kentta: syötekenttä, johon halutaan kirjoittaa
    :param str sisalto: kirjoitettava sisältö
    """

    kentta.insert(0, sisalto)

def luo_vaakaerotin(kehys, marginaali=2):
    """
    Luo vaakatason erottimen, jolla voidaan esim. erottaa selkeämmin
    käyttöliittymän osia toisistaan. Funktiolle voidaan lisäksi antaa toinen
    argumentti, joka kertoo paljonko ylimääräistä tyhjää laitetaan viivan
    molemmin puolin.

    :param widget kehys: kehys, johon erotin sijoitetaan
    :param int marginaali: ylimääräisen tyhjän määrä pikseleinä
    """

    erotin = Separator(kehys, orient="horizontal")
    erotin.pack(side=tk.TOP, fill=tk.BOTH, pady=marginaali)

def luo_pystyerotin(kehys, marginaali=2):
    """
    Luo pystysuoran erottimen, jolla voidaan esim. erottaa selkeämmin
    käyttöliittymän osia toisistaan. Funktiolle voidaan lisäksi antaa toinen
    argumentti, joka kertoo paljonko ylimääräistä tyhjää laitetaan viivan
    molemmin puolin.

    :param widget kehys: kehys, johon erotin sijoitetaan
    :param int marginaali: ylimääräisen tyhjän määrä pikseleinä
    """

    erotin = Separator(kehys, orient="vertical")
    erotin.pack(side=tk.TOP, fill=tk.BOTH, pady=marginaali)

def avaa_viesti_ikkuna(otsikko, viesti, virhe=False):
    """
    Avaa ponnahdusikkunan, jossa on viesti käyttäjälle. Viesti-ikkuna voidaan
    määritellä virhe-argumentilla virheikkunaksi, jolloin siinä näkyy eri
    kuvake. Ikkunalle annetaan otsikko ja viesti.

    :param str otsikko: ikkunan otsikko
    :param str viesti: ikkunaan kirjoitettava viesti
    :param bool virhe: totuusarvo, joka kertoo onko kyseessä virheviesti
    """

    if virhe:
        messagebox.showerror(otsikko, viesti)
    else:
        messagebox.showinfo(otsikko, viesti)

def avaa_hakemistoikkuna(otsikko, alkuhakemisto="."):
    """
    Avaa ikkunan, josta käyttäjä voi valita hakemiston. Hyödyllinen erityisesti
    datakansion lataamiseen. Ikkunalle tulee antaa otsikko, ja lisäksi sille
    voidaan määrittää mikä hakemisto aukeaa aluksi (oletuksena se hakemisto,
    josta ohjelma käynnistettiin). Funktio palauttaa polun käyttäjän valitsemaan
    hakemistoon merkkijonona.

    :param str otsikko: hakemistoikkunan otsikko
    :param str alkuhakemisto: hakemisto, joka avautuu ikkunaan
    :return: käyttäjän valitseman hakemiston polku
    """

    polku = filedialog.askdirectory(title=otsikko, mustexist=True, initialdir=alkuhakemisto)
    return polku

def avaa_tiedostoikkuna(otsikko, alkuhakemisto="."):
    """
    Avaa ikkunan, josta käyttäjä voi valita olemassaolevan tiedoston. Ikkunalle
    tulee antaa otsikko, ja lisäksi sille voidaan määrittää mikä hakemisto
    aukeaa aluksi (oletuksena se kansio mistä ohjelma käynnistettiin). Funktio
    palauttaa polun käyttäjän valitsemaan tiedostoon merkkijonona.

    :param str otsikko: tiedostoikkunan otsikko
    :param str alkuhakemisto: hakemisto, joka avautuu ikkunaan
    :return: käyttäjän valitseman tiedoston polku
    """

    polku = filedialog.askopenfilename(title=otsikko, initialdir=alkuhakemisto)
    return polku

def avaa_tallennusikkuna(otsikko, alkuhakemisto=".", paate=""):
    """
    Avaa tallennusikkunan, jolla käyttäjä voi valita tallennettavalle
    tiedostolle sijainnin ja nimen. Ikkunalle tulee antaa otsikko, ja lisäksi
    sille voidaan määrittää mikä hakemisto aukeaa aluksi (oletuksena se
    hakemisto, josta ohjelma käynnistettiin). Funktio palauttaa polun käyttäjän
    nimeämään tiedostoon.

    :param str otsikko: tallennusikkunan otsikko
    :param str alkuhakemisto: hakemisto, joka avautuu ikkunaan
    :param str paate: tiedoston pääte
    :return: käyttäjän nimeämän tiedoston polku
    """

    polku = filedialog.asksaveasfilename(title=otsikko, initialdir=alkuhakemisto, defaultextension=paate)
    # Muutos: lisättiin parametriksi tiedostopääte.
    return polku

def poista_elementti(elementti):
    """
    Poistaa määritetyn elementin käyttöliittymästä. Tarpeen, jos haluat
    käyttöliittymään tilapäisiä elementtejä.

    :param widget elementti: poistettava elementti
    """

    try:
        elementti.destroy()
    except AttributeError:
        elementti.get_tk_widget().destroy()

def luo_ali_ikkuna(otsikko):
    """
    Luo ali-ikkunan, jonka sisältöä voidaan muokata. Ali-ikkuna toimii samalla
    tavalla kuin kehys, eli siihen voidaan laittaa mitä tahansa muita
    käyttöliittymäkomponentteja. Ali-ikkuna voidaan piilottaa ja avata
    uudestaan käyttämällä näytä_ali_ikkuna- ja piilota_ali_ikkuna-funktioita.
    Ali-ikkuna piiloutuu myös jos käyttäjä painaa oikean yläkulman rastia.

    :param str otsikko: ali-ikkunan otsikko
    :return: luotu ali-ikkunaobjekti
    """

    ali = tk.Toplevel()
    ali.title(otsikko)
    ali.protocol("WM_DELETE_WINDOW", ali.withdraw)
    return ali

def nayta_ali_ikkuna(ali, otsikko=None):
    """
    Näyttää valitun ali-ikkunan.

    :param object ali: näytettävä ali-ikkuna
    """

    if otsikko:
        ali.title(otsikko)
    ali.deiconify()

def piilota_ali_ikkuna(ali):
    """
    Piilottaa valitun ali-ikkunan.

    :param object ali: piilotettava ali-ikkuna
    """

    ali.withdraw()

def kaynnista():
    """
    Käynnistää ohjelman. Kutsu tätä kun olet määritellyt käyttöliittymän.
    """

    ikkuna.mainloop()

def lopeta():
    """
    Sammuttaa ohjelman.
    """

    ikkuna.destroy()

if __name__ == "__main__":
    # Poistetaan kaksi pylint-varoitusta pois käytöstä, koska testikoodi
    # antaa ne aiheettomasti
    # pylint: disable=invalid-name,missing-docstring


    # funktio määritellään poikkeuksellisesti täällä, koska sitä ei ole
    # tarkoitus käyttää muuhun kuin kirjaston demoamiseen.
    def tervehdi():
        nimi = lue_kentan_sisalto(nimikentta)
        ammatti = lue_kentan_sisalto(ammattikentta)
        if nimi and ammatti:
            viesti = "Terve {}, olet kuulemma {}.".format(nimi, ammatti)
            kirjoita_tekstilaatikkoon(tekstilaatikko, viesti)
        else:
            avaa_viesti_ikkuna("Tietoja puuttuu",
                "Et antanut nimeä ja ammattia",
                virhe=True
            )

    testi_ikkuna = luo_ikkuna("Terve!")
    ylakehys = luo_kehys(testi_ikkuna, YLA)
    alakehys = luo_kehys(testi_ikkuna, YLA)
    nappikehys = luo_kehys(ylakehys, VASEN)
    syotekehys = luo_kehys(ylakehys, VASEN)
    tervehdysnappi = luo_nappi(nappikehys, "terve", tervehdi)
    lopetusnappi = luo_nappi(nappikehys, "lopeta", lopeta)
    nimiohje = luo_tekstirivi(syotekehys, "Nimi:")
    nimikentta = luo_tekstikentta(syotekehys)
    ammattiohje = luo_tekstirivi(syotekehys, "Ammatti:")
    ammattikentta = luo_tekstikentta(syotekehys)
    tekstilaatikko = luo_tekstilaatikko(alakehys, 34, 20)
    kaynnista()
