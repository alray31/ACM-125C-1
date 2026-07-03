# ACM-125C-1

Intégration Home Assistant (HACS, custom repository) pour l'éclairage RF 433.92 MHz de l'écumoire de piscine. Elle remplace la logique qui était auparavant codée en dur dans le firmware ESPHome (button/switch/select avec tous les codes `rc_switch`) en s'appuyant sur la nouvelle plateforme d'entité **`radio_frequency`** introduite dans **Home Assistant 2026.5** et **ESPHome (`ir_rf_proxy`)**.

## Architecture

- **Côté ESPHome** : le firmware ne fait plus qu'exposer un émetteur RF brut (`radio_frequency:` / `platform: ir_rf_proxy`) — voir `esphome-piscine-eclairage.yaml`. Il ne connaît plus aucun code de télécommande.
- **Côté Home Assistant** : cette intégration ("consumer integration") découvre l'émetteur RF compatible (433.92 MHz, OOK) exposé par ESPHome, et envoie les commandes RF via `radio_frequency.async_send_command`.

C'est exactement le modèle documenté par Home Assistant pour les intégrations comme *Honeywell String Lights* ou *Novy Cooker Hood*, sorties dans la même release.

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

## Important : vérifier l'encodage avant de tout migrer

Les 24 bits de chaque code (`rc_switch`) viennent tels quels de l'ancien YAML. Ils sont réencodés en timings bruts (microsecondes) dans `custom_components/acm_125c_1/codes.py`, avec les mêmes paramètres que l'ancien firmware :

- `pulse_length`: 260 µs
- `sync`: (3, 1) — repris de votre YAML
- `zero`/`one`: (1,3) / (3,1) — valeurs par défaut du protocole `rc_switch` d'ESPHome, non surchargées dans votre YAML d'origine
- 10 répétitions, 7510 µs d'écart entre chaque répétition

Ces valeurs par défaut (`zero`/`one`) sont documentées de longue date côté ESPHome, mais elles n'étaient pas visibles explicitement dans votre configuration puisque vous ne les surchargiez pas. **Testez d'abord `button.pair` et `switch.on_off`** : si la piscine réagit exactement comme avant, l'encodage est bon et vous pouvez faire confiance aux selects (intensité/effet/couleur) qui utilisent le même encodeur.

## Dépendances

- `radio_frequency` (intégration cœur Home Assistant, disponible depuis 2026.5)
- Paquet Python [`rf-protocols`](https://github.com/home-assistant-libs/rf-protocols) (déclaré dans `manifest.json`, installé automatiquement par HA)
