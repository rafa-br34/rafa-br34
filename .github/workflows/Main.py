import sys
import os
import re
import subprocess
import PyCLOC
from github import Github

FILE_README = "README.md"
FILE_README_TEMPLATE = "README_TEMPLATE.md"

GithubClient = Github(os.environ["GH_ACCESS_TOKEN"])

def main():
	User = GithubClient.get_user()
	for Repo in User.get_repos():
		if not Repo.fork:
			print(Repo.clone_url)
		


	Template = ""
	with open(FILE_README_TEMPLATE, "r") as TemplateFile:
		Template = TemplateFile.read()
		TemplateFile.close()

	for Key in Dictionary:
		Flag = "%" + Key + "%"
		print(Flag, "->", Dictionary[Key])
		Template = Template.replace(Flag, str(Dictionary[Key]))

	if os.path.isfile(FILE_README):
		os.remove(FILE_README)
	with open(FILE_README, "w") as Output:
		Output.write(Template)
		Output.close()

if __name__ == '__main__':
	main()