extends RefCounted
## Local standalone preview progression. Not a downloaded-world storage API.
const DISCOVERIES = ["field", "farm", "shrine", "woodland", "watchtower", "ford", "bridge", "village", "chapel", "forecourt", "crypt_entry", "galleries", "ossuary", "armory", "antechamber", "guardian"]
const UPGRADES = ["damage", "cooldown", "health"]
var lifetime_xp := 0
var run_xp := 0
var discoveries: Array = []
var build: Array = []
var equipped := "amber"
var path := ""
var writable := false
var dirty := false
var error := ""

func configure(save_path: String) -> bool:
	path = save_path
	writable = false
	error = ""
	lifetime_xp = 0
	discoveries = []
	equipped = "amber"
	new_run()
	dirty = false
	if FileAccess.file_exists(path):
		var file = FileAccess.open(path, FileAccess.READ)
		if file == null or file.get_length() > 16384:
			error = "Save unreadable or oversized; original preserved. Temporary play only."
			return false
		var parser = JSON.new()
		if parser.parse(file.get_as_text()) != OK or not valid_record(parser.data):
			error = "Save corrupt or unsupported; original preserved. Temporary play only."
			return false
		var data: Dictionary = parser.data
		lifetime_xp = int(data.lifetime_xp)
		discoveries = data.discoveries.duplicate()
		equipped = data.equipped
	writable = true
	return true

func valid_record(data: Variant) -> bool:
	if not data is Dictionary or data.size() != 4: return false
	if data.get("schema_version") != 1: return false
	if not (data.get("lifetime_xp") is int or data.get("lifetime_xp") is float): return false
	if not data.get("discoveries") is Array or data.discoveries.size() > DISCOVERIES.size(): return false
	var seen = []
	for id in data.discoveries:
		if not id is String or not id in DISCOVERIES or id in seen: return false
		seen.append(id)
	if data.lifetime_xp != seen.size() * 25: return false
	return data.get("equipped") == "amber" or (data.get("equipped") == "teal" and data.lifetime_xp >= 100)

func award_exploration(id: String) -> bool:
	if not id in DISCOVERIES or id in discoveries: return false
	discoveries.append(id)
	lifetime_xp += 25
	run_xp += 25
	dirty = true
	return true

func player_level() -> int:
	return 1 + lifetime_xp / 100

func pending_choices() -> int:
	return maxi(0, run_xp / 100 - build.size())

func choose_upgrade(id: String) -> bool:
	if not id in UPGRADES or pending_choices() == 0 or build.count(id) >= 4: return false
	build.append(id)
	return true

func stats() -> Dictionary:
	return {"damage": 10 + 2 * build.count("damage"), "cooldown": 0.8 - 0.1 * build.count("cooldown"), "max_health": 100 + 20 * build.count("health")}

func equip(id: String) -> bool:
	if id != "amber" and not (id == "teal" and lifetime_xp >= 100): return false
	equipped = id
	dirty = true
	return true

func new_run():
	run_xp = 0
	build = []

func save() -> bool:
	if not writable: return false
	var record = {"schema_version": 1, "lifetime_xp": lifetime_xp, "discoveries": discoveries, "equipped": equipped}
	var pending = path + ".pending"
	var file = FileAccess.open(pending, FileAccess.WRITE)
	if file == null:
		error = "Cannot write local save. Progress is unsaved."
		return false
	file.store_string(JSON.stringify(record))
	file.flush()
	var result = file.get_error()
	file.close()
	if result != OK or DirAccess.rename_absolute(pending, path) != OK:
		error = "Cannot replace local save. Progress is unsaved."
		return false
	dirty = false
	error = ""
	return true

func reset_progress() -> bool:
	if not writable: return false
	var old = [lifetime_xp, discoveries.duplicate(), equipped, run_xp, build.duplicate()]
	lifetime_xp = 0
	discoveries = []
	equipped = "amber"
	new_run()
	dirty = true
	if save(): return true
	lifetime_xp = old[0]
	discoveries = old[1]
	equipped = old[2]
	run_xp = old[3]
	build = old[4]
	return false
