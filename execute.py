# -*- coding: utf-8 -*-
#  Copyright (C) 2010 elishowk@nonutc.fr
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from optparse import OptionParser

import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)-8s %(message)s")

from mongodbhandler import CablegateDatabase
from cableimporter import CableImporter
from cableindexer import CableIndexer
from cablenetwork import CoocNetwork

import yaml

def get_parser():
    parser = OptionParser()
    parser.add_option("-e", "--execute", dest="execute", help="execution action", metavar="FILE")
    parser.add_option("-a", "--archive", dest="archive", help="cablegate archive path", metavar="FILE")
    parser.add_option("-o", "--occurrences", dest="minoccs", help="minimum keyphrases' occurrences", metavar="int")
    parser.add_option("-c", "--config", dest="config", help="config yaml file path", metavar="FILE")
    return parser

if __name__ == "__main__":
    parser = get_parser()
    (options, args) = parser.parse_args()
    print options, args
    
    config = yaml.safe_load( file( options.config, 'rU' ) )
   
    mongoconnection = CablegateDatabase("localhost")
    if options.execute == 'import':
        importer = CableImporter( mongoconnection["cablegate"], options.archive )
    if options.execute == 'index':
        extractor = CableIndexer(mongoconnection["cablegate"], config)
    if options.execute == 'graph':
        extractor = CoocGraph(mongoconnection["cablegate"], config, int(options.minoccs))
    if options.execute == 'print':
        for ngram in mongoconnection["cablegate"].ngrams.find().limit(10):
            logging.debug( ngram )
        for doc in mongoconnection["cablegate"].cables.find().limit(2):
            logging.debug( doc )