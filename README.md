# ACM-125C-1

Intégration Home Assistant (HACS, custom repository) pour l'éclairage RF 433.92 MHz de la piscine. Elle remplace la télécommande RF ACM-125C-1 en s'appuyant sur la nouvelle plateforme d'entité **`radio_frequency`** introduite dans **Home Assistant 2026.5** et **ESPHome (`ir_rf_proxy`)**.

## Architecture

- Cette intégration découvre l'émetteur RF compatible (433.92 MHz, OOK) exposé par ESPHome ou autre émmeteur RF compatible, et envoie les commandes RF via `radio_frequency.async_send_command`.

## Installation

1. Copier le dossier `custom_components/acm_125c_1` dans la config Home Assistant (ou publier ce dépôt sur GitHub et l'ajouter comme *custom repository* HACS de type "Integration").
2. Installer via HACS puis redémarrer Home Assistant.
3. Flasher l'ESP avec `esphome-piscine-eclairage.yaml` (adapter le nom du device, wifi, etc. — ce fichier ne contient que le bloc RF).
4. **Paramètres → Appareils et services → Ajouter une intégration → ACM-125C-1**. Choisir l'entité `radio_frequency` de l'ESP dans la liste (elle n'apparaît que si l'ESPHome est déjà intégré et expose bien l'entité 433.92 MHz OOK).

## Entités créées

- `button.pair` — envoie le code d'appairage.
- `switch.on_off` — allume/éteint (état "assumed", restauré au redémarrage — la RF est unidirectionnelle, HA ne peut pas confirmer l'état réel de la lumière).
- `select.light_intensity_or_effect_speed` — 1 à 8.
- `select.effect` — Gradual / Wave / Jumping / Fading / Wave + Jumping / White / Color.
- `select.color` — Purple / Blue / Cyan / Green / Yellow / Orange / Red / Pink.

## Dépendances

- `radio_frequency` (intégration cœur Home Assistant, disponible depuis 2026.5)
- Paquet Python [`rf-protocols`](https://github.com/home-assistant-libs/rf-protocols) (déclaré dans `manifest.json`, installé automatiquement par HA)
