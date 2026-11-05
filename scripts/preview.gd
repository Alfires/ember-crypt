extends Node3D
## Author-side desktop preview. Never include this script in a safe world package.
var body: CharacterBody3D
var camera: Camera3D
var panel: PanelContainer
var content: RichTextLabel
var prompt: Label
var stations: Array[Node] = []
var station: Node3D
var progression = preload("res://scripts/progression.gd").new()
var pages: HFlowContainer
var actions: HBoxContainer
var page := "Overview"
var reset_confirmation := false
var area_markers: Array[Node] = []

func button(parent: Node, text: String, callback: Callable):
	var control = Button.new()
	control.text = text
	control.pressed.connect(callback)
	parent.add_child(control)
	return control

func _ready():
	progression.configure("user://ember-crypt-progress.json")
	body = CharacterBody3D.new()
	body.name = "PreviewPlayer"
	var shape = CollisionShape3D.new()
	var capsule = CapsuleShape3D.new()
	capsule.radius = 0.35
	capsule.height = 1.8
	shape.shape = capsule
	shape.position.y = 0.9
	body.add_child(shape)
	camera = Camera3D.new()
	camera.position.y = 1.65
	camera.far = 650
	body.add_child(camera)
	add_child(body)
	body.position = Vector3(0, 0.1, 95)
	stations = get_tree().get_nodes_in_group("stations")
	area_markers = get_tree().get_nodes_in_group("areas")
	var layer = CanvasLayer.new()
	add_child(layer)
	var title = Label.new()
	title.text = "EMBER CRYPT / ASHEN VALE\nWASD move · Shift run · Mouse look · E station · Esc release mouse\nDiscover landmarks for one-time XP · enemy combat not implemented"
	title.position = Vector2(24, 20)
	layer.add_child(title)
	prompt = Label.new()
	prompt.position = Vector2(24, 115)
	layer.add_child(prompt)
	panel = PanelContainer.new()
	panel.position = Vector2(260, 160)
	panel.custom_minimum_size = Vector2(780, 540)
	layer.add_child(panel)
	var column = VBoxContainer.new()
	panel.add_child(column)
	pages = HFlowContainer.new()
	column.add_child(pages)
	content = RichTextLabel.new()
	content.custom_minimum_size = Vector2(760, 460)
	content.bbcode_enabled = true
	column.add_child(content)
	actions = HBoxContainer.new()
	column.add_child(actions)
	var close = Button.new()
	close.text = "Close / return to exploration"
	close.pressed.connect(close_menu)
	column.add_child(close)
	panel.hide()
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _unhandled_input(event):
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		body.rotation.y -= event.relative.x * 0.002
		camera.rotation.x = clampf(camera.rotation.x - event.relative.y * 0.002, -1.4, 1.4)
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode == KEY_ESCAPE:
			if panel.visible: close_menu()
			else: Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		if event.physical_keycode == KEY_E and station != null and not panel.visible:
			open_menu(station)
	if event is InputEventMouseButton and event.pressed and not panel.visible:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _physics_process(delta):
	if panel.visible: return
	var direction = Vector3.ZERO
	if Input.is_physical_key_pressed(KEY_W): direction.z -= 1
	if Input.is_physical_key_pressed(KEY_S): direction.z += 1
	if Input.is_physical_key_pressed(KEY_A): direction.x -= 1
	if Input.is_physical_key_pressed(KEY_D): direction.x += 1
	direction = body.basis * direction.normalized()
	var speed = 10.0 if Input.is_physical_key_pressed(KEY_SHIFT) else 6.0
	body.velocity.x = direction.x * speed
	body.velocity.z = direction.z * speed
	if not body.is_on_floor(): body.velocity.y -= 20 * delta
	else: body.velocity.y = 0
	body.move_and_slide()
	if body.position.y < -15: body.position = Vector3(0, 1, 95)
	for marker in area_markers:
		if body.position.distance_to(marker.global_position) < 9:
			if progression.award_exploration(str(marker.get_meta("area_id"))):
				progression.save()
	station = null
	for candidate in stations:
		if body.global_position.distance_to(candidate.global_position) < 5:
			station = candidate
			break
	prompt.text = "E — " + str(station.get_meta("title")) if station != null else ""

func open_menu(target):
	panel.show()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	if target.get_meta("kind") == "credits":
		clear_controls(pages)
		clear_controls(actions)
		var manifest = JSON.parse_string(FileAccess.get_file_as_string("res://assets/provenance.json"))
		content.text = "[font_size=26]Asset creator credits[/font_size]\n\n"
		for asset in manifest.assets:
			content.text += "[b]%s[/b]\n%s · %s\n%s\n\n" % [asset.title, asset.author, asset.license, asset.source]
	else:
		page = "Level up" if progression.pending_choices() > 0 else "Overview"
		reset_confirmation = false
		render_page()

func clear_controls(parent: Node):
	for child in parent.get_children():
		parent.remove_child(child)
		child.queue_free()

func select_page(value: String):
	page = value
	reset_confirmation = false
	render_page()

func render_page():
	clear_controls(pages)
	clear_controls(actions)
	for name in ["Overview", "Stats", "Upgrades", "Level up", "Build", "Milestones", "Cosmetics", "XP", "Map", "Save data"]:
		button(pages, name, select_page.bind(name))
	var status = progression.error if not progression.error.is_empty() else ("Unsaved" if progression.dirty else "Saved on this PC")
	content.text = "[font_size=26]%s[/font_size]\n%s\n\n" % [page, status]
	match page:
		"Overview":
			content.text += "Player level %s · Lifetime XP %s\nRun XP %s · Pending upgrades %s\nCosmetic: %s\n\nDiscover new landmarks for 25 XP each. Every 100 XP grants a run upgrade.\nDiscoveries are one-time rewards across runs; resetting a run cannot farm XP.\nCombat rewards will be added with the combat system.\n\nNew exploration run clears temporary upgrades, not lifetime progress." % [progression.player_level(), progression.lifetime_xp, progression.run_xp, progression.pending_choices(), progression.equipped]
			if station.name == "Station_camp": button(actions, "New exploration run", new_exploration_run)
		"Stats":
			var stats = progression.stats()
			content.text += "Damage: 10 → %s\nAttack cooldown: 0.8 → %.1f seconds\nMaximum health: 100 → %s\n\nThese are calculated build stats. Combat and player damage are not implemented yet." % [stats.damage, stats.cooldown, stats.max_health]
		"Upgrades":
			content.text += "Damage: +2 per rank\nCooldown: -0.1 seconds per rank\nHealth: +20 maximum per rank\n\nEach family caps at four ranks. Player level unlocks cosmetics, not permanent damage."
		"Level up":
			content.text += "Pending choices: %s\nChoose exactly one bonus per earned level.\n" % progression.pending_choices()
			for id in progression.UPGRADES:
				var control = button(actions, "%s (%s/4)" % [id.capitalize(), progression.build.count(id)], choose.bind(id))
				control.disabled = progression.pending_choices() == 0 or progression.build.count(id) >= 4
		"Build": content.text += "No run upgrades yet." if progression.build.is_empty() else " → ".join(progression.build)
		"Milestones": content.text += "Level 1 / 0 XP: Amber cosmetic\nLevel 2 / 100 XP: Teal cosmetic\nFurther levels currently show experience only; no hidden stat boosts."
		"Cosmetics":
			content.text += "Selected: %s\nCosmetic preference is saved; spell visuals arrive with combat.\nTeal requires 100 lifetime XP." % progression.equipped
			button(actions, "Equip amber", equip.bind("amber"))
			button(actions, "Equip teal", equip.bind("teal")).disabled = progression.lifetime_xp < 100
		"XP": content.text += "Lifetime: %s / 400 discovery XP\nCurrent run: %s\nLandmarks found: %s / 16\n\nNo XP for menus, repeat visits, or retries. Discoveries persist; mid-run state does not." % [progression.lifetime_xp, progression.run_xp, progression.discoveries.size()]
		"Map": content.text += "Camp → Field → Bridge → Village → Chapel → Crypt\nWest: Farm → Shrine → Woodland → Watchtower → Village\nCrypt: Entry → Galleries → Ossuary / Armory → Guardian hall\n\nLeveling stations: Camp, Shrine, Chapel, Crypt entry\nGate objectives and enemies are not implemented."
		"Save data":
			content.text += "Local standalone save: user://ember-crypt-progress.json\nNo cloud, account or relay data. Corrupt/future saves are preserved.\nReset is available only at camp. It removes discovery XP and cosmetics."
			button(actions, "Retry saving", retry_save).disabled = not progression.writable
			if station.name == "Station_camp":
				button(actions, "Confirm RESET all progress" if reset_confirmation else "Reset player progression…", reset_progress).disabled = not progression.writable

func choose(id: String):
	progression.choose_upgrade(id)
	render_page()

func equip(id: String):
	if progression.equip(id): progression.save()
	render_page()

func retry_save():
	progression.save()
	render_page()

func reset_progress():
	if not reset_confirmation:
		reset_confirmation = true
	else:
		progression.reset_progress()
		reset_confirmation = false
	render_page()

func new_exploration_run():
	progression.new_run()
	render_page()

func close_menu():
	panel.hide()
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
