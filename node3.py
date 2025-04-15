import multiprocessing
import time
import concurrent.futures
import hashlib
import datetime
import time
import random
from threading import get_ident
from solcx import compile_standard, install_solc
import json
from web3 import Web3
import requests
from flask import Flask, jsonify, request
from uuid import uuid4
from urllib.parse import urlparse

myNodePort = '5002'
myNodeIP = '127.0.0.1'
myNodeAddress = myNodeIP +':'+ myNodePort
my_address = '0xDfC0a95F48B8aADB60cdc5791E2A2765753A7032'
private_key = '0x7707fb73e3634a9eb3d348ab377cee7279a58ea9925f0b6b1aff5d7fda37604c'
contract_Address = '0x4b82a45D0CE8B716E1CF206fbfCdE0639d19145B'
NODES = {'127.0.0.1:5000': 0x0, '127.0.0.1:5001': 0x0, '127.0.0.1:5002':0x0, '127.0.0.1:5003': 0x0}



class Blockchain:
    def __init__(self,blockNo=0,nonce=0,data='',prevhash=0):
        genesis = {
            'Block#': blockNo,
            'Nonce' : nonce,
            'TimeStamp': str(datetime.datetime.fromtimestamp(time.time())),
            'Data' : data,
            'PrevHash': prevhash,
            'Hash' : hashlib.sha256((str(blockNo)+str(nonce)+data+str(prevhash)+str(time.time())).encode()).hexdigest(),
        }

        self.w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
        self.chain=[]
        self.chain.append(genesis)
        self.transactions = []
        self.nodes = NODES
        self.account_id = 0x0
        self.consensusTime=15
        self.averageBlockGenerationTime = 0
        self.hashpower = 9
        self.blockCreation = []
        self.chainUpdated=False


    def create_block(self):
        blockNo = len(self.chain)
        nonce = 0
        timeStamp = str(time.time())
        data = self.transactions
        prevHash = self.chain[-1]['Hash']
        hash = hashlib.sha256((str(blockNo)+str(nonce)+str(data)+str(prevHash)+str(time.time())).encode()).hexdigest()
        block = {
            'Block#': blockNo,
            'Nonce': nonce,
            'TimeStamp': str(timeStamp),
            'Data': data,
            'PrevHash': prevHash,
            'Hash': hash
        }
        self.mineBlock(block)
        if not self.chainUpdated:
            if self.chain[-1]['Block#'] == block['Block#']-1:
                self.chain.append(block)
                Consensus()
        self.transactions = []
        self.chainUpdated=False
        return block


    def mineBlock(self, block):
        hash = str(block['Hash'])
        nonce = block['Nonce']
        while hash[:5] != '00000':
            nonce+=1
            tstamp = time.time()
            hash = str(hashlib.sha256((str(block['Block#'])+str(nonce)+str(block['Data'])+str(block['PrevHash'])+str(tstamp)).encode()).hexdigest())
        block['Hash'] = self.w3.to_hex(hexstr=hash)
        block['Nonce'] = nonce
        block['TimeStamp'] = str(datetime.datetime.fromtimestamp(tstamp))



    def getUnmatchedBlock(self, recvdChain):
        curChain = self.chain
        if len(recvdChain)>len(curChain):
            for i in range(len(curChain)):
                if curChain[i]['Hash'] != recvdChain[i]['Hash']:
                    return i
        return 0
        

    def modifiedConsensus(self, recvdChain, nodeSent):
        unmatchedBlock = self.getUnmatchedBlock(recvdChain) 
        if unmatchedBlock:
            timeStampofLastBlock = datetime.datetime.strptime(recvdChain[-1]['TimeStamp'], "%Y-%m-%d %H:%M:%S.%f").timestamp()
            timeStampofFirstBlock = datetime.datetime.strptime(recvdChain[unmatchedBlock]['TimeStamp'], "%Y-%m-%d %H:%M:%S.%f").timestamp()
            timeGap = timeStampofLastBlock - timeStampofFirstBlock
            print(timeGap)
            if timeGap>self.consensusTime:
                requests.post(f'http://{nodeSent}/cancelChain', json={'Chain':self.chain})
                return {'isValid':False, 'index': unmatchedBlock}
            else:
                return {'isValid': True, 'index': unmatchedBlock} 
        return {'isValid': True, 'index': len(self.chain)} 



    def transact(self, _from='abc', _to='def', _amnt=123):
        transaction = {
            'from': _from,
            'to': _to,
            'amount': _amnt
        }
        self.transactions.append(transaction)


    #Chain Validation
    def validateChain(self, _chain):
        for i in range(1,len(_chain)):
            if _chain[i]['PrevHash'] != _chain[i-1]['Hash']:
                return False
        return True


    #Consensus Algorithm
    def start_Consensus(self):
        network = list(self.nodes.keys())
        for node in network:
            if myNodeAddress in network and node != myNodeAddress:
                response = requests.post(f'http://{node}/consensus', json={'BlockChain': {'Chain': self.chain}, 'Node':myNodeAddress})   


        
def Consensus():
    requests.get(f'http://{myNodeAddress}/startConsensus')

def CreateBlock():
    while 1:
        time.sleep(bc.hashpower)
        requests.get(f'http://{myNodeAddress}/createBlock')
        
def BWA():
    time.sleep(120)
    while 1:
        time.sleep(1)
        requests.get(f'http://{myNodeAddress}/remove')
        time.sleep(180)
        requests.get(f'http://{myNodeAddress}/add')
        Consensus()



def App():
    #Creating a Web App
    app = Flask(__name__)

    @app.route('/getBlockchain', methods = ['GET'])
    def getBlockchain():
        response = {
                "BlockChain": {'Chain': bc.chain},
                "BlockCount": len(bc.chain),
                "HashPower": bc.hashpower
        }
        return jsonify(response), 200
    
    
    # Connecting new nodes
    @app.route('/createBlock', methods = ['GET'])
    def createBlock():
        bc.transact(myNodeAddress,'def',2)
        bc.transact(myNodeAddress,'fgf',3)
        bc.transact(myNodeAddress,'wqw',7)
        block = bc.create_block()
        response = {
            'Block': block,
        }
        return jsonify(response), 200
    

    @app.route('/startConsensus', methods = ['GET'])
    def startConsensus():
        bc.start_Consensus()
        response = {
                "BlockChain": {'Chain': bc.chain},
                "BlockCount": len(bc.chain)
        }
        return jsonify(response), 200
    
    
    @app.route('/consensus', methods = ['POST'])
    def consensus():
        req = request.get_json()
        if len(req) != 0:
            chainReceived = req['BlockChain']['Chain']
            nodeSent = req['Node']
            modified = bc.modifiedConsensus(chainReceived, nodeSent)
            if not modified['isValid']:
                    droppedBlocks = len(bc.chain) - modified['index']
                    if droppedBlocks:
                        requests.post('http://127.0.0.1:5009/blocksdropped', json = {'droppedBlocks': droppedBlocks}) 
            if len(chainReceived)>len(bc.chain) and modified['isValid'] and bc.validateChain(chainReceived): 
                bc.chain = chainReceived
                bc.chainUpdated=True
        response = {
            'BlockChain': 'Consensus applied'
        }
        return jsonify(response), 201
    

    @app.route('/remove', methods = ['GET'])
    def remove():
        if myNodeAddress in bc.nodes:
            bc.nodes.pop(myNodeAddress)
        for node in bc.nodes.keys():
            if node != myNodeAddress:
                requests.post(f'http://{node}/Remove', json={'address': myNodeAddress})
        response={
            'Current-Network': {
                'Network': bc.nodes
            } 
        }
        return jsonify(response), 200
    
    @app.route('/Remove', methods=['POST'])
    def Remove():
        res = request.get_json()
        if len(res) !=0:
            if res['address'] in bc.nodes.keys():
                bc.nodes.pop(res['address'])
        response ={
            'Current-Network': {
                'Network': bc.nodes
            }
        }
        return jsonify(response), 201

    
    @app.route('/add', methods = ['GET'])
    def add():
        bc.nodes[myNodeAddress] = 0x0
        for node in bc.nodes.keys():
            if node != myNodeAddress:
                requests.post(f'http://{node}/addToOthers', json={'address': myNodeAddress})
        response={
            'Current-Network':{
                'Network':bc.nodes
            }
        }
        return jsonify(response), 200
    

    @app.route('/addToOthers', methods=['POST'])
    def addToOthers():
        res = request.get_json()
        if len(res):
            if res['address'] not in bc.nodes.keys():
                bc.nodes[res['address']] = 0x0
        response={
            'Current-Network':{
                'Network':bc.nodes
            }
        }
        return jsonify(response), 201
    

    @app.route('/cancelChain', methods=['POST'])
    def cancelChain():
        res = request.get_json()
        if len(res):
            if len(res['Chain']):
                bc.chain = res['Chain']
        response = {
            'BlockChain': {'Chain': bc.chain},
            'BlockCount': len(bc.chain)
        } 
        return jsonify(response), 201
    

    # Running the app
    app.run(host = '0.0.0.0', port = myNodePort)


bc = Blockchain()
if __name__ == "__main__":
    blockCreationProcess = multiprocessing.Process(target=CreateBlock)
    appProcess = multiprocessing.Process(target=App)
    #consensus_process.start()
    blockCreationProcess.start()
    #BWAProcess.start()
    appProcess.start()
    #consensus_process.join()
    blockCreationProcess.join()
    appProcess.join()