alphabet = ["C", "D", "E", "F","G", "A","B"]
interval = [1,3,5,6,8,10,12]
interval_enharmonics = [12,None,6,5,None,None,1]
alph_dict = dict((k,v) for (k,v) in zip(alphabet,interval))
alph_dict_enharm = dict((v,k) for (k,v) in zip(alphabet,interval))
flat = "b♭"
sharp = "#♯"
slash = r"\/\／\\\＼"
accidentals = flat + sharp
alph_dict_val = list(alph_dict.values())
alph_dict_keys = list(alph_dict.keys())