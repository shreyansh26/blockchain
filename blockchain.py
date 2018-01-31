from urllib.parse import urlparse
from time import time
import json
import hashlib
import requests

class Blockchain(object):
	def __init__(self):
		self.chain = []
		self.current_transactions = []
		self.nodes = set()

		self.new_block(proof=100, previous_hash=1)

	def new_block(self, proof, previous_hash=None, ):
		"""
		Creates a new Block and adds it to the chain
		Params -
		1. previous_hash - The hash of the previous block
		2. proof - The proof obtained from the Proof Of Work algorithm
		3. return - <dict> New Block
		"""
		block = {
			'index': len(self.chain)+1,
			'timestamp': time(),
			'transactions': self.current_transactions,
			'proof': proof,
			'previous_hash': previous_hash or self.hash(self.chain[-1])
		}

		# Reset the current list of transactions
		self.current_transactions = []
		self.chain.append(block)
		return block

	def new_transaction(self, sender, recipient, amount):
		"""
		Creates a new transaction to go into the Blockchain
		Params -
		1. sender - Address of the sender
		2. recipient - Address of the recipient
		3. amount - The amount to be sent
		4. return - <int> The index of the block that will hold this transaction
		"""
		self.current_transactions.append({
			'sender': sender,
			'recipient': recipient,
			'amount': amount,
			})

		return self.last_block['index'] + 1

	@staticmethod
	def hash(block):
		"""
		Creates a SHA-256 hash of the block
		Params -
		1. block - The Block
		2. return - <str> The hash
		"""
		block_string = json.dumps(block, sort_keys=True).encode()
		return hashlib.sha256(block_string).hexdigest()

	@property
	def last_block(self):
		return self.chain[-1]

	def proof_of_work(self, last_proof):
		"""
		Simple Proof of Work Algorithm:
		 - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
		 - p is the previous proof, and p' is the new proof
		Params-
		1. last_proof: <int> last proof
		2. return: <int> new proof
		"""
		proof = 0
		while(self.valid_proof(last_proof, proof) is False):
			proof += 1

		return proof

	@staticmethod
	def valid_proof(last_proof, proof):
		"""
		Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
		:param last_proof: <int> Previous Proof
		:param proof: <int> Current Proof
		:return: <bool> True if correct, False if not.
		"""
		guess = f'{last_proof}{proof}'.encode()
		guess_hash = hashlib.sha256(guess).hexdigest()
		return guess_hash[:4] == "0000"

	def register_node(self, address):
		"""
		Add a new node to the list of nodes
		Params-
		1. address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
		2. return None
		"""
		parsed_url = urlparse(address)
		self.nodes.add(parsed_url.netloc)

	def valid_chain(self, chain):
		"""
		Determine if a blockchain is valid
		Params-
		1. <list> A Blockchain
		2. <bool> True if valid, False if not
		"""
		last_block = chain[0]
		current_index = 1

		while(current_index < len(chain)):
			block = chain[current_index]
			print(f'{last_block}')
			print(f'{block}')
			print('\n-----------\n')
			
			# Check that the hash of the block is correct
			if block['previous_hash'] != self.hash(last_block):
				return False
			# Check that the Proof of Work is correct
			if not self.valid_proof(last_block['proof'], block['proof']):
				return False

			last_block = block
			current_index += 1

		return True

	def resolve_conflicts(self):
		"""
		This is our Consensus Algorithm, it resolves conflicts
		by replacing our chain with the longest one in the network

		return- <bool> true if our chain was replaced, False otherwise
		"""
		neighbours = self.nodes
		new_chain = None

		# We're only looking for chains longer than ours
		max_length = len(self.chain)

		# Grab and verify the chains from all the nodes in our network
		for node in neighbours:
			response = requests.get(f'http://{node}/chain')

			if response.status_code == 200:
				length = response.json()['length']
				chain = response.json()['chain']

				# Check if the length is longer and the chain is valid
				if length > max_length and self.valid_chain(chain):
					max_length = length
					new_chain = chain

		# Replace our chain if we discovered a new, valid chain longer than ours
		if new_chain:
			self.chain = new_chain
			return True

		return False