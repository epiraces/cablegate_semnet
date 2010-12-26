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

import logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)-8s %(message)s")

import os
from os.path import join

import re
import nltk
from BeautifulSoup import BeautifulSoup, SoupStrainer

class CableImporter(object):
  
    """
    Reads and parses all available cables and updates the mongodb
    usage : mirror = CableGateMirror(wikileaksdb, 'data/cablegate.wikileaks.org')
    """
    
    file_regex = re.compile("\.html$")
    
    counts = {
      'files_not_processed':0
    }
  
    def __init__(self, db, data_directory, overwrite=False):
        self.data_directory = join(data_directory, "cable")
        self.db = db
        self.cable_id = []
        self.tablesoup = SoupStrainer("table", attrs={ "class" : "cable" })
        self.contentsoup = SoupStrainer("pre")
        self.walk_archive(overwrite)
    
    def walk_archive(self, overwrite):
        """
        Walks the archive directory
        """
        try:
            for root, dirs, files in os.walk(self.data_directory):
                for name in files:
                    if self.file_regex.search(name) is None: continue
                    path = join( root, name )
                    self.read_file(path,overwrite)
        except OSError, oserr:
            logging.error("%s"%oserr)
  
    def read_file(self, path, overwrite):
        """
        Reads the cable file
        """
        logging.info('CableImporter.read_file')
        try:
            file = open(path)
        except OSError:
            logging.warning('Processor.read_file : CANNOT OPEN FILE %s, skipping...s'%path)
            self.counts['files_not_processed'] += 1
            return
        self.extract_content(file.read(), overwrite)
    
    def extract_content(self, raw, overwrite):
        """
        Cable Content extractor
        """
        tablesoup = BeautifulSoup(raw, parseOnlyThese = self.tablesoup)
        cable_table = tablesoup.find("table")
        cable_id = cable_table.findAll('tr')[1].findAll('td')[0].contents[1].contents[0]

        if overwrite is False and self.db.cables.find_one( {'_id': cable_id} ) is not None:   
            logging.info('CABLE ALREADY EXISTS : SKIPPING')
            self.cable_id += [cable_id]
            self.print_counts()
            return
        try:
            #import pdb; pdb.set_trace()
            contentsoup = BeautifulSoup(raw, parseOnlyThese = self.contentsoup)
            cablecontent = contentsoup.findAll("pre")[1].contents[1].contents[0]
            del raw

            cable = {
                # auto index
                '_id' : cable_id,
                'id' : cable_id,
                'label' : cable_id,
                'date_time' : cable_table.findAll('tr')[1].findAll('td')[1].contents[1].contents[0],
                'classification' : cable_table.findAll('tr')[1].findAll('td')[3].contents[1].contents[0],
                'origin' : cable_table.findAll('tr')[1].findAll('td')[4].contents[1].contents[0],
                'content' : unicode( nltk.clean_html( str(cablecontent) ), encoding="utf_8", errors="replace" ),
                'edges': {
                    'NGram': {},
                    'Document': {}
                }
            }
            # insert or auto overwrites existing cable (indexed by '_id')
            self.db.cables.save(cable)
            self.cable_id += [cable_id]
            self.print_counts()
        except Exception, exc:
            logging.warning("error importing cable : %s"%exc)
            self.counts['files_not_processed'] += 1
            self.print_counts()
            
    
    def print_counts(self):
        logging.info("cables processed = %d, cables impossible to process = %d"%(len(self.cable_id), self.counts['files_not_processed']))