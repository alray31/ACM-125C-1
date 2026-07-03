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
- `light.<device>` — une seule entité `light` regroupant tout le reste (voir ci-dessous). Remplace les anciennes `switch.on_off`, `select.color`, `select.effect` et `select.light_intensity_or_effect_speed`, qui n'existent plus.

### Le light entity

Home Assistant affiche nativement une roue de couleur pour les lights en mode couleur HS, donc plus besoin de select pour la couleur :

- **Roue de couleur** : au clic, envoie le code "effect color", attend 0.3 s (`COLOR_COMMAND_DELAY_S` dans `const.py`), puis envoie le code RF correspondant à la position sur la roue (64 positions possibles, encodage continu — voir "Roue de couleur : l'encodage RF" plus bas).
- **Mode blanc** : envoie simplement le code "effect white".
- **Slider de luminosité** : envoie un des 8 codes "intensity or effect speed" (paliers de 12.5%). C'est le même bouton physique que la télécommande utilise soit pour l'intensité (en mode couleur/blanc) soit pour la vitesse d'effet (quand un effet d'animation est actif) — Home Assistant ne permet pas de renommer dynamiquement le libellé du slider natif du light card, donc ce double-sens n'est documenté que **ici**, pas dans l'interface.
- **Liste d'effets** (menu natif "Effect" du light) : Gradual, Wave, Jumping, Fading, Wave + Jumping. ("Color" et "White" ne sont pas dans cette liste puisqu'ils sont gérés par la roue de couleur / le mode blanc directement.)

## Roue de couleur : l'encodage RF

Contrairement aux autres commandes (24 bits, table fixe), la roue de couleur physique encode une position continue sur 25 bits :

```
préfixe constant (17 bits) + valeur 7 bits (64 +