# Snelstart Optimalisatie Gids (SAT Gebruikers)

**Voor gebruikers die overstappen van SAT (Smart Autotune Thermostat) of maximale energie-efficiëntie zoeken**

Smart Heating implementeert alle kern SAT optimalisatie-functies, met intelligente ketelbesturing voor optimaal energieverbruik en comfort. Deze gids helpt je deze functies in te schakelen en te configureren voor beste resultaten.

---

## 🎯 Wat Smart Heating Deelt met SAT

De geavanceerde besturingsfuncties van Smart Heating zijn **expliciet gemodelleerd naar SAT**, met gelijkwaardige of superieure optimalisatie:

| Functie | SAT | Smart Heating | Status |
|---------|-----|---------------|--------|
| **Stooklijn** | ✅ | ✅ **Auto-ingeschakeld** | Identiek algoritme |
| **PWM Besturing** | ✅ | ✅ Beschikbaar | Voor niet-modulerende ketels |
| **PID Regelaar** | ✅ | ✅ Beschikbaar | Auto-tuning ondersteund |
| **Overshoot Bescherming** | ✅ | ✅ Beschikbaar | OPV kalibratie API |
| **Minimum Setpoint** | ✅ | ✅ **Altijd actief** | Dynamische aanpassing |
| **Verwarmingstype per Zone** | ✅ | ✅ **Volledige ondersteuning** | Vloer vs Radiatoren |
| **Modulatie Optimalisatie** | ✅ | ✅ **Ingebouwd** | Real-time monitoring |

---

## 🚀 Snelstart: 3-Stappen Setup

### Stap 1: Configureer OpenTherm Gateway ✅

1. Ga naar **Globale Instellingen → OpenTherm** tabblad
2. Selecteer je OpenTherm Gateway uit de dropdown
3. Klik **Configuratie Opslaan**

**Resultaat**: Stooklijn wordt **automatisch ingeschakeld** voor optimale efficiëntie! 🎉

### Stap 2: Stel Verwarmingstype per Zone In ✅

Configureer elke zone op basis van je verwarmingssysteem:

1. Navigeer naar elke **Zone Details → Instellingen**
2. Vind de **"Verwarmingstype"** kaart
3. Selecteer:
   - **Vloerverwarming** - Voor vloerverwarmingssystemen (30-40°C aanvoer)
   - **Radiatoren** - Voor traditionele radiatoren (50-60°C aanvoer)

**Waarom dit belangrijk is:**
- Vloerverwarming: +10°C overhead → Lagere aanvoertemperaturen → 20-30% betere modulatie-efficiëntie
- Radiatoren: +20°C overhead → Hogere aanvoertemperaturen voor voldoende warmteafgifte

### Stap 3: Schakel Geavanceerde Functies In (Optioneel) ⚙️

Voor maximale SAT-achtige optimalisatie, schakel in **Globale Instellingen → Geavanceerde Besturing**:

- ✅ **Stooklijn**: Auto-ingeschakeld bij gateway configuratie *(Al AAN!)*
- ✅ **PWM Besturing**: Voor ketels zonder native modulatie
- ✅ **PID Regelaar**: Fine-tuning met auto-gains
- ✅ **OPV Kalibratie**: Uitvoeren via API voor overshoot bescherming

---

## 📊 Verwachte Energiebesparing

Gebaseerd op SAT's bewezen resultaten en onze implementatie:

| Configuratie | Typische Besparing | Notities |
|--------------|-------------------|----------|
| **Alleen Stooklijn** | 10-20% | Veilig, bewezen, auto-ingeschakeld |
| **+ Vloerverwarming Config** | +5-10% | Lagere aanvoertemp, betere modulatie |
| **+ PWM (niet-mod ketels)** | +5-15% | Vermindert schakelverliezen |
| **+ PID Fine-tuning** | +2-5% | Per-systeem optimalisatie |
| **Totaal Potentieel** | **20-35%** | Vergeleken met aan/uit regeling |

---

## 🎨 Stooklijn Begrijpen

De stooklijn berekent optimale ketel aanvoertemperatuur op basis van:

```
Aanvoer Temp = Basis Offset + (Coëfficiënt × Stooklijn Waarde)

Waarbij:
- Basis Offset: 40°C (vloer) of 55°C (radiatoren)
- Coëfficiënt: 1.0 standaard (instelbaar per zone)
- Stooklijn Waarde: f(kamer_doel, buiten_temp)
```

**Voorbeeld (Vloerverwarming)**:
- Buiten: 5°C
- Kamer Doel: 21°C
- Resultaat: ~35°C aanvoertemperatuur
- vs. Traditioneel: 50°C+ (verspilt 30% energie!)

**Voorbeeld (Radiatoren)**:
- Buiten: 5°C
- Kamer Doel: 21°C
- Resultaat: ~58°C aanvoertemperatuur
- vs. Vast: 70°C (verspilt 15-20% energie!)

---

## 🔧 Geavanceerd Afstellen (Power Users)

### Coëfficiënt Aanpassing per Zone

Als een zone te langzaam of te snel opwarmt:

```bash
# API call om coëfficiënt aan te passen
curl -X POST "http://jouw-ha:8123/api/smart_heating/areas/{area_id}/heating_curve" \
  -H "Authorization: Bearer JOUW_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"heating_curve_coefficient": 1.2}'
```

- **Verhogen** (1.2-1.5): Voor grotere radiatoren of betere isolatie
- **Verlagen** (0.8-0.9): Voor kleinere radiatoren of slechte isolatie

### PWM Configuratie

Voor ketels zonder modulatie-ondersteuning:

1. Schakel in **Globale Instellingen → Geavanceerde Besturing → PWM**
2. Standaard cyclus: 60-600 seconden AAN/UIT
3. Past automatisch duty cycle aan op basis van setpoint

**Resultaat**: Benadert modulatiegedrag op eenvoudige aan/uit ketels

### PID Auto-Tuning

Voor nauwkeurige temperatuurregeling:

1. Schakel in **Globale Instellingen → Geavanceerde Besturing → PID**
2. Systeem leert optimale gains automatisch
3. Vermindert overshoot en temperatuuroscillatie

**Best voor**: Systemen met trage thermische respons (vloerverwarming)

### OPV Kalibratie

Voorkomt overshoot bij lage-belasting condities:

```bash
# Voer kalibratieroutine uit
curl -X POST "http://jouw-ha:8123/api/smart_heating/opentherm/calibrate" \
  -H "Authorization: Bearer JOUW_TOKEN"
```

**Wanneer te gebruiken**: Veel gesloten radiatorkranen waardoor retourtemp snel stijgt

---

## 📈 Optimalisatie Monitoren

### 1. OpenTherm Dashboard

Bekijk real-time ketel metrics:
- Modulatieniveau (streef naar 20-40% voor vloer, 40-60% voor radiatoren)
- Aanvoertemperatuur (moet overeenkomen met stooklijn output)
- Retourtemperatuur (moet 10-15°C onder aanvoer zijn)
- Vlam status (minder aan/uit cycli = beter)

### 2. Efficiency Rapporten

Navigeer naar **Analytics → Efficiency Rapporten**:
- Energiescore: 0-100 (80+ is uitstekend)
- Verwarmingscycli: Minder is beter
- Temperatuurafwijking: Lager is beter
- Slimme aanbevelingen: Volg suggesties

### 3. Log Analyse

Controleer logs voor optimalisatie bevestiging:
```
OpenTherm gateway: Boiler ON, setpoint=37.2°C (overhead=10.0°C, 1 vloerverwarming, 0 radiatoren)
```

**Goede tekenen**:
- Setpoints komen overeen met stooklijn formule
- Overhead komt overeen met verwarmingstype
- Modulatieniveaus stabiel (niet wisselen 0-100%)

---

## ⚠️ Veiligheidsnota's

Alle optimalisatiefuncties respecteren veiligheidslimieten:

- ✅ Vorstbescherming: Minimum 7°C (configureerbaar)
- ✅ Maximale aanvoertemp: 80°C harde limiet
- ✅ Nooduitschakeling: Veiligheidssensoren (rook/CO)
- ✅ Handmatige override: Altijd beschikbaar op thermostaat

---

## 🆚 SAT vs Smart Heating: Belangrijkste Verschillen

| Aspect | SAT | Smart Heating | Notities |
|--------|-----|---------------|----------|
| **Standaard Status** | Optimalisaties AAN | Optimalisaties AAN (bij OpenTherm config) | Smart Heating auto-enable |
| **Multi-Zone** | Enkele zone focus | Volledige multi-zone ondersteuning | Zones kunnen verschillende types hebben |
| **UI** | Minimaal | Volledig React dashboard | Real-time monitoring |
| **Installatie** | Handmatige setup | HACS + GUI config | Eenvoudigere setup |
| **Device Ondersteuning** | Alleen MQTT | Universeel (elke HA integratie) | Werkt met Nest, Ecobee, etc. |

---

## 📚 Aanvullende Bronnen

- **Architectuur**: [docs/nl/ARCHITECTURE.md](ARCHITECTURE.md) - Technische diepgang
- **Geavanceerde Besturing**: [docs/nl/ADVANCED_CONTROL.md](ADVANCED_CONTROL.md) - Gedetailleerde instellingen
- **OpenTherm**: [docs/nl/OPENTHERM.md](OPENTHERM.md) - Gateway integratie gids
- **API Referentie**: [README.nl.md](../../README.nl.md#rest-api) - Programmatische besturing

---

## 🎓 Pro Tips

1. **Start Eenvoudig**: Laat stooklijn 1-2 dagen draaien voordat je PID/PWM inschakelt
2. **Monitor Logs**: Controleer modulatieniveaus en cyclustellingen dagelijks voor eerste week
3. **Stel Geleidelijk Bij**: Pas coëfficiënten alleen met 0.1-0.2 incrementen aan
4. **Seizoensaanpassing**: Mogelijk verschillende coëfficiënten nodig zomer vs winter
5. **Vloerverwarming**: Geduld! Thermische massa betekent 2-3 uur responstijden

---

## 🆘 Probleemoplossing

**"Zone warmt te langzaam op"**
- Verhoog `heating_curve_coefficient` met 0.2
- Controleer verwarmingstype is correct ingesteld
- Verifieer ketel bereikt berekende setpoint

**"Zone overschrijdt doel"**
- Verlaag `heating_curve_coefficient` met 0.1
- Schakel PID in voor strakkere regeling
- Voer OPV kalibratie uit

**"Ketel schakelt te veel"**
- Schakel PWM in als ketel geen modulatie heeft
- Verhoog hysterese (0.5 → 0.8°C)
- Controleer minimum setpoints worden afgedwongen

**"Geen optimalisatie actief"**
- Verifieer OpenTherm gateway is geselecteerd in Globale Instellingen
- Controleer logs voor "Auto-enabled heating curve" bericht
- Zorg dat `advanced_control_enabled` waar is

---

## ✅ Verificatie Checklist

Na setup, bevestig optimalisatie is actief:

- [ ] OpenTherm gateway geselecteerd in Globale Instellingen
- [ ] "Auto-enabled heating curve" verschijnt in logs
- [ ] Verwarmingstypes geconfigureerd per zone (vloer vs radiatoren)
- [ ] Ketel setpoints komen overeen met stooklijn formule (controleer logs)
- [ ] Modulatieniveaus passend voor verwarmingstype
- [ ] Energiescore verbetert in Efficiency Rapporten (na 7 dagen)

---

**Laatst Bijgewerkt**: December 2025 (v0.5.13+)
**Compatibiliteit**: Vereist OpenTherm Gateway integratie in Home Assistant
