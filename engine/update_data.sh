#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
W="$ROOT/data/wiki"; mkdir -p "$W/t"
BASE="https://taskbarhero.wiki/data"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
TOP="heroes monsters skills passive_skills attributes buffs status_effects items items_detail gear_types grades runes rune_tree stages stat_strings mechanics catalog manifest"
SUB="attribute_groups buff_groups crafting_recipes cube_levels cube_recipes cube_sub_recipes currencies drops extraction_costs gear gear_type_scales inventory item_groups item_level_scales item_type_scales levels materials offline_rewards pet_stats pets rune_levels skill_levels skins sounds stage_levels stash stat_mod_groups stat_mods storage synthesis_drops synthesis_recipes trading_stash unique_mods"

ok=0; fail=0
get(){
  if curl -s -f -A "$UA" -m 60 "$1" -o "$2"; then ok=$((ok+1)); else fail=$((fail+1)); echo "  FAIL $1"; fi
}
echo "refreshing top-level tables..."
for t in $TOP; do get "$BASE/$t.json" "$W/$t.json"; done
echo "refreshing lookup (t/) tables..."
for t in $SUB; do get "$BASE/t/$t.json" "$W/t/$t.json"; done
echo "downloaded OK=$ok FAIL=$fail"

WIKI_V=$(grep -o '"version"[^,]*' "$W/manifest.json" 2>/dev/null | head -1 | grep -o '[0-9.]*' | head -1)
SAVE="C:/Users/${USER:-${USERNAME:-}}/AppData/LocalLow/TesseractStudio/TaskbarHero/Version.txt"
INSTALL_V=$(cat "C:/Program Files (x86)/Steam/steamapps/common/TaskbarHero/Version.txt" 2>/dev/null | tr -d '\r\n ')
echo "wiki version: ${WIKI_V:-?}  | installed game: ${INSTALL_V:-?}"
[ -n "$WIKI_V" ] && [ -n "$INSTALL_V" ] && [ "$WIKI_V" != "$INSTALL_V" ] && \
  echo " DRIFT: wiki $WIKI_V != game $INSTALL_V — re-validate formulas if balance changed."
echo "next: python engine/build_bundle.py && python engine/download_assets.py && node engine/test.cjs"
