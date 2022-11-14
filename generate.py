import zlib
import sys
import hashlib
import re
import os
import io

class GitAuthor:
	def __init__(self, username, email, timepoint, timezone):
		self.username  = username
		self.email     = email
		self.timepoint = timepoint
		self.timezone  = timezone
	
	def __str__(self):
		return f"{self.username:s} <{self.email:s}> {self.timepoint:d} {self.timezone:+05d}"

class GitCommit:
	def __init__(self, treeHash, parentCommitHash, author, committer, message, gpgsig=""):
		self.treeHash         = treeHash
		self.parentCommitHash = parentCommitHash
		self.author           = author
		self.committer        = committer
		self.message          = message
		self.gpgsig           = gpgsig
	
	def createCommit(self):
		content  = self.encoding()
		file     = f"commit {len(content):d}\0{content}".encode()
		hashcode = hashlib.sha1(file).hexdigest()
		return (zlib.compress(file), hashcode)
	
	def encoding(self):
		string = f"tree {self.treeHash:s}"
		if len(self.parentCommitHash) > 0:
			string += f"\nparent {self.parentCommitHash:s}"
		string += f"\nauthor {self.author}\ncommitter {self.committer}"
		if len(self.gpgsig) > 0:
			gpgsig = re.sub("\n", "\n ", self.gpgsig)
			string += f"\ngpgsig -----BEGIN PGP SIGNATURE-----\n\n{gpgsig:s}\n -----END PGP SIGNATURE-----"
		string += f"\n\n{self.message:s}"
		return string

class GitTreeEntry:
	def __init__(self, mode, hash, name):
		self.mode = mode
		self.hash = hash
		self.name = name
	
	def encoding(self):
		return f"{self.mode:d} {self.name:s}\0".encode() + bytes.fromhex(self.hash)

class GitTree:
	def __init__(self, entries = []):
		self.entries = entries
	
	def addBlob(self, name, mode, hash):
		self.entries.append(GitTreeEntry(mode, hash, name))
	
	def addTree(self, name, mode, hash):
		self.entries.append(GitTreeEntry(mode, hash, name))
	
	def createTree(self):
		content  = self.encoding()
		file     = f"tree {len(content):d}\0".encode() + content
		hashcode = hashlib.sha1(file).hexdigest()
		return (zlib.compress(file), hashcode)
	
	def encoding(self):
		string = b""
		for entry in self.entries:
			if len(string) > 0:
				string += b"\n"
			string += f"{entry.mode:d} {entry.name:s}\0".encode()
			string += bytes.fromhex(entry.hash)
		return string

class GitBlob:
	def __init__(self, content):
		self.content = content
	
	def createBlob(self):
		content  = self.encoding()
		file     = f"blob {len(content):d}\0".encode() + content
		hashcode = hashlib.sha1(file).hexdigest()
		return (zlib.compress(file), hashcode)
	
	def encoding(self):
		return f"{self.content}".encode()

def AddObject(object):
	dir      = f".git/objects/{object[1][:2]:s}"
	filepath = f"{dir:s}/{object[1][2:]:s}"
	try:
		os.makedirs(dir)
	except:
		pass
	open(filepath, "wb").write(object[0])

author = GitAuthor("MarcasRealAccount", "thetremine.lumicks@gmail.com", 0, 0)

max       = 4294967295
deltaT    = 10800
timepoint = 0
i         = 0

print(f"Creating commits from 0 -> {max}, {max / deltaT} commits")
input("... Wait ...")
previousCommitHash = ""
while timepoint < max:
	author.timepoint = timepoint
	
	blob       = GitBlob(f"Commit {i}")
	blobObject = blob.createBlob()
	
	tree = GitTree([])
	tree.addBlob("README.md", 100644, blobObject[1])
	treeObject = tree.createTree()
	
	commit       = GitCommit(treeObject[1], previousCommitHash, author, author, f"Commit {i}")
	commitObject = commit.createCommit()
	
	AddObject(blobObject)
	AddObject(treeObject)
	AddObject(commitObject)
	
	if (i & 8) == 0:
		sys.stdout.write(f"\rCommit {i} '{commitObject[1]}'")
	previousCommitHash = commitObject[1]
	timepoint += deltaT
	i += 1

print(f"\nHEAD commit: '{previousCommitHash:s}'")