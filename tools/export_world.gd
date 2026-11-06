extends SceneTree
## Trusted author-side conversion only. No GDScript is included in the package.
var destination := ""
var resources: Array[String] = []
var nodes: Array[String] = []
var mesh_cache: Dictionary = {}
var material_cache: Dictionary = {}
var texture_cache: Dictionary = {}
var vertex_total := 0
var index_total := 0
var mesh_count := 0
var errors: Array[String] = []

func write_text(relative: String, text: String):
	DirAccess.make_dir_recursive_absolute(destination.path_join(relative).get_base_dir())
	var file = FileAccess.open(destination.path_join(relative), FileAccess.WRITE)
	if file == null:
		errors.append("Cannot write " + relative)
		return
	file.store_string(text)

func texture_ref(texture: Texture2D) -> String:
	if texture_cache.has(texture.get_instance_id()): return texture_cache[texture.get_instance_id()]
	var id = "tex" + str(texture_cache.size())
	var path = "textures/" + id + ".png"
	var image = texture.get_image()
	if image.is_compressed() and image.decompress() != OK:
		errors.append("Cannot decompress " + texture.resource_path)
	DirAccess.make_dir_recursive_absolute(destination.path_join("textures"))
	if image.save_png(destination.path_join(path)) != OK: errors.append("Cannot convert texture")
	resources.append('[ext_resource type="Texture2D" path="res://' + path + '" id="' + id + '"]')
	var result = 'ExtResource("' + id + '")'
	texture_cache[texture.get_instance_id()] = result
	return result

func material_ref(material: Material) -> String:
	if material == null: return ""
	if material_cache.has(material.get_instance_id()): return material_cache[material.get_instance_id()]
	if not material is StandardMaterial3D:
		errors.append("Unsupported source material")
		return ""
	var id = "mat" + str(material_cache.size())
	var path = "materials/" + id + ".tres"
	var declarations: Array[String] = []
	var properties: Array[String] = []
	var color = material.albedo_color
	properties.append("albedo_color = Color(%s, %s, %s, %s)" % [color.r, color.g, color.b, color.a])
	properties.append("roughness = " + str(material.roughness))
	properties.append("metallic = " + str(material.metallic))
	properties.append("shading_mode = " + str(material.shading_mode))
	# Texture declarations belong to each material resource namespace.
	for channel in ["albedo", "normal", "roughness", "metallic", "ao"]:
		var texture = material.get(channel + "_texture")
		if texture == null: continue
		var ref = texture_ref(texture)
		var tex_id = ref.trim_prefix('ExtResource("').trim_suffix('")')
		for declaration in resources:
			if declaration.ends_with('id="' + tex_id + '"]') and not declaration in declarations: declarations.append(declaration)
		properties.append(channel + "_texture = " + ref)
		if channel in ["roughness", "metallic", "ao"]:
			properties.append(channel + "_texture_channel = " + str(material.get(channel + "_texture_channel")))
		if channel in ["normal", "ao"]: properties.append(channel + "_enabled = true")
	if material.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR:
		properties.append("transparency = " + str(BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR))
		properties.append("alpha_scissor_threshold = " + str(material.alpha_scissor_threshold))
	properties.append("cull_mode = " + str(material.cull_mode))
	write_text(path, '[gd_resource type="StandardMaterial3D" format=3]\n' + "\n".join(declarations) + '\n[resource]\n' + "\n".join(properties) + "\n")
	resources.append('[ext_resource type="Material" path="res://' + path + '" id="' + id + '"]')
	var result = 'ExtResource("' + id + '")'
	material_cache[material.get_instance_id()] = result
	return result

func mesh_ref(mesh: Mesh, surface: int) -> Array:
	var key = str(mesh.get_instance_id()) + ":" + str(surface)
	if mesh_cache.has(key): return mesh_cache[key]
	var arrays = mesh.surface_get_arrays(surface)
	var chosen = arrays[Mesh.ARRAY_INDEX]
	if chosen == null or chosen.is_empty():
		chosen = PackedInt32Array()
		for index in arrays[Mesh.ARRAY_VERTEX].size(): chosen.append(index)
	# Reduce overly dense scanned source surfaces using the engine's author-side LODs.
	# This is a detailed scan with baked maps, not a faceted low-poly replacement.
	var source_material = mesh.surface_get_material(surface)
	var foliage = source_material != null and source_material.resource_name.contains("pine_sapling_small_twig")
	var target_indices = 90000 if foliage else 45000
	if chosen.size() > target_indices:
		var importer = ImporterMesh.new()
		importer.add_surface(Mesh.PRIMITIVE_TRIANGLES, arrays)
		importer.generate_lods(60, 60, [])
		for lod in importer.get_surface_lod_count(0):
			var candidate = importer.get_surface_lod_indices(0, lod)
			if candidate.size() <= target_indices:
				chosen = candidate
				break
	var refs: Array = []
	# Small independent surfaces fit the parser's per-document fuel budget.
	# Partition triangles, rather than further reducing visible scan detail.
	for offset in range(0, chosen.size(), 9000):
		refs.append(write_mesh_chunk(mesh, arrays, chosen.slice(offset, offset + 9000)))
	mesh_cache[key] = refs
	return refs

func write_mesh_chunk(mesh: Mesh, arrays: Array, chosen: PackedInt32Array) -> String:
	var remap = {}
	var data = {"schema": 1, "vertices": [], "indices": [], "normals": [], "uv": []}
	for old in chosen:
		if not remap.has(old):
			remap[old] = data.vertices.size()
			var vertex = arrays[Mesh.ARRAY_VERTEX][old]
			data.vertices.append([vertex.x, vertex.y, vertex.z])
			var normal = arrays[Mesh.ARRAY_NORMAL][old] if arrays[Mesh.ARRAY_NORMAL] != null else Vector3.UP
			data.normals.append([normal.x, normal.y, normal.z])
			var uv = arrays[Mesh.ARRAY_TEX_UV][old] if arrays[Mesh.ARRAY_TEX_UV] != null else Vector2.ZERO
			# Bake triplanar projection for authored masonry/trail boxes to regular UVs.
			if mesh is BoxMesh:
				if absf(normal.y) > 0.5: uv = Vector2(vertex.x, vertex.z) * 0.3
				elif absf(normal.x) > 0.5: uv = Vector2(vertex.z, vertex.y) * 0.3
				else: uv = Vector2(vertex.x, vertex.y) * 0.3
			data.uv.append([uv.x, uv.y])
		data.indices.append(remap[old])
	vertex_total += data.vertices.size()
	index_total += data.indices.size()
	if data.vertices.size() > 50000 or data.indices.size() > 150000: errors.append("Source mesh exceeds safe surface budget")
	var id = "mesh" + str(mesh_count)
	mesh_count += 1
	var path = "models/" + id + ".worldmesh"
	write_text(path, JSON.stringify(data))
	resources.append('[ext_resource type="ArrayMesh" path="res://' + path + '" id="' + id + '"]')
	var result = 'ExtResource("' + id + '")'
	return result

func transform_text(value: Transform3D) -> String:
	var b = value.basis
	var o = value.origin
	return "Transform3D(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" % [b.x.x,b.x.y,b.x.z,b.y.x,b.y.y,b.y.z,b.z.x,b.z.y,b.z.z,o.x,o.y,o.z]

func visit(node: Node, transform: Transform3D = Transform3D.IDENTITY, body_parent: String = "", body_transform: Transform3D = Transform3D.IDENTITY):
	# The publisher scene is a three-variant catalogue, not one tree. Use a single
	# tree per placement and spend geometry on needles instead of three trunks.
	if str(node.name) in ["pine_sapling_small_b", "pine_sapling_small_c"]: return
	if node is Node3D: transform = transform * node.transform
	if node is RigidBody3D and node.get_meta("world_pickup", false):
		var id = str(node.get_meta("world_entity_id"))
		body_parent = str(node.name)
		body_transform = transform
		nodes.append('[node name="%s" type="RigidBody3D" parent="."]\ntransform = %s\nmass = %s\nmetadata/world_entity_id = "%s"\nmetadata/world_pickup = true' % [body_parent, transform_text(transform), node.mass, id])
	if node is MeshInstance3D and node.mesh != null:
		if not node.visible:
			for child in node.get_children(): visit(child, transform, body_parent, body_transform)
			return
		for surface in node.mesh.get_surface_count():
			var refs = mesh_ref(node.mesh, surface)
			var material = node.material_override if node.material_override != null else node.mesh.surface_get_material(surface)
			var mat = material_ref(material)
			for ref in refs:
				var parent = body_parent if not body_parent.is_empty() else "."
				var local = body_transform.affine_inverse() * transform if not body_parent.is_empty() else transform
				nodes.append('[node name="Visual%s" type="MeshInstance3D" parent="%s"]\ntransform = %s\nmesh = %s\n%s' % [nodes.size(), parent, transform_text(local), ref, "material_override = " + mat if not mat.is_empty() else ""])
	elif node is CollisionShape3D and node.shape is BoxShape3D:
		var id = "shape" + str(nodes.size())
		var size = node.shape.size
		resources.append('[sub_resource type="BoxShape3D" id="%s"]\nsize = Vector3(%s, %s, %s)' % [id, size.x, size.y, size.z])
		if not body_parent.is_empty():
			nodes.append('[node name="Shape" type="CollisionShape3D" parent="%s"]\ntransform = %s\nshape = SubResource("%s")' % [body_parent, transform_text(body_transform.affine_inverse() * transform), id])
		else:
			var name = "Body" + str(nodes.size())
			nodes.append('[node name="%s" type="StaticBody3D" parent="."]\ntransform = %s' % [name, transform_text(transform)])
			nodes.append('[node name="Shape" type="CollisionShape3D" parent="%s"]\nshape = SubResource("%s")' % [name, id])
	elif node is DirectionalLight3D or node is OmniLight3D:
		var color = node.light_color
		var extra = "\nomni_range = " + str(node.omni_range) if node is OmniLight3D else ""
		nodes.append('[node name="Light%s" type="%s" parent="."]\ntransform = %s\nlight_color = Color(%s, %s, %s, 1)\nlight_energy = %s%s' % [nodes.size(), node.get_class(), transform_text(transform), color.r,color.g,color.b,node.light_energy,extra])
	elif node is Marker3D and node.get_meta("world_spawn", false):
		nodes.append('[node name="Spawn" type="Marker3D" parent="."]\ntransform = %s\nmetadata/world_entity_id = "spawn"\nmetadata/world_spawn = true' % transform_text(transform))
	elif node.name.begins_with("Station_"):
		var id = str(node.name).trim_prefix("Station_")
		nodes.append('[node name="%s" type="Node3D" parent="."]\ntransform = %s\nmetadata/world_entity_id = "%s"\nmetadata/world_script = "logic/%s.worldscript"' % [node.name, transform_text(transform), id, id])
	for child in node.get_children(): visit(child, transform, body_parent, body_transform)

func _initialize(): call_deferred("run")

func run():
	var args = OS.get_cmdline_user_args()
	if args.size() != 1:
		print("Expected destination directory")
		quit(2)
		return
	destination = args[0]
	var world = load("res://scenes/world.tscn").instantiate()
	world.get_node("Preview").free() # Never run or export local preview/player code.
	visit(world)
	world.free()
	if vertex_total > 200000 or index_total > 600000: errors.append("Aggregate safe geometry budget exceeded")
	if not errors.is_empty():
		print(errors)
		quit(1)
		return
	write_text("scenes/world.tscn", '[gd_scene format=3]\n' + "\n".join(resources) + '\n[node name="EmberCrypt" type="Node3D"]\n' + "\n".join(nodes) + "\n")
	print("Safe export: %s nodes, %s meshes, %s vertices, %s indices" % [nodes.size(),mesh_count,vertex_total,index_total])
	quit()
