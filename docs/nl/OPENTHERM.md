# OpenTherm Gateway (opentherm_gw) Integratie

Smart Heating integreert met de Home Assistant OpenTherm Gateway integratie om globale ketelbesturing over zones mogelijk te maken.

Belangrijk:
- Smart Heating verwacht de OpenTherm Gateway integratie `id` (slug), niet de climate entity ID. De `id` is bijvoorbeeld `gateway1`.
- Voeg een gateway toe via Instellingen → Apparaten & Diensten → Integratie toevoegen → OpenTherm Gateway, vul de velden in (naam, pad/URL, ID) en gebruik een slug voor het ID-veld.
- Na het toevoegen van de OTGW config entry, ga naar Smart Heating → Instellingen → OpenTherm en selecteer de gateway uit de dropdown, klik Opslaan.
- Voor geautomatiseerde setups gebruik de Home Assistant REST config flow voor veilige configuratie.

Probleemoplossing:
- Als de OTGW integratie niet aanwezig is, zal de dropdown leeg zijn.
- Als je MQTT gebruikt om een OTGW te simuleren, zal Smart Heating specifiek OTGW-gedrag missen; gebruik bij voorkeur de OpenTherm integratie.
