extends SceneTree
var checks := 0
var failures := 0

func check(value: bool, label: String):
	checks += 1
	if not value:
		failures += 1
		print("FAIL: ", label)

func _initialize(): call_deferred("run")

func run():
	var result = load("res://scripts/worlds/world_builder.gd").new().build_package("res://ember-crypt.cworld")
	check(result.ok, "actual Ember Crypt archive loads through Comunicare builder: " + str(result.get("error", "")))
	if not result.ok:
		quit(1)
		return
	var world = result.scene.instantiate()
	root.add_child(world)
	check(Vector3(result.spawn_point[0], result.spawn_point[1], result.spawn_point[2]).is_equal_approx(Vector3(0, 0.1, 95)), "spawn survives export")
	check(world.find_children("*", "Camera3D", true, false).is_empty(), "world does not create its own camera/player")
	for child in world.find_children("*", "Node", true, false):
		check(child.get_script() == null, "no downloaded GDScript attached")
	check(result.document.meshes.size() > 0 and result.document.textures.size() > 0, "actual static models and PNG materials loaded")
	var runtime = load("res://scripts/worlds/world_runtime.gd").new()
	world.add_child(runtime)
	check(runtime.configure(world, result.document).ok, "configure production world runtime")
	var store = load("res://scripts/worlds/world_local_store.gd").new()
	check(store.configure("isolated-test-player", "local-test:ember"), "configure client-owned store")
	runtime.local_store = store
	for id in ["camp", "shrine", "chapel", "crypt_entry"]:
		check(runtime.dispatch("use", id).ok and is_instance_valid(runtime.menu), id + " opens actual Comunicare menu")
		runtime.close_menu()
	check(store.values.is_empty() and runtime.run_state.is_empty(), "opening menus never grants progress")
	runtime.dispatch("use", "camp")
	check(runtime.dispatch_ui("camp", [{"op": "menu", "page": "build"}], runtime.menu).ok, "page navigation works")
	var action = runtime.menu.widgets.set_note.control
	action.pressed.emit()
	check(runtime.run_state.get("note") == "Exploring Ashen Vale", "real world menu button updates scoped run state")
	runtime.close_menu()
	runtime.dispatch("use", "shrine")
	check(runtime.menu.widgets.run_note.control.text == "Exploring Ashen Vale", "second station displays same run state")
	runtime.dispatch_ui("camp", [{"op": "menu", "page": "saved"}], runtime.menu)
	runtime.menu.widgets.remember.control.pressed.emit()
	check(store.values.get("map_note") == "Ashen Vale routes reviewed", "real menu button persists through client store")
	var restored = load("res://scripts/worlds/world_local_store.gd").new()
	check(restored.configure("isolated-test-player", "local-test:ember") and restored.values == store.values, "saved note restores for same player/world")
	runtime.close_menu()
	runtime.dispatch("use", "credits")
	check(runtime.menu.widgets.credit0.control.text.contains("Creator:"), "spawn Credits identify actual artists")
	runtime.stop_scripts()
	check(not is_instance_valid(runtime.menu), "stop closes world-owned menu")
	world.free()
	await process_frame
	print("Comunicare package: %s checks, %s failures" % [checks, failures])
	quit(1 if failures else 0)
