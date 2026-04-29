"""
Udlejning business case - Ceresbyen ejerlejlighed.

100% helaarsudlejning. Beregner cashflow og sammenligner skattemetoder:
  1. Personlig kapitalindkomst (default - ingen ordning)
  2. Virksomhedsskatteordningen (VSO) - fuldt udbetalt
  3. Virksomhedsskatteordningen (VSO) - alt opsparet (foreloebig 22%)
  4. Kapitalafkastordningen (KAO)

Juster INPUT-blokken nedenfor og koer:  python3 udlejning_case.py
"""

# ---------- INPUT ----------

# Laan (Jyske Bank prioritetslaan Cibor3, pr. 01.04.2026)
RESTGAELD       = 2_086_317      # kr
DEBITORRENTE    = 2.84           # % p.a. (basisrente 2,04% + tillaeg 0,80%)
YDELSE_MD       = 12_150         # kr/md (ydelse foer skat fra Jyske Bank)

# Ejendom
EJENDOMSVURDERING = 4_324_000    # kr (offentlig vurdering)
GRUNDVAERDI       = 2_338_000    # kr
GRUNDSKYLD_PROMILLE = 5.6        # promille (Aarhus 2026, ca. - tjek vurderingsportalen.dk)
ANSKAFFELSESSUM   = 4_875_000    # kr (kontant - inkl. de 50% koebt af bror)

# Drift (maanedligt)
EJERFORENING_MD   = 1_810        # kr/md (fast hele aaret)
INDBOFORSIKRING_MD = 250         # kr/md
VEDLIGEHOLD_PCT_AARLIG = 0.5     # % af ejendomsvurdering p.a. (0,3-1,0% typisk)
ANDRE_FASTE_MD    = 0            # kr/md

# Forbrug betaler lejer aconto -> ikke en udgift for ejer (sat til 0)
# Hvis ejer betaler: indtast her og det fratraekkes i cashflow
FORBRUG_EJER_MD   = 0            # kr/md

# Skat
KAP_PLUS  = 37.7    # % marginalskat positiv kapitalindkomst
KAP_MINUS = 25.6    # % marginalskat negativ kap.indk. (Jyske Banks "skattesats")
PERS_SKAT = 52.07   # % marginalskat personlig indkomst (uden topskat)
VSO_FORELOEBIG = 22 # % foreloebig sats ved opsparing i VSO
KAO_AFKASTSATS = 3.0 # % kapitalafkastsats (2024-niveau, Skat fastsaetter aarligt)

# Leje
TANKT_LEJE_MD = 16_000   # kr/md - hvad I overvejer at udleje for
TOMGANG_PCT   = 0        # % af aaret uden lejer (default 0 = 100% udlejet)


# ---------- BEREGNING ----------

def kr(x):
    """Format som dansk valuta uden decimaler."""
    return f"{x:,.0f}".replace(",", ".") + " kr"

def pct(x):
    return f"{x:.1f}%"

def line(char="-", n=64):
    print(char * n)

def header(text):
    print()
    line("=")
    print(f"  {text}")
    line("=")

# Laan - opdel ydelse
renter_md = RESTGAELD * (DEBITORRENTE / 100) / 12
afdrag_md = YDELSE_MD - renter_md
renter_aar = renter_md * 12
afdrag_aar = afdrag_md * 12

# Drift
grundskyld_aar = GRUNDVAERDI * (GRUNDSKYLD_PROMILLE / 1000)
grundskyld_md = grundskyld_aar / 12
vedligehold_aar = EJENDOMSVURDERING * (VEDLIGEHOLD_PCT_AARLIG / 100)
vedligehold_md = vedligehold_aar / 12

drift_md = (
    EJERFORENING_MD
    + INDBOFORSIKRING_MD
    + grundskyld_md
    + vedligehold_md
    + ANDRE_FASTE_MD
    + FORBRUG_EJER_MD
)
drift_aar = drift_md * 12

# Leje
udlejnings_andel = 1 - TOMGANG_PCT / 100
leje_md_eff = TANKT_LEJE_MD * udlejnings_andel
leje_aar = leje_md_eff * 12

# Cashflow (likviditet) per maaned
cashflow_md = leje_md_eff - drift_md - YDELSE_MD
oekonomisk_md = cashflow_md + afdrag_md  # afdrag er formueopbygning, ikke udgift

# Skattepligtigt resultat (regnskabsmaessigt)
resultat_foer_renter = leje_aar - drift_aar
resultat_efter_renter = resultat_foer_renter - renter_aar


# ---- Skat per metode (aarlig) ----

# Metode 1: Privat kapitalindkomst
# Lejeoverskud (foer renter) -> kap.indk. positiv (37,7%)
# Renter er privat negativ kap.indk. - fradragsvaerdi 25,6%
if resultat_foer_renter >= 0:
    m1_skat_lejeoverskud = resultat_foer_renter * KAP_PLUS / 100
else:
    m1_skat_lejeoverskud = resultat_foer_renter * KAP_MINUS / 100
m1_rentefradrag = renter_aar * KAP_MINUS / 100
m1_netto_skat = m1_skat_lejeoverskud - m1_rentefradrag

# Metode 2: VSO udbetalt (alt overskud taget ud som personlig indkomst)
m2_skat = resultat_efter_renter * PERS_SKAT / 100

# Metode 3: VSO opsparet (foreloebig 22%, eftalbetales naar haevet)
m3_skat = resultat_efter_renter * VSO_FORELOEBIG / 100

# Metode 4: KAO
# Kapitalafkast = sats * (anskaffelsessum, simplificeret)
# Begraenset til aarets overskud foer kapitalafkast (= resultat_efter_renter)
kao_kapafkast_max = ANSKAFFELSESSUM * KAO_AFKASTSATS / 100
kao_kapafkast = max(0, min(kao_kapafkast_max, resultat_efter_renter))
kao_personlig_del = resultat_efter_renter - kao_kapafkast
m4_skat = (kao_personlig_del * PERS_SKAT / 100
           + kao_kapafkast * KAP_PLUS / 100)

# Overskud efter skat (aarligt) - foer afdrag (afdrag er formueopbygning)
oekonomisk_aar_foer_skat = resultat_foer_renter - renter_aar  # = resultat_efter_renter
overskud_efter_skat = {
    "M1 Kap.indk.":    oekonomisk_aar_foer_skat - m1_netto_skat,
    "M2 VSO udbetalt": oekonomisk_aar_foer_skat - m2_skat,
    "M3 VSO opsparet": oekonomisk_aar_foer_skat - m3_skat,
    "M4 KAO":          oekonomisk_aar_foer_skat - m4_skat,
}

# Cashflow efter skat (likviditet) - INKL. afdrag som cash-out
cashflow_efter_skat = {k: v - afdrag_aar for k, v in overskud_efter_skat.items()}


# ---- Break-even leje ----

def beregn_skat(leje_md, metode):
    """Beregner aarlig skat ved given maanedsleje, for valgt metode."""
    leje_a = leje_md * 12 * udlejnings_andel
    rfr = leje_a - drift_aar              # resultat foer renter
    rer = rfr - renter_aar                # resultat efter renter
    if metode == "M1":
        skat_l = rfr * (KAP_PLUS if rfr >= 0 else KAP_MINUS) / 100
        return skat_l - renter_aar * KAP_MINUS / 100
    if metode == "M2":
        return rer * PERS_SKAT / 100
    if metode == "M3":
        return rer * VSO_FORELOEBIG / 100
    if metode == "M4":
        kao_max = ANSKAFFELSESSUM * KAO_AFKASTSATS / 100
        kao = max(0, min(kao_max, rer))
        return (rer - kao) * PERS_SKAT / 100 + kao * KAP_PLUS / 100
    raise ValueError(metode)

def break_even_likviditet(metode):
    """Maanedsleje hvor cashflow EFTER skat (incl. afdrag) = 0."""
    # cashflow_a = leje_a - drift_a - ydelse_a - skat = 0
    # Vi soeger via simpel binaer soegning
    lo, hi = 0, 100_000
    for _ in range(60):
        mid = (lo + hi) / 2
        leje_a = mid * 12 * udlejnings_andel
        skat = beregn_skat(mid, metode)
        cashflow = leje_a - drift_aar - YDELSE_MD * 12 - skat
        if cashflow < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

def break_even_oekonomisk(metode):
    """Maanedsleje hvor OEKONOMISK overskud efter skat = 0 (afdrag tilbage som formue)."""
    lo, hi = 0, 100_000
    for _ in range(60):
        mid = (lo + hi) / 2
        leje_a = mid * 12 * udlejnings_andel
        skat = beregn_skat(mid, metode)
        # cashflow + afdrag = oekonomisk
        oek = leje_a - drift_aar - renter_aar - skat
        if oek < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------- OUTPUT ----------

header("UDLEJNINGS BUSINESS CASE - CERESBYEN")

print(f"  Forudsaetning: 100% helaarsudlejning, lejer betaler forbrug aconto")
print(f"  Tankt leje:    {kr(TANKT_LEJE_MD)} / md  ({pct(TOMGANG_PCT)} tomgang)")

header("LAAN (Jyske Bank prioritetslaan Cibor3)")
print(f"  Restgaeld:           {kr(RESTGAELD)}")
print(f"  Debitorrente:        {pct(DEBITORRENTE)}")
print(f"  Maanedlig ydelse:    {kr(YDELSE_MD)}")
print(f"    heraf renter:      {kr(renter_md)}  ({kr(renter_aar)} / aar)")
print(f"    heraf afdrag:      {kr(afdrag_md)}  ({kr(afdrag_aar)} / aar)")

header("DRIFTSUDGIFTER (maanedlig)")
print(f"  Ejerforeningsbidrag:           {kr(EJERFORENING_MD)}")
print(f"  Indboforsikring:               {kr(INDBOFORSIKRING_MD)}")
print(f"  Grundskyld ({pct(GRUNDSKYLD_PROMILLE/10)} af grundvaerdi): {kr(grundskyld_md)}")
print(f"  Vedligehold ({pct(VEDLIGEHOLD_PCT_AARLIG)} p.a.):           {kr(vedligehold_md)}")
print(f"  Andre faste:                   {kr(ANDRE_FASTE_MD)}")
print(f"  Forbrug (ejer betaler):        {kr(FORBRUG_EJER_MD)}")
line()
print(f"  TOTAL drift:                   {kr(drift_md)} / md   ({kr(drift_aar)} / aar)")

header(f"CASHFLOW VED LEJE = {kr(TANKT_LEJE_MD)} / MD")
print(f"  Bruttoleje:           +{kr(leje_md_eff)} / md")
print(f"  Drift:                -{kr(drift_md)} / md")
print(f"  Ydelse (rente+afdr.): -{kr(YDELSE_MD)} / md")
line()
print(f"  Likviditet:            {kr(cashflow_md)} / md   "
      f"({'overskud' if cashflow_md >= 0 else 'UNDERSKUD - du skal laegge til'})")
print(f"  + Afdrag (formue):    +{kr(afdrag_md)} / md")
line()
print(f"  Oekonomisk overskud:   {kr(oekonomisk_md)} / md   (foer skat)")

header("SKATTEPLIGTIGT RESULTAT (aarligt, regnskabsmaessigt)")
print(f"  Bruttoleje (aarlig):           +{kr(leje_aar)}")
print(f"  Driftsudgifter:                -{kr(drift_aar)}")
print(f"  Resultat foer renter:           {kr(resultat_foer_renter)}")
print(f"  Renter:                        -{kr(renter_aar)}")
print(f"  Resultat efter renter:          {kr(resultat_efter_renter)}")
print(f"  Note: ejendomsvaerdiskat bortfalder ved 100% udlejning hele aaret")

header("SKATTEMETODER - SAMMENLIGNING (aarligt)")
fmt = "  {:<22} {:>14} {:>16} {:>16}"
print(fmt.format("Metode", "Skat", "Overskud e.skat", "Cashflow e.skat"))
print(fmt.format("", "(aar)", "(aar, ekskl afdr)", "(aar, inkl afdr)"))
line()

skat_per_metode = {
    "M1 Kap.indk.":    m1_netto_skat,
    "M2 VSO udbetalt": m2_skat,
    "M3 VSO opsparet": m3_skat,
    "M4 KAO":          m4_skat,
}
for navn, skat in skat_per_metode.items():
    oek = overskud_efter_skat[navn]
    cf  = cashflow_efter_skat[navn]
    print(fmt.format(navn, kr(skat), kr(oek), kr(cf)))

# Find optimal metode (mindst skat) blandt 'reelle' metoder (M3 er kun udskudt)
reelle = {k: v for k, v in skat_per_metode.items() if k != "M3 VSO opsparet"}
optimal = min(reelle, key=reelle.get)
print()
print(f"  >> Realistisk optimal metode (lavest reel skat): {optimal}")
print(f"     M3 VSO opsparet udskyder kun skatten - ved haevning betales op til pers.skat.")

header("BREAK-EVEN MAANEDLIG LEJE")
fmt2 = "  {:<22} {:>16} {:>16}"
print(fmt2.format("Metode", "Likviditet=0", "Oekon. ovrskd.=0"))
print(fmt2.format("", "(inkl. afdrag)", "(ekskl. afdrag)"))
line()
for metode_kode, navn in [("M1", "M1 Kap.indk."),
                          ("M2", "M2 VSO udbetalt"),
                          ("M3", "M3 VSO opsparet"),
                          ("M4", "M4 KAO")]:
    bel = break_even_likviditet(metode_kode)
    beo = break_even_oekonomisk(metode_kode)
    print(fmt2.format(navn, kr(bel) + " / md", kr(beo) + " / md"))

print()
print("  Likviditet=0:    Lejen daekker drift + hele ydelsen (incl. afdrag).")
print("                   Du laegger 0 kr til af egne penge per md.")
print("  Oekon. ovrskd.=0: Lejen daekker drift + renter (afdrag tilbage som formue).")
print("                   Du opbygger formue via afdrag - reelt overskud.")

header("KONKLUSION VED 16.000 KR / MD")
m_anbefalet = optimal
print(f"  Anbefalet skattemetode:   {m_anbefalet}")
print(f"  Aarlig skat ({m_anbefalet}):  {kr(skat_per_metode[m_anbefalet])}")
print(f"  Likviditet (md):          {kr(cashflow_md - skat_per_metode[m_anbefalet]/12)}  (efter skat)")
print(f"  Oekonomisk overskud (md): {kr(oekonomisk_md - skat_per_metode[m_anbefalet]/12)}  (efter skat, formue tael med)")
print(f"  Formueopbygning (md):     {kr(afdrag_md)}  (afdrag paa laanet)")

print()
print("  FORBEHOLD:")
print("  - Ved erhvervsmaessig udlejning kan parcelhusreglen mistes -> evt. skat ved salg.")
print("  - Lejen skal vaere markedsleje (Skat kan fiksere ved underleje).")
print("  - VSO kraever fuldt adskilt regnskab og bankkonto.")
print("  - KAO-beregningen her er forenklet (ignorerer de praecise reguleringsregler).")
print("  - Grundskyldspromille er anslaaet - tjek dit reelle tal paa vurderingsportalen.dk.")
print("  - Cibor3-renten varierer kvartalsvist; tallene gaelder for nuvaerende rente 2,84%.")
print()
