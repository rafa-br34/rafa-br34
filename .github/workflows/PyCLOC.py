from pathlib import Path
import copy
import re

_TEST_BUILD = True

LanguageFlags = {
	"COMPILED": 	1 << 0, # Compiled Languages: CPP, C, Fortran, Etc
	"ASSEMBLED": 	1 << 1, # Assembled Languages: S, ASM, X86, X64
	"BC_ASSEMBLED": 1 << 2, # ByteCode Assembled Languages: Java, C#, Etc
	"INTEPRETED": 	1 << 3, # Interpreted Languages: Lua, Python, Etc
	
	"LOW_LEVEL": 	1 << 4, # Low Level Languages: Assembly, C++, C, Etc
	"HIGH_LEVEL": 	1 << 5, # High Level Languages: Java, Lua, Python, C#, Etc

	"LANG_DATA_DESCRIPTION": 	1 << 6, # HTML, XML, JSON, Etc
	"LANG_PROGRAM_DESCRIPTION": 1 << 7, # CPP, CS, JAVA, Etc
	"LANG_USER_DESCRIPTION": 	1 << 8,	# MD, TXT, HTML, Etc
	"LANG_OTHER_DESCRIPTION": 	1 << 9,	# Unknown Formats
}
def FLAG(Name, Dict=LanguageFlags):
	return Dict[Name]

_LANGS_BLANK_DEFAULT = [r"^[\s\t]*$\r?\n", re.MULTILINE]

_LANGUAGES = [
	{
		"Name": "Unknown",
		"Flags": FLAG("LANG_OTHER_DESCRIPTION"),
		"Suffixes": [],
		"IdentConditions": None,
		"Format": {
			"Type": "REGEX",
			"RemovalOrder": ["Blank", "Comments", "Code"],

			"Comments": [],
			"Blank": [_LANGS_BLANK_DEFAULT],
			"Code": [],
		}
	},
	{
		"Name": "C++ Source",
		"Flags": FLAG("COMPILED") | FLAG("LOW_LEVEL") | FLAG("LANG_PROGRAM_DESCRIPTION"),
		"Suffixes": [".cpp"],
		"IdentConditions": None,
		"Format": {
			"Type": "REGEX",
			"RemovalOrder": ["Blank", "Comments", "Code"],

			"Comments": [r"\/\/.*\n", r"\/\*(.|\n)+?\*\/"],
			"Blank": [_LANGS_BLANK_DEFAULT],
			"Code": [r"(?:.|\n)+"],
		}
	},
	{
		"Name": "C Source",
		"Flags": FLAG("COMPILED") | FLAG("LOW_LEVEL") | FLAG("LANG_PROGRAM_DESCRIPTION"),
		"Suffixes": [".c"],
		"IdentConditions": None,
		"Format": {
			"Type": "REGEX",
			"RemovalOrder": ["Blank", "Comments", "Code"],

			"Comments": [r"\/\/.*\n", r"\/\*(.|\n)+?\*\/"],
			"Blank": [_LANGS_BLANK_DEFAULT],
			"Code": [r"(?:.|\n)+"],
		}
	},
	{
		"Name": "C/C++ Header",
		"Flags": FLAG("COMPILED") | FLAG("LOW_LEVEL") | FLAG("LANG_PROGRAM_DESCRIPTION"),
		"Suffixes": [".h"],
		"IdentConditions": None,
		"Format": {
			"Type": "REGEX",
			"RemovalOrder": ["Blank", "Comments", "Code"],

			"Comments": [r"\/\/.*\n", r"\/\*(.|\n)+?\*\/"],
			"Blank": [_LANGS_BLANK_DEFAULT],
			"Code": [r"(?:.|\n)+"],
		}
	},
]

def _GetFilesFromDir(Dir=""):
	return Path(".").glob(f"{Dir}/**/*.*")

def _IdentifyLang(Data, Suffix=""):
	PossibleLangs = []
	for Lang in _LANGUAGES:
		if (Suffix in Lang["Suffixes"]):
			if callable(Lang["IdentConditions"]) and not Lang["IdentConditions"](Data):
				continue
			PossibleLangs.append(Lang)

	
	if len(PossibleLangs) > 1 and _TEST_BUILD:
		print("WARNING: Filtered Table Had More Than One Element", PossibleLangs)

	return (len(PossibleLangs) >= 1) and PossibleLangs[0]

def _CLOC(Lang, Data):
	Metadata = {}

	LANG_NAME = (("Name" in Lang) and Lang["Name"]) or "Unnamed"
	if not ("Format" in Lang) or not ("Name" in Lang):
		raise Exception(f"Malformed Language Dictionary In Language: {Name}")
	LFMT = Lang["Format"]

	if LFMT["Type"] == "REGEX":
		for RemovalKey in LFMT["RemovalOrder"]:

			if not RemovalKey in Metadata:
				Metadata[RemovalKey] = 0

			for RegExData in LFMT[RemovalKey]:
				RegEx = (type(RegExData) == str and RegExData) or (type(RegExData) == list and RegExData[0]) or None
				Flags = (type(RegExData) == list and RegExData[1]) or None
				if not RegEx:
					raise Exception(f"Invalid RegEx Data For {LANG_NAME}")

				Result = None
				if Flags:
					Result = re.findall(string=Data, pattern=RegEx, flags=Flags)
					Data = re.sub(pattern=RegEx, repl="", string=Data, flags=Flags)
				else:
					Result = re.findall(string=Data, pattern=RegEx)
					Data = re.sub(pattern=RegEx, repl="", string=Data)
				
				TotalLines = 0
				for Chunk in Result:
					TotalLines += Chunk.count("\n")
				
				Metadata[RemovalKey] += TotalLines
				
	else:
		raise Exception("Unsupported String Match Type")

	return Metadata

def ScanData(Data, Suffix, ReturnMetadata=False):
	Lang = _IdentifyLang(Data, Suffix) or _LANGUAGES[0]
	MT = _CLOC(Lang, Data)
	if ReturnMetadata:
		return MT, Lang
	else:
		return {
			"BlankLines": MT["Blank"], 
			"CommentLines": MT["Comments"], 
			"CodeLines": MT["Code"], 
			"TotalLines": MT["Blank"] + MT["Comments"] + MT["Code"],
			"Language": Lang
		}


def ScanFile(FilePath):
	if not FilePath:
		raise Exception("FilePath Argument Is Empty/None")

	FPO = Path(FilePath)
	MT, Lang = ScanData(FPO.read_text(), FPO.suffix, ReturnMetadata=True)
	return {
		"CommentLines": MT["Comments"],
		"BlankLines": MT["Blank"], 
		"CodeLines": MT["Code"], 
		"TotalLines": MT["Blank"] + MT["Comments"] + MT["Code"],
		"Language": Lang,
		"File": FPO
	}
	
	

def ScanDir(DirPath):
	if not DirPath:
		raise Exception("DirPath Argument Is Empty/None")

	Results = []

	for FP in _GetFilesFromDir(DirPath):
		Results.append(ScanFile(FP))
		
	Totals = {}

	for Result in Results:
		if not (Result["Language"]["Name"] in Totals):
			Totals[Result["Language"]["Name"]] = {
				"CommentLines": 0,
				"BlankLines": 0,
				"CodeLines": 0,
				"TotalLines": 0,
				"Language": Result["Language"]
			}
		Total = Totals[Result["Language"]["Name"]]
		Total["CommentLines"] += Result["CommentLines"]
		Total["BlankLines"] += Result["BlankLines"]
		Total["CodeLines"] += Result["CodeLines"]

	for Key in Totals:
		Total = Totals[Key]
		Total["TotalLines"] = Total["CommentLines"] + Total["BlankLines"] + Total["CodeLines"]

	return Totals, Results

def TEST():
	T,L=ScanDir("BigLib")
	print(T["Language"]["Name"], T["TotalLines"])


if __name__ == "__main__":
	if not _TEST_BUILD:
		raise Exception("Should Be Ran As Module")
	else:
		TEST()