// SPDX-License-Identifier: MIT
/**
 * Typed, semantic emoji map.
 *
 * Every emoji used in the UI is a native unicode glyph looked up by a stable
 * semantic key — never an image sprite, so it adds zero bytes to the bundle and
 * scales with the user's font. Emoji are decorative: render them through the
 * {@link Emoji} component so each one is `aria-hidden` and paired with a real
 * text label. This module is platform-agnostic data; the component lives in
 * `Emoji.tsx` to keep the (Fast-Refresh-sensitive) component boundary clean.
 */

/** Semantic keys for every emoji surface in the app. */
export type EmojiKey =
  // Navigation
  | "calculator"
  | "savings"
  | "leaderboard"
  | "profile"
  // Savings sources / modes
  | "carpool"
  | "bus"
  | "rail"
  | "manual"
  | "import"
  | "ticket"
  | "verified"
  // Gamification
  | "points"
  | "streak"
  | "trophy"
  | "tip"
  | "sprout"
  | "tree"
  | "region"
  | "globe"
  // Ranks
  | "rank1"
  | "rank2"
  | "rank3"
  // Badges
  | "badge_bronze"
  | "badge_silver"
  | "badge_gold"
  | "badge_week_warrior"
  | "badge_fortnight_hero"
  | "badge_verified_rider";

/** Stable semantic-key -> native unicode emoji. */
export const EMOJI: Record<EmojiKey, string> = {
  calculator: "\u{1F9EE}", // abacus
  savings: "\u{1F33F}", // herb
  leaderboard: "\u{1F3C6}", // trophy
  profile: "\u{1F464}", // bust in silhouette
  carpool: "\u{1F697}", // automobile
  bus: "\u{1F68C}", // bus
  rail: "\u{1F686}", // train
  manual: "\u{270D}\u{FE0F}", // writing hand
  import: "\u{1F4C4}", // page facing up
  ticket: "\u{1F39F}\u{FE0F}", // admission tickets
  verified: "\u{2705}", // check mark button
  points: "\u{1F31F}", // glowing star
  streak: "\u{1F525}", // fire
  trophy: "\u{1F3C6}", // trophy
  tip: "\u{1F4A1}", // light bulb
  sprout: "\u{1F331}", // seedling
  tree: "\u{1F333}", // deciduous tree
  region: "\u{1F4CD}", // round pushpin
  globe: "\u{1F30D}", // globe showing Europe-Africa
  rank1: "\u{1F947}", // 1st place medal
  rank2: "\u{1F948}", // 2nd place medal
  rank3: "\u{1F949}", // 3rd place medal
  badge_bronze: "\u{1F949}", // 3rd place medal
  badge_silver: "\u{1F948}", // 2nd place medal
  badge_gold: "\u{1F947}", // 1st place medal
  badge_week_warrior: "\u{1F525}", // fire
  badge_fortnight_hero: "\u{2694}\u{FE0F}", // crossed swords
  badge_verified_rider: "\u{2705}", // check mark button
};

/** Emoji used to decorate anonymous animal handles, keyed by animal name. */
export const ANIMAL_EMOJI: Record<string, string> = {
  fox: "\u{1F98A}",
  owl: "\u{1F989}",
  otter: "\u{1F9A6}",
  deer: "\u{1F98C}",
  hawk: "\u{1F985}",
  wolf: "\u{1F43A}",
  bear: "\u{1F43B}",
  lynx: "\u{1F408}",
  hare: "\u{1F407}",
  swan: "\u{1F9A2}",
  bee: "\u{1F41D}",
  crane: "\u{1F426}",
  panda: "\u{1F43C}",
  koala: "\u{1F428}",
  tiger: "\u{1F405}",
  whale: "\u{1F40B}",
};

/** Ordered fallback pool for deterministic emoji when no animal is detected. */
const ANIMAL_EMOJI_POOL = Object.values(ANIMAL_EMOJI);

/** djb2 hash → small, stable integer for deterministic client-side choices. */
function hashString(value: string): number {
  let hash = 5381;
  for (let i = 0; i < value.length; i += 1) {
    hash = ((hash << 5) + hash + value.charCodeAt(i)) >>> 0;
  }
  return hash;
}

/**
 * Resolve a decorative emoji for an anonymous handle.
 *
 * Prefers a server-provided emoji, then a known animal name embedded in the
 * handle (e.g. "SwiftFox-4821"), then a deterministic hash of the handle so the
 * same user always gets the same glyph.
 */
export function emojiForHandle(handle: string, provided?: string): string {
  if (provided) return provided;
  const lower = handle.toLowerCase();
  for (const [animal, glyph] of Object.entries(ANIMAL_EMOJI)) {
    if (lower.includes(animal)) return glyph;
  }
  const index = hashString(handle) % ANIMAL_EMOJI_POOL.length;
  return ANIMAL_EMOJI_POOL[index] ?? EMOJI.profile;
}

/** Emoji for a leaderboard rank: medals for the top three, else a sprout. */
export function emojiForRank(rank: number): string {
  switch (rank) {
    case 1:
      return EMOJI.rank1;
    case 2:
      return EMOJI.rank2;
    case 3:
      return EMOJI.rank3;
    default:
      return EMOJI.sprout;
  }
}

/** Emoji for a badge id; falls back to a generic medal for unknown ids. */
export function emojiForBadge(badgeId: string): string {
  const key = `badge_${badgeId}` as EmojiKey;
  return EMOJI[key] ?? EMOJI.trophy;
}
