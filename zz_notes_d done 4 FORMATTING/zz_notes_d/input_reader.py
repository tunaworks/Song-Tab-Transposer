import os
import sys
import re
import settings
import alphabet

"""
Reads from input text file, creates
	- Song() class containing a list of Section() objects
	- Each Section() contains a sequence of Chord() objects that can be transposed later
"""
def Read(file,outdir=None):

	with open(file,"r") as infile:
		# automatic output file naming
		infilename = os.path.basename(file)
		fileno = re.findall(r"\d+", infilename)[0]
		outname = os.path.join(outdir,f"out{fileno}.txt")

		# create new output file (overwrite existing)
		if os.path.exists(outname):
			k = input(f"{outname} exists. Overwrite? [Y/N]")
			if k.upper() == "Y":
				print(f"Writing to {os.path.basename(outname)}...")
				outfile = open(outname,"w")
			elif k.upper() == "N":
				print("Writing cancelled.")
				return
			else:
				print("Invalid input. Writing cancelled.")
				return
		# read input file

		# [In] (Key:G) ひびけファンファーレ...
		# [target] is always captured, (key:target) is optional, lyrics.. is ignored
		#patt_head = r"\[(\w+)\]\s*(?:.*\:(.+)\))?"
		patt_head = r"\[(?P<name>\w+[^\s]*)\](\s*\((Key\:\s*(?P<key>[^\s]+))\s*\))?"

		# \[(?P<name>\w+[^\s]*)\](\s*\((Key\:\s*(?P<key>[^\s]+))\s*\))?
		# | Db      | Cb/Db  | Gb     | Gbm      |
		patt_body = r"([^\s"+ f"\{settings.delimiter}" + "])+"
		# 3/4 or 4282484/42248428248
		patt_timesig = r"\((\d+)\/(\d+)\)"
		song = Song()

		for line in infile:
			newline = line
			# section header
			if line.startswith("["):
				res = re.search(patt_head,line,re.I)
				# if ^[name] ... found
				if res:
					section = Section()
					section.name = res.group("name")
					# if found a new specified key, store AND get transpose number
					if res.group("key") is not None:
						section.key = res.group("key")
						section.transpose = transpose_num(section.key)
						if settings.flag_show_original_key is False:

							newchord = transpose_note(section.transpose, section.key)
							line = re.sub(res.group("key"),newchord,line)
					else:
						# inherit previous key sig if not specified in this header
						if len(song.sections) > 0:
							prev_sect = song.sections[-1]
							if prev_sect.key is not None:
								section.key = prev_sect.key
							else:
								section.key= settings.defaultkey
						else:
							section.key = settings.defaultkey



					reshead_time = re.search(patt_timesig, line,re.I)

					# in case TIME SIG is on header line
					if reshead_time:
						section.timesig_num = reshead_time.group(1)
						section.timesig_denom = reshead_time.group(2)
					else:
						# else, inherit TIME SIG from previous section
						if len(song.sections) > 0:
							prev_sect = song.sections[-1]
							if prev_sect.timesig_num is not None:
								section.timesig_num = prev_sect.timesig_num
								section.timesig_denom = prev_sect.timesig_denom
					#print("\n" + "="*50 + f"\nok:{section.key} nk:{settings.targetkey}")
					song.add(section)

			# SECTION CHORD LINE
			#elif line.startswith(settings.delimiter):
			else:
				res = re.finditer(patt_body,line,re.I)
				res_list = [x for x in res]
				if res_list:
					# parsing each |   item   |
					for token_match in res_list:
						token_idx = [token_match.start(),token_match.end()]
						token = token_match.group()
						res_time = re.search(patt_timesig,token)

						# TIME_SIG: if (4/5) or something found
						# if section already has time sig, this is a time sig change
						if res_time:
							if section.timesig_num is not None:
								newsection = Section(name=section.name,key=section.key)
								newsection.timesig_num = res_time.group(1)
								newsection.timesig_denom = res_time.group(2)
								song.add(newsection)
								section = newsection
								# add previous (same name, diff time sig) section to song
							# same section time sig
							else:
								section.timesig_num = res_time.group(1)
								section.timesig_denom = res_time.group(2)

						# CHORDS
						else:
							# jazz spelling: % means repeat last chord
							if token=="%":
								continue
								if len(section.sequence) is not None:
									chord = Chord(title=token,fullname=section.sequence[-1])
							else:
								# Em/Cb5-7, Cb/Db
								#(?P<chord>[^\s\/\／\\\＼]+)([\/\／\\\＼](?P<slash>[^\s]+)){0,1}
								patt_chord = \
								f"(?P<chord>[^\s{alphabet.slash}]+)([{alphabet.slash}](?P<slash>[^\s]+))" + "{0,1}"
								patt_chord = re.compile(patt_chord,re.I)
								res_token = re.search(patt_chord,token)
								if res_token:
									#print(res_token.group("slash"))
									chord = Chord(title=token,fullname=res_token.group("chord"),slashnote=res_token.group("slash"))
									#print(res_token.group("slash"), chord.slashnote)
									newchord = transpose_chord(section,chord)
									newline = text_formatter(chord,newchord,line,newline,token_match)
									section.sequence.append(chord)

			#print()
			outfile.write(newline)
			#print(line)
		#print(song)

def transpose_chord(section,chord):
	newnote = transpose_note(section.transpose,chord.note)
	remainder = [chord.qual,chord.ext,chord.slashnote]
	newfullname = newnote
	for thing in remainder:
		if thing is not None:
			if thing == chord.slashnote:
				newfullname+= "/"
				newslashnote = transpose_note(section.transpose,chord.slashnote)
				newfullname += newslashnote
			else:
				newfullname+=thing
	#print(chord.slashnote)
	return newfullname
"""
	Note_num()
		returns (interval number) of given note
		* accounts for accidentals
"""
def note_num(note):
	alph_dict = alphabet.alph_dict
	alph_dict_val = alphabet.alph_dict_val
	alph_dict_keys = alphabet.alph_dict_keys
	# note_num = whole note interval val + accidental modifier (-1/0/+1)
	note_num = alphabet.alph_dict.get(note[0]) + isaccidental(note)
	return note_num
"""
	Transpose_num
		returns number of semitones to transpose by (-/+)
		* already accounts for accidentals
"""
def transpose_num(note):
	# only contains values of whole tones as if there were accidentals
	# we dont have combinations of every accidental,
	# we just check if its -1 or +1 later along with the whole note
	#alph_dict = dict((k,v*2) for (v,k) in enumerate(alphabet.alphabet))
	alph_dict = alphabet.alph_dict
	alph_dict_val = alphabet.alph_dict_val
	# eg Eb7-5/A
	oldnote = note
	targetkey = settings.targetkey

	# get whole note number (excl accidentals)
	oldnote_num = note_num(oldnote)
	targetkey_num = note_num(targetkey)

	# IMPORTANT: MAKE SURE ITS targetkey - oldnote, else its transposing UP
	transpose_mod = (targetkey_num - oldnote_num) % alph_dict_val[-1]

	# READABILITY fix: shift transpose number up/down an octave if it's too high
	if abs(transpose_mod) > 6:
		if transpose_mod >= 0:
			transpose_mod -= 12
		else:
			transpose_mod += 12
	return transpose_mod
	# print(f"{oldnote}->{targetkey} | {oldnote_num} -> {targetkey_num} ({transpose_mod})")
	# return "Ab"
def transpose_note(transpose_mod,note):
	# only contains values of whole tones as if there were accidentals
	# we dont have combinations of every accidental,
	# we just check if its -1 or +1 later along with the whole note
	#alph_dict = dict((k,v*2) for (v,k) in enumerate(alphabet.alphabet))
	alph_dict = alphabet.alph_dict
	alph_dict_val = alphabet.alph_dict_val
	alph_dict_keys = alphabet.alph_dict_keys
	alph_dict_enharm = alphabet.alph_dict_enharm

	# get whole note name
	oldnote_num = note_num(note)
	newnote_num = ((oldnote_num + transpose_mod - 1 )  % ((alph_dict_val[-1]))) + 1
	if newnote_num not in alph_dict_val:
		# new note is flat
		if isaccidental(note) == -1:
			# (newnote_num already includes accidentals)
			# if oldnote was flat, use next whole note for name
			# if oldnote was sharp, use prev whole note for name
			new_scaledegree = (newnote_num + 1 )  % ((alph_dict_val[-1]) + 1)
			newnote_num = alph_dict_val.index(new_scaledegree)
			newnote = alph_dict_keys[newnote_num]
			# (upper note name we rounded up to) (flat)
			newnote += alphabet.flat[0]
			#print(f"{note}{newnote} -> {settings.targetkey} |{oldnote_num}-> {new_scaledegree} ({transpose_mod})")

		# new note is accidental
		else:
			new_scaledegree = (newnote_num - 1 )  % ((alph_dict_val[-1]) + 1)
			newnote_num = alph_dict_val.index(new_scaledegree)
			newnote = alph_dict_keys[newnote_num]
			# (lower note name we rounded down to) (sharp)
			newnote += alphabet.sharp[0]
			#print(alph_dict_keys[alph_dict_val.index(new_idx)])
			#newnote = str(alph_dict_keys[alph_dict_val.index(new_idx)])

	# new note is whole note
	else:
		newnote = alph_dict_keys[alph_dict_val.index(newnote_num)]


	# TODO? check for ENHARMONIC SPELLING
	if note=="Cb":
		#print(newnote)
		if len(newnote) > 1:
			if newnote[0] == alph_dict_enharm.get(newnote_num):
				print("yeah", newnote_num, newnote)


	#print(f"{note} -> {settings.targetkey} |{oldnote_num}-> {newnote_num} ({transpose_mod})")
	#return "C"
	return newnote
	#print(f"{chord.fullname}({note_num}):{newfullname}({newnote_num})")
	#print(chord)


def isaccidental(note):
	patt_flat = f"[{alphabet.flat}]" + "{1}"
	patt_sharp = f"[{alphabet.sharp}]" + "{1}"
	if len(note) > 1:
		if re.search(patt_flat,note):
			return -1
		elif re.search(patt_sharp,note):
			return 1
	return 0

"""

- works, tranpose chords given certain key
- makes sure transpose number is readable (<=6 )

TODO:
- make sure chord note name is according to scale (ie Key:D Should have F#, not Gb)
"""
def text_formatter(chord,newchord,line,newline,token_match):
	# [^\S]+[^\s]*[^\S]+(?=[\,])
	# ([\s]*[^\s]*[\s]*)([\s]*(?=[\|]))
	# [\s*](?![^\w])[^\s]*[\s]*(?=[\|]|[^\S]+)
	#patt_entry = fr"[^\S]+[^\s]*[^\S]+(?=[{settings.delimiter}])"
	#res = (re.search(patt_entry,line))
	#if res is not None:
		#print (res.group())
	token_start = token_match.start()
	token_end = token_match.end()
	token = token_match.group()
	patt_chord = "(?<![^\s])"+ f"{token}" + r"(?=(\s|" + f"[{alphabet.slash}]" "))"

	if len(newchord) < len(chord.title):
		spacing = abs(len(newchord) - len(chord.title))
		#print(chord.title,newchord, spacing)
		spacing = " " * spacing
		newchord += spacing


	# Trims extra spacing (if present in original text)
	# if new chord name is LONGER than original chord name (eg F -> F#m replaces two spaces along with chord name)
	elif len(newchord) > len(chord.title):
		spacing = abs(len(newchord) - len(chord.title))
		# next immediate spacing
		patt_imm_space = "[\s]+(?=\b|"+ f"[{settings.delimiter}]" + ")"
		excerpt = line[token_start:]
		if (len(excerpt) >= spacing):
			res = re.search(patt_imm_space,excerpt).group()
			if res:
				if len(res) >= spacing:
					patt_chord = r"(?<![^\s])" + f"{chord.title}" + f"[\s]{{{spacing}}}" + f"(?=\s|(" f"[{alphabet.slash}]"+ "))"
	#(?<![^\s]){note_name}\b


	#print(patt_chord)
	patt_chord = re.compile(patt_chord,re.I)
	"""
	if re.search(patt_chord,line ) is None:
		print(token + " | " + repr(patt_chord))
		print(line)
		print(re.search(patt_chord,line))
	"""
	newline = re.sub(patt_chord,newchord,newline)


	return newline


def transpose_old(section,chord,line):
	# only contains values of whole tones as if there were accidentals
	# we dont have combinations of every accidental,
	# we just check if its -1 or +1 later along with the whole note
	#alph_dict = dict((k,v*2) for (v,k) in enumerate(alphabet.alphabet))
	alph_dict = alphabet.alph_dict

	oldkey = section.key
	targetkey = settings.targetkey
	note = chord.note
	oldkey_num = alph_dict.get(oldkey[0])
	targetkey_num = alph_dict.get(targetkey[0])

	flag_newflat = False
	flag_newsharp = False
	newnote = None
	# tranpose modifiers for accidentals

	alph_dict_val = list(alphabet.alph_dict.values())
	oldkey_num += isaccidental(oldkey)

	targetkey_num += isaccidental(targetkey)
	# IMPORTANT: MAKE SURE ITS targetkey - oldkey, else its transposing UP
	transpose_mod = (targetkey_num - oldkey_num) % alph_dict_val[-1]

	# READABILITY fix: shift transpose number up/down an octave if it's too high
	if abs(transpose_mod) > 6:
		if transpose_mod >= 0:
			transpose_mod -= 12
		else:
			transpose_mod += 12

	# get whole note name
	note_num = alph_dict.get(chord.note[0])
	newnote_num = (note_num + transpose_mod) % alph_dict_val[-1]
	alph_dict_keys = list(alphabet.alph_dict.keys())
	if newnote_num not in alph_dict_val:

		# new note is flat
		if isaccidental(note) == -1:
			new_idx = (newnote_num - 1) % (alph_dict_val[-1] + 1)
			newnote = alph_dict_keys[alph_dict_val.index(new_idx)]
			#newnote += alphabet.flat[0]
		# new note is accidental
		else:
			new_validx = (newnote_num + 1) % (alph_dict_val[-1] + 1)
			new_idx = alph_dict_val.index(new_validx)
			newnote = alph_dict_keys[new_idx]
			#newnote += alphabet.sharp[0]
			#print(alph_dict_keys[alph_dict_val.index(new_idx)])
			#newnote = str(alph_dict_keys[alph_dict_val.index(new_idx)])

	# new note is whole note
	else:
		newnote = alph_dict_keys[alph_dict_val.index(newnote_num)]

	remainder = [chord.qual,chord.ext,chord.slashnote]
	newfullname = newnote
	for thing in remainder:
		if thing is not None:
			if thing == chord.slashnote:
				newfullname+= "/"
			newfullname+=thing
	return newfullname
	#print(f"{chord.fullname}({note_num}):{newfullname}({newnote_num})")
	#print(chord)
	"""
	if flag_newflat:
		newnote = list(alph_dict.keys())[transpose_mod+1]
	elif flag_newflat:
		newnote = list(alph_dict.keys())[transpose_mod-1]
	else:
		newnote = list(alph_dict.keys())[transpose_mod]
	"""
	"""
	if transpose_mod % 2:
		newnote = alphabet.alphabet[abs(transpose_mod)]
	print(transpose_mod)
	"""
	#transpose_mod = alph_dict.get(targetkey[0]) - alph_dict.get(oldkey[0])
	#newnote_idx = (alphabet.index(note[0]) + transpose_mod) % len(alphabet)
	#newnote = alphabet[newnote_idx]
	#
	#print(transpose_mod)
	#print(f"({chord.note} -> {newnote}) ",end="")



"""
Chord
-------------
CHORD NAMES ARE NOT PROCESSED HERE. eg A Chord could be (Em7-5)

TODO (01/04/2022) PROCESS CHORDS IN ANOTHER FILE.

title = chord name to print out
name = actual chord value to process internally (eg we print % as %, but process it as (previous chord name))
"""
class Chord():
	def __init__(self,title=None,fullname=None,slashnote=None):
		# name to display on screen
		self.title = title
		# actual chord name
		self.fullname = fullname
		self.note = None
		self.qual = None
		self.ext = None

		# alphabets/private regex alphabet
		self.accidentals = alphabet.accidentals
		self.alph_qual = "+oo+"
		self.slashnote = slashnote
		# Asus4, Amaj7, AminM7 etc
		self.alph_qual_two = "sus|maj|min|aug|dim"
		#
		self.alph_qual_three = "m|maj|min"
		self.process()
	# prints out true chord name (eg Ab % would return Ab Ab)
	def __repr__(self):
		output = f"string:{self.title}\tinternal:{self.fullname}"
		return output
	def process(self):
		# A, Ab, C# etc
		# ^(?P<note>\D{1}[b#♯♭]{0,1})

		# maj$,min$,m$,M$, sus..,maj..,aug..., etc
		# (?P<quality>[+oo+]{0,1}(sus|maj|min|aug|dim){0,1}(m|maj|min$){0,1})

		# 7,7#9, 7b9 etc
		# (?P<extension>([\d]){0,2}([b#♯♭]\d{1,2}){0,1})

		# ... /C , .../Ab ,etc
		# (\/(?P<note2>\D{1}[b#♯♭]{0,1})){0,1}
		patt_note = r"^(?P<note>\D{1}[" + self.accidentals + "]{0,1})"
		patt_qual = r"(?P<quality>[" + self.alph_qual + "]{0,1}(" + self.alph_qual_two + "){0,1}(" + self.alph_qual_three + "$){0,1})"
		patt_ext = r"(?P<extension>([\d]){0,2}([b#♯♭]\d{1,2}){0,1}([-]\d{1,2}){0,1})"
		#patt_note2 = r"(\/(?P<note2>\D{1}[" + self.accidentals + "]{0,1})){0,1}"

		full_patt = re.compile(patt_note + patt_qual + patt_ext, re.I)
		#print(patt_note + patt_qual + patt_ext + patt_note2)

		res = re.search(full_patt,str(self.fullname))
		if res:
			self.note = res.group("note") if res.group("note") else None
			self.qual = res.group("quality") if res.group("quality") else None
			self.ext = res.group("extension") if res.group("extension") else None
			#self.slashnote = res.group("note2") if res.group("note2") else None

class Song():
	def __init__(self):
		self.name = None
		self.sections = list()
		self.tempo = None
	def __repr__(self):
		output = ""
		if len(self.sections) > 0 :
			for section in self.sections:
				output += str(section)
		else:
			output+=("input_reader Read() is not adding Section objects to Song class.")
		return output
	def add(self,section):
		self.sections.append(section)
"""
Section
eg. [FF] Key:D, 3/8
"""
class Section():
	def __init__(self,name=None,key=None):
		self.key=key
		self.targetkey = None
		self.name=name
		self.timesig_num=None
		self.timesig_denom=None
		self.transpose = 0
		self.sequence=list()
	def __repr__(self):
		header = f"Section:{self.name} | Key:{self.key} | ({self.timesig_num}/{self.timesig_denom})\n"
		body = f"{self.sequence}\n"
		return (header+body)