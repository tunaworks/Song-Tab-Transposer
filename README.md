# chord_transposer
Transposes a given chord progression sheet to a specific key 

Files:
* main.py (program to run)
* input_reader.py (bulk of program, handles parsing of text and transposing of chords)
* alphabet.py (contains scale and interval degrees, musical notation references)

settings.py (edit new key and formatting settings here)
.env (placeholder)


Input: A .txt file containing a song tab in the following format

input.txt
  ```
  $a = name of song section (eg. A,B,Chorus)
  $b = original key of section
  $c = (optional) a time signature (default: 4/4)
  $delimiter = any character to distinguish between bars (eg "|", ",")
  =====================================================
  [$a] (Key:$b)
  $c $delimiter $lyrics
  chord1 chord2 $delimiter chord3 $delimiter etc...
  ```

<h2>example</h2>
---------------------------------------
(delimiter at the start of the line is optional.)
```
[Cho] (Key:G) Lyrics
| GM7     | %      | F#m7-5 | B7       |
| Em      | Dm7    | C#m7-5 | %        |
| CM7     | D      | Bm7    | Bbdim7   |
| Am7     | G/B    | Eb     | F        |
```

after running `main.py` with a targetkey of `C`: 

```
[Cho] (Key:C) ひびけファンファーレ とどけゴールまで
| CM7     | %      | Bm7-5  | E7       |
| Am      | Gm7    | F#m7-5 | %        |
| FM7     | G      | Em7    | Ebdim7   |
| Dm7     | C/E    | Ab     | A#       |
```
