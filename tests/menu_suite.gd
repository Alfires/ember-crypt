extends SceneTree
var checks := 0
var failures := 0

func check(value: bool, message: String):
	checks += 1
	if not value:
		failures += 1
		print("FAIL: ", message)

func _initialize():
	call_deferred("run")

func run():
	var world = load("res://scenes/world.tscn").instantiate()
	root.add_child(world)
	await process_frame
	var preview = world.get_node("Preview")
	preview.set_physics_process(false)
	preview.progression.configure("user://menu-suite.json")
	for place in ["camp", "shrine", "chapel", "crypt_entry"]:
		preview.station = world.get_node("Station_" + place)
		preview.open_menu(preview.station)
		check(preview.panel.visible and preview.pages.get_child_count() == 10, place + " opens ten functional pages")
		for control in preview.pages.get_children():
			var name = control.text
			preview.select_page(name)
			check(preview.content.text.contains(name), place + " page " + name)
			# select_page replaces the button nodes, so inspect only the captured name.
		preview.close_menu()
	check(preview.progression.lifetime_xp == 0, "visiting all station pages never grants XP")
	for area in ["field", "farm", "woodland", "watchtower"]:
		preview.progression.award_exploration(area)
	preview.station = world.get_node("Station_shrine")
	preview.open_menu(preview.station)
	check(preview.page == "Level up", "pending choice opens level-up page at shrine")
	preview.actions.get_child(0).pressed.emit()
	check(preview.progression.stats().damage == 12 and preview.progression.pending_choices() == 0, "actual upgrade button changes shared model once")
	check(preview.actions.get_child(0).disabled, "consumed upgrade cannot be confirmed twice")
	preview.station = world.get_node("Station_chapel")
	preview.open_menu(preview.station)
	preview.select_page("Stats")
	check(preview.content.text.contains("12"), "other station reflects chosen build")
	preview.select_page("Cosmetics")
	preview.actions.get_child(1).pressed.emit()
	check(preview.progression.equipped == "teal" and not preview.progression.dirty, "cosmetic button equips and saves")
	preview.select_page("Save data")
	check(preview.actions.get_child_count() == 1, "remote station does not expose reset")
	preview.station = world.get_node("Station_camp")
	preview.open_menu(preview.station)
	preview.select_page("Save data")
	preview.actions.get_child(1).pressed.emit()
	check(preview.reset_confirmation and preview.progression.lifetime_xp == 100, "first reset click requires confirmation")
	preview.select_page("Overview")
	check(not preview.reset_confirmation and preview.progression.lifetime_xp == 100, "navigation cancels reset")
	preview.select_page("Save data")
	preview.reset_progress()
	preview.reset_progress()
	check(preview.progression.lifetime_xp == 0, "confirmed reset clears progression")
	preview.open_menu(world.get_node("Station_credits"))
	check(preview.content.text.contains("Asset creator credits") and preview.pages.get_child_count() == 0, "Credits stays separate from progression")
	preview.close_menu()
	check(not preview.panel.visible, "close dismisses panel")
	world.free()
	print("Station menus: %s checks, %s failures" % [checks, failures])
	quit(1 if failures else 0)
