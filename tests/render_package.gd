extends SceneTree
## Review the actual safe package, not the higher-feature author scene.
func _initialize(): call_deferred("run")

func run():
	var result = load("res://scripts/worlds/world_builder.gd").new().build_package("res://ember-crypt.cworld")
	if not result.ok:
		print(result.error)
		quit(1)
		return
	root.size = Vector2i(1280, 800)
	var world = result.scene.instantiate()
	root.add_child(world)
	var camera = Camera3D.new()
	camera.far = 800
	world.add_child(camera)
	var shots = [
		["chapel", Vector3(54, 8, -56), Vector3(75, 3, -80)],
		["crypt_interior", Vector3(105, 2, 34), Vector3(105, 3, 43)],
		["grass_detail", Vector3(-23, 1.7, 57), Vector3(-13, 0.3, 43)],
		["camp", Vector3(-12, 8, 110), Vector3(0, 1, 80)],
		["field", Vector3(35, 14, 65), Vector3(-15, 1, -20)],
		["woodland", Vector3(-125, 12, 10), Vector3(-95, 2, -35)],
		["overview", Vector3(220, 260, 260), Vector3(0, 0, 10)],
	]
	for shot in shots:
		var args = OS.get_cmdline_user_args()
		if args.size() > 1 and shot[0] != args[1]: continue
		camera.position = shot[1]
		camera.look_at(shot[2])
		for frame in 8: await process_frame
		await RenderingServer.frame_post_draw
		var image = root.get_texture().get_image()
		var path = OS.get_cmdline_user_args()[0].path_join(shot[0] + ".png")
		if image.save_png(path) != OK:
			quit(1)
			return
		print("Rendered review: ", path)
	world.free()
	quit()
