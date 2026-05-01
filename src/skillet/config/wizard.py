"""Interactive global configuration (questionary)."""

from __future__ import annotations

import click
import questionary

from skillet.config.settings import (
    AGENT_KEYS,
    AGENT_LABELS,
    agent_checkbox_instruction,
    agent_multiselect_choice_label,
    agent_multiselect_prompt_global,
    agent_reference_hint_line,
    format_agent_target_mapping_summary,
    get_config_path,
    load_config,
    save_config,
)


def prompt_agent_targets(
    *,
    message: str,
    hint_previous_keys: list[str] | None = None,
) -> list[str]:
    """Multi-select agent keys; all rows start unchecked; at least one required."""
    full_message = message.rstrip()
    if hint_previous_keys:
        hint = agent_reference_hint_line(hint_previous_keys)
        if hint:
            full_message = f"{full_message}\n{hint}"

    choices = [
        {"name": agent_multiselect_choice_label(k), "value": k, "checked": False}
        for k in AGENT_KEYS
    ]

    def _need_at_least_one(selected: list[str]) -> bool | str:
        if len(selected) >= 1:
            return True
        return (
            "Select at least one agent (Space toggles a row, Enter confirms). "
            "You cannot continue with none selected."
        )

    while True:
        picked = questionary.checkbox(
            full_message,
            choices=choices,
            validate=_need_at_least_one,
            instruction=agent_checkbox_instruction(),
        ).ask()
        if picked is None:
            raise KeyboardInterrupt
        filtered = [p for p in picked if p in AGENT_LABELS]
        if filtered:
            return filtered


def _ask_text(message: str, default: str) -> str:
    ans = questionary.text(message, default=default).ask()
    if ans is None:
        return default
    return ans


def run_config_wizard() -> None:
    """Interactive wizard: default agent targets and optional GitHub token for Skillet."""
    config_path_existed = get_config_path().exists()
    config = load_config()

    prior = config.get("agent")
    if not isinstance(prior, list) or not prior:
        prior = list(AGENT_KEYS)
    prior_norm = [k for k in prior if k in AGENT_LABELS]
    agent_selected = prompt_agent_targets(
        message=agent_multiselect_prompt_global(),
        hint_previous_keys=prior_norm if config_path_existed else None,
    )
    config["agent"] = agent_selected

    config["github_token"] = _ask_text(
        "GitHub token (optional; private skill repos and API limits for `skillet add`):",
        config.get("github_token", "") or "",
    )

    save_config(config)

    _print_config_wizard_footer(config)


def _print_config_wizard_footer(config: dict) -> None:
    click.echo("\n✓ Configuration saved to ~/.config/skillet/config.json")

    agents = config.get("agent")
    if isinstance(agents, list) and agents:
        summary = format_agent_target_mapping_summary(
            [k for k in agents if k in AGENT_LABELS]
        )
        if summary:
            click.echo(f"\n{summary}")

    click.echo(
        "\nSkillet reads `GITHUB_TOKEN` from the environment or this file when "
        "fetching GitHub skill sources. Set it in `.env` or your shell if you prefer."
    )
    click.echo("  GITHUB_TOKEN — optional")

    if (config.get("github_token") or "").strip():
        click.echo(
            "\nA token was saved in ~/.config/skillet/config.json. "
        )
    else:
        click.echo("\nNo GitHub token was entered; add one when you use private `skillet add` sources.")
