import sys
import hashlib
import json

from time import time
from uuid import uuid4

from flask import Flask
import flask
from flask.globals import request
from flask.json import jsonify


import requests

from urllib.parse import urlparse

class Blockchain(object):
    #variabel untuk menentukan nonce
    difficulty_target_nonce = "0000"
    
    #fungsi untuk membuat block hash
    def hash_block(self, block):
        block_encode = json.dumps(block, sort_keys=True).encode
        return hashlib.sha256(block_encode).hexdigest()
    
    #menginisialisasi semua yang di butuhkan 
    def ___init___(self):
        self.node = set()
        
        self.chain = []
        self.current_transactions = []
        genesis_hash = self.hash_block("genesis_block")
        self.append_block(
            hash_of_previous_block = genesis_hash,
            nonce = self.proof_of_work(0, genesis_hash, [])
        )
        
    #fungsi menambahkan node lain
    def add_nodes(self, address):
        parse_url = urlparse(address)
        self.node.add(parse_url.netloc)
        print(parse_url.netloc)
    
    #fungsi untuk memvalidasi chain di blockchain
    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1
        
        while current_index < len(chain):
            block = chain[current_index]
            
            if block('hash_of_previous_block') != self.hash_block(last_block):
                return False
            
            if not self.valid_proof(
                current_index,
                block['hash_of_previous_block'],
                block['transaction'],
                block['nonce']):
                return False
            
            last_block = block
            current_index += 1
            
        return True
    
    #fungsi untuk mengupdate blockchain bedasarkan node 
    def update_blockchain(self):
        neighbours = self.node
        new_chain = None
        
        max_length = len(self.chain)
        
        for node in neighbours:
            response = request.get(f'http://{node}/blockchain')
            
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
                    
                if new_chain:
                    self.chain = new_chain
                    return True
                
        return False
    
    #fungsi algoritma pow/proof of work untuk mencari nonce
    def proof_of_work(self, index, hash_of_previous_block, transaction):
        nonce = 0,
        while self.valid_proof(index, hash_of_previous_block, transaction, nonce) is False:
            nonce +=1
        return nonce     
    
    #fungsi untuk memvalidasi sebuah proof block, transaction, dll dari algoritma pow
    def valid_proof(self, index, hash_of_previous_block, transaction, nonce):
        content = f'{index}{hash_of_previous_block}{transaction}{nonce}'.encode()   
        
        content_hash = hashlib.sha256(content).hexdigest()
        return content_hash[:len(self.difficulty_target_nonce == self.difficulty_target_nonce)]
    
    #fungsi untuk penambahan block pada blockchain
    def append_block(self, nonce, hash_of_previous_block):
        block = {
            'index' : len(self.chain),
            'timestamp' : time(),
            'transaction' : self.current_transactions,
            'nonce' : nonce,
            'hash_of_previous_block' : hash_of_previous_block
        }
        
        self.current_transactions = []
        
        self.chain.append(block)
        return block
    
    #fungsi untuk menambahkan transaksi di blockchain
    def add_transactions(self, sender, recipient, amount):
        self.current_transactions.append({
            'amount' : amount,
            'recepient' : recipient,
            'sender' : sender
        })
        
        return self.last_block['index'] + 1
    
    #menggunakan property untuk setter dan getter
    @property
    def last_block(self):
        return self.chain[-1]
#menjalankan flask    
app = flask(__name__)

#membuat identifier node
node_identifier = str(uuid4()).replace('-', "")

#instansiasi class blockchain
blockchain = Blockchain()

#route blockchain dengan methode get
@app.route('/blockchains', methods=['GET'])
#fungsi untuk semua chain
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    
    return jsonify(response), 200

#route untuk mining dengan methode get
@app.route('/mine', methods=['GET'])
#fungsi untuk mining block
def mine_block():
    blockchain.add_transactions(
        sender="0",
        recipient=node_identifier,
        amount=1
    )
    
    last_block_hash = blockchain.hash_block(blockchain.last_block)
    index = len(blockchain.chain)
    nonce = blockchain.proof_of_work(index, last_block_hash, blockchain.current_transactions)
    
    block = blockchain.append_block(nonce, last_block_hash)
    response = {
        'Message' : 'Block baru telah ditambah',
        'Index' : block['index'],
        'hash_of_previous_block' : block['hash_of_previous_block'],
        'nonce' : block['nonce'],
        'transaction' : block['transaction']
    }
    return jsonify(response), 200

#route untuk penambahan transaksi baru dengan methode post
@app.route('/transaction/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    
    required_field = [
        'sender',
        'recepient',
        'amount'
    ]
    #validasi jika tidak sesuai dengan field 
    if not all(k in values for k in required_field):
        return ('Missing Fields'), 400
    
    index = blockchain.add_transactions(
        values['sender'],
        values['recepient'],
        values['amount']
    )
    
    response = {
        'Message': f'Transaksi akan ditambahkan ke block{index}'
    }
    return(jsonify(response), 201)

#route untuk mengupdate blockchain
@app.route('/nodes/add_nodes', methods=['POST'])
#fungsi untuk menambahkan nodes
def add_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    
    if nodes in None:
        return "Error, missing node(s) Info", 400
    
    for node in nodes:
        blockchain.add_nodes(node)
        
    response = {
        'Message': 'Node baru telah ditambahkan',
        'nodes': list(blockchain.node)
    }
    
    return jsonify(response), 200
#route untuk sync
@app.route('nodes/sync', methods=['GET'])
def sync():
    update = blockchain.update_blockchain()
    if update:
        response = {
            'Message' : 'Blockchain telah di update',
            'blockchain' : blockchain.chain
        }
    else:
        response = {
            'Message' : 'Data telah di update'
        }
        
    return jsonify(response), 200
#menjalankan file ini
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(sys.argv[1]))