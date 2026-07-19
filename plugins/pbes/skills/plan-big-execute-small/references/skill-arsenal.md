# Skill selection

The Codex PBES package ships the coordinator skill. It can coordinate any
other skill that the current session exposes, whether built in, personal, or
provided by another plugin.

Before selecting another skill:

1. confirm it appears in the current available-skills list;
2. have the coordinator read its complete `SKILL.md` and mandatory references;
3. pass only assignment-relevant constraints to the subagent;
4. keep fan-out skills in the coordinator when nesting is unavailable;
5. warn the user when a material skill is missing, then continue with bounded
   judgment instead of pretending it was used.

Never install a missing dependency or plugin without authorization.

The full PBES arsenal remains in the Claude package while its Claude-specific
frontmatter is migrated to a dual-runtime contract. Track that work in:

https://github.com/TiagoSnows/claude-plugins/issues/2
