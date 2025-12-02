# Changelog - Crypto Trading Bot

## 2025-11-30 - Corrections Dashboard

### 🐛 Bugs Corrigés

#### 1. Graphique démesuré
**Problème** : Le graphique Balance History prenait toute la hauteur de l'écran
**Solution** :
- Ajout de `max-height: 400px` sur `.chart-card`
- Ajout de `max-height: 320px !important` sur le canvas
- Ajout de `position: relative` pour meilleur contrôle

```css
.chart-card {
    min-height: 300px;
    max-height: 400px;
    position: relative;
}

.chart-card canvas {
    max-height: 320px !important;
    width: 100% !important;
}
```

#### 2. Débordement horizontal
**Problème** : Potentiel débordement sur mobile
**Solution** :
- Ajout de `overflow-x: hidden` sur body et container

#### 3. Listes sans limite de hauteur
**Problème** : Les sections Trades, Positions, AI pouvaient devenir énormes
**Solution** :
- `.trades-list`: max-height 500px avec scroll
- `.positions-list`: max-height 400px avec scroll
- `.ai-list`: max-height 600px avec scroll

### ✨ Améliorations

#### Scrollbars personnalisées
Ajout de scrollbars stylisées pour les listes :
- Largeur réduite (8px)
- Couleurs cohérentes avec le thème
- Hover effect

#### Responsive amélioré
Sur mobile (< 768px) :
- Graphiques adaptés : max-height 300px
- Tables réduites : font-size 0.85rem
- Listes limitées : max-height 300-400px

### 📱 Responsive

| Élément | Desktop | Mobile |
|---------|---------|--------|
| Graphique | 400px max | 300px max |
| Canvas | 320px max | 250px max |
| Trades List | 500px max | 400px max |
| Positions | 400px max | 300px max |
| AI List | 600px max | 300px max |

## État Actuel

✅ Dashboard responsive et bien proportionné
✅ Graphiques de taille appropriée
✅ Scroll fluide avec scrollbars stylisées
✅ Optimisé pour mobile et desktop

## Prochaines Améliorations Possibles

- [ ] Ajouter des animations de transition
- [ ] Mode sombre/clair toggle
- [ ] Graphiques supplémentaires (profit par paire, etc.)
- [ ] Notifications push
- [ ] Export des données en CSV
- [ ] Graphiques interactifs (zoom, etc.)
