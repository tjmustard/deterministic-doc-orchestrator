<!--
Source brief for the `blog_post` worked example (tests/data/blog_post_example.yaml).
This is a real-feeling internal notes doc — the kind of raw material a writer turns
into a blog post — not a rendered DDO output. The example's evidence_bank entries
trace back to the facts recorded here, per the zero-hallucination constraint.
-->

# Content Brief: Why We Killed Our Daily Standup

**Prepared by:** Priya Nakamura, Eng Manager, Fernwood Robotics
**Date:** 2026.05.18
**Purpose:** Notes for a company blog post about moving the 14-person firmware team from a
live daily standup to an async written/video update.

## Background

The firmware team has run a daily 9:30am standup since the team was 4 people. By early 2026
the team had grown to 14 engineers across three time zones (Portland, Berlin, Bangalore).
The meeting slot only overlapped with "reasonable working hours" for 9 of the 14 people, so
5 engineers were either joining at 6am/11pm local time or skipping the meeting entirely.

## What we measured before changing anything

- Average standup length over the two weeks we timed it: 27 minutes for 14 people (about
  1.9 minutes of speaking time per person, once queueing and tangents are counted).
- We asked the team anonymously: "Does the daily standup usually surface a blocker you
  didn't already know about?" 3 of 14 said yes; 11 of 14 said no.
- Two engineers on the Bangalore sub-team said they had considered proposing they skip the
  live call entirely and just read the notes the next morning.

## What we changed (rolled out 2026.04.01)

- Replaced the live call with an async written update posted in a shared channel by 10am in
  each person's local time: what shipped yesterday, what's planned today, and any blocker,
  flagged with a `@blocked` tag that pings the on-call lead directly.
- Kept a single 15-minute live "sync huddle" twice a week (Tuesday/Thursday) for anything
  that genuinely needed live back-and-forth.
- Gave the on-call lead a standing rule: any `@blocked` tag gets a reply within 2 working
  hours, not "whenever the next standup is."

## Results after 6 weeks (measured 2026.05.15)

- Time spent in standup-related meetings dropped from about 27 minutes/day/person-average to
  roughly 6 minutes/day/person-average (two 15-minute huddles a week, divided across a 5-day
  week).
- Blockers flagged with `@blocked` got a first response in a median of 41 minutes, versus the
  old average of "next day's standup" (up to 24 hours).
- In the same anonymous follow-up survey, 12 of 14 engineers said they preferred the new
  format; the 2 who preferred the old format cited missing the "casual catch-up" feeling of
  a live call.
- One Bangalore engineer, quoted with permission: "I used to set an alarm for a meeting I
  wasn't going to talk in for more than 90 seconds. Now I write my update with my coffee and
  I'm not staring at a clock during someone else's evening."

## Angle for the post

Priya wants the post to be practical and a little irreverent — not "thought leadership," more
"here's exactly what we did and what happened, so you can steal it." She specifically wants
the post to end by pointing readers to the internal template Fernwood used for the async
update format, since several people who heard about this informally have asked for it.
