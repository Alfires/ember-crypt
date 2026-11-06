"""An exploration objective loop authored entirely in the supported world IR."""


def set_value(key, value):
    return {"op": "save_set", "key": key, "value": value}


def condition(key, value, yes, no=None):
    return {"op": "if_saved", "key": key, "equals": value, "then": yes, "else": no or []}


def menu(page):
    return {"op": "menu", "page": page}


def add_loop(pages):
    relics = ["relic_watchtower", "relic_village", "relic_forecourt"]
    start = [set_value("run_active", True), set_value("run_xp", 0)]
    start += [set_value(key, False) for key in relics]
    start += [menu("objectives")]
    pages["overview"]["widgets"].insert(1, {
        "id": "start_run", "type": "button", "entity": "camp",
        "text": "Start / restart relic run (resets current relics)", "actions": start,
    })
    pages["overview"]["widgets"][0]["text"] = "Explore Ashen Vale, recover three relic seals and activate the crypt altar. This is an exploration objective loop, not combat. Starting/restarting clears current relics; completed-run count persists."
    def page(title, text):
        return {"title": title, "widgets": [{"id": "description", "type": "text", "text": text}]}
    pages["objectives"] = page("Relic expedition", "Use the brass relic plinths at the watchtower, village and forecourt. Then use the final altar in the guardian hall. Normal Comunicare interaction controls apply. No enemies or timed damage yet. Saves allow this objective run to resume; no mid-combat state is implied.")
    for key in ["run_active", *relics, "run_xp", "wins"]:
        pages["objectives"]["widgets"] += [
            {"id": key + "_label", "type": "text", "text": key.replace("_", " ").title()},
            {"id": key, "type": "text", "bind": "saved." + key},
        ]
    pages["locked"] = page("Objective unavailable", "Start a run at a station first. The final altar also requires all three relic seals. No reward was granted.")
    pages["victory"] = page("Expedition completed", "All three seals restored. The crypt altar is active and your completed-run count is saved on this PC. Return to a station to start another run. This is an exploration victory, not a guardian combat victory.")
    programs = {}
    for key in relics:
        award = [set_value(key, True), {"op": "save_add", "key": "run_xp", "value": 25}, menu("objectives")]
        programs[key] = [condition("run_active", True, [condition(key, True, [menu("objectives")], award)], [menu("locked")])]
    finish = [set_value("run_active", False), {"op": "save_add", "key": "wins", "value": 1}, menu("victory")]
    for key in reversed(relics):
        finish = [condition(key, True, finish, [menu("locked")])]
    programs["altar"] = [condition("run_active", True, finish, [menu("locked")])]
    return programs
