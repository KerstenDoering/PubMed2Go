#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
    Copyright (c) 2014, Kersten Doering <kersten.doering@gmail.com>
"""

# Kersten Doering 27.01.2015

import psycopg2
from psycopg2 import extras
import time
from optparse import OptionParser

# read PubMed-IDs
def get_pmids(infile):
    # input file
    f = open(infile,"r")
    pmids = []
    # one line equals one PubMed-ID
    for line in f:
        pmids.append(line.strip())
    f.close()
    # return list of PubMed-IDs
    return pmids

# join abstract title and text for a given PubMed-ID "pmid" and return the triple as a list [PubMed-ID, title, text]
def get_title_text(pmid):
    stmt = """
    SELECT 
        pmid,
        article_title as title,
        abstract_text as abstract
    FROM 
        pubmed.tbl_medline_citation
            LEFT OUTER JOIN
        pubmed.tbl_abstract
                ON pmid = fk_pmid
    WHERE
        pmid = '"""+pmid+"""'
    ;
    """

    cursor.execute(stmt)
    output = cursor.fetchone()
    return output

# generate BioC XML document format for the triple [PubMed-ID, title, text]
def get_BioC_format(triple):
    #open document tag
    f_text = "\t<document>\n"

    #add PubMed-ID
    f_text += "\t\t<id>" + str(triple[0]) + "</id>\n"

    #add title passage
    f_text += "\t\t<passage>\n"
    #add infon
    f_text += "\t\t\t<infon key=\"type\">title</infon>\n"
    #add offset
    f_text += "\t\t\t<offset>0</offset>\n"
    #add title
    f_text += "\t\t\t<text>" + triple[1].strip() + "</text>\n"
    #close passage tag
    f_text += "\t\t</passage>\n"

    #some PubMed-IDs do not have an abstract text
    if triple[2]:
        #add text passage
        f_text += "\t\t<passage>\n"
        #add infon
        f_text += "\t\t\t<infon key=\"type\">abstract</infon>\n"
        #add offset
        f_text += "\t\t\t<offset>" + str(len(triple[1])) + "</offset>\n"
        #add text, some texts contain line breaks
        f_text += "\t\t\t<text>" + triple[2].replace("\n"," ").strip() + "</text>\n"
        #close passage tag
        f_text += "\t\t</passage>\n"

    #close document tag
    f_text += "\t</document>\n"
    return f_text

if __name__=="__main__":
    parser = OptionParser()
    parser.add_option("-i", "--infile", dest="i", help='name of the input file containing all PubMed-IDs', default="pmid_list.txt")
    parser.add_option("-o", "--outfile", dest="o", help='name of the output file containing all abstract titles and texts in BioC format', default="text_BioC.xml")
    parser.add_option("-d", "--database", dest="d", help='name of the database to connect to', default="pancreatic_cancer_db")
    
    (options, args) = parser.parse_args()
    
    # save file names in an extra variable
    infile = options.i
    outfile = options.o

    # settings for psql connection
    postgres_user           = "parser"
    postgres_password       = "parser"
    postgres_host           = "localhost" 
    postgres_port           = "5432"
    postgres_db = options.d

    # connect to database
    connection = psycopg2.connect("dbname='"+postgres_db+"' user='"+postgres_user+"' host='"+postgres_host+"' password='"+postgres_password+"' port='"+postgres_port+"'")
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # get PubMed-IDs
    pmids = get_pmids(infile)

    # updloaded test case for PubMed XML document with 4 PubMed-IDs from PubMed2Go documentation (pancreatic cancer): pmids[0] - first list element, "1019833" - no abstract text, "10064755" - line breaks, "10063743" - standard example
#    pmids = [pmids[0],"1019833","10064755","10063743"]
#    print "test case - processed PubMed-IDs:", pmids

    # write output file beginning
    f = open(outfile,"w")
    f.write("<collection>\n")
    f.write("\t<source>PubMed</source>\n")
    f.write("\t<date>" + time.strftime("%Y-%B-%d") + "</date>\n")
    f.write("\t<key>Explanation.key</key>\n")
    # get [PubMed-ID, title, text] and generate BioC XML format to write to file
    for pmid in pmids:
        pmid_title_text = get_title_text(pmid)
#        print pmid_title_text
        formatted_text = get_BioC_format(pmid_title_text)
        f.write(formatted_text)
    # write output file ending
    f.write("</collection>")
    f.close()

    # disconnect from database
    cursor.close()
    connection.close()
