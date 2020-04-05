import argparse
import zmq
import netifaces
from string import ascii_letters
import random
import hashlib
from os import listdir, remove
from os.path import isfile, join
from abstractServer import Server


class InitialServer(Server):
    """
    Lo unico que cambia entre el servidor normal y el inicial es que la llave 
    del inicial es la minima y la maxima al mismo tiempo, y que su sucesor y 
    predecesor es el mismo
    """

    def __init__(self, ip, port, folder_name):
        super().__init__(ip, port, folder_name)
        self.sucessor = self.ip + ":" + self.port
        self.predecessor = self.sucessor
        self.min_key = self.max_key

def crateParserConsole():
    parser = argparse.ArgumentParser()
    parser.add_argument("ip", type=str)
    parser.add_argument("port", type=str)
    parser.add_argument("folder", type=str)
    return parser.parse_args()


if __name__ == "__main__":
    args = crateParserConsole()
    server = InitialServer(args.ip, args.port, args.folder)
    server.listen()
