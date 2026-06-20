---
name: twitter-algorithm-optimizer
aliases:
  - tweet-optimizer
  - x-algorithm
version: "1.0"
description: >-
  Analyze and rewrite tweets/X posts for reach and engagement using a
  clean-room model of publicly documented recommendation-ranking principles.
  Use to improve drafts, diagnose weak posts, and align content with how
  ranking systems reward early engagement and penalize negative signals.
platforms:
  cursor: true
  claude: true
  copilot: true
  codex: true
  antigravity: true
scope:
  - "**/*.md"
  - "**/*.txt"
triggers:
  - "optimize this tweet"
  - "improve engagement on this post"
  - "rewrite this for reach"
  - "why is this tweet underperforming"
  - "make this thread perform better"
license: MIT
---

# Twitter / X Algorithm Optimizer (clean-room)

## Purpose
Help draft and rewrite posts to maximize reach and engagement, using an
original, clean-room description of widely documented social-ranking
principles. This skill contains no third-party (AGPL) source — only general
principles restated independently and actionable guidance.

## When to Use
- Optimizing a tweet/X-post draft before publishing.
- Diagnosing why a post likely underperformed.
- Rewriting posts or threads to better fit ranking incentives.

## When NOT to Use
- Generating spam, engagement-bait, or content that violates platform rules.
- Buying/faking engagement — covered below as a penalized behavior.

## Ranking model (general principles)
Modern feed ranking scores each candidate post by a weighted sum of *predicted*
user reactions, then applies boosts and penalties. Treat these as directional
heuristics, not exact weights:

- **Positive signals (drive reach):** replies — especially replies the author
  then engages with — profile clicks that lead to follows, reposts/quotes,
  dwell time and (for video) watch time, and likes. Conversation-style
  engagement is generally weighted higher than a passive like.
- **Negative signals (suppress reach, often heavily):** "not interested" /
  "show less", mutes, blocks, reports, and unfollows shortly after viewing.
  A single strong negative can outweigh several positives.
- **Early velocity:** engagement in the first minutes after posting strongly
  influences whether the post is expanded to wider, out-of-network audiences.
- **Author reputation:** consistent positive engagement and follower
  interaction history raise baseline distribution.
- **Recency:** scores decay with age; freshness matters.
- **In-network vs out-of-network:** content first reaches followers; clearing
  the early-engagement bar unlocks recommendation to non-followers.

## Content heuristics that tend to help
- **Native over outbound:** keep people on-platform. Put external links in a
  reply rather than the primary post when reach matters.
- **Native media:** original images/video and well-cropped visuals lift dwell
  time. Add captions/alt text.
- **Invite replies:** ask a genuine question or take a clear stance; reply to
  early commenters quickly to compound conversation signal.
- **Lead with a strong hook:** first line must earn the tap-to-expand; front-load
  the payoff, avoid slow build-ups.
- **Readable formatting:** short lines, one idea per line, minimal hashtags
  (1-2 max; walls of hashtags read as spam).
- **Threads:** put the most compelling claim in tweet 1; each subsequent tweet
  should stand alone enough to be quotable.
- **Timing:** post when your audience is active to maximize early velocity.

## Behaviors that get penalized (avoid)
- Engagement-bait phrasing ("RT if…", "reply YES"), follower-for-follower asks.
- Excessive hashtags, repeated near-duplicate posts, automated mass-posting.
- Outbound links in the primary post when the goal is reach.
- Coordinated/fake engagement — detectable and strongly demoted.

## Instructions
1. Identify the post's **goal**: reach, replies, profile/follows, clicks, or
   conversions. Optimize for that objective, not vanity metrics.
2. Score the draft against the positive/negative signals above; name the
   single biggest weakness.
3. Produce **2-3 rewrites**: (a) hook-optimized, (b) conversation-optimized,
   (c) media/format-optimized. Keep the author's voice.
4. For each rewrite, give a one-line rationale tied to a ranking principle.
5. Add a short pre-publish checklist (hook, media, reply-prompt, link
   placement, hashtag count, timing).

## Output Format
```
Goal: <objective>
Biggest weakness: <one line>

Rewrite A (hook): <text>
  why: <principle>
Rewrite B (conversation): <text>
  why: <principle>
Rewrite C (format/media): <text>
  why: <principle>

Pre-publish checklist:
- [ ] Hook earns the expand
- [ ] Native media + alt text
- [ ] Reply prompt / clear stance
- [ ] Links in reply, not primary post
- [ ] <= 2 hashtags
- [ ] Posting at a high-activity time
```

## References
- General, publicly discussed social-feed ranking concepts (engagement
  prediction, early velocity, negative-feedback suppression, recency decay).
  No third-party source code or text is reproduced in this skill.
