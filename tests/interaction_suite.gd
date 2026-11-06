extends SceneTree
## Production targeting adapter + real exported plinths, no synthetic use calls.
class LoaderFixture extends Node:
	var world_runtime: Node

var checks := 0
var failures := 0

func check(value: bool, label: String):
	checks += 1
	if not value:
		failures += 1
		print("FAIL: ", label)

func _initialize(): call_deferred("run")

func run():
	print("Interaction fixture: loading package")
	var built = load("res://scripts/worlds/world_builder.gd").new().build_package("res://ember-crypt.cworld")
	if not built.ok:
		print("FAIL: ", built.error)
		quit(1)
		return
	var world = built.scene.instantiate()
	root.add_child(world)
	print("Interaction fixture: world instantiated")
	var runtime = load("res://scripts/worlds/world_runtime.gd").new()
	world.add_child(runtime)
	runtime.configure(world, built.document)
	var store = load("res://scripts/worlds/world_local_store.gd").new()
	store.configure("interaction-player", "interaction-world", true)
	runtime.local_store = store
	var loader = LoaderFixture.new()
	loader.world_runtime = runtime
	world.add_child(loader)
	var adapter = load("res://scripts/worlds/world_pickup_controller.gd").new()
	world.add_child(adapter)
	adapter.configure(null, loader)
	adapter.set_process(false)
	adapter.set_physics_process(false)
	var anchor = Node3D.new()
	world.add_child(anchor)
	await physics_frame
	await physics_frame
	for id in ["relic_watchtower", "relic_village", "relic_forecourt", "altar"]:
		print("Interaction fixture: targeting ", id)
		var target = world.get_node(NodePath(built.document.entities[id].path))
		anchor.global_position = target.global_position + Vector3(0, 0.6, 1)
		check(adapter.activate_nearest(anchor, 1.5), "production targeting reaches actual plinth: " + id)
		check(is_instance_valid(runtime.menu), "world script opens objective response via actual adapter")
		check(not adapter.activate_nearest(anchor, 1.5), "open menu suppresses repeated world input")
		runtime.close_menu()
		anchor.global_position += Vector3(0,0,5)
		check(not adapter.activate_nearest(anchor, 1.5), "out-of-range interaction rejected")
	check(store.values.is_empty(), "unstarted objective interactions award no progress")
	var target = world.get_node(NodePath(built.document.entities.relic_watchtower.path))
	anchor.global_position = target.global_position + Vector3(0,0.6,1)
	var blocker = StaticBody3D.new()
	var collider = CollisionShape3D.new()
	var box = BoxShape3D.new()
	box.size = Vector3(2,2,0.1)
	collider.shape = box
	blocker.add_child(collider)
	world.add_child(blocker)
	blocker.global_position = target.global_position + Vector3(0,0.3,0.5)
	await physics_frame
	await physics_frame
	check(not adapter.activate_nearest(anchor,1.5), "world objective cannot be activated through a blocking wall")
	check(not is_instance_valid(runtime.menu), "occluded interaction does not open a menu")
	runtime.stop_scripts()
	world.free()
	await process_frame
	print("World interactions: %s checks, %s failures" % [checks, failures])
	quit(1 if failures else 0)
