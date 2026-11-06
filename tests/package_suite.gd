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
	await physics_frame
	await physics_frame
	check(Vector3(result.spawn_point[0], result.spawn_point[1], result.spawn_point[2]).is_equal_approx(Vector3(0, 0.1, 95)), "spawn survives export")
	check(world.find_children("*", "Camera3D", true, false).is_empty(), "world does not create its own camera/player")
	for child in world.find_children("*", "Node", true, false):
		check(child.get_script() == null, "no downloaded GDScript attached")
	check(result.document.meshes.size() > 0 and result.document.textures.size() > 0, "actual static models and PNG materials loaded")
	var alpha_materials = 0
	var sky_materials = 0
	for path in result.document.materials:
		for section in result.document.scenes[path]:
			if section.kind != "resource": continue
			var properties: Dictionary = section.properties
			if properties.get("transparency", 0) == BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR:
				alpha_materials += 1
				check(properties.get("cull_mode") == BaseMaterial3D.CULL_DISABLED, "foliage preserves double-sided cutout material")
			if properties.get("shading_mode", 1) == BaseMaterial3D.SHADING_MODE_UNSHADED:
				sky_materials += 1
	check(alpha_materials > 0, "export retains actual alpha-scissor enum instead of alpha-prepass")
	check(sky_materials > 0, "static sky material survives safe conversion")
	check(result.document.meshes.size() < 350, "repeated map instances share exported geometry")
	var grass_surfaces = 0
	for node in world.find_children("*", "MeshInstance3D", true, false):
		var material = node.material_override
		if material is StandardMaterial3D and material.albedo_color.is_equal_approx(Color(0.25, 0.34, 0.12, 1)):
			grass_surfaces += 1
			check(material.cull_mode == BaseMaterial3D.CULL_DISABLED, "grass blades remain visible from both sides")
			check(node.find_children("*", "CollisionShape3D", true, false).is_empty(), "grass adds no movement collision")
	check(grass_surfaces >= 35, "real grass mesh patches survive Comunicare safe loader")
	var pickups = []
	for id in result.document.entities:
		var entry = result.document.entities[id]
		if not entry.pickup: continue
		var item = world.get_node(NodePath(entry.path))
		pickups.append(item)
		check(item is RigidBody3D, "pickup remains dynamic after safe export")
		check(item.find_children("*", "MeshInstance3D", true, false).size() > 0, "pickup geometry stays attached to body")
		check(item.find_children("*", "CollisionShape3D", true, false).size() == 1, "pickup owns its collision shape")
	check(pickups.size() == 12, "all twelve supply items survive safe package export")
	for frame in 90: await physics_frame
	for item in pickups:
		check(item.global_position.y > -0.2 and item.global_position.y < 1, "exported item falls onto actual floor without sinking")
	var archive = ZIPReader.new()
	archive.open("res://ember-crypt.cworld")
	var map = JSON.parse_string(archive.read_file("map.json").get_string_from_utf8())
	archive.close()
	check(int(map.size_m[0]) == 440 and int(map.size_m[1]) == 370 and map.trees >= 100 and map.rocks >= 65, "expanded scenery counts recorded in actual package")
	check(map.grass_blades > 12000 and map.grass_patches == grass_surfaces, "grass density metadata matches real package geometry")
	var physics = world.get_world_3d().direct_space_state
	for center in [Vector2(-35,48), Vector2(48,65), Vector2(-55,-12)]:
		var hit = physics.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(center.x, 2, center.y), Vector3(center.x, -1, center.y)))
		check(not hit.is_empty() and hit.position.y > 0.4, "earth bank collision survives safe export")
	for edge in map.routes:
		var a = map.areas[edge[0]]
		var b = map.areas[edge[1]]
		var start = Vector3(a[0], 1, a[1])
		var finish = Vector3(b[0], 1, b[1])
		check(physics.intersect_ray(PhysicsRayQueryParameters3D.create(start, finish)).is_empty(), "exported route clear: " + str(edge))
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
