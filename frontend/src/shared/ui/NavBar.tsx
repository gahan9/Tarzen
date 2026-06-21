// SPDX-License-Identifier: MIT
/**
 * Primary navigation. Each link pairs a decorative (aria-hidden) emoji with a
 * real text label, and the active route is marked with `aria-current="page"`.
 */

import { NavLink } from "react-router-dom";

import { Emoji } from "./Emoji";
import { type EmojiKey } from "./emojiMap";

interface NavItem {
  to: string;
  label: string;
  emoji: EmojiKey;
}

const ITEMS: readonly NavItem[] = [
  { to: "/", label: "Calculator", emoji: "calculator" },
  { to: "/savings", label: "Add savings", emoji: "savings" },
  { to: "/leaderboard", label: "Leaderboard", emoji: "leaderboard" },
  { to: "/profile", label: "Profile", emoji: "profile" },
];

export function NavBar() {
  return (
    <nav className="app-nav" aria-label="Primary">
      <ul className="app-nav-list">
        {ITEMS.map((item) => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                isActive ? "app-nav-link app-nav-link--active" : "app-nav-link"
              }
            >
              <Emoji name={item.emoji} className="app-nav-emoji" />
              <span>{item.label}</span>
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
