# Nest-achtige Thermostaatfuncties (Ontwerp & Implementatie Roadmap)

Dit document beschrijft een roadmap en ontwerp voor het implementeren van Nest-achtige thermostaatfunctionaliteit in Smart Heating. Het is bedoeld om toekomstige ontwikkeling te begeleiden met prioriteiten, aanpak en veiligheidsvoorwaarden.

## Doelen
- Implementeer Nest-achtige functies incrementeel, veilig, modulair en opt-in.
- Prioriteer functies die comfort en energie besparen, terwijl ketelveiligheid wordt gewaarborgd.
- Bied tests, observatie en terugdraaimogelijkheden voor elke stap.

## Featureset (Hoog niveau)
1. Presence-aware learning
2. Auto-planning en leren
3. Energiegeoptimaliseerde besturing
4. Auto-away (presence afleiding)
5. Weersafhankelijke aanpassingen
6. Adaptive gains en PID tuning
7. Veilig leren dat limieten respecteert
8. Gebruikersfeedback voor geleerde aanpassingen

## MVP
- Per-zone LearningAgent class die gebruikerswijzigingen (handmatige temperatuuraanpassingen) gebruikt en eenvoudige voorspellingen doet
- UI: Suggesties tab in Zone instellingen

## Architectuur, Veiligheid en Uitrol
Zie `docs/en/NEST_THERMOSTAT_FEATURES.md` (English) voor details.

Auteur: Smart Heating Team
Datum: 2025-12-10
