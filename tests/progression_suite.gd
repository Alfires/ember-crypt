extends SceneTree
var checks := 0
var failures := 0

func check(value: bool, message: String):
	checks += 1
	if not value:
		failures += 1
		print("FAIL: ", message)

func _initialize():
	if not FileAccess.file_exists("res://scripts/progression.gd"):
		print("FAIL: progression service missing")
		quit(1)
		return
	var model = load("res://scripts/progression.gd").new()
	check(model.configure("user://progress-test.json"), "configure new save")
	check(model.lifetime_xp == 0 and model.run_xp == 0, "fresh progress starts empty")
	check(model.award_exploration("field"), "first field discovery awards XP")
	check(not model.award_exploration("field"), "duplicate discovery rejected")
	check(not model.award_exploration("invented"), "unknown discovery rejected")
	check(model.lifetime_xp == 25 and model.run_xp == 25, "one discovery grants exactly 25 XP")
	check(model.pending_choices() == 0, "no early level-up")
	for area in ["farm", "woodland", "watchtower"]:
		model.award_exploration(area)
	check(model.pending_choices() == 1, "100 run XP earns one choice")
	check(not model.choose_upgrade("invented"), "unknown upgrade rejected")
	check(model.choose_upgrade("damage"), "one pending upgrade applied")
	check(not model.choose_upgrade("damage"), "double confirmation rejected")
	check(model.stats().damage == 12, "damage bonus applied to base stats")
	check(model.save(), "save progression atomically")
	var restored = load("res://scripts/progression.gd").new()
	check(restored.configure("user://progress-test.json") and restored.lifetime_xp == 100, "lifetime XP survives reload")
	check(restored.run_xp == 0 and restored.stats().damage == 10, "run state is not permanent")
	check(not restored.award_exploration("field"), "relaunch cannot farm lifetime discovery XP")
	check(model.equip("teal"), "earned cosmetic equips")
	check(not model.equip("unknown"), "unknown cosmetic rejected")
	check(model.save(), "equipped cosmetic saves")
	check(restored.configure("user://progress-test.json") and restored.equipped == "teal", "cosmetic survives reload")
	var old_xp = model.lifetime_xp
	model.new_run()
	check(model.run_xp == 0 and model.pending_choices() == 0 and model.stats().damage == 10, "new run clears XP/choices/upgrades")
	check(model.lifetime_xp == old_xp, "new run keeps lifetime XP")
	check(not model.award_exploration("field"), "retry cannot farm discoveries")
	# Reach multiple thresholds through real bounded discovery IDs.
	for area in model.DISCOVERIES:
		model.award_exploration(area)
	check(model.pending_choices() >= 2, "multiple earned choices queue")
	while model.pending_choices() > 0:
		check(model.choose_upgrade("health"), "queued health upgrade applies")
	check(model.stats().max_health > 100, "health bonuses reflected")
	check(model.reset_progress(), "explicit service reset succeeds")
	check(model.lifetime_xp == 0 and model.equipped == "amber" and model.run_xp == 0, "reset clears all progression")
	# Unknown versions and malformed JSON must remain byte-for-byte recoverable.
	for text in ['{"schema_version":999}', '{broken', '{"schema_version":1,"lifetime_xp":-1}']:
		var file = FileAccess.open("user://invalid.json", FileAccess.WRITE)
		file.store_string(text)
		file.close()
		var invalid = load("res://scripts/progression.gd").new()
		check(not invalid.configure("user://invalid.json"), "invalid/future save rejected")
		check(not invalid.save() and not invalid.reset_progress(), "invalid original cannot be overwritten")
		check(FileAccess.get_file_as_string("user://invalid.json") == text, "original bytes preserved")
	var blocked = load("res://scripts/progression.gd").new()
	check(blocked.configure("res://missing-parent/progress.json"), "absent file begins unsaved session")
	blocked.award_exploration("field")
	check(not blocked.save() and blocked.dirty and not blocked.error.is_empty(), "disk write failure retains pending progress and error")
	print("Progression: %s checks, %s failures" % [checks, failures])
	quit(1 if failures else 0)
