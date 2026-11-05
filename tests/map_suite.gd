extends SceneTree
var failures := 0
var checks := 0

func check(value: bool, message: String):
	checks += 1
	if not value:
		failures += 1
		print("FAIL: ", message)

func _initialize():
	call_deferred("run")

func run():
	var packed = load("res://scenes/world.tscn")
	var world = packed.instantiate()
	# Do not start preview UI/capture in isolated map tests.
	world.get_node("Preview").free()
	root.add_child(world)
	await physics_frame
	await physics_frame
	var data = JSON.parse_string(FileAccess.get_file_as_string("res://map.json"))
	check(data.areas.size() >= 12, "at least twelve named areas")
	check(get_nodes_in_group("areas").size() == data.areas.size(), "area markers match map data")
	check(get_nodes_in_group("stations").size() == 5, "four leveling stations plus spawn Credits")
	check(data.stations == ["camp", "shrine", "chapel", "crypt_entry"], "distributed safe-station locations")
	var reached = [data.spawn]
	var pending = [data.spawn]
	while not pending.is_empty():
		var current = pending.pop_back()
		for edge in data.routes:
			if current in edge:
				var other = edge[1] if edge[0] == current else edge[0]
				if not other in reached:
					reached.append(other)
					pending.append(other)
	check(reached.size() == data.areas.size(), "entire authored route graph connected")
	var physics = world.get_world_3d().direct_space_state
	for edge in data.routes:
		var a = data.areas[edge[0]]
		var b = data.areas[edge[1]]
		var start = Vector3(a[0], 1, a[1])
		var finish = Vector3(b[0], 1, b[1])
		var ray = PhysicsRayQueryParameters3D.create(start, finish)
		check(physics.intersect_ray(ray).is_empty(), "walkable centerline: " + str(edge))
		for step in 11:
			var point = start.lerp(finish, step/10.0)
			var ground = PhysicsRayQueryParameters3D.create(point, point - Vector3(0, 3, 0))
			check(not physics.intersect_ray(ground).is_empty(), "ground under route: " + str(edge) + " / " + str(step))
	# Verify the open field has actual floor collision over a large playable area.
	for x in range(-35, 36, 10):
		for z in range(0, 61, 10):
			var ground = PhysicsRayQueryParameters3D.create(Vector3(x, 2, z), Vector3(x, -2, z))
			check(not physics.intersect_ray(ground).is_empty(), "playable field floor")
	for node in get_nodes_in_group("stations"):
		check(node.get_meta("kind", "") in ["leveling", "credits"], "station exposes usable preview action")
	var spawn = world.get_node("Spawn")
	check(spawn.get_meta("world_spawn", false), "spawn metadata present")
	check(spawn.position.distance_to(world.get_node("Station_credits").position) < 5, "creator Credits beside spawn")
	world.free()
	print("Map physics: %s checks, %s failures" % [checks, failures])
	quit(1 if failures else 0)
