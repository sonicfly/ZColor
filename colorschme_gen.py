import os
import sys
import math
import re
import colorsys

def draw_color_table(x, y, z, xValues, yValues, zValues, xNames = None, yNames = None, zNames = None):
	# condition check
	conditions = {
			x.lower() : { "var": "x", "values": xValues, "names": xNames },
			y.lower() : { "var": "y", "values": yValues, "names": yNames },
			z.lower() : { "var": "z", "values": zValues, "names": zNames },
	}

	if "hue" not in conditions:
		raise RuntimeError("Cannot draw color table without hue")
		return
	else:
		conditions["hue"]["suffix"] = ""

	if "saturation" not in conditions:
		raise RuntimeError("Cannot draw color table without saturation")
	else:
		conditions["saturation"]["suffix"] = "%"

	if "luma" not in conditions:
		raise RuntimeError("Cannot draw color table without luma")
	else:
		conditions["luma"]["suffix"] = "%"
		findFunction = find_color_for_lumas

	# find colors
	table = []
	index = {}
	condition1 = conditions["hue"]
	var1 = condition1["var"]
	for i1, hue in enumerate(condition1["values"]):
		index[var1] = i1
		condition2 = conditions["saturation"]
		var2 = condition2["var"]
		for i2, saturation in enumerate(condition2["values"]):
			index[var2] = i2
			condition3 = conditions["luma"]
			var3 = condition3["var"]
			lumas = condition3["values"]
			result = findFunction(hue, saturation, lumas)
			for i3, value in enumerate(result):
				index[var3] = i3
				iz = index["z"]
				ix = index["x"]
				if len(table) <= iz:
					tablexy = []
					table.append(tablexy)
				else:
					tablexy = table[iz]
				if len(tablexy) <= ix:
					tabley = []
					tablexy.append(tabley)
				else:
					tabley = tablexy[ix]
				tabley.append(value)
	
	# output color table
	count = len(xValues)
	width = (count if count < 10 else 10 ) * 10 + 5
	print("="*width)
	print(" "*(width/2 - 6) + "Color Table")
	print("="*width)
	if xNames is None:
		suffix = conditions[x.lower()]["suffix"]
		if count == 1:
			xNames = [ "{}({}{})".format(x, xValues[0], suffix) ]
		else:
			xNames = [ "{}{}".format(i, suffix) for i in xValues ]
		margin = width - len(x) - 10
		if (margin < 0):
			count = 0
			remain = 0
		else:
			count = margin / 4
			remain = margin % 4
		prefix = {
			0: "",
			1: "",
			2: " ",
			3: "- "
		}
		suffix = {
			0: "",
			1: " ",
			2: " ",
			3: " "
		}
		title = " " * 8 + "<" + "- " * count + prefix[remain] + x + suffix[remain] + " -" * count + ">"
	else:
		title = None
	if yNames is None:
		suffix = conditions[y.lower()]["suffix"]
		yNames = [ "{}{}".format(i, suffix) for i in yValues ]
	if zNames is None:
		suffix = conditions[z.lower()]["suffix"]
		zNames = [ "{}({}{})".format(z, i, suffix) for i in zValues ]
	for iz, zName in enumerate(zNames):
		print("{}:".format(zName))
		base = 0
		count = len(xNames)
		if title is not None:
			print(title)
		while count > 0:
			sys.stdout.write(y)
			margin = 5 - len(y)
			if margin > 0:
				sys.stdout.write(" "*margin)
			for i in range(base, count if count < 10 else 10 ):
				if margin > 0:
					sys.stdout.write("{:>10s}".format(xNames[i]))
				else:
					margin += 10 - len(xNames[i])
					if margin > 0:
						sys.stdout.write(" "*margin)
					else:
						# minimum one space separation
						margin -=1
						sys.stdout.write(" ")
					sys.stdout.write(xNames[i])
			print
			for j in range(len(yValues)):
				sys.stdout.write("{:<5s}".format(yNames[j]))
				for i in range(base, count if count < 10 else 10 ):
					rgb = table[iz][i][j]
					if rgb:
						sys.stdout.write("   #{:02X}{:02X}{:02X}".format(*rgb))
					else:
						sys.stdout.write("<NotFound>".format(*rgb))
				print
			base += 10
			count -= 10
		print
	print("="*width)
	return

def find_color_for_lumas(hue, saturation, lumas, debug = False):
	algorithm = what_luma_algorithm()
	rgbRatio = get_rgb_ratio(hue)
	if hue is None:
		hue = 0
		saturation = 0
	loRGB = [0]*3
	hiRGB = [0]*3
	loLuma = []
	loColor = []
	loDiff = []
	hiLuma = []
	hiColor = []
	hiDiff = []
	threshold = 5.0 # minimum 1.0
	weight = [0.5, 0.2, 0.3]
	for i in range(256):
		loMin = i * (100.0 - saturation) / (100.0 + saturation)
		hiMax = i + 2.0 * saturation * (255 - i) / (100.0 + saturation)
		for x, v in enumerate(rgbRatio):
			if v == 0:
				loRGB[x] = int(round(loMin))
				hiRGB[x] = i
			elif v == 1:
				loRGB[x] = i
				hiRGB[x] = int(round(hiMax))
			else:
				loRGB[x] = int(round(v * (i - loMin) + loMin))
				hiRGB[x] = int(round(v * (hiMax - i) + i))
		hls = colorsys.rgb_to_hls(*[ x / 255.0 for x in loRGB])
		diff = [ math.fabs(hue - hls[0]*360.0), math.fabs(saturation - hls[2]*100.0) ]
		if (diff[0] <= threshold and diff[1] <= threshold):
			loColor.append(list(loRGB))
			loDiff.append(list(diff))
			loLuma.append(algorithm(*loRGB))
		elif debug:
			print("Filter low i={}, RGB={}, diff={}".format(i, loRGB, diff))
		hls = colorsys.rgb_to_hls(*[ x / 255.0 for x in hiRGB])
		diff = [ math.fabs(hue - hls[0]*360.0), math.fabs(saturation - hls[2]*100.0) ]
		if (diff[0] <= threshold and diff[1] <= threshold):
			hiColor.append(list(hiRGB))
			hiDiff.append(list(diff))
			hiLuma.append(algorithm(*hiRGB))
		elif debug:
			print("Filter high i={}, RGB={}, diff={}".format(i, hiRGB, diff))

	if debug:
		print("COUNT(low) = {}".format(len(loLuma)))
		print("COUNT(high) = {}".format(len(hiLuma)))

	result = []
	for target in lumas:
		minDeviation = threshold
		color = []
		for i in range(len(loLuma)-1, -1, -1):
			diff = target - loLuma[i] * 100.0
			if diff > threshold:
				if debug:
					print("Break low at i={}, luma={}".format(i, loLuma[i]*100.0))
				break
			if diff < -threshold:
				if debug:
					print("Skip low at i={}, luma={} ".format(i, loLuma[i]*100.0))
				continue
			other = loDiff[i]
			deviation = math.sqrt(weight[0]*other[0]*other[0]
					+ weight[1]*other[1]*other[1]
					+ weight[2]*diff*diff)
			if debug:
				print("Calculate low at i={}, RGB={} dev={}, luma={}, diff={} "
						.format(i, loColor[i], deviation, loLuma[i]*100.0, other))
			if deviation < minDeviation:
				minDeviation = deviation
				color = loColor[i]
		for i, luma in enumerate(hiLuma):
			diff = luma * 100.0 - target
			if diff > threshold:
				if debug:
					print("Break high at i={}, luma={}".format(i, hiLuma[i]))
				break
			if diff < - threshold:
				if debug:
					print("Skip high at i={}, luma={} ".format(i, hiLuma[i]))
				continue
			other = hiDiff[i]
			deviation = math.sqrt(weight[0]*other[0]*other[0]
					+ weight[1]*other[1]*other[1]
					+ weight[2]*diff*diff)
			if debug:
				print("Calculate high at i={}, RGB={}, dev={}, luma={}, diff={}"
						.format(i, hiColor[i], deviation, hiLuma[i]*100.0, other))
			if deviation < minDeviation:
				minDeviation = deviation
				color = hiColor[i]
		result.append(list(color))
	return result

def find_blackwhite_by_luma(lumas):
	colorNames = [ "Black", "brBlack", "White", "brWhite" ]

	if (len(lumas) != len(colorNames)):
		raise RuntimeError("lumas count is not correct for find_blackwhite_by_luma().")
		
	rgbColors = find_color_for_lumas(None, 0, lumas)
	scheme = {}
	for i, color in enumerate(colorNames):
		scheme[color] = rgbColors[i]
	return scheme

def find_dark_set_by_luma_and_saturation(luma, saturation):
	colorNames = [ "Red", "Green", "Blue", "Yellow", "Cyan", "Magenta" ]
	scheme = {}
	colorHueMap = what_color_hue()
	for color in colorNames:
		if color not in colorHueMap:
			raise RuntimeError("Cannot find hue definition for {}", color)
		hue = colorHueMap[color]
		[rgbColor] = find_color_for_lumas(hue, saturation, [luma])
		scheme[color] = rgbColor

	return scheme

def find_light_set_by_luma_and_saturation(luma, saturation):
	colorNames = [ "brRed", "brGreen", "brBlue", "brYellow", "brCyan", "brMagenta" ]
	scheme = {}
	colorHueMap = what_color_hue()
	for color in colorNames:
		hue = None
		if color in colorHueMap:
			hue = colorHueMap[color]
		else:
			match = re.match("br([A-Z][a-z]*)", color)
			if match.group(1) in colorHueMap:
				hue = colorHueMap[match.group(1)]
		if hue is None:
			raise RuntimeError("Cannot find hue value for {} as {}".format(color, hue))
		[rgbColor] = find_color_for_lumas(hue, saturation, [luma])
		scheme[color] = rgbColor

	return scheme

def find_color_by_definition(colorDefinitions):
	scheme = {}
	for color, colorDef in colorDefinitions.iteritems():
		if "debug" in colorDef and colorDef["debug"]:
			debug = True
		else:
			debug = False
	
		hue = colorDef["hue"]
		saturation = colorDef["saturation"]
		luma = colorDef["luma"]
		[rgbColor] = find_color_for_lumas(hue, saturation, [luma], debug)
		scheme[color] = rgbColor
	return scheme

def print_color_scheme(scheme):
	print("<Colorscheme>")
	colors = what_color_order()
	for color in colors:
		if not color:
			print
			continue
		sys.stdout.write("{:<10}:".format(color))
		if color in scheme:
			rgb = scheme[color]
			if rgb:
				sys.stdout.write(" #{:02X}{:02X}{:02X}".format(*rgb))
				sys.stdout.write("   {:3d},{:3d},{:3d}".format(*rgb))
				print
				continue
		print("     <not found>")
	print
	return

def print_color_scheme_details(scheme):
	print("<Details>")
	colors = what_color_order()
	for color in colors:
		if not color:
			print
			continue
		sys.stdout.write("{:<10}:".format(color))
		rgb = scheme.get(color)
		print_color_detail(rgb)

	# print extra unlisted colors
	newLine = True
	for color in scheme:
		if color in colors:
			continue
		if newLine:
			print
			newLine = False
		sys.stdout.write("{:<10}:".format(color))
		rgb = scheme.get(color)
		print_color_detail(rgb)
	return

def print_color_detail(rgb):
	if not rgb:
		print("     <not found>")
		return
	algorithm=what_luma_algorithm()
	sys.stdout.write(" #{:02X}{:02X}{:02X}".format(*rgb))
	sys.stdout.write("   {:3d},{:3d},{:3d}".format(*rgb))
	print
	value = [ x / 255.0 for x in rgb]
	hls = colorsys.rgb_to_hls(*value)
	print("  HSL = {:.2f}, {:.4f}, {:.4f} (Hue Saturation% Lightness%)".format(hls[0]*360.0, hls[2]*100.0, hls[1]*100.0))
	hsv = colorsys.rgb_to_hsv(*value)
	print("  HSV = {:.2f}, {:.4f}, {:.4f} (Hue Saturation% Value%)".format(hsv[0]*360.0, hsv[1]*100.0, hsv[2]*100.0))
	print("  Luma% = {:.4f}".format(algorithm(*rgb)*100.0))
	return

def print_color_string(color):
	match = re.match("#?([0-9a-fA-F]{3}$)", color)
	if match:
		r = int(match.group(1)[0] + match.group(1)[0], 16)
		g = int(match.group(1)[1] + match.group(1)[1], 16)
		b = int(match.group(1)[2] + match.group(1)[2], 16)
		print "Color:"
		print_color_detail([r, g, b])
		return
	match = re.match("#?([0-9a-fA-F]{6})$", color)
	if match:
		print "Color:"
		print_color_detail([int(match.group(1)[:2], 16), int(match.group(1)[2:4], 16), int(match.group(1)[4:], 16)])
		return
	match = re.match("#?([1-2][0-9]{2})[, ]([1-2][0-9]{2})[, ]([1-2][0-9]{2})$", color)
	if match:
		print "Color:"
		print_color_detail([int(match.group(1)), int(match.group(2)), int(match.group(1)[4:])])
		return

def print_color_info(color, unknown = True):
	if isinstance(color, basestring):
		print_color_string(color)
	elif type(color) is list:
		if len(color) == 3 and isinstance(color[0], (int, long)):
			print_color_details(color)
			return
		for elem in color:
			print_color_info(elem, False)
	elif unknown:
		print("Unkown object {}".format(color))
	return

def generate_iterm2_colorscheme_file(scheme, template, output, maskAlpha = None):
	import xml.etree.ElementTree as xmlElementTree
	print("Read template from {} ... ".format(template))

	source = os.path.join(os.path.dirname(os.path.abspath(__file__)), template)
	target = os.path.join(os.path.dirname(os.path.abspath(__file__)), output)

	tree = xmlElementTree.parse(source)

	colorKeyMap = {
		"Ansi 0 Color": "Black",
		"Ansi 1 Color": "Red",
		"Ansi 2 Color": "Green",
		"Ansi 3 Color": "Yellow",
		"Ansi 4 Color": "Blue",
		"Ansi 5 Color": "Magenta",
		"Ansi 6 Color": "Cyan",
		"Ansi 7 Color": "White",
		"Ansi 8 Color": "brBlack",
		"Ansi 9 Color": "brRed",
		"Ansi 10 Color": "brGreen",
		"Ansi 11 Color": "brYellow",
		"Ansi 12 Color": "brBlue",
		"Ansi 13 Color": "brMagenta",
		"Ansi 14 Color": "brCyan",
		"Ansi 15 Color": "brWhite",
		"Background Color": "Background",
		"Foreground Color": "Foreground",
		"Selection Color": "SelectBg",
		"Selected Text Color": "SelectFg",
		"Link Color": "Links",
		"Cursor Guide Color": "LineMask",
	}
	alphaKey = [
		"Cursor Guide Color"
	]
	rgbElement = ["Red Component", "Green Component", "Blue Component"]
	alphaElement = "Alpha Component"
	
	colorList = tree.find("./dict")
	if colorList is None:
		raise RuntimeError("Cannot find main element dictionary")

	rgb = []
	alphaFlag = None
	for node in colorList.iter():
		if node.tag == "dict" and rgb:
			value = None
			for elem in node.iter():
				if elem.tag == "real" and value is not None:
					elem.text = "{}".format(value)
					value = None
				if elem.tag == "key":
					if elem.text in rgbElement:
						value = rgb[rgbElement.index(elem.text)] / 255.0
					elif alphaFlag is not None and elem.text == alphaElement:
						value = maskAlpha / 100.0
			rgb = []
		elif node.tag == "key" and node.text in colorKeyMap:
			colorName = colorKeyMap[node.text]
			if colorName in scheme:
				rgb = scheme[colorName]
			if maskAlpha and node.text in alphaKey:
				alphaFlag = alphaElement
			else:
				alphaFlag = None
	
	print("Write new colorscheme to {} ...".format(output))
	
	absPath = os.path.abspath(output)
	tree.write(target, xml_declaration=True, encoding='UTF-8', method="xml")
	print("Done with {}".format(absPath))

	return

def calculateLuma1(r, g, b):
	# W3C Method (Working Draft)
	return (0.299*r + 0.587*g + 0.114*b) / 255.0

def calculateLuma2(r, g, b):
	# sRGB Luma (Rec. 709)
	return (0.2126*r + 0.7152*g + 0.0722*b) / 255.0

def calculateLuma3(r, g, b):
	# Weighted Euclidean Distance in 3D RGB Space
	return math.sqrt(0.299*r*r + 0.587*g*g + 0.114*b*b) / 255.0

def get_color_list():
	colorNames0 = [
		"Black",
		"Red",
		"Green",
		"Blue",
		"Yellow",
		"Cyan",
		"Magenta",
		"White",
		"brBlack",
		"brRed",
		"brGreen",
		"brBlue",
		"brYellow",
		"brCyan",
		"brMagenta",
		"brWhite"
	]
	return colorNames0

def get_rgb_ratio(hue):
	hueMap = {
		0:	[   1,   0,   0], # red
		30:	[   1, 0.5,   0], # orange30
		45: [   1,0.75,   0], # yellow45
		60: [   1,   1,   0], # yellow
		90: [ 0.5,   1,   0], # green90
		120:[   0,   1,   0], # green
		150:[   0,   1, 0.5], # green150
		180:[   0,   1,   1], # cyan
		210:[   0, 0.5,   1], # blue210
		225:[   0,0.25,   1], # blue225
		240:[   0,   0,   1], # blue
		270:[ 0.5,   0,   1], # violet270
		300:[   1,   0,   1], # magenta
		330:[   1,   0, 0.5], # pink330
	}
	if hue in hueMap:
		return hueMap[hue]
	else:
		return [1,1,1]

# these function have options can be used for customization
def what_color_order():
	colorNames0 = [
		"Black", "Red", "Green", "Blue", "Yellow", "Cyan", "Magenta", "White",
		"brBlack", "brRed", "brGreen", "brBlue", "brYellow", "brCyan", "brMagenta", "brWhite",
		"",
		"Background", "Foreground", "SelectBg", "SelectFg", "Links"
	]
	colorNames1 = [
		"Black", "Red", "Green", "Blue", "Yellow", "Cyan", "Magenta", "White",
		"brBlack", "brRed", "brGreen", "brBlue", "brYellow", "brCyan", "brMagenta", "brWhite"
	]
	return colorNames0

def what_color_hue():
	standard = {
		"Red": 0,
		"Green": 120,
		"Blue": 240,
		"Yellow": 60,
		"Cyan": 180,
		"Magenta": 300,
		"White": None,
	}
	nicer = {
		"Red": 0,
		"Green": 120,
		"Blue": 225,
		"Yellow": 45,
		"Cyan": 180,
		"Magenta": 300,
		"White": None,
	}
	return nicer
		
def what_luma_algorithm():
	return calculateLuma3

# this is the MAIN function
def find_color_scheme():

	schema1 = {
		"name" : "ZDark",
		"loLuma" : 50,
		"loSaturation" : 80,
		"hiLuma" : 70,
		"hiSaturation" : 60,
		"SelectBgLuma" : 30,
		"SelectBgSaturation" : 20,
		"SelectFgLuma" : 80,
		"SelectFgSaturation" : 20,
	}
	schema2 = {
		"name" : "ZDark Shine",
		"loLuma" : 60,
		"loSaturation" : 90,
		"hiLuma" : 80,
		"hiSaturation" : 70,
		"SelectBgLuma" : 40,
		"SelectBgSaturation" : 20,
		"SelectFgLuma" : 100,
		"SelectFgSaturation" : 20,
	}
	loLuma = 50
	loSaturation = 80
	hiLuma = 70
	hiSaturation = 60
	scheme = {}
	scheme.update(find_blackwhite_by_luma([0,40,70,100]))
	scheme.update(find_dark_set_by_luma_and_saturation(loLuma, loSaturation))
	scheme.update(find_light_set_by_luma_and_saturation(hiLuma, hiSaturation))

	specialColors = {
		"Background": { "hue": 210, "luma": 10, "saturation": 10 },
		"Foreground": { "hue": 30, "luma": 90, "saturation": 10 },
		"SelectBg": { "hue": 210, "luma": 30, "saturation": 20 },
		"SelectFg": { "hue": 30, "luma": 80, "saturation": 20 },
		"Links": { "hue": 270, "luma": loLuma, "saturation": loSaturation },
		"LineMask": { "hue": 30, "luma": 50, "saturation": 50 },
	}
	scheme.update(find_color_by_definition(specialColors))

	print_color_scheme(scheme)
	#print_color_scheme_details(scheme)
	generate_iterm2_colorscheme_file(scheme,
			template="template/iTerm2.itermcolors",
			output="ZDark.itermcolors",
			maskAlpha = 10)
	return

def print_color_luma_table():
	colors = [ "Red", "Green", "Blue", "Yellow", "Cyan", "Magenta", "White" ]
	hueMap = what_color_hue()
	hues = [ hueMap[x] for x in colors ]
	lumas = range(10, 100, 10)
	definition = {
		"x" : "hue",
		"y" : "luma",
		"z" : "saturation",
		"zValues" : [100],
		"xValues" : hues,
		"yValues" : lumas,
		"xNames" : colors,
	}
	draw_color_table(**definition)
	return

def print_luma_saturation_table():
	saturations = range(10, 101, 10)
	lumas = range(10, 101, 5)
	draw_color_table("saturation", "luma", "hue", saturations, lumas, [120, 300, 210, None])
	#draw_color_table("luma", "saturation", "hue", lumas, saturations, [210])
	return

# use to find a color scheme
find_color_scheme()

# draw color table
#print_color_luma_table()
print_luma_saturation_table()


print_color_info(["c1deff","a4cdff","6F9FCF", "90b4e0","93B7DB","67A0D9"])
