extends SceneTree
var failures := 0
var checks := 0
var runtime
var store

func check(value: bool, label: String):
	checks += 1
	if not value:
		failures += 1
		print("FAIL: ", label)

func use(id: String):
	# Real disk store enforces one write per second. Never forge its clock.
	await create_timer(1.05).timeout
	return runtime.dispatch("use", id)

func _initialize(): call_deferred("run")

func run():
	var result = load("res://scripts/worlds/world_builder.gd").new().build_package("res://ember-crypt.cworld")
	if not result.ok:
		print("FAIL: package unavailable: ", result.error)
		quit(1)
		return
	var world = result.scene.instantiate()
	root.add_child(world)
	runtime = load("res://scripts/worlds/world_runtime.gd").new()
	world.add_child(runtime)
	store = load("res://scripts/worlds/world_local_store.gd").new()
	store.configure("loop-player", "test:ember-loop")
	runtime.local_store = store
	runtime.configure(world, result.document)
	for id in ["relic_watchtower", "relic_village", "relic_forecourt", "altar"]:
		var response = await use(id)
		check(response.ok and store.values.is_empty(), "objective cannot award before start: " + id)
	runtime.dispatch("use", "camp")
	check(runtime.menu.widgets.has("start_run"), "camp exposes actual start button")
	if not runtime.menu.widgets.has("start_run"):
		world.free()
		quit(1)
		return
	runtime.menu.widgets.start_run.control.pressed.emit()
	check(store.values.get("run_active") == true, "start button begins real saved run")
	var before = store.values.duplicate(true)
	check(not runtime.dispatch("use", "relic_watchtower").ok and store.values == before, "write throttle cannot partially award a relic")
	check(runtime.enabled, "throttled award remains retryable")
	check((await use("altar")).ok and not store.values.has("wins"), "altar rejects missing relics")
	for place in ["watchtower", "village", "forecourt"]:
		var id = "relic_" + place
		check((await use(id)).ok and store.values.get(id) == true, "relic acquired at " + place)
		var xp = store.values.get("run_xp")
		check((await use(id)).ok and store.values.get("run_xp") == xp, "repeated interaction cannot farm XP")
		if place == "watchtower":
			var resumed = load("res://scripts/worlds/world_local_store.gd").new()
			check(resumed.configure("loop-player", "test:ember-loop") and resumed.values.get("relic_watchtower") == true, "in-progress relic state restores from disk")
			runtime.stop_scripts()
			runtime.configure(world, result.document)
			runtime.local_store = resumed
			store = resumed
			check(store.values.run_active == true and store.values.run_xp == 25, "reconfigured runtime resumes active run before collecting remaining seals")
	check(store.values.get("run_xp") == 75, "three relics award exactly 75 run XP")
	check((await use("altar")).ok and store.values.get("wins") == 1 and store.values.run_active == false, "altar completes run once")
	check((await use("altar")).ok and store.values.wins == 1, "repeat finish cannot duplicate completion")
	var restored = load("res://scripts/worlds/world_local_store.gd").new()
	check(restored.configure("loop-player", "test:ember-loop") and restored.values.wins == 1, "completion persists through real store reload")
	await create_timer(1.05).timeout
	runtime.dispatch("use", "camp")
	runtime.menu.widgets.start_run.control.pressed.emit()
	check(store.values.run_active == true and store.values.run_xp == 0 and store.values.wins == 1, "new run resets objective state but keeps completions")
	check(store.values.relic_watchtower == false and store.values.relic_village == false and store.values.relic_forecourt == false, "new run clears all relics")
	check((await use("altar")).ok and store.values.wins == 1, "old completion cannot bypass a new run")
	runtime.stop_scripts()
	check(not runtime.dispatch("use", "relic_watchtower").ok, "stopped world cannot advance objective")
	world.free()
	await process_frame
	print("World objective loop: %s checks, %s failures" % [checks, failures])
	quit(1 if failures else 0)
