extends Node3D
## Author-side desktop preview. Never include this script in a safe world package.
var body: CharacterBody3D
var camera: Camera3D
var panel: PanelContainer
var content: RichTextLabel
var prompt: Label
var stations: Array[Node] = []
var station: Node3D

func _ready():
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
	var layer = CanvasLayer.new()
	add_child(layer)
	var title = Label.new()
	title.text = "EMBER CRYPT / ASHEN VALE\nWASD move · Shift run · Mouse look · E station · Esc release mouse\nExploration build — enemy combat and progression not implemented"
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
	content = RichTextLabel.new()
	content.custom_minimum_size = Vector2(760, 460)
	content.bbcode_enabled = true
	column.add_child(content)
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
		var manifest = JSON.parse_string(FileAccess.get_file_as_string("res://assets/provenance.json"))
		content.text = "[font_size=26]Asset creator credits[/font_size]\n\n"
		for asset in manifest.assets:
			content.text += "[b]%s[/b]\n%s · %s\n%s\n\n" % [asset.title, asset.author, asset.license, asset.source]
	else:
		content.text = "[font_size=26]%s[/font_size]\n\n" % target.get_meta("title")
		content.text += "[b]Map & destinations[/b]\nCamp → Field → Bridge → Village → Chapel → Crypt\nWest loop: Farm → Shrine → Woodland → Watchtower\nCrypt: Entry → Galleries → Ossuary / Armory → Guardian\n\n"
		content.text += "[b]Leveling station — exploration preview[/b]\nPlayer overview · Character stats · Upgrade library\nCurrent build · Milestones · Cosmetics · XP breakdown\n\nProgression, healing and combat are not implemented in this map build.\nThese station panels are functional navigation menus, not fake XP controls."

func close_menu():
	panel.hide()
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
